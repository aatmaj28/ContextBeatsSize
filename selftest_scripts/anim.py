# Known good Blender 5.2 script, category: anim. Ball bouncing three times over 60 frames, linear keys.
import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 60

bpy.ops.mesh.primitive_plane_add(size=20)
mat = bpy.data.materials.new("Red")
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.9, 0.1, 0.1, 1.0)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5)
ball = bpy.context.active_object
ball.data.materials.append(mat)

frames = [1, 10, 20, 30, 40, 50, 60]
for i, f in enumerate(frames):
    x = -6 + 12 * (f - 1) / 59
    z = 0.5 if i % 2 == 0 else 3.0
    ball.location = (x, 0, z)
    ball.keyframe_insert(data_path="location", frame=f)

# 5.0+: action.fcurves is gone; F-Curves live in the channelbag of the action slot.
ad = ball.animation_data
channelbag = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
for fc in channelbag.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", type="SUN"))
sun.rotation_euler = (math.radians(45), 0, math.radians(20))
scene.collection.objects.link(sun)

cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -16, 3)
cam.rotation_euler = (math.radians(85), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam
