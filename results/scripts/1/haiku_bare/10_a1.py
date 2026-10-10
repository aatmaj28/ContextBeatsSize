import bpy
import math
from mathutils import Matrix, Vector

# ---------- Clean up any existing content ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene


# ---------- Materials ----------
def make_mat(name, color, roughness=0.5, emit_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emit_strength > 0.0:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat


mat_body = make_mat("BodyBlue", (0.45, 0.68, 0.92), roughness=0.4)
mat_accent = make_mat("AccentOrange", (1.0, 0.5, 0.1), roughness=0.35)
mat_dark = make_mat("DarkGrey", (0.12, 0.12, 0.14), roughness=0.6)
mat_eye = make_mat("EyeGlow", (0.2, 0.9, 1.0), roughness=0.2, emit_strength=4.0)
mat_tip = make_mat("TipRed", (1.0, 0.15, 0.15), roughness=0.3)
mat_ground = make_mat("Ground", (0.85, 0.85, 0.82), roughness=0.9)
mat_metal = make_mat("Metal", (0.6, 0.62, 0.66), roughness=0.3)


# ---------- Helpers ----------
def link(obj):
    scene.collection.objects.link(obj)
    return obj


def cube(name, loc, scale, mat, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    return o


def cyl(name, loc, radius, depth, mat, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


def sphere(name, loc, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=24, ring_count=12)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


def limb_center(p0, angle, length):
    d = (math.sin(angle), 0.0, math.cos(angle))
    return (p0[0] + d[0] * length / 2, p0[1], p0[2] + d[2] * length / 2), d


def limb(name, p0, angle, length, radius, mat):
    center, _ = limb_center(p0, angle, length)
    return cyl(name, center, radius, length, mat, rot=(0.0, angle, 0.0))


def make_pivot(name, loc, rot_y):
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.empty_display_size = 0.2
    empty.location = loc
    empty.rotation_euler = (0.0, rot_y, 0.0)
    link(empty)
    world = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rot_y, 4, 'Y')
    return empty, world


def parent_to(child, parent, parent_world):
    child.parent = parent
    child.matrix_parent_inverse = parent_world.inverted()


# ---------- Robot body ----------
torso = cube("Torso", (0.0, 0.0, 1.6), (0.6, 0.45, 0.8), mat_body)
belly = cube("BeltPlate", (0.0, -0.46, 1.5), (0.3, 0.03, 0.18), mat_accent)

neck = cyl("Neck", (0.0, 0.0, 2.2), 0.08, 0.9, mat_metal)

head = cube("Head", (0.0, 0.0, 2.85), (0.55, 0.5, 0.45), mat_body)
eye_l = cyl("EyeL", (-0.18, -0.27, 2.9), 0.09, 0.04, mat_eye, rot=(math.pi / 2, 0.0, 0.0))
eye_r = cyl("EyeR", (0.18, -0.27, 2.9), 0.09, 0.04, mat_eye, rot=(math.pi / 2, 0.0, 0.0))
mouth = cube("Mouth", (0.0, -0.27, 2.68), (0.25, 0.02, 0.05), mat_dark)

antenna = cyl("Antenna", (0.0, 0.0, 3.3), 0.03, 0.5, mat_metal)
antenna_tip = sphere("AntennaTip", (0.0, 0.0, 3.6), 0.08, mat_tip)

# Legs and feet
for side, x in (("L", -0.22), ("R", 0.22)):
    cyl(f"Leg{side}", (x, 0.0, 0.7), 0.1, 0.8, mat_metal)
    cube(f"Foot{side}", (x, -0.05, 0.15), (0.2, 0.35, 0.15), mat_accent)

# Left arm, hanging relaxed
left_angle = math.pi + 0.15
limb("UpperArmL", (-0.75, 0.0, 2.0), left_angle, 0.85, 0.09, mat_metal)
hand_l_center, d_l = limb_center((-0.75, 0.0, 2.0), left_angle, 0.85)
cyl("HandL", (hand_l_center[0] + d_l[0] * 0.5, 0.0, hand_l_center[2] + d_l[2] * 0.5 + 0.0),
    0.12, 0.18, mat_accent, rot=(0.0, left_angle, 0.0))

# ---------- Right arm raised in a wave ----------
shoulder_pos = (0.75, 0.0, 2.0)
shoulder_angle = 0.6
upper_len = 0.8
forearm_len = 0.7
rest_elbow = 0.9  # total forearm angle at rest

# Upper arm (static, tilted outward and up)
limb("UpperArmR", shoulder_pos, shoulder_angle, upper_len, 0.1, mat_body)
d_up = (math.sin(shoulder_angle), 0.0, math.cos(shoulder_angle))
elbow_pos = (shoulder_pos[0] + d_up[0] * upper_len, 0.0, shoulder_pos[2] + d_up[2] * upper_len)

# Shoulder joint sphere
sphere("ShoulderR", shoulder_pos, 0.12, mat_accent)

# Elbow pivot
elbow, elbow_world = make_pivot("ElbowR", elbow_pos, rest_elbow)

# Forearm, child of elbow pivot
forearm_center, _ = limb_center(elbow_pos, rest_elbow, forearm_len)
forearm = cyl("ForearmR", forearm_center, 0.09, forearm_len, mat_body, rot=(0.0, rest_elbow, 0.0))
parent_to(forearm, elbow, elbow_world)

# Hand (mitt), child of elbow pivot
hand_offset = forearm_len + 0.1
hand_center = (elbow_pos[0] + math.sin(rest_elbow) * hand_offset, 0.0,
               elbow_pos[2] + math.cos(rest_elbow) * hand_offset)
hand = cyl("HandR", hand_center, 0.13, 0.2, mat_accent, rot=(0.0, rest_elbow, 0.0))
parent_to(hand, elbow, elbow_world)

# Wave animation on the elbow pivot
FRAME_START = 1
FRAME_END = 48
wave_keys = [
    (1, 0.9),
    (12, 1.3),
    (24, 0.5),
    (36, 1.3),
    (48, 0.9),
]
for frame, angle in wave_keys:
    elbow.rotation_euler.y = angle
    elbow.keyframe_insert(data_path="rotation_euler", index=1, frame=frame)

scene.frame_start = FRAME_START
scene.frame_end = FRAME_END
scene.frame_set(FRAME_START)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=20.0, location=(0.0, 0.0, 0.0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(mat_ground)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(12)
sun = link(bpy.data.objects.new("KeySun", sun_data))
sun.location = (4.0, -5.0, 8.0)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))

fill_data = bpy.data.lights.new(name="FillArea", type='AREA')
fill_data.energy = 400
fill_data.size = 4.0
fill = link(bpy.data.objects.new("FillArea", fill_data))
fill.location = (-5.0, -4.0, 3.5)
fill.rotation_euler = (math.radians(70), 0.0, math.radians(-50))

rim_data = bpy.data.lights.new(name="RimArea", type='AREA')
rim_data.energy = 250
rim_data.size = 3.0
rim = link(bpy.data.objects.new("RimArea", rim_data))
rim.location = (0.0, 5.0, 4.0)
rim.rotation_euler = (math.radians(-60), 0.0, math.radians(180))

# ---------- World background ----------
world = bpy.data.worlds.new("SkyWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.62, 0.8, 0.95, 1.0)
bg.inputs["Strength"].default_value = 0.8
scene.world = world

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("RobotCam")
cam_data.lens = 50
cam = link(bpy.data.objects.new("RobotCam", cam_data))
cam.location = (5.5, -8.0, 3.0)
target = Vector((0.0, 0.0, 1.9))
direction = target - Vector(cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
