import bpy
import math

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene

# Material
mat = bpy.data.materials.new("CubeMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.1, 0.45, 0.85, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35

# Geometry Nodes group
ng = bpy.data.node_groups.new("CubeGrid", 'GeometryNodeTree')
iface = ng.interface
iface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
size_sock = iface.new_socket(name="Grid Size", in_out='INPUT', socket_type='NodeSocketInt')
size_sock.default_value = 10
size_sock.min_value = 1
size_sock.max_value = 100
sp_sock = iface.new_socket(name="Spacing", in_out='INPUT', socket_type='NodeSocketFloat')
sp_sock.default_value = 1.5
sp_sock.min_value = 0.0
cs_sock = iface.new_socket(name="Cube Size", in_out='INPUT', socket_type='NodeSocketFloat')
cs_sock.default_value = 1.0
cs_sock.min_value = 0.0
iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = ng.nodes
links = ng.links

gin = nodes.new('NodeGroupInput'); gin.location = (-800, 0)
gout = nodes.new('NodeGroupOutput'); gout.location = (800, 0)

sub = nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; sub.location = (-550, 150)
sub.inputs[1].default_value = 1.0
mul = nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.location = (-350, 150)

grid = nodes.new('GeometryNodeMeshGrid'); grid.location = (-150, 150)

cube = nodes.new('GeometryNodeMeshCube'); cube.location = (-150, -150)
comb = nodes.new('ShaderNodeCombineXYZ'); comb.location = (-350, -150)

inst = nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (100, 0)
realize = nodes.new('GeometryNodeRealizeInstances'); realize.location = (330, 0)
setmat = nodes.new('GeometryNodeSetMaterial'); setmat.location = (560, 0)
setmat.inputs["Material"].default_value = mat

links.new(gin.outputs["Grid Size"], sub.inputs[0])
links.new(sub.outputs[0], mul.inputs[0])
links.new(gin.outputs["Spacing"], mul.inputs[1])
links.new(mul.outputs[0], grid.inputs["Size X"])
links.new(mul.outputs[0], grid.inputs["Size Y"])
links.new(gin.outputs["Grid Size"], grid.inputs["Vertices X"])
links.new(gin.outputs["Grid Size"], grid.inputs["Vertices Y"])
links.new(gin.outputs["Cube Size"], comb.inputs[0])
links.new(gin.outputs["Cube Size"], comb.inputs[1])
links.new(gin.outputs["Cube Size"], comb.inputs[2])
links.new(comb.outputs[0], cube.inputs["Size"])
links.new(grid.outputs["Mesh"], inst.inputs["Points"])
links.new(cube.outputs["Mesh"], inst.inputs["Instance"])
links.new(inst.outputs["Instances"], realize.inputs["Geometry"])
links.new(realize.outputs["Geometry"], setmat.inputs["Geometry"])
links.new(setmat.outputs["Geometry"], gout.inputs["Geometry"])

# Host object
mesh = bpy.data.meshes.new("GridHost")
host = bpy.data.objects.new("CubeGrid", mesh)
scene.collection.objects.link(host)
host.location = (0, 0, 0.5)
mod = host.modifiers.new("CubeGrid", 'NODES')
mod.node_group = ng
mod[size_sock.identifier] = 10
mod[sp_sock.identifier] = 1.5
mod[cs_sock.identifier] = 1.0
host.data.materials.append(mat)

# Ground
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("Ground")
gmat.use_nodes = True
gb = gmat.node_tree.nodes.get("Principled BSDF")
if gb:
    gb.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
    gb.inputs["Roughness"].default_value = 0.8
ground.data.materials.append(gmat)

# Lighting
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(5)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(35))
scene.collection.objects.link(sun)

area_data = bpy.data.lights.new("Fill", 'AREA')
area_data.energy = 1500
area_data.size = 10
area = bpy.data.objects.new("Fill", area_data)
area.location = (-12, -8, 12)
scene.collection.objects.link(area)

# World
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Camera
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 0.5)
scene.collection.objects.link(target)

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (16, -18, 15)
scene.collection.objects.link(cam)
tc = cam.constraints.new('TRACK_TO')
tc.target = target
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
