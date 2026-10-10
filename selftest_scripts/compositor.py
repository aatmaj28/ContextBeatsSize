# Known good Blender 5.2 script, category: compositor. Neon OPEN sign on a brick wall with Glare.
import bpy
import math

scene = bpy.context.scene

neon = bpy.data.materials.new("Neon")
n = neon.node_tree.nodes["Principled BSDF"]
n.inputs["Base Color"].default_value = (1.0, 0.1, 0.5, 1.0)
n.inputs["Emission Color"].default_value = (1.0, 0.1, 0.5, 1.0)
n.inputs["Emission Strength"].default_value = 15.0

brick = bpy.data.materials.new("Brick")
bnt = brick.node_tree
tex = bnt.nodes.new("ShaderNodeTexBrick")
tex.inputs["Color1"].default_value = (0.12, 0.04, 0.03, 1.0)
tex.inputs["Color2"].default_value = (0.08, 0.03, 0.02, 1.0)
bnt.links.new(tex.outputs["Color"], bnt.nodes["Principled BSDF"].inputs["Base Color"])

bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0.1, 0), rotation=(math.pi / 2, 0, 0))
bpy.context.active_object.data.materials.append(brick)

curve = bpy.data.curves.new("Open", type="FONT")
curve.body = "OPEN"
curve.align_x = "CENTER"
curve.align_y = "CENTER"
curve.extrude = 0.05
text = bpy.data.objects.new("Open", curve)
text.rotation_euler = (math.pi / 2, 0, 0)
text.data.materials.append(neon)
scene.collection.objects.link(text)

cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -6, 0)
cam.rotation_euler = (math.pi / 2, 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

# 5.0+: scene.node_tree is gone; the compositor is a node group assigned to the scene,
# and the old Composite node is replaced by a Group Output with a Color socket.
tree = bpy.data.node_groups.new("Compositing", "CompositorNodeTree")
scene.compositing_node_group = tree
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = tree.nodes.new("CompositorNodeRLayers")
glare = tree.nodes.new("CompositorNodeGlare")
glare.inputs["Type"].default_value = "Fog Glow"   # node options are menu input sockets now
glare.inputs["Strength"].default_value = 1.0
out = tree.nodes.new("NodeGroupOutput")
tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
tree.links.new(glare.outputs["Image"], out.inputs["Image"])
