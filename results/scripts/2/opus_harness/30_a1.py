import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60
scene.render.fps = 30

# --- Text ---
curve = bpy.data.curves.new("HelloText", type='FONT')
curve.body = "HELLO"
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.size = 1.5
curve.extrude = 0.15
curve.bevel_depth = 0.02
curve.bevel_resolution = 3
txt = bpy.data.objects.new("HELLO", curve)
scene.collection.objects.link(txt)
txt.rotation_euler = (math.radians(90), 0, 0)
txt.location = (0, 0, 1.2)

mat = bpy.data.materials.new("TextMat")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (1.0, 0.35, 0.08, 1)
bsdf.inputs["Roughness"].default_value = 0.3
bsdf.inputs["Metallic"].default_value = 0.2
curve.materials.append(mat)

# --- Animation: scale 0 -> 1 with elastic easing ---
txt.scale = (0.0, 0.0, 0.0)
txt.keyframe_insert("scale", frame=1)
txt.scale = (1.0, 1.0, 1.0)
txt.keyframe_insert("scale", frame=30)

ad = txt.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
for fc in cb.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'ELASTIC'
        kp.easing = 'EASE_OUT'
    fc.update()

# --- Floor / backdrop ---
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
floor = bpy.context.active_object
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 6, 10), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
fmat = bpy.data.materials.new("FloorMat")
fb = fmat.node_tree.nodes.get("Principled BSDF")
fb.inputs["Base Color"].default_value = (0.08, 0.1, 0.18, 1)
fb.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(fmat)
wall.data.materials.append(fmat)

# --- Lights ---
key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", 'AREA'))
key.data.energy = 600
key.data.size = 4
key.location = (-4, -6, 6)
key.rotation_euler = (math.radians(55), 0, math.radians(-35))
scene.collection.objects.link(key)

fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
fill.data.energy = 250
fill.data.size = 5
fill.data.color = (0.6, 0.75, 1.0)
fill.location = (5, -5, 3)
fill.rotation_euler = (math.radians(70), 0, math.radians(45))
scene.collection.objects.link(fill)

# --- World ---
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.02, 0.025, 0.04, 1)
bg.inputs["Strength"].default_value = 1.0

# --- Camera ---
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.lens = 50
cam.location = (0, -12, 2.2)
cam.rotation_euler = (math.radians(85), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

scene.frame_set(1)
