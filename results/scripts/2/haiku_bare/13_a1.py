import bpy
import bmesh
import math
import random
from mathutils import Vector, Euler

random.seed(7)

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene


# ---------- Helpers ----------
def make_material(name, color, roughness=0.4, specular=0.5, clearcoat=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = specular
    if clearcoat > 0:
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = clearcoat
            bsdf.inputs["Coat Roughness"].default_value = 0.05
        elif "Clearcoat" in bsdf.inputs:
            bsdf.inputs["Clearcoat"].default_value = clearcoat
            bsdf.inputs["Clearcoat Roughness"].default_value = 0.05
    return mat


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def link(obj):
    scene.collection.objects.link(obj)
    return obj


# ---------- Materials ----------
dough_mat = make_material("Dough", (0.78, 0.48, 0.22), roughness=0.45, specular=0.4)
frosting_mat = make_material("PinkFrosting", (1.0, 0.45, 0.68), roughness=0.12,
                             specular=0.6, clearcoat=0.8)
plate_mat = make_material("WhitePlate", (0.92, 0.92, 0.9), roughness=0.18, specular=0.5,
                          clearcoat=0.3)

sprinkle_colors = [
    (1.0, 0.85, 0.1),
    (0.2, 0.7, 1.0),
    (0.4, 1.0, 0.3),
    (0.7, 0.2, 1.0),
    (1.0, 0.25, 0.2),
    (1.0, 1.0, 1.0),
]
sprinkle_mats = [make_material(f"Sprinkle_{i}", c, roughness=0.25, specular=0.5)
                 for i, c in enumerate(sprinkle_colors)]

# ---------- Plate ----------
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=2.6, depth=0.12,
                                    location=(0, 0, -0.06))
plate = bpy.context.active_object
plate.name = "Plate"
plate.data.materials.append(plate_mat)
smooth(plate)
bpy.ops.object.modifier_add(type='BEVEL') if False else None
plate.data.update()

# ---------- Dough ring ----------
R = 1.0      # major radius
r_dough = 0.40
zc_dough = 0.40
bpy.ops.mesh.primitive_torus_add(major_segments=96, minor_segments=40,
                                 major_radius=R, minor_radius=r_dough,
                                 location=(0, 0, zc_dough))
dough = bpy.context.active_object
dough.name = "DonutDough"
dough.data.materials.append(dough_mat)
smooth(dough)

# ---------- Frosting glaze (flattened torus sitting on top) ----------
r_frost = 0.44
zs_frost = 0.50
zc_frost = 0.60
bpy.ops.mesh.primitive_torus_add(major_segments=96, minor_segments=40,
                                 major_radius=R, minor_radius=r_frost,
                                 location=(0, 0, zc_frost))
frost = bpy.context.active_object
frost.name = "PinkFrosting"
frost.scale = (1.0, 1.0, zs_frost)
frost.data.materials.append(frosting_mat)
smooth(frost)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# ---------- Sprinkles ----------
# Build one mesh per color
sprinkle_meshes = []
for i in range(len(sprinkle_colors)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=10,
                          radius1=0.022, radius2=0.022, depth=0.13)
    me = bpy.data.meshes.new(f"SprinkleMesh_{i}")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(sprinkle_mats[i])
    for p in me.polygons:
        p.use_smooth = True
    sprinkle_meshes.append(me)

count = 160
min_v = math.asin(0.15)
max_v = math.pi - math.asin(0.15)

for n in range(count):
    u = random.uniform(0, 2 * math.pi)
    v = random.uniform(min_v, max_v)

    ring = R + r_frost * math.cos(v)
    x = ring * math.cos(u)
    y = ring * math.sin(u)
    z = zc_frost + r_frost * zs_frost * math.sin(v)

    # Approximate outward normal on the glaze
    nx = math.cos(v) * math.cos(u)
    ny = math.cos(v) * math.sin(u)
    nz = math.sin(v) / zs_frost
    normal = Vector((nx, ny, nz)).normalized()

    # Push slightly out so sprinkles sit on the glaze
    pos = Vector((x, y, z)) + normal * 0.02

    # Random tangent direction for the sprinkle's long axis
    rand_vec = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
    tangent = normal.cross(rand_vec)
    if tangent.length < 1e-5:
        tangent = Vector((1, 0, 0))
    tangent.normalize()

    # Partially embed sprinkles, tilt a bit for variety
    tangent = (tangent + normal * random.uniform(-0.15, 0.15)).normalized()

    ci = random.randrange(len(sprinkle_colors))
    obj = bpy.data.objects.new(f"Sprinkle_{n:03d}", sprinkle_meshes[ci])
    obj.location = pos
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = tangent.to_track_quat('Z', 'Y')
    obj.scale = (1.0, 1.0, random.uniform(0.8, 1.2))
    link(obj)

# ---------- Link main objects ----------
link(plate)
link(dough)
link(frost)

# ---------- World ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.04, 0.045, 0.05, 1.0)
bg.inputs["Strength"].default_value = 0.6
scene.world = world

# ---------- Lights ----------
bpy.ops.object.light_add(type='AREA', location=(3.0, -3.0, 4.5))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 900
key.data.size = 3.0
key.data.color = (1.0, 0.96, 0.92)
key.rotation_euler = Euler((math.radians(55), 0, math.radians(45)), 'XYZ')

bpy.ops.object.light_add(type='AREA', location=(-3.5, 2.5, 2.5))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 250
fill.data.size = 4.0
fill.data.color = (0.85, 0.92, 1.0)
fill.rotation_euler = Euler((math.radians(65), 0, math.radians(-135)), 'XYZ')

bpy.ops.object.light_add(type='AREA', location=(0.0, 3.5, 2.0))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 400
rim.data.size = 2.0
rim.rotation_euler = Euler((math.radians(100), 0, math.radians(180)), 'XYZ')

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 65
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (3.4, -4.2, 3.0)

target = Vector((0.0, 0.0, 0.45))
direction = target - cam.location
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = direction.to_track_quat('-Z', 'Y')
scene.camera = cam

# ---------- Frame settings ----------
scene.frame_start = 1
scene.frame_end = 1
