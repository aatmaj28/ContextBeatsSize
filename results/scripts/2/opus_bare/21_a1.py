import bpy
import math

scene = bpy.context.scene

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Default new keyframes to linear interpolation
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass

scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 24

# Materials
floor_mat = bpy.data.materials.new("FloorMat")
floor_mat.use_nodes = True
bsdf = floor_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.6, 0.6, 0.65, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.6

ball_mat = bpy.data.materials.new("BallMat")
ball_mat.use_nodes = True
bsdf = ball_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.9, 0.15, 0.1, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.3

# Floor
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)

# Ball
radius = 0.5
bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=48, ring_count=24, location=(-6, 0, 4))
ball = bpy.context.active_object
ball.name = "Ball"
bpy.ops.object.shade_smooth()
ball.data.materials.append(ball_mat)

# Keyframes: start high, three floor contacts (frames 10, 30, 50)
keys = [
    (1, 4.0),
    (10, radius),
    (20, 3.0),
    (30, radius),
    (40, 2.0),
    (50, radius),
    (60, 1.2),
]
x_start, x_end = -6.0, 6.0
for f, z in keys:
    t = (f - 1) / 59.0
    ball.location = (x_start + (x_end - x_start) * t, 0.0, z)
    ball.keyframe_insert(data_path="location", frame=f)

# Force linear interpolation on every keyframe (handles layered & legacy actions)
def iter_fcurves(action):
    try:
        for fc in action.fcurves:
            yield fc
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

if ball.animation_data and ball.animation_data.action:
    for fc in iter_fcurves(ball.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), 0, math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(-4, -6, 6))
area = bpy.context.active_object
area.data.energy = 400
area.data.size = 5
area.rotation_euler = (math.radians(50), 0, math.radians(-35))

# World
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)

# Camera
bpy.ops.object.camera_add(location=(0, -16, 4))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(82), 0, 0)
cam.data.lens = 35
scene.camera = cam
