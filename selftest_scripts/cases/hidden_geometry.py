# category: basic
# expect: check_failed
# expect_message: visible geometry
import bpy
scene = bpy.context.scene
bpy.ops.mesh.primitive_cube_add()
bpy.context.active_object.hide_render = True
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); scene.collection.objects.link(cam); scene.camera = cam
