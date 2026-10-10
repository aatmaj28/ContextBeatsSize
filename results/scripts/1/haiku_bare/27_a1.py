import bpy
import math
from mathutils import Vector

# ---------- Clean scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

GRID_SIZE = 10
SPACING = 1.5
CUBE_SIZE = 0.8

# ---------- Material ----------
mat = bpy.data.materials.new("CubeMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.2, 0.55, 0.9, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35

# ---------- Geometry Nodes group ----------
ng = bpy.data.node_groups.new("GridOfCubes", "GeometryNodeTree")

# Interface
grid_item = ng.interface.new_socket(name="Grid Size", in_out='INPUT', socket_type='NodeSocketInt')
grid_item.default_value = GRID_SIZE
grid_item.min_value = 1
grid_item.max_value = 100

spacing_item = ng.interface.new_socket(name="Spacing", in_out='INPUT', socket_type='NodeSocketFloat')
spacing_item.default_value = SPACING
spacing_item.min_value = 0.0

ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = ng.nodes
links = ng.links

gi = nodes.new("NodeGroupInput")
gi.location = (-900, 0)
go = nodes.new("NodeGroupOutput")
go.location = (600, 0)

# Size computation: (GridSize - 1) * Spacing
sub = nodes.new("ShaderNodeMath")
sub.operation = 'SUBTRACT'
sub.inputs[1].default_value = 1.0
sub.location = (-650, 150)

mul = nodes.new("ShaderNodeMath")
mul.operation = 'MULTIPLY'
mul.location = (-450, 150)

links.new(gi.outputs["Grid Size"], sub.inputs[0])
links.new(sub.outputs[0], mul.inputs[0])
links.new(gi.outputs["Spacing"], mul.inputs[1])

# Grid mesh
grid = nodes.new("GeometryNodeMeshGrid")
grid.location = (-250, 0)
links.new(mul.outputs[0], grid.inputs["Size X"])
links.new(mul.outputs[0], grid.inputs["Size Y"])
links.new(gi.outputs["Grid Size"], grid.inputs["Vertices X"])
links.new(gi.outputs["Grid Size"], grid.inputs["Vertices Y"])

# Mesh -> Points
m2p = nodes.new("GeometryNodeMeshToPoints")
m2p.location = (-50, 0)
links.new(grid.outputs["Mesh"], m2p.inputs["Mesh"])

# Cube instance source
cube = nodes.new("GeometryNodeMeshCube")
cube.location = (-50, -250)
cube.inputs["Size"].default_value = (CUBE_SIZE, CUBE_SIZE, CUBE_SIZE)

# Instance on points
iop = nodes.new("GeometryNodeInstanceOnPoints")
iop.location = (150, 0)
links.new(m2p.outputs["Points"], iop.inputs["Points"])
links.new(cube.outputs["Mesh"], iop.inputs["Instance"])

# Realize instances
realize = nodes.new("GeometryNodeRealizeInstances")
realize.location = (330, 0)
links.new(iop.outputs["Instances"], realize.inputs["Geometry"])

# Material assignment
setmat = nodes.new("GeometryNodeSetMaterial")
setmat.location = (450, 0)
setmat.inputs["Material"].default_value = mat
links.new(realize.outputs["Geometry"], setmat.inputs["Geometry"])

links.new(setmat.outputs["Geometry"], go.inputs["Geometry"])

# ---------- Object with Geometry Nodes modifier ----------
base_mesh = bpy.data.meshes.new("GridBase")
base_mesh.from_pydata([], [], [])
base_mesh.update()
obj = bpy.data.objects.new("CubeGrid", base_mesh)
bpy.context.collection.objects.link(obj)

# Center the grid around the origin
offset = (GRID_SIZE - 1) * SPACING / 2.0
obj.location = (-offset, -offset, 0.0)

mod = obj.modifiers.new(name="GridOfCubes", type='NODES')
mod.node_group = ng

# Set exposed inputs from the script
mod[grid_item.identifier] = GRID_SIZE
mod[spacing_item.identifier] = SPACING

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(35))

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 800.0
fill_data.size = 10.0
fill = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill)
fill.location = (-15.0, -15.0, 15.0)
fill.rotation_euler = (math.radians(60), 0.0, math.radians(-45))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)

cam_loc = Vector((22.0, -22.0, 20.0))
target = Vector((0.0, 0.0, 0.0))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam

# ---------- Frame range (static scene) ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
