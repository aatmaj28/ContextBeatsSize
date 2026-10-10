import bpy, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

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
dark_m = mat("Dark", (0.15, 0.15, 0.18), 0.6, 0.3)
acc_m = mat("Accent", (1.0, 0.55, 0.1), 0.1, 0.4)
eye_m = mat("Eye", (0.6, 1.0, 1.0), 0, 0.2, emit=(0.4, 1.0, 1.0))
floor_m = mat("Floor", (0.85, 0.85, 0.8), 0, 0.8)
white_m = mat("White", (0.95, 0.95, 0.95), 0.0, 0.3)

def bevel(o, w=0.04):
    m = o.modifiers.new("Bevel", 'BEVEL')
    m.width = w
    m.segments = 3
    for p in o.data.polygons:
        p.use_smooth = True

def cube(name, loc, scale, m, rot=(0, 0, 0), bw=0.04, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(m)
    bevel(o, bw)
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

def cyl(name, loc, r, d, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    bevel(o, min(0.02, r * 0.3))
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

# Floor
bpy.ops.mesh.primitive_plane_add(size=30)
bpy.context.object.data.materials.append(floor_m)

# Legs and feet
for s in (-1, 1):
    x = 0.35 * s
    cyl("Leg", (x, 0, 0.55), 0.14, 0.7, dark_m)
    cube("Foot", (x, -0.08, 0.12), (0.38, 0.55, 0.24), body_m, bw=0.06)

# Torso and its details
cube("Hip", (0, 0, 0.95), (0.9, 0.55, 0.2), dark_m)
cube("Torso", (0, 0, 1.55), (1.3, 0.85, 1.05), body_m, bw=0.1)
cube("Panel", (0, -0.43, 1.6), (0.7, 0.05, 0.5), white_m, bw=0.02)
for i, c in enumerate([acc_m, eye_m, acc_m]):
    cyl("Button", (-0.2 + 0.2 * i, -0.47, 1.68), 0.06, 0.05, c, rot=(math.pi / 2, 0, 0))
cube("Bar", (0, -0.47, 1.47), (0.45, 0.04, 0.06), dark_m, bw=0.01)

# Neck and head
cyl("Neck", (0, 0, 2.17), 0.15, 0.2, dark_m)
head = cube("Head", (0, 0, 2.6), (1.0, 0.8, 0.7), body_m, bw=0.12)
cube("Visor", (0, -0.4, 2.62), (0.8, 0.05, 0.4), dark_m, bw=0.05)
for s in (-1, 1):
    cyl("Eye", (0.2 * s, -0.44, 2.66), 0.09, 0.04, eye_m, rot=(math.pi / 2, 0, 0))
cube("Smile", (0, -0.44, 2.5), (0.25, 0.03, 0.04), eye_m, bw=0.01)
for s in (-1, 1):
    cyl("Ear", (0.53 * s, 0, 2.6), 0.15, 0.1, acc_m, rot=(0, math.pi / 2, 0))
cyl("Antenna", (0, 0, 3.1), 0.025, 0.35, dark_m)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(0, 0, 3.3))
ball = bpy.context.object
ball.data.materials.append(acc_m)
bpy.ops.object.shade_smooth()

# Left arm hanging down (robot's left = +X)
cyl("ShoulderL", (0.75, 0, 1.9), 0.13, 0.2, acc_m, rot=(0, math.pi / 2, 0))
cyl("UpperArmL", (0.8, 0, 1.6), 0.09, 0.5, dark_m, rot=(0, 0.1, 0))
cyl("ForeArmL", (0.84, 0, 1.15), 0.12, 0.45, body_m)
cube("HandL", (0.84, 0, 0.83), (0.22, 0.18, 0.2), acc_m)

# Right arm raised in a wave, pivoting at the shoulder
pivot = bpy.data.objects.new("WavePivot", None)
pivot.location = (-0.75, 0, 1.9)
scene.collection.objects.link(pivot)
cyl("ShoulderR", (-0.75, 0, 1.9), 0.13, 0.2, acc_m, rot=(0, math.pi / 2, 0))
cyl("UpperArmR", (-1.1, 0, 2.1), 0.09, 0.5, dark_m, rot=(0, math.radians(-60), 0), parent=pivot)
cyl("ElbowR", (-1.32, 0, 2.23), 0.11, 0.2, acc_m, rot=(math.pi / 2, 0, 0), parent=pivot)
cyl("ForeArmR", (-1.32, 0, 2.5), 0.12, 0.45, body_m, parent=pivot)
cube("HandR", (-1.32, 0, 2.85), (0.24, 0.12, 0.26), acc_m, parent=pivot)
for i in range(3):
    cube("Finger", (-1.4 + 0.08 * i, 0, 3.03), (0.05, 0.08, 0.14), acc_m, bw=0.015, parent=pivot)
cube("Thumb", (-1.19, 0, 2.92), (0.1, 0.08, 0.05), acc_m, bw=0.015, parent=pivot)

# Wave animation: rock the arm back and forth around the Y axis
scene.frame_start = 1
scene.frame_end = 60
for f, a in [(1, -15), (15, 15), (30, -15), (45, 15), (60, -15)]:
    pivot.rotation_euler = (0, math.radians(a), 0)
    pivot.keyframe_insert("rotation_euler", frame=f)

# Lighting
bpy.ops.object.light_add(type='AREA', location=(-3, -4, 5))
key = bpy.context.object
key.data.energy = 800
key.data.size = 4
key.rotation_euler = (math.radians(50), 0, math.radians(-35))
bpy.ops.object.light_add(type='AREA', location=(4, -2, 3))
fill = bpy.context.object
fill.data.energy = 300
fill.data.size = 3
fill.rotation_euler = (math.radians(60), 0, math.radians(60))
bpy.ops.object.light_add(type='AREA', location=(0, 4, 4))
rim = bpy.context.object
rim.data.energy = 400
rim.rotation_euler = (math.radians(-50), 0, 0)

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.6, 0.75, 0.95, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5

# Camera
bpy.ops.object.camera_add(location=(-2.0, -7.0, 2.6))
cam = bpy.context.object
cam.data.lens = 45
target = Vector((-0.2, 0, 1.75))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
