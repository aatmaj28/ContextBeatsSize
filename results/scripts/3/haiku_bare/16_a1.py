import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, noise

random.seed(7)

# ---------- Clear scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
collection = scene.collection


def set_input(bsdf, names, value):
    """Set the first matching input name on a Principled BSDF node."""
    for n in names:
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = value
            return True
    return False


def make_material(name, color, roughness, transmission=0.0, ior=1.45,
                  alpha=1.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, ["Base Color"], (color[0], color[1], color[2], 1.0))
    set_input(bsdf, ["Roughness"], roughness)
    set_input(bsdf, ["IOR"], ior)
    set_input(bsdf, ["Transmission Weight", "Transmission"], transmission)
    set_input(bsdf, ["Alpha"], alpha)
    if emission is not None:
        set_input(bsdf, ["Emission Color", "Emission"],
                  (emission[0], emission[1], emission[2], 1.0))
        set_input(bsdf, ["Emission Strength"], emission_strength)
    return mat


def link_object(obj):
    collection.objects.link(obj)
    return obj


# ---------- Dark rock ----------
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)

rock_offset = Vector((3.1, 1.7, -2.4))
for v in bm.verts:
    p = v.co * 1.3 + rock_offset
    n1 = noise.noise(p)
    n2 = noise.noise(p * 2.7 + Vector((5.0, 2.0, 1.0)))
    displacement = 1.0 + 0.30 * n1 + 0.08 * n2
    co = v.co * displacement
    co.x *= 1.35
    co.y *= 1.15
    co.z *= 0.75
    # Flatten the underside so the rock sits on a ground plane
    if co.z < -0.35:
        co.z = -0.35 + (co.z + 0.35) * 0.35
    v.co = co

bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
rock_mesh = bpy.data.meshes.new("RockMesh")
bm.to_mesh(rock_mesh)
bm.free()
for p in rock_mesh.polygons:
    p.use_smooth = True
rock_obj = link_object(bpy.data.objects.new("DarkRock", rock_mesh))
rock_mesh.materials.append(
    make_material("DarkRockMat", (0.035, 0.032, 0.036), roughness=0.85))

# ---------- Crystal geometry ----------
def build_crystal_mesh(name, length, radius, sides=6):
    bm = bmesh.new()
    bottom = []
    top = []
    for i in range(sides):
        a = 2.0 * math.pi * i / sides
        bottom.append(bm.verts.new((radius * math.cos(a), radius * math.sin(a), 0.0)))
    for i in range(sides):
        a = 2.0 * math.pi * i / sides
        r_top = radius * 0.88
        top.append(bm.verts.new((r_top * math.cos(a), r_top * math.sin(a), length * 0.78)))
    apex = bm.verts.new((0.0, 0.0, length))

    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
        bm.faces.new((top[i], top[j], apex))
    bm.faces.new(list(reversed(bottom)))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False  # keep facets crisp
    return me


crystal_mat = make_material(
    "AmethystMat",
    color=(0.55, 0.12, 0.85),
    roughness=0.03,
    transmission=1.0,
    ior=1.55,
    alpha=0.6,
    emission=(0.35, 0.05, 0.6),
    emission_strength=0.15,
)

# ---------- Place crystal cluster on rock top ----------
crystal_count = 16
placed = 0
attempts = 0
while placed < crystal_count and attempts < 2000:
    attempts += 1
    x = random.uniform(-1.4, 1.4) * 0.6
    y = random.uniform(-1.1, 1.1) * 0.6
    origin = Vector((x, y, 6.0))
    hit, loc, normal, _ = rock_obj.ray_cast(origin, Vector((0.0, 0.0, -1.0)))
    if not hit or normal.z < 0.25:
        continue

    # Size: larger near the cluster centre, smaller at the edges
    centre_factor = max(0.0, 1.0 - math.hypot(x, y) / 1.0)
    length = random.uniform(0.35, 0.7) + 0.35 * centre_factor
    radius = random.uniform(0.08, 0.13) + 0.04 * centre_factor

    me = build_crystal_mesh(f"Crystal_{placed}", length, radius)
    obj = link_object(bpy.data.objects.new(f"Crystal_{placed}", me))
    me.materials.append(crystal_mat)

    # Lean outward from the cluster centre plus random jitter
    lean_dir = (normal + Vector((random.uniform(-0.35, 0.35),
                                 random.uniform(-0.35, 0.35),
                                 0.0))).normalized()
    # Bias tilt away from cluster centre
    outward = Vector((x, y, 0.0))
    if outward.length > 1e-4:
        lean_dir = (lean_dir + outward.normalized() * 0.25 * centre_factor).normalized()

    rot = Vector((0.0, 0.0, 1.0)).rotation_difference(lean_dir).to_matrix().to_4x4()
    spin = Matrix.Rotation(random.uniform(0, 2 * math.pi), 4, 'Z')
    sink = loc - lean_dir * (length * 0.12)
    obj.matrix_world = Matrix.Translation(sink) @ rot @ spin

    placed += 1

# A few small shards lying around the base
for k in range(5):
    attempts = 0
    while attempts < 500:
        attempts += 1
        x = random.uniform(-1.2, 1.2)
        y = random.uniform(-1.0, 1.0)
        hit, loc, normal, _ = rock_obj.ray_cast(Vector((x, y, 6.0)), Vector((0, 0, -1)))
        if hit and normal.z > 0.3:
            break
    else:
        continue
    length = random.uniform(0.15, 0.3)
    me = build_crystal_mesh(f"Shard_{k}", length, 0.05)
    obj = link_object(bpy.data.objects.new(f"Shard_{k}", me))
    me.materials.append(crystal_mat)
    tilt = Vector((random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), 1.0)).normalized()
    rot = Vector((0.0, 0.0, 1.0)).rotation_difference(tilt).to_matrix().to_4x4()
    obj.matrix_world = Matrix.Translation(loc - normal * 0.02) @ rot

# ---------- Lighting ----------
def make_light(name, light_type, location, energy, color, size=None, target=None):
    ld = bpy.data.lights.new(name=name, type=light_type)
    ld.energy = energy
    ld.color = color
    if size is not None and light_type == 'AREA':
        ld.shape = 'RECTANGLE'
        ld.size = size[0]
        ld.size_y = size[1]
    lo = link_object(bpy.data.objects.new(name, ld))
    lo.location = location
    if target is not None:
        direction = (Vector(target) - Vector(location)).normalized()
        lo.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return lo


make_light("KeyLight", 'AREA', (3.0, -3.0, 4.0), 400.0, (1.0, 0.95, 0.9),
           size=(2.5, 2.5), target=(0.0, 0.0, 0.3))
make_light("RimLight", 'AREA', (-3.5, 2.5, 2.5), 250.0, (0.75, 0.45, 1.0),
           size=(2.0, 2.0), target=(0.0, 0.0, 0.4))
make_light("FillLight", 'POINT', (2.0, 3.5, 0.8), 40.0, (0.6, 0.6, 0.8))

# ---------- World ----------
world = bpy.data.worlds.new("DarkWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.008, 0.007, 0.01, 1.0)
    bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 55
cam_obj = link_object(bpy.data.objects.new("MainCamera", cam_data))
cam_location = Vector((3.0, -4.2, 2.3))
look_at = Vector((0.0, 0.0, 0.35))
cam_obj.location = cam_location
direction = (look_at - cam_location).normalized()
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- Timeline ----------
scene.frame_start = 1
scene.frame_end = 1
