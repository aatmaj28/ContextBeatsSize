# category: world
# expect: check_failed
# expect_message: beyond the default
import bpy
scene = bpy.context.scene
bpy.ops.mesh.primitive_cube_add()
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); scene.collection.objects.link(cam); scene.camera = cam
scene.world = bpy.data.worlds.new("W")
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.2, 0.3, 0.8, 1)
