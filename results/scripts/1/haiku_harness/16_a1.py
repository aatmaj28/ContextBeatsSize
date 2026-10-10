import bpy
import math
import random
from mathutils import Vector, Euler, noise

random.seed(7)

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

scene = bpy.context.scene
collection = scene.collection


def link(obj):
    collection.objects.link(obj)
    return obj


def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


# ---------- Materials ----------
def make_rock_material():
    mat = bpy.data.materials.new("DarkRock")
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", (0.035, 0.032, 0.035, 1.0))
    set_input(bsdf, "Roughness", 0.92)
    set_input(bsdf, "Specular IOR Level", 0.3)
    return mat


def make_crystal_material():
    mat = bpy.data.materials.new("PurpleCrystal")
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", (0.55, 0.12, 0.85, 1.0))
    set_input(bsdf, "Roughness", 0.04)
    set_input(bsdf, "IOR", 1.52)
    set_input(bsdf, "Transmission Weight", 1.0)
    set_input(bsdf, "Specular IOR Level", 0.6)
    set_input(bsdf, "Emission Color", (0.6, 0.2, 1.0, 1.0))
    set_input(bsdf, "Emission Strength", 0.25)
    return mat


rock_mat = make_rock_material()
crystal_mat = make_crystal_material()


# ---------- Rock ----------
def make_rock():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=(0, 0, 0))
    rock = bpy.context.active_object
    rock.name = "Rock"
    rock.scale = (1.6, 1.6, 0.9)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    mesh = rock.data
    for v in mesh.vertices:
        co = v.co.copy()
        n = noise.noise(co * 1.6)
        n2 = noise.noise(co * 4.0 + Vector((5.2, 1.3, 7.7)))
        factor = 1.0 + 0.18 * n + 0.06 * n2
        v.co = co * factor
        
    mesh.update()
    for poly in mesh.polygons:
        poly.use_smooth = True
    rock.data.materials.append(rock_mat)
    return link(rock)


rock = make_rock()


# ---------- Crystal geometry ----------
def make_crystal_mesh(name, r, h, sides=6):
    verts = []
    faces = []

    # Base ring (embedded slightly below surface)
    base_z = -0.12 * h
    for i in range(sides):
        a = 2 * math.pi * i / sides
        verts.append((r * math.cos(a), r * math.sin(a), base_z))
    # Top ring
    for i in range(sides):
        a = 2 * math.pi * i / sides
        verts.append((r * 0.9 * math.cos(a), r * 0.9 * math.sin(a), h))
    # Apex
    tip_r = r * 0.9
    apex_idx = len(verts)
    verts.append((0.0, 0.0, h + tip_r * 1.6))

    # Side faces
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((i, j, sides + j, sides + i))
    # Pyramid tip
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((sides + i, sides + j, apex_idx))
    # Bottom
    faces.append(tuple(range(sides)))

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for poly in mesh.polygons:
        poly.use_smooth = False
    mesh.materials.append(crystal_mat)

    obj = bpy.data.objects.new(name, mesh)
    return link(obj)


def place_crystal(obj, base_point, normal, tilt_strength):
    up = Vector(normal).normalized()
    align = up.to_track_quat('Z', 'Y')
    tilt = Euler((
        random.uniform(-tilt_strength, tilt_strength),
        random.uniform(-tilt_strength, tilt_strength),
        random.uniform(0, 2 * math.pi),
    )).to_quaternion()
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = align @ tilt
    obj.location = base_point


# ---------- Crystal cluster ----------
crystals = []
cluster_count = 15
for i in range(cluster_count):
    # Pick a direction biased toward the top of the rock
    while True:
        d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.2, 1.0)))
        if d.length <= 1.0 and d.length > 0.2:
            break
    d = d.normalized()
    # Surface point and normal of the squashed ellipsoid rock
    sx, sy, sz = 1.6, 1.6, 0.9
    surf = Vector((d.x * sx, d.y * sy, d.z * sz))
    normal = Vector((d.x / sx, d.y / sy, d.z / sz)).normalized()
    base_point = surf - normal * 0.05

    r = random.uniform(0.07, 0.16)
    h = random.uniform(0.35, 0.8) * (1.0 - 0.4 * d.z * 0.0 + 0.2 * (1 - d.z))
    # Leaning crystals spread outward from cluster center
    obj = make_crystal(f"Crystal_{i}", r, h) if False else make_crystal_mesh(f"Crystal_{i}", r, h)
    place_crystal(obj, base_point, normal, tilt_strength=0.35)
    crystals.append(obj)

# A few larger central crystals for the focal point
for i in range(4):
    angle = 2 * math.pi * i / 4 + random.uniform(-0.3, 0.3)
    spread = random.uniform(0.0, 0.35)
    x = spread * math.cos(angle)
    y = spread * math.sin(angle)
    z_surf = 0.9 * math.sqrt(max(0.0, 1.0 - (x / 1.6) ** 2 - (y / 1.6) ** 2)) + 0.02
    base_point = Vector((x, y, z_surf - 0.05))
    normal = Vector((x / 1.6 ** 2, y / 1.6 ** 2, z_surf / 0.81)).normalized()
    obj = make_crystal_mesh(f"CoreCrystal_{i}", random.uniform(0.14, 0.2), random.uniform(0.9, 1.25))
    place_crystal(obj, base_point, normal, tilt_strength=0.12)
    crystals.append(obj)


# ---------- Lighting ----------
# Key light
key_data = bpy.data.lights.new(name="KeyLight", type='AREA')
key_data.energy = 900
key_data.size = 3.0
key_data.color = (1.0, 0.97, 0.94)
key = link(bpy.data.objects.new("KeyLight", key_data))
key.location = (3.0, -3.0, 4.0)
key.rotation_euler = Euler((math.radians(55), 0, math.radians(45)))

# Purple rim light
rim_data = bpy.data.lights.new(name="RimLight", type='POINT')
rim_data.energy = 180
rim_data.color = (0.7, 0.35, 1.0)
rim = link(bpy.data.objects.new("RimLight", rim_data))
rim.location = (-2.5, 2.5, 1.8)

# Soft fill
fill_data = bpy.data.lights.new(name="FillLight", type='AREA')
fill_data.energy = 120
fill_data.size = 4.0
fill_data.color = (0.8, 0.85, 1.0)
fill = link(bpy.data.objects.new("FillLight", fill_data))
fill.location = (-4.0, -2.0, 2.0)
fill.rotation_euler = Euler((math.radians(70), 0, math.radians(-60)))


# ---------- World ----------
world = scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    set_input(bg, "Color", (0.012, 0.010, 0.016, 1.0))
    set_input(bg, "Strength", 1.0)


# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 65
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = 5.2
cam_data.dof.aperture_fstop = 4.0
cam = link(bpy.data.objects.new("Camera", cam_data))
cam.location = (3.4, -4.6, 2.4)
target = Vector((0.0, 0.0, 0.7))
direction = target - cam.location
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = direction.to_track_quat('-Z', 'Y')
scene.camera = cam


# ---------- Render settings (no render is started) ----------
scene.render.engine = 'CYCLES'
try:
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
except Exception:
    pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
