import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene

# Clear any default objects so the scene starts empty
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# --- World: dark neutral background ---
world = bpy.data.worlds.new("World")
scene.world = world
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs["Color"].default_value = (0.02, 0.02, 0.025, 1.0)
    bg_node.inputs["Strength"].default_value = 1.0

# --- Material: glossy warm metal-like color ---
mat = bpy.data.materials.new("HelloMaterial")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (1.0, 0.45, 0.1, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.3
    bsdf.inputs["Roughness"].default_value = 0.25

# --- Text object ---
text_curve = bpy.data.curves.new("HELLO", type='FONT')
text_curve.body = "HELLO"
text_curve.align_x = 'CENTER'
text_curve.align_y = 'CENTER'
text_curve.extrude = 0.08
text_curve.bevel_depth = 0.01
text_curve.bevel_resolution = 3
text_curve.size = 1.0

text_obj = bpy.data.objects.new("HELLO", text_curve)
scene.collection.objects.link(text_obj)
text_obj.data.materials.append(mat)

# Start invisible (scale zero), then keyframe scale up to full size
text_obj.scale = (0.0, 0.0, 0.0)
text_obj.keyframe_insert(data_path="scale", frame=1)

text_obj.scale = (1.0, 1.0, 1.0)
text_obj.keyframe_insert(data_path="scale", frame=30)

# --- Elastic easing on the scale F-Curves (Blender 5.x layered action API) ---
action = text_obj.animation_data.action
slot = text_obj.animation_data.action_slot
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)
for fcurve in channelbag.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'ELASTIC'
        kp.easing = 'EASE_OUT'
    fcurve.update()

# --- Lighting ---
key_data = bpy.data.lights.new(name="KeyLight", type='AREA')
key_data.energy = 800.0
key_data.size = 6.0
key_obj = bpy.data.objects.new("KeyLight", key_data)
scene.collection.objects.link(key_obj)
key_obj.location = (3.0, -6.0, 5.0)
key_obj.rotation_euler = (math.radians(60), 0.0, math.radians(30))

fill_data = bpy.data.lights.new(name="FillLight", type='AREA')
fill_data.energy = 250.0
fill_data.size = 8.0
fill_obj = bpy.data.objects.new("FillLight", fill_data)
scene.collection.objects.link(fill_obj)
fill_obj.location = (-5.0, -5.0, 2.0)
fill_obj.rotation_euler = (math.radians(75), 0.0, math.radians(-45))

# --- Camera framing the text head-on ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_obj.location = (0.0, -9.0, 0.0)
cam_obj.rotation_euler = (math.radians(90), 0.0, 0.0)
scene.camera = cam_obj

# --- Timeline ---
scene.frame_start = 1
scene.frame_end = 30
scene.frame_set(1)
