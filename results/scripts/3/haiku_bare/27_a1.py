import bpy
import math
from mathutils import Vector

# ---------- Clean up default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Material ----------
mat = bpy.data.materials.new(name="CubeMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.2, 0.55, 0.9, 1.0)
bsdf.inputs["Roughness"].default_value = 0.35

# ---------- Geometry Nodes group ----------
ng = bpy.data.node_groups.new("GridOfCubes", "GeometryNodeTree")

grid_size_socket = ng.interface.new_socket(
    name="Grid Size", in_out="INPUT", socket_type="NodeSocketInt")
grid_size_socket.default_value = 10
grid_size_socket.min_value = 1
grid_size_socket.max_value = 100

ng.interface.new_socket(
    name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = ng.nodes
links = ng.links

group_in = nodes.new("NodeGroupInput")
group_in.location = (-900, 0)
group_out = nodes.new("NodeGroupOutput")
group_out.location = (900, 0)

# Spacing math: span = (N - 1) * spacing
spacing = 1.5
sub = nodes.new("ShaderNodeMath")
sub.operation = "SUBTRACT"
sub.inputs[1].default_value = 1.0
sub.location = (-650, 150)

mul = nodes.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
mul.inputs[1].default_value = spacing
mul.location = (-500, 150)

grid = nodes.new("GeometryNodeMeshGrid")
grid.location = (-350, 0)

to_points = nodes.new("GeometryNodeMeshToPoints")
to_points.location = (-150, 0)

cube = nodes.new("GeometryNodeMeshCube")
cube.location = (-150, -250)
cube.inputs["Size"].default_value = (0.8, 0.8, 0.8)

inst = nodes.new("GeometryNodeInstanceOnPoints")
inst.location = (50, 0)

realize = nodes.new("GeometryNodeRealizeInstances")
realize.location = (250, 0)

set_mat = nodes.new("GeometryNodeSetMaterial")
set_mat.location = (450, 0)
set_mat.inputs["Material"].default_value = mat

# Links
links.new(group_in.outputs["Grid Size"], sub.inputs[0])
links.new(sub.outputs["Value"], mul.inputs[0])
links.new(mul.outputs["Value"], grid.inputs["Size X"])
links.new(mul.outputs["Value"], grid.inputs["Size Y"])
links.new(group_in.outputs["Grid Size"], grid.inputs["Vertices X"])
links.new(group_in.outputs["Grid Size"], grid.inputs["Vertices Y"])

links.new(grid.outputs["Mesh"], to_points.inputs["Mesh"])
links.new(to_points.outputs["Points"], inst.inputs["Points"])
links.new(cube.outputs["Mesh"], inst.inputs["Instance"])
links.new(inst.outputs["Instances"], realize.inputs["Geometry"])
links.new(realize.outputs["Geometry"], set_mat.inputs["Geometry"])
links.new(set_mat.outputs["Geometry"], group_out.inputs["Geometry"])

# ---------- Base object with Geometry Nodes modifier ----------
base_mesh = bpy.data.meshes.new("GridBaseMesh")
base_mesh.materials.append(mat)
grid_obj = bpy.data.objects.new("CubeGrid", base_mesh)
bpy.context.scene.collection.objects.link(grid_obj)

mod = grid_obj.modifiers.new(name="CubeGridModifier", type="NODES")
mod.node_group = ng
# Set the exposed input from the script
mod[grid_size_socket.identifier] = 10

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="Sun", type="SUN")
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.location = (6, -8, 12)
sun_obj.rotation_euler = (math.radians(50), 0, math.radians(35))

fill_data = bpy.data.lights.new(name="Fill", type="AREA")
fill_data.energy = 800.0
fill_data.size = 12.0
fill_obj = bpy.data.objects.new("Fill", fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.location = (-12, 10, 10)
fill_obj.rotation_euler = (math.radians(60), 0, math.radians(-135))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = Vector((16.0, -16.0, 14.0))

target = Vector((0.0, 0.0, 0.0))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

bpy.context.scene.camera = cam_obj

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
