import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene

# Clear default objects
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Text object ----------
text_curve = bpy.data.curves.new("HELLO_Text", 'FONT')
text_curve.body = "HELLO"
text_curve.size = 1.0
text_curve.extrude = 0.08
text_curve.bevel_depth = 0.02
text_curve.bevel_resolution = 3
text_curve.align_x = 'CENTER'
text_curve.align_y = 'CENTER'

text_obj = bpy.data.objects.new("HELLO", text_curve)
scene.collection.objects.link(text_obj)

# Stand the text up, facing the camera (-Y side), readable along +X
text_obj.rotation_euler = (math.radians(90), 0.0, 0.0)

# Material
mat = bpy.data.materials.new("HELLO_Material")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (1.0, 0.45, 0.1, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Metallic"].default_value = 0.0
text_curve.materials.append(mat)

# ---------- Animation: scale 0 -> 1 over 30 frames ----------
scene.frame_start = 1
scene.frame_end = 30

text_obj.scale = (0.0, 0.0, 0.0)
text_obj.keyframe_insert(data_path="scale", frame=1)

text_obj.scale = (1.0, 1.0, 1.0)
text_obj.keyframe_insert(data_path="scale", frame=30)

action = text_obj.animation_data.action
slot = text_obj.animation_data.action_slot
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, slot)

for fcurve in channelbag.fcurves:
    if fcurve.data_path == "scale":
        for kp in fcurve.keyframe_points:
            kp.interpolation = 'ELASTIC'
            kp.easing = 'EASE_OUT'
        fcurve.update()

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.03, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Lights ----------
key_light_data = bpy.data.lights.new("KeyLight", 'AREA')
key_light_data.energy = 800.0
key_light_data.size = 6.0
key_light = bpy.data.objects.new("KeyLight", key_light_data)
scene.collection.objects.link(key_light)
key_light.location = (3.0, -6.0, 4.0)
key_light.rotation_euler = (math.radians(60), 0.0, math.radians(20))

fill_data = bpy.data.lights.new("FillLight", 'AREA')
fill_data.energy = 250.0
fill_data.size = 8.0
fill_light = bpy.data.objects.new("FillLight", fill_data)
scene.collection.objects.link(fill_light)
fill_light.location = (-5.0, -5.0, 1.5)
fill_light.rotation_euler = (math.radians(80), 0.0, math.radians(-40))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_obj.location = (0.0, -8.0, 0.0)
cam_obj.rotation_euler = (math.radians(90), 0.0, 0.0)
scene.camera = cam_obj
