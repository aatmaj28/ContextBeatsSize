import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 24

# Make new keyframes linear by default
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
    bsdf.inputs["Base Color"].default_value = (0.75, 0.75, 0.72, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(floor_mat)

# Ball
radius = 0.5
bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=48, ring_count=24, location=(-6, 0, 3))
ball = bpy.context.active_object
ball.name = "Ball"
bpy.ops.object.shade_smooth()
ball_mat = bpy.data.materials.new("BallMat")
ball_mat.use_nodes = True
bsdf = ball_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.85, 0.12, 0.08, 1)
    bsdf.inputs["Roughness"].default_value = 0.3
ball.data.materials.append(ball_mat)

# Keyframes: (frame, x, z) — three floor contacts at frames 10, 30, 50
keys = [
    (1, -6.0, 3.0),
    (10, -4.2, radius),
    (20, -2.2, 2.4),
    (30, -0.2, radius),
    (40, 1.8, 1.8),
    (50, 3.8, radius),
    (60, 5.8, 1.3),
]
for f, x, z in keys:
    ball.location = (x, 0, z)
    ball.keyframe_insert(data_path="location", frame=f)

# Force linear interpolation on every keyframe
def iter_fcurves(action):
    if hasattr(action, "fcurves"):
        try:
            for fc in action.fcurves:
                yield fc
            return
        except Exception:
            pass
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                for fc in cb.fcurves:
                    yield fc

for action in bpy.data.actions:
    for fc in iter_fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()

# Lighting
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))

area_data = bpy.data.lights.new("Fill", type='AREA')
area_data.energy = 400
area_data.size = 6
fill = bpy.data.objects.new("Fill", area_data)
scene.collection.objects.link(fill)
fill.location = (-4, -6, 6)
fill.rotation_euler = (Vector((0, 0, 1)) - fill.location).to_track_quat('-Z', 'Y').to_euler()

# World
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.6, 0.7, 0.85, 1)
    bg.inputs["Strength"].default_value = 0.5

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -15, 3.5)
target = Vector((0, 0, 1.3))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_set(1)
