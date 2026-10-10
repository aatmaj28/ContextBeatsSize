import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clear default objects so the scene starts empty
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------------------------------------------------------------
# Geometry Nodes group: grid of cubes driven by exposed inputs
# ---------------------------------------------------------------
ng = bpy.data.node_groups.new("GridOfCubes", "GeometryNodeTree")

# Interface
ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
grid_item = ng.interface.new_socket(name="Grid Size", in_out="INPUT", socket_type="NodeSocketInt")
grid_item.default_value = 10
grid_item.min_value = 1
grid_item.max_value = 100

spacing_item = ng.interface.new_socket(name="Spacing", in_out="INPUT", socket_type="NodeSocketFloat")
spacing_item.default_value = 1.5
spacing_item.min_value = 0.1
spacing_item.max_value = 10.0

ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = ng.nodes
links = ng.links

group_in = nodes.new("NodeGroupInput")
group_in.location = (-900, 0)
group_out = nodes.new("NodeGroupOutput")
group_out.location = (700, 0)

# Size of grid span: (N - 1) * spacing so that N vertices are exactly `spacing` apart
sub_node = nodes.new("ShaderNodeMath")
sub_node.operation = 'SUBTRACT'
sub_node.inputs[1].default_value = 1.0
sub_node.location = (-700, 150)

mul_node = nodes.new("ShaderNodeMath")
mul_node.operation = 'MULTIPLY'
mul_node.location = (-500, 150)

grid = nodes.new("GeometryNodeMeshGrid")
grid.location = (-300, 0)

to_points = nodes.new("GeometryNodeMeshToPoints")
to_points.location = (-100, 0)

cube = nodes.new("GeometryNodeMeshCube")
cube.location = (-100, -250)
cube.inputs["Size"].default_value = (0.8, 0.8, 0.8)

inst = nodes.new("GeometryNodeInstanceOnPoints")
inst.location = (100, 0)

realize = nodes.new("GeometryNodeRealizeInstances")
realize.location = (320, 0)

# Links
links.new(group_in.outputs["Grid Size"], sub_node.inputs[0])
links.new(sub_node.outputs[0], mul_node.inputs[0])
links.new(group_in.outputs["Spacing"], mul_node.inputs[1])

links.new(mul_node.outputs[0], grid.inputs["Size X"])
links.new(mul_node.outputs[0], grid.inputs["Size Y"])
links.new(group_in.outputs["Grid Size"], grid.inputs["Vertices X"])
links.new(group_in.outputs["Grid Size"], grid.inputs["Vertices Y"])

links.new(grid.outputs["Mesh"], to_points.inputs["Mesh"])
links.new(to_points.outputs["Points"], inst.inputs["Points"])
links.new(cube.outputs["Mesh"], inst.inputs["Instance"])
links.new(inst.outputs["Instances"], realize.inputs["Geometry"])
links.new(realize.outputs["Geometry"], group_out.inputs["Geometry"])

# ---------------------------------------------------------------
# Base object with the Geometry Nodes modifier
# ---------------------------------------------------------------
mesh = bpy.data.meshes.new("GridCubesMesh")
obj = bpy.data.objects.new("GridCubes", mesh)
scene.collection.objects.link(obj)

mod = obj.modifiers.new(name="GridCubes", type='NODES')
mod.node_group = ng

# Set exposed inputs from the script
getattr(mod.properties.inputs, grid_item.identifier).value = 10
getattr(mod.properties.inputs, spacing_item.identifier).value = 1.5

# ---------------------------------------------------------------
# Material
# ---------------------------------------------------------------
mat = bpy.data.materials.new("CubeMaterial")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.2, 0.55, 0.9, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
obj.data.materials.append(mat)

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))

fill_data = bpy.data.lights.new("Fill", "AREA")
fill_data.energy = 400.0
fill_data.size = 10.0
fill = bpy.data.objects.new("Fill", fill_data)
scene.collection.objects.link(fill)
fill.location = (-15, -15, 15)
fill.rotation_euler = (math.radians(60), 0, math.radians(-45))

# World background
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------------------------------------------------------------
# Camera framing the grid (grid spans ~13.5 units, centered at origin)
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((22.0, -22.0, 18.0))

target = Vector((0.0, 0.0, 0.0))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam

# Render settings (not rendering; only configuring)
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
