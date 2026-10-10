import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Text
curve = bpy.data.curves.new("HelloText", 'FONT')
curve.body = "HELLO"
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.extrude = 0.15
curve.bevel_depth = 0.02
curve.bevel_resolution = 3
curve.size = 1.5
text = bpy.data.objects.new("HELLO", curve)
scene.collection.objects.link(text)
text.rotation_euler = (math.radians(90), 0, 0)
text.location = (0, 0, 1.0)

mat = bpy.data.materials.new("TextMat")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (1.0, 0.35, 0.1, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.3
    bsdf.inputs["Roughness"].default_value = 0.3
curve.materials.append(mat)

# Ground
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("GroundMat")
gb = gmat.node_tree.nodes.get("Principled BSDF")
if gb:
    gb.inputs["Base Color"].default_value = (0.08, 0.1, 0.15, 1.0)
    gb.inputs["Roughness"].default_value = 0.6
ground.data.materials.append(gmat)

# Animation: scale 0 -> 1 with elastic easing
scene.frame_start = 1
scene.frame_end = 60
text.scale = (0.0, 0.0, 0.0)
text.keyframe_insert("scale", frame=1)
text.scale = (1.0, 1.0, 1.0)
text.keyframe_insert("scale", frame=31)

ad = text.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
if cb:
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'ELASTIC'
            kp.easing = 'EASE_OUT'
            kp.amplitude = 0.0
            kp.period = 6.0

# Lighting
key = bpy.data.lights.new("Key", 'AREA')
key.energy = 800
key.size = 4
ko = bpy.data.objects.new("Key", key)
ko.location = (4, -6, 6)
ko.rotation_euler = (math.radians(50), 0, math.radians(35))
scene.collection.objects.link(ko)

fill = bpy.data.lights.new("Fill", 'AREA')
fill.energy = 300
fill.size = 5
fo = bpy.data.objects.new("Fill", fill)
fo.location = (-5, -5, 3)
fo.rotation_euler = (math.radians(65), 0, math.radians(-45))
scene.collection.objects.link(fo)

rim = bpy.data.lights.new("Rim", 'POINT')
rim.energy = 500
ro = bpy.data.objects.new("Rim", rim)
ro.location = (0, 4, 4)
scene.collection.objects.link(ro)

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.03, 0.06, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -10, 2.2)
scene.collection.objects.link(cam)
target = bpy.data.objects.new("Target", None)
target.location = (0, 0, 1.0)
scene.collection.objects.link(target)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_set(1)
