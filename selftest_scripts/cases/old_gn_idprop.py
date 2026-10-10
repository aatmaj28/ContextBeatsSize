# category: gn
# expect: TypeError
# Pre-5.2 Geometry Nodes modifier input access via custom properties. Must fail on 5.2.
import bpy
scene = bpy.context.scene
ng = bpy.data.node_groups.new("G", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
s = ng.interface.new_socket("Density", in_out="INPUT", socket_type="NodeSocketFloat")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput"); ng.links.new(gi.outputs[0], go.inputs[0])
bpy.ops.mesh.primitive_plane_add()
mod = bpy.context.active_object.modifiers.new("GN", "NODES"); mod.node_group = ng
mod[s.identifier] = 10.0
