import bpy
import math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60

# Clean scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# Materials
def make_mat(name, color, rough=0.5):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = rough
    return m

floor_mat = make_mat("FloorMat", (0.55, 0.55, 0.6, 1.0), 0.8)
ball_mat = make_mat("BallMat", (0.9, 0.15, 0.1, 1.0), 0.3)

# Floor
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)

# Ball
R = 0.5
bpy.ops.mesh.primitive_uv_sphere_add(radius=R, segments=48, ring_count=24, location=(-6, 0, 3))
ball = bpy.context.active_object
ball.name = "Ball"
bpy.ops.object.shade_smooth()
ball.data.materials.append(ball_mat)

# Keyframes: start high, 3 floor contacts, end high
keys = [
    (1,  -6.0, 3.5),
    (10, -4.0, R),
    (20, -2.0, 3.0),
    (30,  0.0, R),
    (40,  2.0, 2.5),
    (50,  4.0, R),
    (60,  6.0, 2.0),
]
for f, x, z in keys:
    ball.location = (x, 0.0, z)
    ball.keyframe_insert(data_path="location", frame=f)

# Linear interpolation on every keyframe
ad = ball.animation_data
if ad and ad.action:
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    if cb:
        for fc in cb.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
            fc.update()

# Lighting
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))
scene.collection.objects.link(sun)

area_data = bpy.data.lights.new("Fill", type='AREA')
area_data.energy = 500
area_data.size = 6
area = bpy.data.objects.new("Fill", area_data)
area.location = (-5, -6, 7)
area.rotation_euler = (Vector((0, 0, 1)) - area.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(area)

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.07, 0.1, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -15, 4.5)
target = Vector((0, 0, 1.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(cam)
scene.camera = cam

scene.frame_set(1)
