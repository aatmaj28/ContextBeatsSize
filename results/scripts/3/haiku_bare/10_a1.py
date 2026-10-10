import bpy
import math
from mathutils import Vector

# ---------- Clean up ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
collection = scene.collection


# ---------- Helpers ----------
def make_material(name, color, roughness=0.45, emission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission > 0.0:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission
    return m


def assign(obj, mat):
    obj.data.materials.append(mat)


def box(name, loc, size, mat, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 3
    bpy.ops.object.shade_smooth()
    assign(obj, mat)
    return obj


def sphere(name, loc, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=32, ring_count=16, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    assign(obj, mat)
    return obj


def segment(name, p0, p1, radius, mat, verts=24):
    p0 = Vector(p0)
    p1 = Vector(p1)
    d = p1 - p0
    length = d.length
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts, radius=radius, depth=length, location=(p0 + p1) / 2
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    bpy.ops.object.shade_smooth()
    assign(obj, mat)
    return obj


def cylinder(name, loc, radius, depth, rot, mat, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = rot
    bpy.ops.object.shade_smooth()
    assign(obj, mat)
    return obj


# ---------- Materials ----------
mat_body = make_material("BodyWhite", (0.85, 0.88, 0.92), roughness=0.35)
mat_head = make_material("HeadBlue", (0.25, 0.55, 0.95), roughness=0.35)
mat_accent = make_material("AccentOrange", (1.0, 0.5, 0.1), roughness=0.4)
mat_joint = make_material("JointGrey", (0.3, 0.32, 0.36), roughness=0.5)
mat_eye = make_material("EyeGlow", (0.3, 0.95, 1.0), roughness=0.2, emission=6.0)
mat_hand = make_material("HandYellow", (1.0, 0.8, 0.2), roughness=0.4)
mat_ground = make_material("Ground", (0.55, 0.57, 0.6), roughness=0.9)
mat_antenna_tip = make_material("TipRed", (1.0, 0.15, 0.15), roughness=0.3, emission=1.5)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
assign(ground, mat_ground)

# ---------- Torso ----------
body = box("Torso", (0, 0, 1.3), (1.1, 0.9, 1.2), mat_body)
belly = box("BellyPanel", (0, -0.47, 1.35), (0.6, 0.05, 0.5), mat_accent, bevel=0.02)

# ---------- Head ----------
head = box("Head", (0, 0, 2.65), (1.0, 0.95, 0.95), mat_head)
visor = box("Visor", (0, -0.49, 2.7), (0.8, 0.04, 0.4), mat_body, bevel=0.02)

# Eyes (cylinders facing -Y)
eye_rot = (math.radians(90), 0, 0)
cylinder("EyeL", (-0.22, -0.52, 2.72), 0.11, 0.06, eye_rot, mat_eye)
cylinder("EyeR", (0.22, -0.52, 2.72), 0.11, 0.06, eye_rot, mat_eye)

# Smile
box("Mouth", (0, -0.5, 2.5), (0.42, 0.04, 0.06), mat_accent, bevel=0.015)

# Antenna
segment("AntennaStalk", (0, 0, 3.1), (0, 0, 3.65), 0.035, mat_joint)
sphere("AntennaTip", (0, 0, 3.75), 0.12, mat_antenna_tip)

# Ears
cylinder("EarL", (-0.6, 0, 2.65), 0.12, 0.12, (0, math.radians(90), 0), mat_accent)
cylinder("EarR", (0.6, 0, 2.65), 0.12, 0.12, (0, math.radians(90), 0), mat_accent)

# ---------- Neck ----------
cylinder("Neck", (0, 0, 2.1), 0.14, 0.2, (0, 0, 0), mat_joint)

# ---------- Legs and feet ----------
for side, x in (("L", -0.3), ("R", 0.3)):
    segment(f"Leg{side}", (x, 0, 0.75), (x, 0, 0.3), 0.13, mat_joint)
    box(f"Foot{side}", (x, -0.1, 0.12), (0.36, 0.55, 0.22), mat_accent)

# ---------- Left arm hanging at side ----------
sphere("ShoulderHangL", (-0.66, 0, 1.75), 0.13, mat_joint)
segment("ArmHangL", (-0.66, 0, 1.75), (-0.95, 0, 0.95), 0.1, mat_body)
sphere("HandHangL", (-0.98, 0, 0.85), 0.16, mat_hand)

# ---------- Waving right arm ----------
shoulder = (0.66, 0, 1.75)
elbow = (1.05, 0, 2.5)
sphere("ShoulderWave", shoulder, 0.13, mat_joint)
segment("UpperArmWave", shoulder, elbow, 0.1, mat_body)
sphere("ElbowJoint", elbow, 0.13, mat_joint)

# Pivot at elbow so forearm and hand swing as one
pivot = bpy.data.objects.new("ElbowPivot", None)
pivot.location = elbow
collection.objects.link(pivot)

forearm = segment("ForearmWave", elbow, (1.0, 0, 3.25), 0.095, mat_body)
hand = sphere("HandWave", (1.0, 0, 3.4), 0.17, mat_hand)

for obj in (forearm, hand):
    obj.parent = pivot
    obj.matrix_parent_inverse = pivot.matrix_world.inverted()

# Wave animation: swing the elbow pivot back and forth
scene.frame_start = 1
scene.frame_end = 60
key_frames = [(1, 0.0), (15, 0.55), (30, 0.0), (45, 0.55), (60, 0.0)]
for frame, angle in key_frames:
    pivot.rotation_euler = (0, angle, 0)
    pivot.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)
pivot.rotation_euler = (0, 0, 0)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 3.0
sun_data.angle = math.radians(12)
sun = bpy.data.objects.new("KeySun", sun_data)
collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

fill_data = bpy.data.lights.new(name="FillArea", type='AREA')
fill_data.energy = 400
fill_data.size = 5
fill = bpy.data.objects.new("FillArea", fill_data)
collection.objects.link(fill)
fill.location = (-4, -5, 3.5)
direction = Vector((0, 0, 1.5)) - fill.location
fill.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

rim_data = bpy.data.lights.new(name="RimArea", type='AREA')
rim_data.energy = 250
rim_data.size = 3
rim = bpy.data.objects.new("RimArea", rim_data)
collection.objects.link(rim)
rim.location = (4, 4, 4)
direction = Vector((0, 0, 1.5)) - rim.location
rim.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# ---------- World ----------
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.6, 0.75, 0.95, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("RobotCam")
cam_data.lens = 50
cam = bpy.data.objects.new("RobotCam", cam_data)
collection.objects.link(cam)
cam.location = (5.5, -8.0, 3.0)
target = Vector((0.1, 0.0, 1.9))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
