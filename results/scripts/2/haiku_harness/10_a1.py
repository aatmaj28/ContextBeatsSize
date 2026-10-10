import bpy
import math
from mathutils import Vector, Matrix, Quaternion

# ---------- Clean up the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 48
scene.frame_set(1)


# ---------- Materials ----------
def make_mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


body_mat = make_mat("BodyWhite", (0.85, 0.88, 0.92), rough=0.35, metal=0.1)
accent_mat = make_mat("AccentBlue", (0.15, 0.45, 0.9), rough=0.3, metal=0.2)
joint_mat = make_mat("JointGray", (0.25, 0.27, 0.3), rough=0.5, metal=0.6)
red_mat = make_mat("AntennaRed", (0.9, 0.12, 0.1), rough=0.3)
eye_mat = make_mat("EyeGlow", (0.3, 0.9, 1.0), rough=0.2,
                   emit=(0.3, 0.9, 1.0), strength=6.0)
dark_mat = make_mat("MouthDark", (0.05, 0.05, 0.06), rough=0.6)
yellow_mat = make_mat("ButtonYellow", (1.0, 0.75, 0.1), rough=0.3)
ground_mat = make_mat("Ground", (0.55, 0.58, 0.6), rough=0.9)


# ---------- Helpers ----------
def add_box(name, loc, size, mat, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(mat)
    if bevel > 0:
        m = o.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 3
    return o


def add_cyl(name, loc, radius, depth, mat, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def add_sphere(name, loc, radius, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=32,
                                         ring_count=16, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def add_limb(name, a, b, radius, mat):
    a = Vector(a)
    b = Vector(b)
    mid = (a + b) * 0.5
    length = (b - a).length
    direction = (b - a).normalized()
    o = add_cyl(name, mid, radius, length, mat)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction)
    return o


def add_empty(name, loc):
    e = bpy.data.objects.new(name, None)
    e.location = Vector(loc)
    e.empty_display_size = 0.2
    bpy.context.scene.collection.objects.link(e)
    return e


def attach(child, pivot_world_loc, pivot):
    # Child keeps its world placement while driven by the pivot's rotation
    child.parent = pivot
    child.matrix_parent_inverse = Matrix.Translation(-Vector(pivot_world_loc))


# ---------- Robot body ----------
body = add_box("Torso", (0, 0, 1.5), (1.4, 1.0, 1.3), body_mat)
belly = add_box("ChestPanel", (0, -0.52, 1.5), (0.6, 0.05, 0.5), accent_mat, bevel=0.02)
button = add_cyl("ChestButton", (0, -0.56, 1.5), 0.08, 0.05, yellow_mat,
                 rot=(math.pi / 2, 0, 0))

# Legs and feet
for side, x in (("L", -0.35), ("R", 0.35)):
    add_cyl(f"Leg{side}", (x, 0, 0.525), 0.14, 0.65, joint_mat)
    add_box(f"Foot{side}", (x, -0.1, 0.1), (0.42, 0.62, 0.2), accent_mat)
    add_sphere(f"Hip{side}", (x, 0, 0.85), 0.16, joint_mat)

# Neck and head
add_cyl("Neck", (0, 0, 2.3), 0.12, 0.3, joint_mat)
head = add_box("Head", (0, 0, 2.85), (1.1, 0.9, 0.9), body_mat)

# Face
for side, x in (("L", -0.27), ("R", 0.27)):
    add_cyl(f"Eye{side}", (x, -0.46, 2.95), 0.15, 0.05, eye_mat,
            rot=(math.pi / 2, 0, 0))
add_box("Mouth", (0, -0.46, 2.6), (0.42, 0.04, 0.09), dark_mat, bevel=0.02)

# Antenna
add_cyl("AntennaStem", (0, 0, 3.55), 0.04, 0.5, joint_mat)
add_sphere("AntennaTip", (0, 0, 3.9), 0.11, red_mat)

# ---------- Left arm (relaxed, hanging) ----------
SL = (-0.85, 0, 1.85)
EL = (-1.0, 0, 1.35)
WL = (-1.08, 0, 0.95)
add_sphere("ShoulderL", SL, 0.16, joint_mat)
add_limb("UpperArmL", SL, EL, 0.1, accent_mat)
add_sphere("ElbowL", EL, 0.12, joint_mat)
add_limb("ForearmL", EL, WL, 0.09, body_mat)
add_sphere("HandL", (WL[0], WL[1], WL[2] - 0.12), 0.14, joint_mat,
           scale=(1.0, 0.8, 1.1))

# ---------- Right arm (raised, waving) ----------
S = Vector((0.85, 0, 1.85))
d1 = Vector((0.35, 0, 0.94)).normalized()
E = S + d1 * 0.9
d2 = Vector((0.2, 0, 1.0)).normalized()
W = E + d2 * 0.8

shoulder_pivot = add_empty("ShoulderPivotR", S)
elbow_pivot = add_empty("ElbowPivotR", E - S)
elbow_pivot.parent = shoulder_pivot  # identity parent inverse; local offset E - S

# Shoulder parts (children of shoulder pivot)
shoulder_joint = add_sphere("ShoulderR", S, 0.16, joint_mat)
attach(shoulder_joint, S, shoulder_pivot)
upper = add_limb("UpperArmR", S, E, 0.1, accent_mat)
attach(upper, S, shoulder_pivot)

# Elbow parts (children of elbow pivot)
elbow_joint = add_sphere("ElbowR", E, 0.12, joint_mat)
attach(elbow_joint, E, elbow_pivot)
forearm = add_limb("ForearmR", E, W, 0.09, body_mat)
attach(forearm, E, elbow_pivot)
hand = add_sphere("HandR", W + Vector((0, 0, 0.12)), 0.15, joint_mat,
                  scale=(1.0, 0.7, 1.1))
attach(hand, E, elbow_pivot)

# Wave animation: swing the forearm around the Y axis (sideways in the arm's plane)
wave_keys = {1: 0.0, 7: 0.5, 13: -0.25, 19: 0.5, 25: -0.25,
             31: 0.5, 37: -0.25, 43: 0.3, 48: 0.0}
for frame, angle in wave_keys.items():
    elbow_pivot.rotation_euler = (0.0, angle, 0.0)
    elbow_pivot.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)

# Gentle shoulder sway for life
sway_keys = {1: 0.0, 24: 0.04, 48: 0.0}
for frame, angle in sway_keys.items():
    shoulder_pivot.rotation_euler = (0.0, angle, 0.0)
    shoulder_pivot.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)

