import bpy
import bmesh
import math
from mathutils import Vector

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 48


# ---------- Helpers ----------
def make_mat(name, color, rough=0.5, metal=0.0, emit=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit > 0.0:
        bsdf.inputs["Emission Color"].default_value = (color[0], color[1], color[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit
    return mat


def link(obj):
    scene.collection.objects.link(obj)
    return obj


def _finish(name, bm, loc, scale, rot, mat):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.scale = scale
    obj.rotation_euler = rot
    return link(obj)


def make_box(name, loc, dims, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    return _finish(name, bm, loc, dims, rot, mat)


def make_cyl(name, loc, radius, length, mat, rot=(0, 0, 0)):
    # Cylinder along local Z, centered at loc
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=32,
                          radius1=1.0, radius2=1.0, depth=1.0)
    return _finish(name, bm, loc, (radius, radius, length), rot, mat)


def make_ball(name, loc, radius, mat):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=1.0)
    return _finish(name, bm, loc, (radius, radius, radius), (0, 0, 0), mat)


def make_empty(name, loc):
    obj = bpy.data.objects.new(name, None)
    obj.location = loc
    link(obj)
    return obj


def parent_keep(child, par):
    child.parent = par
    child.matrix_parent_inverse = par.matrix_world.inverted()


# ---------- Materials ----------
mat_body = make_mat("BodyBlue", (0.20, 0.50, 0.92), rough=0.35, metal=0.2)
mat_head = make_mat("HeadSilver", (0.85, 0.87, 0.92), rough=0.3, metal=0.3)
mat_joint = make_mat("JointDark", (0.15, 0.16, 0.20), rough=0.6)
mat_eye = make_mat("EyeWhite", (0.95, 0.97, 1.0), rough=0.2, emit=1.0)
mat_pupil = make_mat("PupilBlue", (0.05, 0.25, 0.85), rough=0.2, emit=2.0)
mat_mouth = make_mat("MouthDark", (0.08, 0.04, 0.04), rough=0.5)
mat_antenna = make_mat("AntennaRed", (0.95, 0.25, 0.15), rough=0.3, emit=0.5)
mat_hand = make_mat("HandYellow", (1.0, 0.78, 0.15), rough=0.4)
mat_panel = make_mat("PanelCyan", (0.3, 0.85, 0.95), rough=0.25, emit=0.6)
mat_ground = make_mat("GroundGrey", (0.55, 0.56, 0.58), rough=0.9)
mat_foot = make_mat("FootDark", (0.25, 0.27, 0.32), rough=0.5)

# ---------- Ground ----------
make_box("Ground", (0, 0, -0.05), (20, 20, 0.1), mat_ground)

# ---------- Torso ----------
body = make_box("Torso", (0, 0, 2.0), (1.4, 1.1, 1.6), mat_body)
make_box("ChestPanel", (0, -0.565, 2.1), (0.7, 0.04, 0.5), mat_panel)
make_ball("ChestButton", (0, -0.6, 1.75), 0.09, mat_eye)

# Neck
make_cyl("Neck", (0, 0, 3.1), 0.15, 0.3, mat_joint)

# ---------- Head ----------
head = make_box("Head", (0, 0, 3.5), (1.2, 1.0, 1.0), mat_head)

# Antenna
make_cyl("AntennaStem", (0, 0, 4.25), 0.05, 0.5, mat_joint)
make_ball("AntennaBall", (0, 0, 4.6), 0.12, mat_antenna)

# Ears
make_cyl("EarLeft", (-0.66, 0, 3.5), 0.15, 0.1, mat_joint, rot=(0, math.pi / 2, 0))
make_cyl("EarRight", (0.66, 0, 3.5), 0.15, 0.1, mat_joint, rot=(0, math.pi / 2, 0))

# Eyes (discs facing -Y)
for side, sx in (("L", -0.3), ("R", 0.3)):
    make_cyl(f"Eye{side}", (sx, -0.52, 3.6), 0.16, 0.03, mat_eye,
             rot=(math.pi / 2, 0, 0))
    make_cyl(f"Pupil{side}", (sx, -0.545, 3.6), 0.08, 0.03, mat_pupil,
             rot=(math.pi / 2, 0, 0))

# Smile
make_box("Mouth", (0, -0.52, 3.25), (0.5, 0.03, 0.08), mat_mouth)
make_box("MouthL", (-0.26, -0.52, 3.31), (0.1, 0.03, 0.08), mat_mouth,
         rot=(0, 0, math.radians(30)))
make_box("MouthR", (0.26, -0.52, 3.31), (0.1, 0.03, 0.08), mat_mouth,
         rot=(0, 0, math.radians(-30)))

# ---------- Legs and feet ----------
for side, x in (("L", -0.36), ("R", 0.36)):
    make_box(f"Leg{side}", (x, 0, 0.75), (0.4, 0.45, 0.9), mat_joint)
    make_box(f"Foot{side}", (x, -0.1, 0.15), (0.46, 0.7, 0.3), mat_foot)
    make_ball(f"Knee{side}", (x, -0.23, 0.9), 0.1, mat_body)

# ---------- Left arm (resting, hanging down) ----------
sh_left = (-0.8, 0.0, 2.4)
make_ball("ShoulderL", sh_left, 0.18, mat_joint)
make_cyl("UpperArmL", (-0.95, 0, 1.9), 0.12, 0.8, mat_body)
make_ball("ElbowL", (-0.95, 0, 1.5), 0.13, mat_joint)
make_cyl("ForearmL", (-0.95, 0, 1.2), 0.11, 0.5, mat_body)
make_ball("HandL", (-0.95, 0, 0.9), 0.16, mat_hand)

# ---------- Right arm (raised, waving) ----------
S = (0.8, 0.0, 2.4)   # shoulder
E = (0.8, 0.0, 3.3)   # elbow (straight up at rest)

shoulder_pivot = make_empty("ShoulderPivotR", S)
bpy.context.view_layer.update()

make_ball("ShoulderR", S, 0.18, mat_joint)
parent_keep(scene.objects["ShoulderR"], shoulder_pivot)

upper = make_cyl("UpperArmR", (S[0], 0, (S[2] + E[2]) / 2), 0.12, E[2] - S[2], mat_body)
parent_keep(upper, shoulder_pivot)

elbow_pivot = make_empty("ElbowPivotR", E)
parent_keep(elbow_pivot, shoulder_pivot)
bpy.context.view_layer.update()

make_ball("ElbowR", E, 0.13, mat_joint)
parent_keep(scene.objects["ElbowR"], elbow_pivot)

forearm = make_cyl("ForearmR", (E[0], 0, E[2] + 0.4), 0.11, 0.8, mat_body)
parent_keep(forearm, elbow_pivot)

hand_r = make_ball("HandR", (E[0], 0, E[2] + 0.9), 0.17, mat_hand)
parent_keep(hand_r, elbow_pivot)

# Raise the shoulder outward, then wave with the elbow
shoulder_pivot.rotation_euler = (0, math.radians(25), 0)

wave_keys = [(1, 0.2), (12, 0.9), (24, 0.2), (36, 0.9), (48, 0.2)]
for frame, ang in wave_keys:
    elbow_pivot.rotation_euler = (0, ang, 0)
    elbow_pivot.keyframe_insert(data_path="rotation_euler", frame=frame)

scene.frame_set(1)
elbow_pivot.rotation_euler = (0, wave_keys[0][1], 0)

# ---------- Lighting ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.62, 0.72, 0.88, 1.0)
    bg.inputs["Strength"].default_value = 1.0

sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.5
sun = bpy.data.objects.new("KeySun", sun_data)
sun.rotation_euler = (math.radians(-50), 0, math.radians(35))
link(sun)

fill_data = bpy.data.lights.new("FillArea", 'AREA')
fill_data.energy = 700
fill_data.size = 5.0
fill = bpy.data.objects.new("FillArea", fill_data)
fill.location = (-4.5, -6.0, 5.0)
target_fill = Vector((0, 0, 2.2))
fill.rotation_euler = (target_fill - fill.location).to_track_quat('-Z', 'Y').to_euler()
link(fill)

rim_data = bpy.data.lights.new("RimPoint", 'POINT')
rim_data.energy = 400
rim = bpy.data.objects.new("RimPoint", rim_data)
rim.location = (4.0, 5.0, 4.0)
link(rim)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("RobotCam")
cam_data.lens = 50
cam = bpy.data.objects.new("RobotCam", cam_data)
cam.location = (6.5, -9.5, 4.0)
link(cam)

target_cam = Vector((0.0, 0.0, 2.6))
direction = target_cam - Vector(cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
