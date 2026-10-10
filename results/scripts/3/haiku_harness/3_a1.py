import bpy
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clear the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def assign(obj, mat):
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


def add_sphere(name, radius, location, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24,
                                         radius=radius, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return assign(obj, mat)


def add_cylinder(name, radius, depth, location, mat, rotation=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    return assign(obj, mat)


# ---------- Materials ----------
snow_mat = make_material("Snow", (0.93, 0.95, 1.0), roughness=0.55)
ground_mat = make_material("GroundSnow", (0.88, 0.91, 0.97), roughness=0.7)
carrot_mat = make_material("Carrot", (1.0, 0.42, 0.05), roughness=0.4)
coal_mat = make_material("Coal", (0.02, 0.02, 0.02), roughness=0.35)
wood_mat = make_material("Wood", (0.32, 0.18, 0.08), roughness=0.8)
hat_mat = make_material("TopHat", (0.015, 0.015, 0.02), roughness=0.3)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
assign(ground, ground_mat)

# Scattered snow mounds around the base (kept away from the snowman's footprint)
for i in range(28):
    while True:
        x = random.uniform(-9, 9)
        y = random.uniform(-7, 5)
        if math.hypot(x, y) > 2.2:
            break
    r = random.uniform(0.25, 0.8)
    add_sphere(f"Mound_{i}", r, (x, y, -0.02 * r), snow_mat,
               scale=(1.0, 1.0, random.uniform(0.25, 0.4)))

# ---------- Snowman body ----------
BOTTOM_R, BOTTOM_Z = 1.0, 1.0
MIDDLE_R, MIDDLE_Z = 0.7, 2.55
HEAD_R, HEAD_Z = 0.5, 3.6

add_sphere("BottomBall", BOTTOM_R, (0, 0, BOTTOM_Z), snow_mat)
add_sphere("MiddleBall", MIDDLE_R, (0, 0, MIDDLE_Z), snow_mat)
add_sphere("Head", HEAD_R, (0, 0, HEAD_Z), snow_mat)

# ---------- Face ----------
# Carrot nose pointing toward the camera (-Y)
NOSE_LEN = 0.6
add_cylinder_cone = bpy.ops.mesh.primitive_cone_add(
    vertices=16, radius1=0.09, radius2=0.0, depth=NOSE_LEN,
    location=(0, -HEAD_R - NOSE_LEN / 2 + 0.02, HEAD_Z),
    rotation=(math.pi / 2, 0, 0))
nose = bpy.context.active_object
nose.name = "CarrotNose"
assign(nose, carrot_mat)

# Coal eyes placed on the head's front surface
EYE_DZ = 0.15
EYE_X = 0.18
eye_y = -math.sqrt(HEAD_R**2 - EYE_DZ**2 - EYE_X**2) + 0.02
for side, sx in (("L", -1), ("R", 1)):
    add_sphere(f"Eye_{side}", 0.06, (sx * EYE_X, eye_y, HEAD_Z + EYE_DZ), coal_mat)

# Mouth: a row of small coal dots
for i, x in enumerate([-0.12, -0.04, 0.04, 0.12]):
    dz = -0.22
    y = -math.sqrt(HEAD_R**2 - dz**2 - x**2) + 0.02
    add_sphere(f"Mouth_{i}", 0.02, (x, y, HEAD_Z + dz), coal_mat)

# ---------- Buttons on the middle ball ----------
for i, dz in enumerate([0.3, 0.0, -0.3]):
    y = -math.sqrt(MIDDLE_R**2 - (dz * 0.8)**2) - 0.01
    add_sphere(f"Button_{i}", 0.07, (0, y, MIDDLE_Z + dz * 0.8), coal_mat)

# ---------- Stick arms ----------
ARM_R, ARM_LEN = 0.03, 1.4
TILT = math.pi / 2 - 0.4  # tilted upward
for side, sx in (("Left", -1), ("Right", 1)):
    d = Vector((sx * math.sin(TILT), 0, math.cos(TILT)))  # direction of arm
    start = Vector((sx * 0.6, 0, 2.75))
    center = start + d * (ARM_LEN / 2)
    rot_y = sx * TILT if False else (TILT if sx > 0 else -TILT)
    add_cylinder(f"Arm_{side}", ARM_R, ARM_LEN, tuple(center), wood_mat,
                 rotation=(0, rot_y, 0))
    # Small twig fork on each arm
    fork_center = center + d * 0.45 + Vector((0, 0, 0.12))
    add_cylinder(f"Twig_{side}", 0.015, 0.3, tuple(fork_center), wood_mat,
                 rotation=(0, rot_y + sx * 0.6, 0))

# ---------- Top hat ----------
HAT_BASE_Z = HEAD_Z + HEAD_R - 0.05
brim = add_cylinder("HatBrim", 0.62, 0.05, (0, 0, HAT_BASE_Z), hat_mat)
crown = add_cylinder("HatCrown", 0.38, 0.6, (0, 0, HAT_BASE_Z + 0.3), hat_mat)
band = add_cylinder("HatBand", 0.385, 0.08, (0, 0, HAT_BASE_Z + 0.12),
                    make_material("HatBand", (0.5, 0.05, 0.05), roughness=0.5))
for o in (brim, crown):
    o.rotation_euler = (math.radians(-6), 0, math.radians(-12))
band.rotation_euler = crown.rotation_euler

# ---------- Lighting ----------
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.55, 0.7, 1.0)
bg.inputs["Strength"].default_value = 0.8

bpy.ops.object.light_add(type='SUN', location=(4, -6, 8))
sun = bpy.context.active_object
sun.name = "KeySun"
sun.data.energy = 3.5
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-5, -6, 4))
fill = bpy.context.active_object
fill.name = "FillArea"
fill.data.energy = 400
fill.data.size = 5
fill.rotation_euler = (math.radians(70), 0, math.radians(-40))

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(0, -14, 2.6))
cam = bpy.context.active_object
cam.name = "Camera"
cam.data.lens = 50

target = Vector((0, 0, 2.4))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
