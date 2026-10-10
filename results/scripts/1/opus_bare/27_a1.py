import bpy
import math
from mathutils import Vector

# Clean scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

GRID_SIZE = 10

# --- Geometry Nodes group ---
ng = bpy.data.node_groups.new("CubeGrid", 'GeometryNodeTree')
try:
    ng.is_modifier = True
except Exception:
    pass

iface = ng.interface
iface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
s_size = iface.new_socket(name="Grid Size", in_out='INPUT', socket_type='NodeSocketInt')
s_size.default_value = 5
s_size.min_value = 1
s_size.max_value = 100
s_space = iface.new_socket(name="Spacing", in_out='INPUT', socket_type='NodeSocketFloat')
s_space.default_value = 1.0
s_cube = iface.new_socket(name="Cube Size", in_out='INPUT', socket_type='NodeSocketFloat')
s_cube.default_value = 0.8
s_mat = iface.new_socket(name="Material", in_out='INPUT', socket_type='NodeSocketMaterial')
iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = ng.nodes
links = ng.links

gin = nodes.new('NodeGroupInput'); gin.location = (-800, 0)
gout = nodes.new('NodeGroupOutput'); gout.location = (800, 0)

sub = nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
sub.location = (-550, 150); sub.inputs[1].default_value = 1.0
mul = nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
mul.location = (-350, 150)

grid = nodes.new('GeometryNodeMeshGrid'); grid.location = (-150, 150)

cube = nodes.new('GeometryNodeMeshCube'); cube.location = (-150, -150)
comb = nodes.new('ShaderNodeCombineXYZ'); comb.location = (-350, -150)

iop = nodes.new('GeometryNodeInstanceOnPoints'); iop.location = (100, 0)
real = nodes.new('GeometryNodeRealizeInstances'); real.location = (320, 0)
setmat = nodes.new('GeometryNodeSetMaterial'); setmat.location = (550, 0)

# Grid dimensions
links.new(gin.outputs["Grid Size"], sub.inputs[0])
links.new(sub.outputs[0], mul.inputs[0])
links.new(gin.outputs["Spacing"], mul.inputs[1])
links.new(mul.outputs[0], grid.inputs["Size X"])
links.new(mul.outputs[0], grid.inputs["Size Y"])
links.new(gin.outputs["Grid Size"], grid.inputs["Vertices X"])
links.new(gin.outputs["Grid Size"], grid.inputs["Vertices Y"])

# Cube size
for k in ("X", "Y", "Z"):
    links.new(gin.outputs["Cube Size"], comb.inputs[k])
links.new(comb.outputs[0], cube.inputs["Size"])

# Instancing
links.new(grid.outputs["Mesh"], iop.inputs["Points"])
links.new(cube.outputs["Mesh"], iop.inputs["Instance"])
links.new(iop.outputs["Instances"], real.inputs["Geometry"])
links.new(real.outputs["Geometry"], setmat.inputs["Geometry"])
links.new(gin.outputs["Material"], setmat.inputs["Material"])
links.new(setmat.outputs["Geometry"], gout.inputs["Geometry"])

# --- Material ---
mat = bpy.data.materials.new("CubeMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.1, 0.45, 0.9, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35

# --- Object with modifier ---
mesh = bpy.data.meshes.new("GridBase")
obj = bpy.data.objects.new("CubeGrid", mesh)
bpy.context.scene.collection.objects.link(obj)
obj.location.z = 0.4

mod = obj.modifiers.new("CubeGrid", 'NODES')
mod.node_group = ng
mod[s_size.identifier] = GRID_SIZE
mod[s_mat.identifier] = mat
obj.data.update()

# --- Ground ---
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("Ground")
gmat.use_nodes = True
gb = gmat.node_tree.nodes.get("Principled BSDF")
if gb:
    gb.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
ground.data.materials.append(gmat)

# --- Lighting ---
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(30))
bpy.context.scene.collection.objects.link(sun)

area_data = bpy.data.lights.new("Fill", 'AREA')
area_data.energy = 800
area_data.size = 8
area = bpy.data.objects.new("Fill", area_data)
area.location = (-10, -6, 10)
area.rotation_euler = (Vector((0, 0, 0)) - area.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.collection.objects.link(area)

# --- Camera ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (12, -12, 11)
cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

# World
world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
