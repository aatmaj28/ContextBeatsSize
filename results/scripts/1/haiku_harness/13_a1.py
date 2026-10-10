import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

random.seed(7)

# ---------------------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene


def link(obj):
    scene.collection.objects.link(obj)
    return obj


def make_mat(name, rgba, roughness, metallic=0.0):
    mat = bpy.data.materials.new(name)  # node tree is created automatically
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
mat_dough = make_mat("Dough", (0.46, 0.26, 0.11, 1.0), roughness=0.38)
mat_frost = make_mat("PinkFrosting", (0.98, 0.45, 0.66, 1.0), roughness=0.18)
mat_plate = make_mat("WhitePlate", (0.93, 0.93, 0.91, 1.0), roughness=0.12)

sprinkle_colors = [
    (0.90, 0.08, 0.12, 1.0),  # red
    (1.00, 0.85, 0.10, 1.0),  # yellow
    (0.10, 0.40, 0.95, 1.0),  # blue
    (0.20, 0.80, 0.30, 1.0),  # green
    (0.60, 0.20, 0.90, 1.0),  # purple
    (0.97, 0.97, 0.95, 1.0),  # white
]
sprinkle_mats = [make_mat(f"Sprinkle_{i}", c, roughness=0.3)
                 for i, c in enumerate(sprinkle_colors)]

# ---------------------------------------------------------------------------
# Torus geometry helpers
# ---------------------------------------------------------------------------
NU, NV = 128, 48
R_MAJOR, R_MINOR = 1.0, 0.4
OFFSET = Vector((0.0, 0.0, 0.43))  # sits on the plate top


def torus_point(u, v):
    cu, su = math.cos(u), math.sin(u)
    cv, sv = math.cos(v), math.sin(v)
    normal = Vector((cv * cu, cv * su, sv))
    pos = Vector(((R_MAJOR + R_MINOR * cv) * cu,
                  (R_MAJOR + R_MINOR * cv) * su,
                  R_MINOR * sv))
    return pos, normal


def frost_disp(u, v):
    """Outward displacement for the frosting layer (wavy, dripping edge)."""
    sv = math.sin(v)
    edge = -0.25 + 0.12 * math.sin(9 * u + 0.5) + 0.06 * math.sin(17 * u + 1.3)
    t = min(max((sv - edge) / 0.25, 0.0), 1.0)
    t = t * t * (3.0 - 2.0 * t)
    thick = 0.055 * (0.7 + 0.3 * math.sin(13 * u + 0.4))
    return -0.004 + (thick + 0.004) * t


def make_grid(disp_fn):
    verts = []
    for i in range(NU):
        u = 2.0 * math.pi * i / NU
        for j in range(NV):
            v = 2.0 * math.pi * j / NV
            pos, n = torus_point(u, v)
            verts.append(pos + n * disp_fn(u, v))
    faces = []
    for i in range(NU):
        i2 = (i + 1) % NU
        for j in range(NV):
            j2 = (j + 1) % NV
            a = i * NV + j
            b = i2 * NV + j
            c = i2 * NV + j2
            d = i * NV + j2
            faces.append((a, b, c, d))
    return verts, faces


def mesh_object(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    return link(obj)


# ---------------------------------------------------------------------------
# Donut body and frosting
# ---------------------------------------------------------------------------
dv, df = make_grid(lambda u, v: 0.0)
donut = mesh_object("Donut", dv, df, mat_dough)
donut.location = OFFSET

fv, ff = make_grid(frost_disp)
frosting = mesh_object("Frosting", fv, ff, mat_frost)
frosting.location = OFFSET

# ---------------------------------------------------------------------------
# Plate
# ---------------------------------------------------------------------------
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=96,
                      radius1=2.2, radius2=2.2, depth=0.08)
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.03, segments=3,
                affect='EDGES')
plate_me = bpy.data.meshes.new("Plate")
bm.to_mesh(plate_me)
bm.free()
for p in plate_me.polygons:
    p.use_smooth = True
plate_me.materials.append(mat_plate)
plate = bpy.data.objects.new("Plate", plate_me)
link(plate)

# ---------------------------------------------------------------------------
# Sprinkles (short capsule-like cylinders lying on the frosting)
# ---------------------------------------------------------------------------
sprinkle_meshes = []
for i, mat in enumerate(sprinkle_mats):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=10,
                          radius1=0.011, radius2=0.011, depth=0.07)
    me = bpy.data.meshes.new(f"SprinkleMesh_{i}")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    sprinkle_meshes.append(me)

placed = []
attempts = 0
target_count = 170
while len(placed) < target_count and attempts < 6000:
    attempts += 1
    u = random.uniform(0.0, 2.0 * math.pi)
    v = math.asin(random.uniform(0.05, 0.98))
    if random.random() < 0.5:
        v = math.pi - v
    d = frost_disp(u, v)
    if d < 0.03:
        continue
    pos, n = torus_point(u, v)
    surface = pos + n * d

    # Reject sprinkles that would overlap others
    if any((surface - q).length < 0.09 for q in placed):
        continue
    placed.append(surface)

    # Random tangent direction so the sprinkle lies on the surface
    rand_dir = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
    tangent = n.cross(rand_dir)
    if tangent.length < 1e-6:
        continue
    tangent.normalize()

    rot = Vector((0.0, 0.0, 1.0)).rotation_difference(tangent).to_matrix().to_4x4()
    spin = Matrix.Rotation(random.uniform(0.0, 2.0 * math.pi), 4, 'Z')
    center = surface + n * 0.006
    mat_world = Matrix.Translation(OFFSET + center) @ rot @ spin

    color_idx = random.randrange(len(sprinkle_meshes))
    s_obj = bpy.data.objects.new(f"Sprinkle_{len(placed)}", sprinkle_meshes[color_idx])
    s_obj.matrix_world = mat_world
    link(s_obj)

# ---------------------------------------------------------------------------
# World (soft studio backdrop)
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("StudioWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.85, 0.88, 0.92, 1.0)
bg.inputs["Strength"].default_value = 0.5


# ---------------------------------------------------------------------------
# Lights
# ---------------------------------------------------------------------------
def aim(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def area_light(name, location, energy, size, color, target):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    obj.location = Vector(location)
    link(obj)
    aim(obj, target)
    return obj


target = Vector((0.0, 0.0, 0.45))
area_light("KeyLight", (-3.0, -2.5, 4.5), 900.0, 3.0, (1.0, 0.97, 0.92), target)
area_light("FillLight", (3.5, -1.5, 2.5), 250.0, 4.0, (0.9, 0.95, 1.0), target)
area_light("RimLight", (1.0, 3.5, 3.5), 600.0, 2.5, (1.0, 1.0, 1.0), target)

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 75.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
cam_obj.location = Vector((3.4, -3.8, 3.1))
link(cam_obj)
aim(cam_obj, Vector((0.0, 0.0, 0.42)))
scene.camera = cam_obj

# ---------------------------------------------------------------------------
# Render settings (not rendering, just framing/size)
# ---------------------------------------------------------------------------
scene.render.resolution_x = 1080
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
