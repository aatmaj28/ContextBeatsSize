import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

def make_mat(name, color, metallic=0.0, rough=0.4, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    return m

body_mat = make_mat("Body", (0.15, 0.45, 0.85), 0.3, 0.35)
accent_mat = make_mat("Accent", (0.95, 0.55, 0.1), 0.1, 0.4)
metal_mat = make_mat("Metal", (0.7, 0.72, 0.75), 1.0, 0.25)
eye_mat = make_mat("Eye", (0.1, 0.9, 1.0), 0, 0.2, (0.2, 0.9, 1.0), 6.0)
dark_mat = make_mat("Dark", (0.03, 0.03, 0.04), 0, 0.5)
red_mat = make_mat("Red", (0.9, 0.1, 0.1), 0, 0.3, (1, 0.1, 0.1), 4.0)
floor_mat = make_mat("Floor", (0.85, 0.8, 0.7), 0, 0.8)

def bevel(obj, w=0.06):
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = w
    mod.segments = 3

def cube(name, loc, size, mat, bev=0.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    if bev:
        bevel(o, bev)
    bpy.ops.object.shade_smooth()
    return o

def cyl(name, loc, r, depth, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=32)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    bevel(o, min(0.03, r * 0.3))
    bpy.ops.object.shade_smooth()
    return o

def cyl_between(name, a, b, r, mat):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = cyl(name, (a + b) / 2, r, d.length, mat)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    return o

def sphere(name, loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=32, ring_count=16)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o

# Floor
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(floor_mat)

# Legs & feet
for x in (-0.45, 0.45):
    cyl("Leg", (x, 0, 0.85), 0.2, 1.1, metal_mat)
    cube("Foot", (x, -0.12, 0.17), (0.55, 0.8, 0.34), accent_mat, 0.08)

# Hips
cube("Hips", (0, 0, 1.45), (1.3, 0.8, 0.3), metal_mat, 0.05)

# Torso
torso = cube("Torso", (0, 0, 2.4), (1.8, 1.1, 1.6), body_mat, 0.12)
# Chest panel
cube("Panel", (0, -0.56, 2.45), (1.0, 0.06, 0.8), dark_mat, 0.03)
for i, c in enumerate([red_mat, eye_mat, accent_mat]):
    cyl("Button", (-0.3 + i * 0.3, -0.6, 2.6), 0.09, 0.06, c, rot=(math.pi / 2, 0, 0))
cube("Heart", (0, -0.6, 2.25), (0.5, 0.04, 0.12), eye_mat, 0.02)

# Neck
cyl("Neck", (0, 0, 3.3), 0.22, 0.3, metal_mat)

# Head
cube("Head", (0, 0, 3.95), (1.4, 1.1, 1.05), body_mat, 0.15)
cube("Face", (0, -0.53, 3.95), (1.15, 0.05, 0.8), dark_mat, 0.04)
for x in (-0.3, 0.3):
    cyl("Eye", (x, -0.57, 4.07), 0.15, 0.05, eye_mat, rot=(math.pi / 2, 0, 0))
# Smile
for i in range(7):
    t = (i - 3) / 3.0
    x = t * 0.3
    z = 3.72 + 0.08 * t * t
    sphere("Smile", (x, -0.57, z), 0.04, eye_mat)
# Ears
for x in (-0.75, 0.75):
    cyl("Ear", (x, 0, 3.95), 0.2, 0.15, accent_mat, rot=(0, math.pi / 2, 0))
# Antenna
cyl("Antenna", (0, 0, 4.7), 0.04, 0.45, metal_mat)
sphere("AntennaTip", (0, 0, 4.98), 0.12, red_mat)

# Left arm (robot's right side, -X) hanging down
sh_l = Vector((-1.0, 0, 2.95))
sphere("ShoulderL", sh_l, 0.22, accent_mat)
el_l = sh_l + Vector((-0.2, 0, -0.75))
cyl_between("UpperArmL", sh_l, el_l, 0.13, metal_mat)
sphere("ElbowL", el_l, 0.16, accent_mat)
hd_l = el_l + Vector((-0.05, -0.1, -0.7))
cyl_between("ForearmL", el_l, hd_l, 0.12, metal_mat)
cube("HandL", hd_l + Vector((0, 0, -0.12)), (0.3, 0.3, 0.3), body_mat, 0.06)

# Right arm (+X) raised in a wave
sh_r = Vector((1.0, 0, 2.95))
sphere("ShoulderR", sh_r, 0.22, accent_mat)
el_r = sh_r + Vector((0.6, 0, 0.45))
cyl_between("UpperArmR", sh_r, el_r, 0.13, metal_mat)
sphere("ElbowR", el_r, 0.16, accent_mat)
hd_r = el_r + Vector((0.15, -0.05, 0.75))
fore = cyl_between("ForearmR", el_r, hd_r, 0.12, metal_mat)
hand = cube("HandR", hd_r + Vector((0.03, 0, 0.15)), (0.32, 0.14, 0.36), body_mat, 0.05)
# Fingers
for i in range(3):
    cyl("Finger", hd_r + Vector((-0.08 + i * 0.09, 0, 0.42)), 0.04, 0.18, metal_mat)
cyl("Thumb", hd_r + Vector((-0.2, 0, 0.18)), 0.04, 0.16, metal_mat, rot=(0, math.radians(-60), 0))

# Wave animation: rotate hand group around elbow
pivot = bpy.data.objects.new("WavePivot", None)
scene.collection.objects.link(pivot)
pivot.location = el_r
bpy.context.view_layer.update()
for o in list(scene.objects):
    if o.name.startswith(("ForearmR", "HandR", "Finger", "Thumb")):
        mw = o.matrix_world.copy()
        o.parent = pivot
        o.matrix_world = mw
scene.frame_start = 1
scene.frame_end = 48
for f, ang in [(1, -15), (12, 15), (24, -15), (36, 15), (48, -15)]:
    pivot.rotation_euler = (0, math.radians(ang), 0)
    pivot.keyframe_insert("rotation_euler", frame=f)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), 0, math.radians(30))
bpy.ops.object.light_add(type='AREA', location=(-4, -5, 5))
key = bpy.context.active_object
key.data.energy = 600
key.data.size = 4
key.rotation_euler = (Vector((0, 0, 2.5)) - key.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.light_add(type='AREA', location=(3, 4, 5))
rim = bpy.context.active_object
rim.data.energy = 400
rim.data.size = 3
rim.rotation_euler = (Vector((0, 0, 3)) - rim.location).to_track_quat('-Z', 'Y').to_euler()

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1)
bg.inputs["Strength"].default_value = 0.6

# Camera
bpy.ops.object.camera_add(location=(4.5, -9.5, 3.8))
cam = bpy.context.active_object
cam.data.lens = 45
target = Vector((0.3, 0, 2.6))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 1080
