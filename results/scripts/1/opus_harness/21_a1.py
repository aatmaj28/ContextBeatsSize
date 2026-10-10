import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 24

# Floor
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor_mat = bpy.data.materials.new("FloorMat")
bsdf = floor_mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.55, 0.55, 0.6, 1.0)
bsdf.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(floor_mat)

# Ball
radius = 0.5
bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=48, ring_count=24, location=(-6, 0, 3))
ball = bpy.context.active_object
ball.name = "Ball"
bpy.ops.object.shade_smooth()
ball_mat = bpy.data.materials.new("BallMat")
bb = ball_mat.node_tree.nodes.get("Principled BSDF")
bb.inputs["Base Color"].default_value = (0.85, 0.12, 0.08, 1.0)
bb.inputs["Roughness"].default_value = 0.3
ball.data.materials.append(ball_mat)

# Keyframes: start high, three floor contacts (frames 10, 30, 50)
keys = [
    (1, 3.5),
    (10, radius),
    (20, 2.6),
    (30, radius),
    (40, 1.7),
    (50, radius),
    (60, 1.0),
]
x_start, x_end = -6.0, 6.0
for f, z in keys:
    t = (f - 1) / 59.0
    ball.location = (x_start + (x_end - x_start) * t, 0.0, z)
    ball.keyframe_insert(data_path="location", frame=f)

# Linear interpolation on every keyframe
ad = ball.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
for fc in cb.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
    fc.update()

# Lighting
bpy.ops.object.light_add(type='SUN', location=(4, -4, 8))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), 0, math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(-4, -5, 5))
area = bpy.context.active_object
area.data.energy = 400
area.data.size = 4
area.rotation_euler = (math.radians(50), 0, math.radians(-35))

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.07, 0.1, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(0, -16, 4))
cam = bpy.context.active_object
cam.data.lens = 40
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 1.3)
scene.collection.objects.link(target)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_set(1)