shoulder_pivot.rotation_euler = (0.0, 0.0, 0.0)
elbow_pivot.rotation_euler = (0.0, 0.0, 0.0)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(ground_mat)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("KeySun", sun_data)
sun.location = (4, -5, 8)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
scene.collection.objects.link(sun)

fill_data = bpy.data.lights.new("FillArea", 'AREA')
fill_data.energy = 400.0
fill_data.size = 4.0
fill = bpy.data.objects.new("FillArea", fill_data)
fill.location = (-5, -4, 3.5)
fill.rotation_euler = (math.radians(70), 0, math.radians(-50))
scene.collection.objects.link(fill)

rim_data = bpy.data.lights.new("RimArea", 'AREA')
rim_data.energy = 250.0
rim_data.size = 3.0
rim = bpy.data.objects.new("RimArea", rim_data)
rim.location = (0, 5, 4)
rim.rotation_euler = (math.radians(-60), 0, math.radians(180))
scene.collection.objects.link(rim)

# ---------- World ----------
world = bpy.data.worlds.new("StudioWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("RobotCamera")
cam_data.lens = 40.0
cam = bpy.data.objects.new("RobotCamera", cam_data)
cam_loc = Vector((7.0, -11.0, 3.2))
target = Vector((0.0, 0.0, 2.0))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = direction.to_track_quat('-Z', 'Y')
scene.collection.objects.link(cam)
scene.camera = cam
