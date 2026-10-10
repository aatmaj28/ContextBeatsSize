import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Geometry Nodes group ----------
group = bpy.data.node_groups.new("CubeGrid", "GeometryNodeTree")
iface = group.interface
iface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
size_item = iface.new_socket("Grid Size", in_out="INPUT", socket_type="NodeSocketInt")
size_item.default_value = 5
size_item.min_value = 1
size_item.max_value = 100
iface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = group.nodes
links = group.links

n_in = nodes.new("NodeGroupInput")
n_in.location = (-800, 0)
n_out = nodes.new("NodeGroupOutput")
n_out.location = (800, 0)

spacing = 1.2
# Physical size = (n - 1) * spacing = n*spacing - spacing
n_math = nodes.new("ShaderNodeMath")
n_math.operation = 'MULTIPLY_ADD'
n_math.location = (-550, 150)
n_math.inputs[1].default_value = spacing
n_math.inputs[2].default_value = -spacing
links.new(n_in.outputs["Grid Size"], n_math.inputs[0])

n_grid = nodes.new("GeometryNodeMeshGrid")
n_grid.location = (-300, 100)
links.new(n_math.outputs[0], n_grid.inputs["Size X"])
links.new(n_math.outputs[0], n_grid.inputs["Size Y"])
links.new(n_in.outputs["Grid Size"], n_grid.inputs["Vertices X"])
links.new(n_in.outputs["Grid Size"], n_grid.inputs["Vertices Y"])

n_cube = nodes.new("GeometryNodeMeshCube")
n_cube.location = (-300, -200)
n_cube.inputs["Size"].default_value = (0.8, 0.8, 0.8)

n_inst = nodes.new("GeometryNodeInstanceOnPoints")
n_inst.location = (0, 0)
links.new(n_grid.outputs["Mesh"], n_inst.inputs["Points"])
links.new(n_cube.outputs["Mesh"], n_inst.inputs["Instance"])

n_real = nodes.new("GeometryNodeRealizeInstances")
n_real.location = (250, 0)
links.new(n_inst.outputs["Instances"], n_real.inputs["Geometry"])

# Material
mat = bpy.data.materials.new("CubeMat")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.1, 0.45, 0.85, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35

n_mat = nodes.new("GeometryNodeSetMaterial")
n_mat.location = (500, 0)
n_mat.inputs["Material"].default_value = mat
links.new(n_real.outputs["Geometry"], n_mat.inputs["Geometry"])
links.new(n_mat.outputs["Geometry"], n_out.inputs[0])

# ---------- Object with modifier ----------
mesh = bpy.data.meshes.new("GridBase")
obj = bpy.data.objects.new("CubeGrid", mesh)
scene.collection.objects.link(obj)
obj.location = (0, 0, 0.4)

mod = obj.modifiers.new("CubeGrid", "NODES")
mod.node_group = group
try:
    getattr(mod.properties.inputs, size_item.identifier).value = 10
except AttributeError:
    mod[size_item.identifier] = 10

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("Ground")
gb = gmat.node_tree.nodes.get("Principled BSDF")
if gb:
    gb.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
    gb.inputs["Roughness"].default_value = 0.8
ground.data.materials.append(gmat)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(5)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(35))
scene.collection.objects.link(sun)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 0)
scene.collection.objects.link(target)

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (13, -13, 12)
scene.collection.objects.link(cam)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
