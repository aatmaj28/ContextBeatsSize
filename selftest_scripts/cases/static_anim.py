# category: anim
# expect: check_failed
# expect_message: nothing animates
import bpy
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, 60
bpy.ops.mesh.primitive_uv_sphere_add()
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); cam.location = (0, -8, 0); scene.collection.objects.link(cam); scene.camera = cam
