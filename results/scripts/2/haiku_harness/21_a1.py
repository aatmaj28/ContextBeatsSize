import bpy
import bmesh
import math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 24


# ---------- Helpers ----------
def make_principled_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def link_object(obj):
    scene.collection.objects.link(obj)
    return obj


# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
bg.inputs["Strength"].default_value = 0.6


# ---------- Floor ----------
floor_mesh = bpy.data.meshes.new("FloorMesh")
half = 12.0
floor_mesh.from_pydata(
    [(-half, -half, 0.0), (half, -half, 0.0), (half, half, 0.0), (-half, half, 0.0)],
    [],
    [(0, 1, 2, 3)],
)
floor_mesh.update()
floor = link_object(bpy.data.objects.new("Floor", floor_mesh))
floor.data.materials.append(make_principled_material("FloorMat", (0.7, 0.7, 0.72), roughness=0.8))


# ---------- Ball ----------
RADIUS = 0.5
ball_mesh = bpy.data.meshes.new("BallMesh")
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=RADIUS)
bm.to_mesh(ball_mesh)
bm.free()
for poly in ball_mesh.polygons:
    poly.use_smooth = True
ball_mesh.update()

ball = link_object(bpy.data.objects.new("Ball", ball_mesh))
ball.data.materials.append(make_principled_material("BallMat", (0.9, 0.25, 0.1), roughness=0.3))

# Bounce keyframes: (frame, height_z, x_position_override or None)
# Ball travels from x = -5 (frame 1) to x = 5 (frame 60).
X_START, X_END = -5.0, 5.0
bounce_keys = [
    (1,  4.0),   # release from height
    (10, RADIUS),  # first contact with floor
    (18, 2.6),   # bounce 1 apex
    (26, RADIUS),  # contact
    (33, 1.5),   # bounce 2 apex
    (40, RADIUS),  # contact
    (46, 0.9),   # bounce 3 apex
    (52, RADIUS),  # final contact
    (60, RADIUS),  # rest on floor
]

ball.animation_data_create()
for frame, z in bounce_keys:
    t = (frame - 1) / (60 - 1)
    x = X_START + (X_END - X_START) * t
    ball.location = Vector((x, 0.0, z))
    ball.keyframe_insert(data_path="location", frame=frame)

# Set every keyframe to linear interpolation
action = ball.animation_data.action
slot = ball.animation_data.action_slot
channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
if channelbag is not None:
    for fcurve in channelbag.fcurves:
        for kp in fcurve.keyframe_points:
            kp.interpolation = 'LINEAR'
        fcurve.update()


# ---------- Lighting ----------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.0
sun = link_object(bpy.data.objects.new("KeySun", sun_data))
sun.location = (4.0, -6.0, 10.0)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(25))

area_data = bpy.data.lights.new("FillArea", 'AREA')
area_data.energy = 400.0
area_data.size = 6.0
area = link_object(bpy.data.objects.new("FillArea", area_data))
area.location = (-6.0, -6.0, 7.0)
area.rotation_euler = (math.radians(60), 0.0, math.radians(-45))


# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = link_object(bpy.data.objects.new("Camera", cam_data))
cam.location = Vector((0.0, -16.0, 5.0))

target = Vector((0.0, 0.0, 1.5))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
