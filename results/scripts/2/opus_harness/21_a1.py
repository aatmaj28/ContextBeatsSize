import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 60

# Materials
def make_mat(name, color, rough=0.5):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    return m

floor_mat = make_mat("Floor", (0.6, 0.6, 0.65, 1), 0.8)
ball_mat = make_mat("Ball", (0.9, 0.15, 0.1, 1), 0.3)

# Floor
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(floor_mat)

# Ball
r = 0.5
bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(-6, 0, 3), segments=48, ring_count=24)
ball = bpy.context.active_object
ball.name = "Ball"
bpy.ops.object.shade_smooth()
ball.data.materials.append(ball_mat)

# Keyframes: peak, contact x3, final peak
keys = [
    (1, 3.5),
    (10, r),
    (20, 2.6),
    (30, r),
    (40, 1.8),
    (50, r),
    (60, 1.2),
]
x0, x1 = -6.0, 6.0
for f, z in keys:
    t = (f - 1) / 59.0
    ball.location = (x0 + (x1 - x0) * t, 0, z)
    ball.keyframe_insert(data_path="location", frame=f)

# Linear interpolation on every keyframe
ad = ball.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
for fc in cb.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
    fc.update()

# Light
bpy.ops.object.light_add(type='SUN', location=(4, -4, 8))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), 0, math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(-3, -5, 5))
area = bpy.context.active_object
area.data.energy = 300
area.data.size = 4
area.rotation_euler = (math.radians(50), 0, math.radians(-30))

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)

# Camera
bpy.ops.object.camera_add(location=(0, -16, 4))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(82), 0, 0)
cam.data.lens = 40
scene.camera = cam

scene.frame_set(1)
