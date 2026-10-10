import bpy
import math

# Clean scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

GRID_SIZE = 10
SPACING = 1.5
CUBE_SIZE = 1.0

# ---------- Material ----------
mat = bpy.data.materials.new("CubeMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.1, 0.45, 0.9, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35

# ---------- Geometry Nodes tree ----------
tree = bpy.data.node_groups.new("CubeGrid", "GeometryNodeTree")
iface = tree.interface
sock_size = iface.new_socket(name="Grid Size", in_out='INPUT', socket_type='NodeSocketInt')
sock_size.default_value = 5
sock_size.min_value = 1
sock_size.max_value = 100
iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = tree.nodes
links = tree.links

n_in = nodes.new("NodeGroupInput"); n_in.location = (-800, 0)
n_out = nodes.new("NodeGroupOutput"); n_out.location = (800, 0)

# size = (N - 1) * spacing
n_sub = nodes.new("ShaderNodeMath"); n_sub.operation = 'SUBTRACT'
n_sub.inputs[1].default_value = 1.0; n_sub.location = (-600, 150)
n_mul = nodes.new("ShaderNodeMath"); n_mul.operation = 'MULTIPLY'
n_mul.inputs[1].default_value = SPACING; n_mul.location = (-400, 150)

n_grid = nodes.new("GeometryNodeMeshGrid"); n_grid.location = (-200, 0)
n_pts = nodes.new("GeometryNodeMeshToPoints"); n_pts.location = (0, 0)

n_cube = nodes.new("GeometryNodeMeshCube"); n_cube.location = (-200, -300)
n_cube.inputs["Size"].default_value = (CUBE_SIZE, CUBE_SIZE, CUBE_SIZE)
n_setmat = nodes.new("GeometryNodeSetMaterial"); n_setmat.location = (0, -300)
n_setmat.inputs["Material"].default_value = mat

n_inst = nodes.new("GeometryNodeInstanceOnPoints"); n_inst.location = (250, 0)
n_real = nodes.new("GeometryNodeRealizeInstances"); n_real.location = (500, 0)

links.new(n_in.outputs["Grid Size"], n_sub.inputs[0])
links.new(n_sub.outputs[0], n_mul.inputs[0])
links.new(n_mul.outputs[0], n_grid.inputs["Size X"])
links.new(n_mul.outputs[0], n_grid.inputs["Size Y"])
links.new(n_in.outputs["Grid Size"], n_grid.inputs["Vertices X"])
links.new(n_in.outputs["Grid Size"], n_grid.inputs["Vertices Y"])
links.new(n_grid.outputs["Mesh"], n_pts.inputs["Mesh"])
links.new(n_cube.outputs["Mesh"], n_setmat.inputs["Geometry"])
links.new(n_pts.outputs["Points"], n_inst.inputs["Points"])
links.new(n_setmat.outputs["Geometry"], n_inst.inputs["Instance"])
links.new(n_inst.outputs["Instances"], n_real.inputs["Geometry"])
links.new(n_real.outputs["Geometry"], n_out.inputs["Geometry"])

# ---------- Object with modifier ----------
mesh = bpy.data.meshes.new("GridHost")
obj = bpy.data.objects.new("CubeGrid", mesh)
bpy.context.scene.collection.objects.link(obj)
obj.location = (0, 0, CUBE_SIZE / 2)
obj.data.materials.append(mat)

mod = obj.modifiers.new("CubeGrid", 'NODES')
mod.node_group = tree
mod[sock_size.identifier] = GRID_SIZE
obj.update_tag()

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("Ground")
gmat.use_nodes = True
gb = gmat.node_tree.nodes.get("Principled BSDF")
if gb:
    gb.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
    gb.inputs["Roughness"].default_value = 0.8
ground.data.materials.append(gmat)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))
bpy.context.scene.collection.objects.link(sun)

area_data = bpy.data.lights.new("Fill", 'AREA')
area_data.energy = 2000
area_data.size = 10
area = bpy.data.objects.new("Fill", area_data)
area.location = (-12, -8, 14)
bpy.context.scene.collection.objects.link(area)
c = area.constraints.new('TRACK_TO')
c.target = obj

world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 0.5)
bpy.context.scene.collection.objects.link(target)

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (16, -16, 15)
bpy.context.scene.collection.objects.link(cam)
tc = cam.constraints.new('TRACK_TO')
tc.target = target
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'

bpy.context.scene.camera = cam
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 1
