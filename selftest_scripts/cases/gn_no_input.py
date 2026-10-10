# category: gn
# expect: check_failed
# expect_message: no inputs besides Geometry
import bpy
scene = bpy.context.scene
ng = bpy.data.node_groups.new("G", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput"); ng.links.new(gi.outputs[0], go.inputs[0])
bpy.ops.mesh.primitive_plane_add()
mod = bpy.context.active_object.modifiers.new("GN", "NODES"); mod.node_group = ng
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); scene.collection.objects.link(cam); scene.camera = cam
