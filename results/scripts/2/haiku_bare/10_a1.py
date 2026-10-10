import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Clear existing objects ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Materials ----------
def make_mat(name, color, roughness=0.5, emit=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emit > 0.0:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit
    return mat

mat_body = make_mat("BodyBlue", (0.20, 0.45, 0.85), 0.35)
mat_head = make_mat("HeadWhite", (0.92, 0.92, 0.95), 0.3)
mat_dark = make_mat("DarkGray", (0.12, 0.12, 0.14), 0.6)
mat_eye = make_mat("EyeWhite", (0.98, 0.98, 1.0), 0.2)
mat_pupil = make_mat("Pupil", (0.02, 0.02, 0.05), 0.2)
mat_accent = make_mat("AccentOrange", (1.0, 0.55, 0.1), 0.4)
mat_glow = make_mat("ChestGlow", (0.3, 1.0, 0.6), 0.2, emit=6.0)
mat_ground = make_mat("Ground", (0.75, 0.75, 0.72), 0.9)
mat_joint = make_mat("JointSilver", (0.6, 0.62, 0.66), 0.25)

# ---------- Helpers ----------
def box(name, loc, dims, mat, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = dims
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj

def sphere(name, loc, radius, mat, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=24, ring_count=12)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    if parent:
        obj.parent = parent
    return obj

def limb(name, a, b, radius, mat, parent=None):
    a = Vector(a)
    b = Vector(b)
    d = b - a
    length = d.length
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, location=(a + b) / 2,
                                        vertices=24)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    if parent:
        obj.parent = parent
    return obj

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(mat_ground)

# ---------- Legs and feet ----------
for side, x in (("L", -0.4), ("R", 0.4)):
    limb(f"Leg_{side}", (x, 0, 1.25), (x, 0, 0.42), 0.15, mat_dark)
    box(f"Foot_{side}", (x, -0.12, 0.1), (0.5, 0.85, 0.2), mat_body)
    sphere(f"Knee_{side}", (x, 0, 0.85), 0.17, mat_joint)

# ---------- Torso ----------
box("Body", (0, 0, 2.0), (1.4, 1.0, 1.6), mat_body)
box("BodyTrim", (0, 0, 1.25), (1.5, 1.1, 0.12), mat_accent)
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.06, location=(0, -0.53, 2.0),
                                    rotation=(math.radians(90), 0, 0))
chest = bpy.context.active_object
chest.name = "ChestLight"
chest.data.materials.append(mat_glow)

# ---------- Neck and head ----------
limb("Neck", (0, 0, 2.7), (0, 0, 3.1), 0.15, mat_dark)
box("Head", (0, 0, 3.5), (1.1, 1.0, 1.1), mat_head)
for side, x in (("L", -0.27), ("R", 0.27)):
    sphere(f"Eye_{side}", (x, -0.52, 3.65), 0.16, mat_eye)
    sphere(f"Pupil_{side}", (x, -0.64, 3.65), 0.075, mat_pupil)
box("Mouth", (0, -0.51, 3.22), (0.5, 0.03, 0.09), mat_dark)
for side, x in (("L", -0.4), ("R", 0.4)):
    box(f"Cheek_{side}", (x, -0.51, 3.35), (0.14, 0.02, 0.14), mat_accent)

# Antenna
limb("Antenna", (0, 0, 4.05), (0, 0, 4.5), 0.04, mat_dark)
sphere("AntennaBall", (0, 0, 4.58), 0.11, mat_accent)

# ---------- Shoulders ----------
sphere("Shoulder_L", (-0.85, 0, 2.3), 0.2, mat_joint)
sphere("Shoulder_R", (0.85, 0, 2.3), 0.2, mat_joint)

# ---------- Left arm (resting at side) ----------
limb("ArmUpper_L", (-0.85, 0, 2.3), (-1.05, 0, 1.3), 0.12, mat_body)
sphere("Elbow_L", (-1.05, 0, 1.3), 0.13, mat_joint)
limb("ArmLower_L", (-1.05, 0, 1.3), (-1.1, 0, 0.7), 0.11, mat_body)
sphere("Hand_L", (-1.1, 0, 0.58), 0.18, mat_head)

# ---------- Right arm (waving) ----------
elbow_world = Vector((1.3, 0, 3.2))
limb("ArmUpper_R", (0.85, 0, 2.3), (1.3, 0, 3.2), 0.12, mat_body)

pivot = bpy.data.objects.new("WavePivot", None)
bpy.context.collection.objects.link(pivot)
pivot.location = elbow_world
pivot.empty_display_size = 0.2
pivot.rotation_mode = 'XYZ'

sphere("Elbow_R", (0, 0, 0), 0.13, mat_joint, parent=pivot)
limb("ArmLower_R", (0, 0, 0), (0.1, 0, 0.95), 0.11, mat_body, parent=pivot)
sphere("Hand_R", (0.12, 0, 1.08), 0.2, mat_head, parent=pivot)
# Thumb
sphere("Thumb_R", (0.27, 0, 1.0), 0.07, mat_accent, parent=pivot)

# Wave animation (rotate around Y so the arm sways in the X-Z plane)
scene.frame_start = 1
scene.frame_end = 48
wave_keys = [
    (1, 0.0),
    (9, 0.45),
    (17, -0.2),
    (25, 0.45),
    (33, -0.2),
    (41, 0.45),
    (48, 0.0),
]
for frame, angle in wave_keys:
    pivot.rotation_euler = (0.0, angle, 0.0)
    pivot.keyframe_insert(data_path="rotation_euler", frame=frame)

pivot.rotation_euler = (0.0, 0.0, 0.0)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(12)
sun_obj = bpy.data.objects.new("KeySun", sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.location = (4, -6, 8)
sun_obj.rotation_euler = (math.radians(50), 0, math.radians(35))

fill_data = bpy.data.lights.new(name="FillArea", type='AREA')
fill_data.energy = 600
fill_data.size = 6
fill_obj = bpy.data.objects.new("FillArea", fill_data)
scene.collection.objects.link(fill_obj)
fill_obj.location = (-5, -5, 4)
direction = Vector((0, 0, 2.2)) - fill_obj.location
fill_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

rim_data = bpy.data.lights.new(name="RimArea", type='AREA')
rim_data.energy = 400
rim_data.size = 3
rim_obj = bpy.data.objects.new("RimArea", rim_data)
scene.collection.objects.link(rim_obj)
rim_obj.location = (4, 5, 5)
direction = Vector((0, 0, 2.0)) - rim_obj.location
rim_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# World background
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
world = scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("RobotCamera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("RobotCamera", cam_data)
scene.collection.objects.link(cam_obj)
cam_pos = Vector((6.0, -9.5, 4.2))
target = Vector((0.1, 0.0, 2.6))
cam_obj.location = cam_pos
cam_obj.rotation_euler = (target - cam_pos).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj
