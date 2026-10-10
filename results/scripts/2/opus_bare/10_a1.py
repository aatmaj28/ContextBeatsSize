import bpy, math
from mathutils import Vector

scene = bpy.context.scene

def mat(name, color, metal=0.0, rough=0.4, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 3.0
    return m

body_m = mat("Body", (0.2, 0.55, 0.9), 0.3, 0.35)
gray_m = mat("Gray", (0.7, 0.72, 0.75), 0.8, 0.3)
dark_m = mat("Dark", (0.05, 0.05, 0.07), 0.2, 0.5)
eye_m = mat("Eye", (0.6, 1.0, 1.0), emit=(0.4, 1.0, 1.0))
red_m = mat("Red", (1.0, 0.25, 0.2), emit=(1.0, 0.2, 0.1))
yellow_m = mat("Yellow", (1.0, 0.8, 0.1), 0.1, 0.4)
ground_m = mat("Ground", (0.9, 0.85, 0.75), 0, 0.8)

def bevel(o, w=0.05):
    mod = o.modifiers.new("Bevel", 'BEVEL')
    mod.width = w
    mod.segments = 3

def cube(name, loc, size, m, bev=0.05, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bev: bevel(o, bev)
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o

def cyl(name, loc, r, d, m, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    bevel(o, min(0.02, r * 0.3))
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o

def sphere(name, loc, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=30)
bpy.context.object.data.materials.append(ground_m)

# Legs and feet
for x in (-0.35, 0.35):
    cyl("Leg", (x, 0, 0.55), 0.13, 0.7, gray_m)
    cube("Foot", (x, -0.1, 0.12), (0.4, 0.6, 0.24), dark_m, 0.06)

# Torso
cube("Torso", (0, 0, 1.55), (1.4, 0.9, 1.3), body_m, 0.12)
cube("Panel", (0, -0.46, 1.5), (0.7, 0.05, 0.6), dark_m, 0.03)
for i, c in enumerate((red_m, eye_m, yellow_m)):
    cyl("Button", (-0.2 + i * 0.2, -0.5, 1.6), 0.06, 0.05, c, rot=(math.pi / 2, 0, 0))
cube("Bar", (0, -0.5, 1.35), (0.45, 0.04, 0.08), eye_m, 0.02)

# Neck and head
cyl("Neck", (0, 0, 2.3), 0.15, 0.25, gray_m)
head = cube("Head", (0, 0, 2.8), (1.1, 0.85, 0.8), body_m, 0.15)
cube("Face", (0, -0.43, 2.8), (0.9, 0.04, 0.55), dark_m, 0.04)
for x in (-0.22, 0.22):
    cyl("Eye", (x, -0.46, 2.88), 0.11, 0.05, eye_m, rot=(math.pi / 2, 0, 0))
# smile: small cylinders in an arc
for i in range(7):
    a = math.radians(-50 + i * (100 / 6))
    sphere("Smile", (math.sin(a) * 0.2, -0.46, 2.72 - math.cos(a) * 0.08 + 0.02), 0.03, eye_m)
for x in (-0.6, 0.6):
    cyl("Ear", (x, 0, 2.8), 0.15, 0.12, gray_m, rot=(0, math.pi / 2, 0))
cyl("Antenna", (0, 0, 3.35), 0.03, 0.35, gray_m)
sphere("AntennaTip", (0, 0, 3.55), 0.08, red_m)

# Shoulders
for x in (-0.8, 0.8):
    sphere("Shoulder", (x, 0, 2.0), 0.17, gray_m)

# Left arm (down) - character's left at -x... robot faces -y so its right is -x
cyl("ArmL_Upper", (0.88, 0, 1.68), 0.1, 0.55, gray_m, rot=(0, math.radians(-10), 0))
sphere("ElbowL", (0.93, 0, 1.4), 0.12, gray_m)
cyl("ArmL_Lower", (0.95, 0, 1.15), 0.1, 0.45, body_m)
cube("HandL", (0.95, 0, 0.85), (0.22, 0.22, 0.22), yellow_m, 0.05)

# Waving arm (raised)
up_ang = math.radians(-130)  # rotation about Y from down
sh = Vector((-0.8, 0, 2.0))
d1 = Vector((math.sin(math.radians(130)) * -1, 0, -math.cos(math.radians(130))))
# d1 points up and outward (-x)
upper_c = sh + d1 * 0.32
cyl("ArmR_Upper", upper_c, 0.1, 0.55, gray_m, rot=(0, math.radians(-130) * -1 + math.pi, 0))
upper = bpy.context.object
upper.rotation_euler = (0, 0, 0)
upper.rotation_euler = d1.to_track_quat('Z', 'Y').to_euler()
elbow = sh + d1 * 0.62
sphere("ElbowR", elbow, 0.12, gray_m)
d2 = Vector((-0.25, 0, 1)).normalized()
fore = cyl("ArmR_Lower", elbow + d2 * 0.25, 0.1, 0.45, body_m)
fore.rotation_euler = d2.to_track_quat('Z', 'Y').to_euler()
hand = cube("HandR", elbow + d2 * 0.55, (0.22, 0.12, 0.3), yellow_m, 0.05)
hand.rotation_euler = d2.to_track_quat('Z', 'Y').to_euler()
# fingers
for i, off in enumerate((-0.07, 0, 0.07)):
    f = cyl("Finger", elbow + d2 * 0.75 + Vector((off, 0, 0)), 0.03, 0.14, yellow_m)
    f.rotation_euler = d2.to_track_quat('Z', 'Y').to_euler()
th = cyl("Thumb", elbow + d2 * 0.55 + Vector((0.14, 0, 0.05)), 0.03, 0.12, yellow_m, rot=(0, math.radians(60), 0))

# Wave animation: rotate forearm group via parenting to an empty at elbow
bpy.ops.object.empty_add(location=elbow)
pivot = bpy.context.object
pivot.name = "WavePivot"
for o in bpy.data.objects:
    if o.name.startswith(("ArmR_Lower", "HandR", "Finger", "Thumb")):
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
scene.frame_start = 1
scene.frame_end = 48
for f, a in ((1, -20), (12, 20), (24, -20), (36, 20), (48, -20)):
    pivot.rotation_euler = (0, math.radians(a), 0)
    pivot.keyframe_insert("rotation_euler", frame=f)

# Lights
bpy.ops.object.light_add(type='AREA', location=(-3, -4, 5))
k = bpy.context.object
k.data.energy = 800
k.data.size = 4
k.rotation_euler = (math.radians(50), 0, math.radians(-35))
bpy.ops.object.light_add(type='AREA', location=(4, -2, 3))
f = bpy.context.object
f.data.energy = 300
f.data.size = 3
f.rotation_euler = (math.radians(60), 0, math.radians(60))
bpy.ops.object.light_add(type='SUN', location=(0, 5, 6))
s = bpy.context.object
s.data.energy = 2
s.rotation_euler = (math.radians(-40), 0, 0)

# World
w = bpy.data.worlds.new("World")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.7, 0.9, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = w

# Camera
bpy.ops.object.camera_add(location=(2.5, -7.5, 2.6))
cam = bpy.context.object
cam.data.lens = 45
target = Vector((0, 0, 1.9))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
