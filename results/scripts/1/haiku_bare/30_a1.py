import bpy
import math

# Clear default scene contents
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 30
scene.frame_set(1)

# Keyframe defaults: elastic easing, ease out
try:
    prefs = bpy.context.preferences.edit
    prefs.keyframe_new_interpolation_type = 'ELASTIC'
    prefs.keyframe_new_easing = 'EASE_OUT'
except Exception:
    pass

# Dark world background
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.03, 1.0)
    bg.inputs["Strength"].default_value = 1.0
scene.world = world

# Material
mat = bpy.data.materials.new("HelloMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (1.0, 0.45, 0.1, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.6
    bsdf.inputs["Roughness"].default_value = 0.25

# Text object
curve = bpy.data.curves.new(name="HelloText", type='FONT')
curve.body = "HELLO"
curve.size = 1.0
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.extrude = 0.08
curve.bevel_depth = 0.02
curve.bevel_resolution = 3
curve.materials.append(mat)

text_obj = bpy.data.objects.new("HELLO", curve)
scene.collection.objects.link(text_obj)
text_obj.location = (0.0, 0.0, 0.0)

# Scale animation: 0 -> 1 over 30 frames
text_obj.scale = (0.0, 0.0, 0.0)
text_obj.keyframe_insert(data_path="scale", frame=1)
text_obj.scale = (1.0, 1.0, 1.0)
text_obj.keyframe_insert(data_path="scale", frame=30)

# Explicitly enforce elastic easing on the created keys (if accessible)
try:
    action = text_obj.animation_data.action
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'ELASTIC'
            kp.easing = 'EASE_OUT'
        fc.update()
except Exception:
    pass

# Key light (sun)
sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("KeySun", sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.location = (3.0, -4.0, 6.0)
sun_obj.rotation_euler = (math.radians(35), 0.0, math.radians(30))

# Fill light (area)
area_data = bpy.data.lights.new(name="FillArea", type='AREA')
area_data.energy = 400.0
area_data.size = 6.0
area_obj = bpy.data.objects.new("FillArea", area_data)
scene.collection.objects.link(area_obj)
area_obj.location = (-4.0, -3.0, 5.0)
area_obj.rotation_euler = (math.radians(20), math.radians(-30), 0.0)

# Camera looking straight down at the text (text lies in XY plane)
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("MainCamera", cam_data)
scene.collection.objects.link(cam_obj)
cam_obj.location = (0.0, 0.0, 9.0)
cam_obj.rotation_euler = (0.0, 0.0, 0.0)
scene.camera = cam_obj
