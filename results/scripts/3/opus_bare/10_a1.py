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
ground_m = mat("Ground", (0.95, 0.85, 0.6), 0.0, 0.8)
yel_m = mat("Yellow", (1.0, 0.8, 0.1), 0.1, 0.4)

def bevel(o, w=0.05):
    mod = o.modifiers.new("Bevel", 'BEVEL')
    mod.width = w
    mod.segments = 3

def cube(name, loc, scale, m, rot=(0, 0, 0), bw=0.05):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    bevel(o, bw)
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o

def cyl(name, loc, r, d, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=32)
    o = bpy.context.object
    o.name = name
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
for x in (-0.4, 0.4):
    cyl("Leg", (x, 0, 0.75), 0.15, 0.9, gray_m)
    cube("Foot", (x, -0.1, 0.18), (0.28, 0.4, 0.18), body_m)

# Torso
cube("Torso", (0, 0, 1.9), (0.85, 0.6, 0.75), body_m, bw=0.12)
# Chest panel
cube("Panel", (0, -0.6, 1.95), (0.5, 0.03, 0.4), dark_m, bw=0.02)
for i, c in enumerate([red_m, yel_m, eye_m]):
    cyl("Button", (-0.25 + i * 0.25, -0.64, 2.1), 0.08, 0.05, c, rot=(math.pi / 2, 0, 0))
cube("Grill", (0, -0.64, 1.75), (0.35, 0.02, 0.1), gray_m, bw=0.02)

# Neck
cyl("Neck", (0, 0, 2.75), 0.18, 0.2, gray_m)

# Head
cube("Head", (0, 0, 3.3), (0.65, 0.55, 0.5), body_m, bw=0.12)
for x in (-0.27, 0.27):
    cyl("EyeRim", (x, -0.55, 3.38), 0.17, 0.06, gray_m, rot=(math.pi / 2, 0, 0))
    sphere("Eye", (x, -0.58, 3.38), 0.12, eye_m)
# Smile: small cubes in an arc
for i in range(7):
    a = math.radians(-60 + i * 20)
    cube("Smile", (math.sin(a) * 0.25, -0.56, 3.12 - math.cos(a) * 0.08 + 0.08),
         (0.035, 0.02, 0.035), dark_m, bw=0.01)
# Ears
for x in (-0.7, 0.7):
    cyl("Ear", (x, 0, 3.3), 0.15, 0.12, gray_m, rot=(0, math.pi / 2, 0))
# Antenna
cyl("Antenna", (0, 0, 3.95), 0.03, 0.4, gray_m)
sphere("AntennaBall", (0, 0, 4.18), 0.1, red_m)

# Left arm (down, viewer's right since robot faces -Y)
sx = 0.85
sphere("ShoulderL", (-1.0, 0, 2.4), 0.18, gray_m)
cyl("UpperArmL", (-1.05, 0, 1.95), 0.11, 0.8, gray_m, rot=(0, math.radians(-8), 0))
cube("HandL", (-1.12, 0, 1.45), (0.16, 0.16, 0.16), body_m)

# Right arm raised waving
sphere("ShoulderR", (1.0, 0, 2.4), 0.18, gray_m)
cyl("UpperArmR", (1.3, 0, 2.6), 0.11, 0.7, gray_m, rot=(0, math.radians(55), 0))
sphere("ElbowR", (1.6, 0, 2.8), 0.14, gray_m)
forearm = cyl("ForeArmR", (1.68, 0, 3.15), 0.1, 0.6, gray_m, rot=(0, math.radians(15), 0))
hand = cube("HandR", (1.78, 0, 3.55), (0.18, 0.08, 0.2), body_m)
for i in range(3):
    cube("Finger", (1.68 + i * 0.1, 0, 3.82), (0.035, 0.05, 0.08), body_m, bw=0.02)
# Thumb
cube("Thumb", (1.55, 0, 3.55), (0.07, 0.05, 0.035), body_m, bw=0.02)

# Waving animation: parent forearm/hand group to empty at elbow
bpy.ops.object.empty_add(location=(1.6, 0, 2.8))
pivot = bpy.context.object
pivot.name = "WavePivot"
for o in list(scene.objects):
    if o.name.startswith(("ForeArmR", "HandR", "Finger", "Thumb")):
        o.parent = pivot
        o.matrix_parent_inverse = pivot.matrix_world.inverted()
scene.frame_start = 1
scene.frame_end = 60
for f, ang in [(1, -15), (15, 15), (30, -15), (45, 15), (60, -15)]:
    pivot.rotation_euler = (0, math.radians(ang), 0)
    pivot.keyframe_insert("rotation_euler", frame=f)

# Lighting
bpy.ops.object.light_add(type='AREA', location=(3, -4, 6))
key = bpy.context.object
key.data.energy = 1000
key.data.size = 4
key.rotation_euler = (math.radians(50), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-4, -3, 3))
fill = bpy.context.object
fill.data.energy = 300
fill.data.size = 5
fill.rotation_euler = (math.radians(65), 0, math.radians(-55))
bpy.ops.object.light_add(type='SUN', location=(0, 5, 6))
rim = bpy.context.object
rim.data.energy = 2
rim.rotation_euler = (math.radians(-40), 0, 0)

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.6, 0.75, 0.95, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5

# Camera
bpy.ops.object.camera_add(location=(3.5, -8.5, 3.2))
cam = bpy.context.object
cam.data.lens = 45
target = Vector((0.3, 0, 2.1))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
