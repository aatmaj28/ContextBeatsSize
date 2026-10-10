import bpy
import math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene

# Clear default objects
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Timeline: animation runs over 30 frames
scene.frame_start = 1
scene.frame_end = 30
scene.render.fps = 30

# World background
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.03, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Material
mat = bpy.data.materials.new("HelloMaterial")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.95, 0.45, 0.1, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.3
    bsdf.inputs["Roughness"].default_value = 0.25

# Text object
text_curve = bpy.data.curves.new("HelloText", type='FONT')
text_curve.body = "HELLO"
text_curve.align_x = 'CENTER'
text_curve.align_y = 'CENTER'
text_curve.extrude = 0.08
text_curve.bevel_depth = 0.01
text_curve.bevel_resolution = 3
text_curve.size = 1.0

text_obj = bpy.data.objects.new("HelloText", text_curve)
scene.collection.objects.link(text_obj)
text_obj.data.materials.append(mat)
text_obj.location = (0.0, 0.0, 0.0)

# Start at zero scale
text_obj.scale = (0.0, 0.0, 0.0)
text_obj.keyframe_insert(data_path="scale", frame=1)

# Full size at frame 30
text_obj.scale = (1.0, 1.0, 1.0)
text_obj.keyframe_insert(data_path="scale", frame=30)

# Apply elastic easing to the scale F-Curves
action = text_obj.animation_data.action
action_slot = text_obj.animation_data.action_slot
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, action_slot)

for fcurve in channelbag.fcurves:
    if fcurve.data_path != "scale":
        continue
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'ELASTIC'
        kp.easing = 'EASE_OUT'
    fcurve.update()

# Lighting
key_data = bpy.data.lights.new("KeySun", type='SUN')
key_data.energy = 3.0
key_obj = bpy.data.objects.new("KeySun", key_data)
scene.collection.objects.link(key_obj)
key_obj.rotation_euler = (math.radians(50), 0.0, math.radians(30))

fill_data = bpy.data.lights.new("FillArea", type='AREA')
fill_data.energy = 400.0
fill_data.size = 6.0
fill_obj = bpy.data.objects.new("FillArea", fill_data)
scene.collection.objects.link(fill_obj)
fill_obj.location = (-4.0, -6.0, 4.0)
direction = Vector((0.0, 0.0, 0.0)) - fill_obj.location
fill_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# Camera framing the text
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_obj.location = (0.0, -9.0, 1.0)
target = Vector((0.0, 0.0, 0.0))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# Start the timeline at the first frame
scene.frame_set(1)
