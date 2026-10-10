# category: materials
# expect: check_failed
# expect_message: material
import bpy
scene = bpy.context.scene
bpy.ops.mesh.primitive_cube_add()
bpy.data.materials.new("Unused")  # created but never assigned
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); scene.collection.objects.link(cam); scene.camera = cam
