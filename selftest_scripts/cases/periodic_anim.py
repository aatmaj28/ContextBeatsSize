# category: anim
# expect: pass
# Blades do exactly 2 turns over frames 0-120, so frame 60 matches frame 0. Correct script; must pass.
import bpy, math
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 0, 120
bpy.ops.mesh.primitive_cube_add(scale=(0.1, 2, 0.3))
blades = bpy.context.active_object
blades.rotation_euler.x = 0; blades.keyframe_insert("rotation_euler", index=0, frame=0)
blades.rotation_euler.x = 4 * math.pi; blades.keyframe_insert("rotation_euler", index=0, frame=120)
for kp in blades.animation_data.action.layers[0].strips[0].channelbag(blades.animation_data.action_slot).fcurves[0].keyframe_points:
    kp.interpolation = "LINEAR"
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); cam.location = (8, 0, 0); scene.collection.objects.link(cam); scene.camera = cam
