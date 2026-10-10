import bpy, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, metal=0.0, rough=0.4, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

M_body = mat("Body", (0.25, 0.55, 0.85), 0.3, 0.35)
M_accent = mat("Accent", (1.0, 0.45, 0.1), 0.1, 0.4)
M_joint = mat("Joint", (0.15, 0.15, 0.18), 0.7, 0.3)
M_white = mat("White", (0.95, 0.95, 0.95), 0.0, 0.2)
M_black = mat("Black", (0.02, 0.02, 0.02), 0.0, 0.2)
M_cheek = mat("Cheek", (1.0, 0.4, 0.5), 0.0, 0.5)
M_glow = mat("Glow", (1.0, 0.9, 0.2), 0.0, 0.3, (1.0, 0.85, 0.2), 6.0)
M_green = mat("Green", (0.2, 1.0, 0.4), 0.0, 0.3, (0.2, 1.0, 0.4), 4.0)
M_ground = mat("Ground", (0.85, 0.82, 0.75), 0.0, 0.8)

def bevel(o, w=0.04):
    m = o.modifiers.new("Bevel", 'BEVEL')
    m.width = w
    m.segments = 3

def cube(name, loc, size, m, bev=0.05, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(m)
    if bev: bevel(o, bev)
    if parent: o.parent = parent
    bpy.ops.object.shade_smooth()
    return o

def cyl(name, loc, r, d, m, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(m)
    bevel(o, min(0.02, r * 0.3))
    o.modifiers["Bevel"].limit_method = 'ANGLE'
    bpy.ops.object.shade_smooth()
    if parent: o.parent = parent
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=30)
g = bpy.context.active_object
g.data.materials.append(M_ground)

X90 = (math.radians(90), 0, 0)
Y90 = (0, math.radians(90), 0)

# Legs & feet
for s in (-1, 1):
    cyl("Leg", (0.32 * s, 0, 0.6), 0.14, 0.8, M_joint)
    cube("Foot", (0.32 * s, -0.1, 0.13), (0.4, 0.6, 0.26), M_accent, 0.06)
    cyl("Knee", (0.32 * s, 0, 0.6), 0.17, 0.12, M_accent)

# Torso
cube("Torso", (0, 0, 1.65), (1.3, 0.85, 1.25), M_body, 0.1)
cube("Belt", (0, 0, 1.08), (1.34, 0.89, 0.12), M_accent, 0.03)
cube("ChestPanel", (0, -0.43, 1.75), (0.7, 0.05, 0.5), M_white, 0.02)
for i, mm in enumerate((M_glow, M_green, M_cheek)):
    cyl("Button", (-0.2 + 0.2 * i, -0.47, 1.85), 0.06, 0.05, mm, X90)
for i in range(3):
    cube("Slot", (0, -0.47, 1.64 - 0.09 * i), (0.45, 0.03, 0.035), M_joint, 0)

# Neck & head
cyl("Neck", (0, 0, 2.38), 0.15, 0.25, M_joint)
head = cube("Head", (0, 0, 2.9), (1.1, 0.85, 0.85), M_body, 0.12)
cube("Visor", (0, -0.42, 2.95), (0.9, 0.04, 0.5), M_joint, 0.03)
for s in (-1, 1):
    cyl("Eye", (0.22 * s, -0.46, 3.0), 0.13, 0.04, M_white, X90)
    cyl("Pupil", (0.22 * s + 0.02, -0.49, 3.01), 0.06, 0.03, M_black, X90)
    cyl("Shine", (0.22 * s + 0.05, -0.51, 3.05), 0.02, 0.02, M_white, X90)
    cyl("Cheek", (0.36 * s, -0.44, 2.82), 0.06, 0.02, M_cheek, X90)
    cyl("Ear", (0.58 * s, 0, 2.9), 0.16, 0.1, M_accent, Y90)
# Smile: small cubes on an arc
for i in range(7):
    a = math.radians(-50 + i * (100 / 6))
    x = 0.17 * math.sin(a)
    z = 2.86 - 0.08 * math.cos(a)
    c = cube("Smile", (x, -0.46, z), (0.05, 0.03, 0.035), M_glow, 0)
    c.rotation_euler.y = -a
# Antenna
cyl("Antenna", (0, 0, 3.5), 0.03, 0.4, M_joint)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(0, 0, 3.73))
bulb = bpy.context.active_object
bulb.data.materials.append(M_glow)
bpy.ops.object.shade_smooth()

# Left (resting) arm
cyl("ShoulderL", (-0.72, 0, 2.05), 0.16, 0.15, M_accent, Y90)
cyl("ArmL", (-0.78, 0, 1.6), 0.1, 0.8, M_joint)
cube("HandL", (-0.78, 0, 1.12), (0.24, 0.24, 0.2), M_accent, 0.05)

# Right (waving) arm on a pivot
pivot = bpy.data.objects.new("ShoulderPivot", None)
scene.collection.objects.link(pivot)
pivot.location = (0.72, 0, 2.05)
cyl("ShoulderR", (0, 0, 0), 0.16, 0.15, M_accent, Y90, parent=pivot)
cyl("ArmR", (0.06, 0, 0.45), 0.1, 0.8, M_joint, parent=pivot)
cube("HandR", (0.06, 0, 0.92), (0.26, 0.2, 0.24), M_accent, 0.05, parent=pivot)
for i in range(3):
    cube("Finger", (-0.03 + 0.09 * i, 0, 1.1), (0.06, 0.08, 0.14), M_accent, 0.02, parent=pivot)
cube("Thumb", (-0.1, 0, 0.98), (0.08, 0.08, 0.06), M_accent, 0.02, parent=pivot)

# Wave animation
scene.frame_start, scene.frame_end = 1, 96
for f, a in [(1, 20), (13, 45), (25, 20), (37, 45), (49, 20), (61, 45), (73, 20), (85, 45), (96, 20)]:
    pivot.rotation_euler = (0, math.radians(a), 0)
    pivot.keyframe_insert("rotation_euler", frame=f)
scene.frame_set(1)

# Lighting
bpy.ops.object.light_add(type='AREA', location=(-3, -4, 5))
k = bpy.context.active_object
k.data.energy = 900; k.data.size = 4
k.rotation_euler = (math.radians(50), 0, math.radians(-35))
bpy.ops.object.light_add(type='AREA', location=(4, -2, 3))
f = bpy.context.active_object
f.data.energy = 300; f.data.size = 3; f.data.color = (0.8, 0.9, 1.0)
f.rotation_euler = (math.radians(65), 0, math.radians(60))
bpy.ops.object.light_add(type='SUN', location=(0, 5, 6))
s = bpy.context.active_object
s.data.energy = 2.0
s.rotation_euler = (math.radians(-40), 0, 0)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1)
bg.inputs["Strength"].default_value = 0.6

# Camera
bpy.ops.object.camera_add(location=(3.2, -7.0, 3.2))
cam = bpy.context.active_object
target = Vector((0.15, 0, 1.9))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 45
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 1280
