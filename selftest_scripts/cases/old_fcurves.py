# category: anim
# expect: AttributeError
# expect_message: fcurves
# Legacy action.fcurves (removed in 5.0). Must fail on 5.2.
import bpy
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, 60
bpy.ops.mesh.primitive_uv_sphere_add()
ball = bpy.context.active_object
ball.keyframe_insert("location", frame=1); ball.location.x = 5; ball.keyframe_insert("location", frame=60)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); scene.collection.objects.link(cam); scene.camera = cam
for fc in ball.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"
