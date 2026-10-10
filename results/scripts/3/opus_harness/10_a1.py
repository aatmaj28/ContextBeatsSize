import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

def make_mat(name, color, metallic=0.0, rough=0.4, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat

body_mat = make_mat("Body", (0.15, 0.45, 0.85), metallic=0.3, rough=0.35)
accent_mat = make_mat("Accent", (0.95, 0.55, 0.1), metallic=0.2, rough=0.4)
metal_mat = make_mat("Metal", (0.7, 0.72, 0.75), metallic=1.0, rough=0.25)
eye_mat = make_mat("Eye", (0.1, 0.9, 1.0), emission=(0.2, 0.95, 1.0), strength=4.0)
dark_mat = make_mat("Dark", (0.03, 0.03, 0.04), rough=0.6)
ground_mat = make_mat("Ground", (0.85, 0.82, 0.75), rough=0.8)
cheek_mat = make_mat("Cheek", (1.0, 0.4, 0.5), rough=0.5)

def bevel(obj, w=0.06):
    m = obj.modifiers.new("Bevel", 'BEVEL')
    m.width = w
    m.segments = 3

def cube(name, loc, scale, mat, bev=0.06, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    if bev:
        bevel(o, bev)
    if parent:
        o.parent = parent
    bpy.ops.object.shade_smooth()
    return o

def cyl(name, loc, radius, depth, mat, rot=(0, 0, 0), parent=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    bevel(o, 0.02)
    bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o

def sphere(name, loc, radius, mat, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=32, ring_count=16)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    if parent:
        o.parent = parent
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.active_object
ground.data.materials.append(ground_mat)

# Legs and feet
for sx in (-0.45, 0.45):
    cyl("Leg", (sx, 0, 0.75), 0.18, 1.0, metal_mat)
    cube("Foot", (sx, -0.12, 0.15), (0.55, 0.8, 0.3), accent_mat, 0.08)

# Hips / Body
cube("Hips", (0, 0, 1.35), (1.3, 0.8, 0.3), metal_mat, 0.08)
body = cube("Body", (0, 0, 2.2), (1.7, 1.1, 1.5), body_mat, 0.15)
# Chest panel
cube("Panel", (0, -0.56, 2.25), (0.9, 0.05, 0.7), dark_mat, 0.03)
for i, c in enumerate([(1, 0.2, 0.2), (0.2, 1, 0.3), (1, 0.85, 0.1)]):
    m = make_mat(f"Button{i}", c, emission=c, strength=2.0)
    cyl("Button", (-0.25 + i * 0.25, -0.6, 2.35), 0.08, 0.06, m, rot=(math.pi / 2, 0, 0))
cube("Grill", (0, -0.6, 2.05), (0.6, 0.04, 0.12), metal_mat, 0.02)

# Neck and head
cyl("Neck", (0, 0, 3.05), 0.22, 0.3, metal_mat)
head = cube("Head", (0, 0, 3.65), (1.4, 1.1, 1.0), body_mat, 0.18)
# Eyes
for sx in (-0.32, 0.32):
    cyl("EyeRim", (sx, -0.55, 3.75), 0.2, 0.08, metal_mat, rot=(math.pi / 2, 0, 0))
    cyl("Eye", (sx, -0.59, 3.75), 0.14, 0.05, eye_mat, rot=(math.pi / 2, 0, 0))
    cyl("Cheek", (sx * 1.5, -0.555, 3.45), 0.09, 0.02, cheek_mat, rot=(math.pi / 2, 0, 0))
# Smile: small cubes arc
for i in range(7):
    t = (i - 3) / 3.0
    x = t * 0.28
    z = 3.38 - 0.08 * (1 - t * t)
    cube("Smile", (x, -0.56, z), (0.07, 0.04, 0.05), dark_mat, 0.01)
# Ears
for sx in (-0.75, 0.75):
    cyl("Ear", (sx, 0, 3.65), 0.2, 0.15, accent_mat, rot=(0, math.pi / 2, 0))
# Antenna
cyl("Antenna", (0, 0, 4.4), 0.04, 0.5, metal_mat)
sphere("AntennaBall", (0, 0, 4.7), 0.12, make_mat("Bulb", (1, 0.2, 0.2), emission=(1, 0.2, 0.15), strength=5.0))

# Arms built on shoulder pivots
def build_arm(side):
    sx = 1.0 * side
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(sx, 0, 2.7))
    pivot = bpy.context.active_object
    pivot.name = "Shoulder_" + ("R" if side > 0 else "L")
    sphere("ShoulderBall", (0, 0, 0), 0.22, accent_mat, parent=pivot)
    cyl("UpperArm", (0, 0, -0.45), 0.13, 0.7, metal_mat, parent=pivot)
    sphere("Elbow", (0, 0, -0.85), 0.16, accent_mat, parent=pivot)
    cube("Forearm", (0, 0, -1.2), (0.3, 0.3, 0.6), body_mat, 0.05, parent=pivot)
    cyl("Wrist", (0, 0, -1.55), 0.12, 0.12, metal_mat, parent=pivot)
    cube("Hand", (0, 0, -1.75), (0.35, 0.18, 0.3), accent_mat, 0.06, parent=pivot)
    for fx in (-0.11, 0.0, 0.11):
        cyl("Finger", (fx, 0, -1.98), 0.04, 0.18, metal_mat, parent=pivot, verts=12)
    cyl("Thumb", (0.2 * side * -1, 0, -1.72), 0.04, 0.16, metal_mat,
        rot=(0, math.pi / 2, 0), parent=pivot, verts=12)
    return pivot

left = build_arm(-1)
left.rotation_euler = (0, math.radians(-8), 0)  # slightly out
right = build_arm(1)

# Wave animation
scene.frame_start = 1
scene.frame_end = 60
base = math.radians(-150)
for f, off in [(1, -15), (15, 15), (30, -15), (45, 15), (60, -15)]:
    right.rotation_euler = (0, base + math.radians(off), 0)
    right.keyframe_insert("rotation_euler", frame=f)
scene.frame_set(1)

# Lighting
def light(name, kind, loc, energy, color=(1, 1, 1), size=1.0):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == 'AREA':
        ld.size = size
    o = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(o)
    o.location = loc
    d = Vector((0, 0, 2.2)) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o

light("Key", 'AREA', (4, -5, 6), 900, (1, 0.95, 0.88), 3)
light("Fill", 'AREA', (-5, -4, 3), 300, (0.8, 0.88, 1.0), 4)
light("Rim", 'AREA', (0, 5, 5), 500, (1, 1, 1), 3)

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1)
bg.inputs["Strength"].default_value = 0.6

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 45
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (4.5, -9.5, 4.0)
target = Vector((0.3, 0, 2.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.resolution_x = 1280
scene.render.resolution_y = 1080
