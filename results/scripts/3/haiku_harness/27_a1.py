import bpy
import mathutils

# Clear default scene objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# ---------------------------------------------------------------
# Geometry Nodes group: grid of cubes driven by a "Grid Size" input
# ---------------------------------------------------------------
group = bpy.data.node_groups.new("CubeGridNodes", "GeometryNodeTree")

# Interface
grid_socket = group.interface.new_socket(
    name="Grid Size", in_out="INPUT", socket_type="NodeSocketInt")
grid_socket.default_value = 10
grid_socket.min_value = 1
grid_socket.max_value = 100

group.interface.new_socket(
    name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
group.interface.new_socket(
    name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = group.nodes
links = group.links

group_in = nodes.new("NodeGroupInput")
group_in.location = (-900, 0)
group_out = nodes.new("NodeGroupOutput")
group_out.location = (900, 0)

# Spacing: size = (Grid Size - 1) * spacing so vertex spacing equals `spacing`
spacing = 2.0

sub_node = nodes.new("ShaderNodeMath")
sub_node.operation = 'SUBTRACT'
sub_node.inputs[1].default_value = 1.0
sub_node.location = (-650, 150)

mul_node = nodes.new("ShaderNodeMath")
mul_node.operation = 'MULTIPLY'
mul_node.inputs[1].default_value = spacing
mul_node.location = (-450, 150)

grid_node = nodes.new("GeometryNodeMeshGrid")
grid_node.location = (-200, 0)

points_node = nodes.new("GeometryNodeMeshToPoints")
points_node.location = (0, 0)

cube_node = nodes.new("GeometryNodeMeshCube")
cube_node.inputs["Size"].default_value = (0.6, 0.6, 0.6)
cube_node.location = (0, -250)

instance_node = nodes.new("GeometryNodeInstanceOnPoints")
instance_node.location = (200, 0)

realize_node = nodes.new("GeometryNodeRealizeInstances")
realize_node.location = (400, 0)

# Links
links.new(group_in.outputs["Grid Size"], sub_node.inputs[0])
links.new(sub_node.outputs[0], mul_node.inputs[0])

links.new(group_in.outputs["Grid Size"], grid_node.inputs["Vertices X"])
links.new(group_in.outputs["Grid Size"], grid_node.inputs["Vertices Y"])
links.new(mul_node.outputs[0], grid_node.inputs["Size X"])
links.new(mul_node.outputs[0], grid_node.inputs["Size Y"])

links.new(grid_node.outputs["Mesh"], points_node.inputs["Mesh"])
links.new(points_node.outputs["Points"], instance_node.inputs["Points"])
links.new(cube_node.outputs["Mesh"], instance_node.inputs["Instance"])
links.new(instance_node.outputs["Instances"], realize_node.inputs["Geometry"])
links.new(realize_node.outputs["Geometry"], group_out.inputs["Geometry"])

# ---------------------------------------------------------------
# Object with Geometry Nodes modifier
# ---------------------------------------------------------------
base_mesh = bpy.data.meshes.new("CubeGridBase")
base_obj = bpy.data.objects.new("CubeGrid", base_mesh)
bpy.context.collection.objects.link(base_obj)

# Material for the cubes
mat = bpy.data.materials.new("CubeMaterial")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.2, 0.55, 0.9, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
base_obj.data.materials.append(mat)

mod = base_obj.modifiers.new("CubeGrid", "NODES")
mod.node_group = group

# Set the exposed Grid Size input from the script
item = group.interface.items_tree["Grid Size"]
getattr(mod.properties.inputs, item.identifier).value = 10

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (mathutils.Euler((0.9, 0.2, 0.6), 'XYZ'))

# World background
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.07, 1.0)

# ---------------------------------------------------------------
# Camera framing the 18x18 grid footprint
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)

cam_loc = mathutils.Vector((28.0, -28.0, 26.0))
cam_obj.location = cam_loc
target = mathutils.Vector((0.0, 0.0, 0.0))
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam_obj
