import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 60

# Make all newly inserted keys linear
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass

# Floor
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor_mat = bpy.data.materials.new("FloorMat")
floor_mat.use_nodes = True
bsdf = floor_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.55, 0.55, 0.6, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(floor_mat)

# Ball
radius = 0.5
bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=48, ring_count=24, location=(-6, 0, 4))
ball = bpy.context.active_object
ball.name = "Ball"
bpy.ops.object.shade_smooth()
ball_mat = bpy.data.materials.new("BallMat")
ball_mat.use_nodes = True
bsdf = ball_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.9, 0.15, 0.1, 1)
    bsdf.inputs["Roughness"].default_value = 0.3
ball.data.materials.append(ball_mat)

# Keyframes: start high, three ground contacts with decreasing bounce heights
ground = radius
keys = [
    (1, 4.0),
    (15, ground),   # bounce 1
    (25, 3.0),
    (35, ground),   # bounce 2
    (45, 2.0),
    (55, ground),   # bounce 3
    (60, 1.2),
]
x_start, x_end = -6.0, 6.0
for frame, z in keys:
    t = (frame - 1) / 59.0
    ball.location = (x_start + (x_end - x_start) * t, 0, z)
    ball.keyframe_insert(data_path="location", frame=frame)

# Force linear interpolation on every keyframe (supports layered/legacy actions)
def iter_fcurves(action, anim_data):
    try:
        for fc in action.fcurves:
            yield fc
        return
    except Exception:
        pass
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        yield fc
    except Exception:
        pass

ad = ball.animation_data
if ad and ad.action:
    for fc in iter_fcurves(ad.action, ad):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), 0, math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(-4, -6, 6))
fill = bpy.context.active_object
fill.data.energy = 300
fill.data.size = 5
fill.rotation_euler = (math.radians(55), 0, math.radians(-35))

# World
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.7, 0.8, 0.95, 1)
    bg.inputs["Strength"].default_value = 0.5

# Camera
bpy.ops.object.camera_add(location=(0, -16, 4))
cam = bpy.context.active_object
target = Vector((0, 0, 1.6))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 35
scene.camera = cam

scene.frame_set(1)
