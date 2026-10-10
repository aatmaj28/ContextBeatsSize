# category: compositor
# expect: check_failed
# expect_message: no effect node
import bpy
scene = bpy.context.scene
bpy.ops.mesh.primitive_cube_add()
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); scene.collection.objects.link(cam); scene.camera = cam
tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); scene.compositing_node_group = tree
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = tree.nodes.new("CompositorNodeRLayers"); out = tree.nodes.new("NodeGroupOutput")
tree.links.new(rl.outputs["Image"], out.inputs["Image"])
