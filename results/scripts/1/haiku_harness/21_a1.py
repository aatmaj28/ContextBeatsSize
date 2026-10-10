import bpy
import math
from mathutils import Vector
from bpy_extras import anim_utils

# ---------- Clear the default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 61  # 60 frames of motion (i = 0..60)

# ---------- Materials ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)  # node tree created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

floor_mat = make_material("FloorMat", (0.75, 0.75, 0.72), roughness=0.8)
ball_mat = make_material("BallMat", (0.85, 0.15, 0.1), roughness=0.3)

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=24, location=(0.0, 0.0, 0.0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)

# ---------- Ball ----------
RADIUS = 0.5
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=RADIUS, segments=48, ring_count=24, location=(-4.0, 0.0, RADIUS)
)
ball = bpy.context.active_object
ball.name = "Ball"
bpy.ops.object.shade_smooth()
ball.data.materials.append(ball_mat)

# ---------- Animation ----------
# Three bounces: contacts at i = 0, 20, 40, 60 (frames 1, 21, 41, 61)
# Peak heights decay per bounce.
PEAKS = [3.0, 1.8, 0.9]
X_START, X_END = -4.0, 4.0
TOTAL = 60
SEG_LEN = 20

for i in range(TOTAL + 1):
    frame = 1 + i
    t = i / TOTAL
    x = X_START + (X_END - X_START) * t

    seg = min(i // SEG_LEN, len(PEAKS) - 1)
    seg_start = seg * SEG_LEN
    u = (i - seg_start) / SEG_LEN
    # Parabolic arc within each bounce, sampled every frame
    height = PEAKS[seg] * 4.0 * u * (1.0 - u)
    z = RADIUS + height

    ball.location = Vector((x, 0.0, z))
    ball.keyframe_insert(data_path="location", frame=frame)

    # Roll the ball according to distance travelled (no slipping)
    roll_angle = -(x - X_START) / RADIUS
    ball.rotation_euler = (0.0, roll_angle, 0.0)
    ball.keyframe_insert(data_path="rotation_euler", frame=frame)

# Set linear interpolation on every keyframe
action = ball.animation_data.action
slot = ball.animation_data.action_slot
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
for fcurve in channelbag.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'LINEAR'
    fcurve.update()

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), 0.0, math.radians(30))

area_data = bpy.data.lights.new(name="Fill", type='AREA')
area_data.energy = 800.0
area_data.size = 6.0
area_obj = bpy.data.objects.new("Fill", area_data)
scene.collection.objects.link(area_obj)
area_obj.location = (4.0, -6.0, 7.0)
area_obj.rotation_euler = (math.radians(60), 0.0, math.radians(35))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_obj.location = (0.0, -15.0, 5.5)

target = Vector((0.0, 0.0, 1.5))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# Start at the first frame
scene.frame_set(1)
