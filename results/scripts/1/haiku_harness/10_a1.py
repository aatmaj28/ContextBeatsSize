import bpy
import bmesh
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Clean up the default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

# ---------- Helpers ----------
def make_material(name, color, rough=0.5, metal=0.0, emit=None, emit_strength=0.0):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat

def make_obj(name, kind, loc, scale, mat, rot=(0.0, 0.0, 0.0), smooth=False, collection=None):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    if kind == 'cube':
        bmesh.ops.create_cube(bm, size=1.0)
    else:  # cylinder: diameter 1, height 1, centered on origin
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=28,
                              radius1=0.5, radius2=0.5, depth=1.0)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.scale = scale
    obj.rotation_euler = rot
    (collection or scene.collection).objects.link(obj)
    return obj

# ---------- Materials ----------
mat_body   = make_material("BodyBlue",   (0.20, 0.45, 0.85), rough=0.35, metal=0.3)
mat_white  = make_material("HeadWhite",  (0.92, 0.92, 0.95), rough=0.4)
mat_gray   = make_material("JointGray",  (0.45, 0.47, 0.50), rough=0.5, metal=0.6)
mat_dark   = make_material("DarkPanel",  (0.08, 0.08, 0.10), rough=0.6)
mat_eye    = make_material("EyeGlow",    (0.2, 0.9, 1.0), rough=0.2,
                           emit=(0.2, 0.9, 1.0), emit_strength=6.0)
mat_chest  = make_material("ChestGlow",  (0.2, 1.0, 0.4), rough=0.3,
                           emit=(0.2, 1.0, 0.4), emit_strength=3.0)
mat_red    = make_material("AntennaRed", (1.0, 0.2, 0.15), rough=0.3,
                           emit=(1.0, 0.2, 0.15), emit_strength=2.5)
mat_yellow = make_material("HandYellow", (1.0, 0.75, 0.15), rough=0.4)
mat_ground = make_material("Ground",     (0.75, 0.75, 0.72), rough=0.9)

robot = bpy.data.collections.new("Robot")
scene.collection.children.link(robot)
col = robot

# ---------- Ground ----------
make_obj("Ground", 'cube', (0, 0, -0.05), (9, 9, 0.1), mat_ground, collection=scene.collection)

# ---------- Body ----------
make_obj("Body", 'cube', (0, 0, 1.3), (1.0, 0.8, 1.2), mat_body, collection=col)
make_obj("ChestPanel", 'cube', (0, -0.41, 1.3), (0.5, 0.04, 0.5), mat_dark, collection=col)
make_obj("ChestLight", 'cube', (0, -0.44, 1.3), (0.22, 0.03, 0.22), mat_chest, collection=col)
make_obj("BeltStripe", 'cube', (0, 0, 0.85), (1.02, 0.82, 0.12), mat_gray, collection=col)

# ---------- Neck & Head ----------
make_obj("Neck", 'cylinder' if False else 'cube', (0, 0, 2.38), (0.5, 0.5, 0.2), mat_gray, collection=col)
make_obj("Head", 'cube', (0, 0, 2.85), (1.0, 0.9, 0.8), mat_white, collection=col)
make_obj("EyeL", 'cube', (-0.25, -0.46, 2.92), (0.22, 0.05, 0.22), mat_eye, collection=col)
make_obj("EyeR", 'cube', (0.25, -0.46, 2.92), (0.22, 0.05, 0.22), mat_eye, collection=col)
make_obj("Mouth", 'cube', (0, -0.46, 2.6), (0.42, 0.03, 0.07), mat_dark, collection=col)
make_obj("EarL", 'cylinder', (-0.52, 0, 2.85), (0.18, 0.18, 0.25), mat_gray,
         rot=(0, math.pi / 2, 0), smooth=True, collection=col)
make_obj("EarR", 'cylinder', (0.52, 0, 2.85), (0.18, 0.18, 0.25), mat_gray,
         rot=(0, math.pi / 2, 0), smooth=True, collection=col)

# Antenna
make_obj("AntennaStem", 'cylinder', (0, 0, 3.4), (0.07, 0.07, 0.45), mat_gray, smooth=True, collection=col)
make_obj("AntennaTip", 'cylinder', (0, 0, 3.7), (0.18, 0.18, 0.18), mat_red, smooth=True, collection=col)

# ---------- Legs & Feet ----------
for side, x in (("L", -0.3), ("R", 0.3)):
    make_obj(f"Leg{side}", 'cylinder', (x, 0, 0.35), (0.22, 0.22, 0.7), mat_gray, smooth=True, collection=col)
    make_obj(f"Foot{side}", 'cube', (x, -0.1, 0.1), (0.4, 0.6, 0.2), mat_body, collection=col)

