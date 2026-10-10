# category: compositor
# expect: AttributeError
# expect_message: node_tree
# Pre-5.0 compositor API. Must fail on 5.2.
import bpy
scene = bpy.context.scene
bpy.ops.mesh.primitive_cube_add()
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); scene.collection.objects.link(cam); scene.camera = cam
scene.use_nodes = True
tree = scene.node_tree
glare = tree.nodes.new("CompositorNodeGlare")
