import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 24

# Text
curve = bpy.data.curves.new("HelloText", type='FONT')
curve.body = "HELLO"
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.size = 1.5
curve.extrude = 0.15
curve.bevel_depth = 0.03
curve.bevel_resolution = 3
text = bpy.data.objects.new("HELLO", curve)
scene.collection.objects.link(text)
text.rotation_euler = (math.radians(90), 0, 0)
text.location = (0, 0, 1.2)

mat = bpy.data.materials.new("TextMat")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (1.0, 0.35, 0.1, 1)
bsdf.inputs["Roughness"].default_value = 0.3
bsdf.inputs["Metallic"].default_value = 0.2
curve.materials.append(mat)

# Floor
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
floor = bpy.context.active_object
fmat = bpy.data.materials.new("FloorMat")
fb = fmat.node_tree.nodes.get("Principled BSDF")
fb.inputs["Base Color"].default_value = (0.08, 0.1, 0.15, 1)
fb.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(fmat)

# Animation: scale 0 -> 1 over 30 frames with elastic easing
text.scale = (0, 0, 0)
text.keyframe_insert("scale", frame=1)
text.scale = (1, 1, 1)
text.keyframe_insert("scale", frame=30)

ad = text.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
for fc in cb.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'ELASTIC'
        kp.easing = 'EASE_OUT'
        kp.amplitude = 0.0
        kp.period = 4.0

# Lights
key = bpy.data.lights.new("Key", 'AREA')
key.energy = 800
key.size = 5
ko = bpy.data.objects.new("Key", key)
ko.location = (4, -6, 6)
ko.rotation_euler = (math.radians(50), 0, math.radians(35))
scene.collection.objects.link(ko)

fill = bpy.data.lights.new("Fill", 'AREA')
fill.energy = 300
fill.size = 6
fo = bpy.data.objects.new("Fill", fill)
fo.location = (-5, -5, 3)
fo.rotation_euler = (math.radians(65), 0, math.radians(-45))
scene.collection.objects.link(fo)

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.03, 0.04, 0.07, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -12, 2.2)
cam.rotation_euler = (math.radians(85), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

scene.frame_set(1)
