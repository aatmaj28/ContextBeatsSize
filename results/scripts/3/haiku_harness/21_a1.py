import bpy
import math
from bpy_extras import anim_utils
from mathutils import Vector

# ---------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

scene = bpy.context.scene

# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

floor_mat = make_material("FloorMat", (0.8, 0.8, 0.78), roughness=0.8)
ball_mat = make_material("BallMat", (0.9, 0.25, 0.1), roughness=0.35)

# ---------------------------------------------------------------
# Floor
# ---------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)

# ---------------------------------------------------------------
# Ball
# ---------------------------------------------------------------
R = 0.5
bpy.ops.mesh.primitive_uv_sphere_add(radius=R, segments=48, ring_count=24, location=(-6, 0, 4))
ball = bpy.context.active_object
ball.name = "Ball"
ball.data.materials.append(ball_mat)
for poly in ball.data.polygons:
    poly.use_smooth = True

# ---------------------------------------------------------------
# Bounce keyframes: (frame, x, z)
# Three impacts (z = R) separated by apexes; x advances across the floor.
# ---------------------------------------------------------------
keys = [
    (1,  -6.0, 4.0),   # drop start
    (12, -3.5, R),     # impact 1
    (20, -1.5, 2.5),   # apex 1
    (28,  0.5, R),     # impact 2
    (36,  2.5, 1.3),   # apex 2
    (44,  4.0, R),     # impact 3
    (52,  5.0, 0.6),   # apex 3
    (60,  6.0, R),     # final contact
]

scene.frame_start = 1
scene.frame_end = 60

for frame, x, z in keys:
    ball.location = (x, 0.0, z)
    ball.keyframe_insert(data_path="location", frame=frame)
    # Roll the ball according to horizontal travel (rolling without slipping)
    ball.rotation_euler = (0.0, -x / R, 0.0)
    ball.keyframe_insert(data_path="rotation_euler", frame=frame)

# ---------------------------------------------------------------
# Linear interpolation on every keyframe
# ---------------------------------------------------------------
def set_all_linear(obj):
    ad = obj.animation_data
    if ad is None or ad.action is None:
        return
    channelbag = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    if channelbag is None:
        return
    for fc in channelbag.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()

set_all_linear(ball)

# Also make newly inserted keys default to linear for good measure
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

# ---------------------------------------------------------------
# World
# ---------------------------------------------------------------
world = bpy.data.worlds.new("World")  # nodes created automatically
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.6, 0.7, 0.85, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.5
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0.0, math.radians(35))

area_data = bpy.data.lights.new(name="Fill", type='AREA')
area_data.energy = 400
area_data.size = 6
area = bpy.data.objects.new("Fill", area_data)
scene.collection.objects.link(area)
area.location = (-6, -8, 8)
area.rotation_euler = (math.radians(60), 0.0, math.radians(-30))

# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.0, -15.0, 6.0)

target = Vector((0.0, 0.0, 1.5))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