# ---------- Left arm (hanging, relaxed) ----------
SHOULDER_L = Vector((-0.72, 0.0, 1.8))
SHOULDER_R = Vector((0.72, 0.0, 1.8))

make_obj("ShoulderL", 'cylinder', SHOULDER_L, (0.2, 0.2, 0.2), mat_gray,
         rot=(0, math.pi / 2, 0), smooth=True, collection=col)
make_obj("UpperArmL", 'cylinder', SHOULDER_L + Vector((-0.05, 0, -0.45)), (0.16, 0.16, 0.9),
         mat_body, smooth=True, collection=col)
make_obj("ForearmL", 'cylinder', SHOULDER_L + Vector((-0.05, 0, -1.1)), (0.14, 0.14, 0.6),
         mat_white, smooth=True, collection=col)
make_obj("HandL", 'cube', SHOULDER_L + Vector((-0.05, 0, -1.5)), (0.28, 0.28, 0.28),
         mat_yellow, collection=col)

# ---------- Right arm (raised, waving) ----------
# Pivot empty at the shoulder; the arm hangs from it and rotates to wave.
pivot = bpy.data.objects.new("WaveShoulderPivot", None)
pivot.empty_display_type = 'PLAIN_AXES'
pivot.empty_display_size = 0.2
pivot.location = SHOULDER_R
col.objects.link(pivot)

def attach_to_pivot(obj):
    obj.parent = pivot
    obj.matrix_parent_inverse = pivot.matrix_world.inverted()

# Build arm parts in world space (pivot is unrotated at build time), then parent.
parts_r = []
parts_r.append(make_obj("ShoulderR", 'cylinder', SHOULDER_R, (0.2, 0.2, 0.2), mat_gray,
                        rot=(0, math.pi / 2, 0), smooth=True, collection=col))
parts_r.append(make_obj("UpperArmR", 'cylinder', SHOULDER_R + Vector((0.05, 0, 0.45)),
                        (0.16, 0.16, 0.9), mat_body, smooth=True, collection=col))
parts_r.append(make_obj("ForearmR", 'cylinder', SHOULDER_R + Vector((0.05, 0, 1.1)),
                        (0.14, 0.14, 0.6), mat_white, smooth=True, collection=col))
parts_r.append(make_obj("HandR", 'cube', SHOULDER_R + Vector((0.05, 0, 1.5)),
                        (0.3, 0.14, 0.3), mat_yellow, collection=col))
parts_r.append(make_obj("ThumbR", 'cylinder', SHOULDER_R + Vector((0.2, 0, 1.45)),
                        (0.07, 0.07, 0.22), mat_yellow, rot=(0, 0, math.radians(-35)),
                        smooth=True, collection=col))
for p in parts_r:
    attach_to_pivot(p)

# Wave animation: swing the raised arm side to side.
wave_keys = [
    (1, -0.35),
    (12, 0.25),
    (24, -0.35),
    (36, 0.25),
    (48, -0.35),
]
for frame, angle in wave_keys:
    pivot.rotation_euler = (0.0, angle, 0.0)
    pivot.keyframe_insert(data_path="rotation_euler", frame=frame)
pivot.rotation_euler = (0.0, wave_keys[0][1], 0.0)

# Little hop-free idle bob on the body group is skipped to keep the robot stable.

# ---------- World ----------
world = bpy.data.worlds.new("RobotWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1.0)
bg.inputs["Strength"].default_value = 0.8

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("KeySun", sun_data)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
scene.collection.objects.link(sun)

fill_data = bpy.data.lights.new(name="FillArea", type='AREA')
fill_data.energy = 600.0
fill_data.size = 4.0
fill = bpy.data.objects.new("FillArea", fill_data)
fill.location = (-4.0, -5.0, 4.0)
fill.rotation_euler = (math.radians(60), 0, math.radians(-40))
scene.collection.objects.link(fill)

rim_data = bpy.data.lights.new(name="RimArea", type='AREA')
rim_data.energy = 400.0
rim_data.size = 2.5
rim = bpy.data.objects.new("RimArea", rim_data)
rim.location = (3.0, 5.0, 4.0)
rim.rotation_euler = (math.radians(-55), 0, math.radians(150))
scene.collection.objects.link(rim)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("RobotCam")
cam_data.lens = 50
cam = bpy.data.objects.new("RobotCam", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((5.5, -7.5, 3.2))
target = Vector((0.0, 0.0, 2.0))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Timeline ----------
scene.frame_start = 1
scene.frame_end = 48
scene.frame_set(1)
