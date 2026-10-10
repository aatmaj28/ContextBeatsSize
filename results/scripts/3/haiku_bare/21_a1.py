import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Start from a clean scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Make every newly inserted keyframe use linear interpolation
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

# ---------- Materials ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat

floor_mat = make_material("FloorMat", (0.8, 0.8, 0.78), roughness=0.8)
ball_mat = make_material("BallMat", (0.9, 0.25, 0.1), roughness=0.3)

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.scale = (20, 20, 1)
floor.data.materials.append(floor_mat)

# ---------- Ball ----------
RADIUS = 0.5
bpy.ops.mesh.primitive_uv_sphere_add(radius=RADIUS, segments=48, ring_count=24,
                                     location=(-4.5, 0, RADIUS))
ball = bpy.context.active_object
ball.name = "Ball"
ball.data.materials.append(ball_mat)
bpy.ops.object.shade_smooth()

# ---------- Keyframe data ----------
# Contacts at frames 1, 20, 39, 60 (three bounces); apexes at 10, 30, 50
key_frames = [1, 10, 20, 30, 39, 50, 60]
key_z = [RADIUS, 3.5, RADIUS, 2.4, RADIUS, 1.6, RADIUS]

X_START, X_END = -4.5, 4.5
F_START, F_END = 1, 60

def x_at(frame):
    t = (frame - F_START) / (F_END - F_START)
    return X_START + (X_END - X_START) * t

# Insert location keys for the ball
for f, z in zip(key_frames, key_z):
    ball.location = (x_at(f), 0.0, z)
    ball.keyframe_insert(data_path="location", frame=f)

# Safety pass: force LINEAR on every keyframe of the ball's action
anim = ball.animation_data
if anim and anim.action:
    try:
        for fc in anim.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    except AttributeError:
        # Layered/slotted actions: iterate through the channelbags instead
        for layer in anim.action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = 'LINEAR'

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(-6, -6, 8))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 300.0
fill.data.size = 6.0
fill.rotation_euler = (math.radians(60), 0, math.radians(-45))

# World background so the scene is not pitch black
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.6, 0.7, 0.85, 1.0)
    bg.inputs["Strength"].default_value = 0.6

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.0, -13.0, 4.5)

target = Vector((0.0, 0.0, 1.5))
direction = target - Vector(cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam_data.lens = 50
scene.camera = cam

# ---------- Timeline ----------
scene.frame_start = F_START
scene.frame_end = F_END
scene.frame_set(F_START)
