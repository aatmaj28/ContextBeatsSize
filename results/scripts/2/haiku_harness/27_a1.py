import bpy
import math
from mathutils import Vector

# ---------- Clean up default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Geometry Nodes group ----------
ng = bpy.data.node_groups.new("CubeGridGroup", "GeometryNodeTree")

# Interface: exposed Grid Size input and geometry output
size_item = ng.interface.new_socket(
    name="Grid Size", in_out="INPUT", socket_type="NodeSocketInt"
)
size_item.default_value = 10
size_item.min_value = 2
size_item.max_value = 50

ng.interface.new_socket(
    name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
)

nodes = ng.nodes
links = ng.links

group_in = nodes.new("NodeGroupInput")
group_in.location = (-900, 0)
group_out = nodes.new("NodeGroupOutput")
group_out.location = (700, 0)

# (Grid Size - 1) * spacing  ->  grid extent so that cube centers are spaced evenly
spacing = 1.5
sub_node = nodes.new("ShaderNodeMath")
sub_node.operation = 'SUBTRACT'
sub_node.inputs[1].default_value = 1.0
sub_node.location = (-700, 150)

mul_node = nodes.new("ShaderNodeMath")
mul_node.operation = 'MULTIPLY'
mul_node.inputs[1].default_value = spacing
mul_node.location = (-500, 150)

grid_node = nodes.new("GeometryNodeMeshGrid")
grid_node.location = (-300, 0)

points_node = nodes.new("GeometryNodeMeshToPoints")
points_node.location = (-100, 0)

cube_node = nodes.new("GeometryNodeMeshCube")
cube_node.location = (-100, -250)
cube_node.inputs["Size"].default_value = (0.8, 0.8, 0.8)

instance_node = nodes.new("GeometryNodeInstanceOnPoints")
instance_node.location = (120, 0)

realize_node = nodes.new("GeometryNodeRealizeInstances")
realize_node.location = (340, 0)

# Wiring
links.new(group_in.outputs["Grid Size"], sub_node.inputs[0])
links.new(sub_node.outputs["Value"], mul_node.inputs[0])
links.new(mul_node.outputs["Value"], grid_node.inputs["Size X"])
links.new(mul_node.outputs["Value"], grid_node.inputs["Size Y"])
links.new(group_in.outputs["Grid Size"], grid_node.inputs["Vertices X"])
links.new(group_in.outputs["Grid Size"], grid_node.inputs["Vertices Y"])

links.new(grid_node.outputs["Mesh"], points_node.inputs["Mesh"])
links.new(points_node.outputs["Points"], instance_node.inputs["Points"])
links.new(cube_node.outputs["Mesh"], instance_node.inputs["Instance"])
links.new(instance_node.outputs["Instances"], realize_node.inputs["Geometry"])
links.new(realize_node.outputs["Geometry"], group_out.inputs["Geometry"])

# ---------- Material ----------
mat = bpy.data.materials.new("CubeMaterial")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.2, 0.55, 0.9, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35

# ---------- Grid object with modifier ----------
mesh = bpy.data.meshes.new("GridMesh")
grid_obj = bpy.data.objects.new("CubeGrid", mesh)
bpy.context.scene.collection.objects.link(grid_obj)
grid_obj.data.materials.append(mat)

mod = grid_obj.modifiers.new("CubeGrid", "NODES")
mod.node_group = ng

# Set the exposed Grid Size input from the script
getattr(mod.properties.inputs, size_item.identifier).value = 10

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("KeySun", "SUN")
sun_data.energy = 3.5
sun_obj = bpy.data.objects.new("KeySun", sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), 0.0, math.radians(35))

fill_data = bpy.data.lights.new("FillArea", "AREA")
fill_data.energy = 400.0
fill_data.size = 12.0
fill_obj = bpy.data.objects.new("FillArea", fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.location = (-18, 18, 20)
fill_obj.rotation_euler = (math.radians(60), 0.0, math.radians(-135))

# ---------- World ----------
world = bpy.data.worlds.new("GridWorld")
bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("GridCamera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("GridCamera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)

target = Vector((0.0, 0.0, 0.0))
cam_loc = Vector((22.0, -22.0, 20.0))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam_obj
