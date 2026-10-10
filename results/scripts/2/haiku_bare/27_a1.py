import bpy
import mathutils

GRID_SIZE = 10
SPACING = 1.5

# Clear default scene contents
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ---------- Geometry Nodes group ----------
tree = bpy.data.node_groups.new("CubeGridNodes", 'GeometryNodeTree')

# Interface: exposed grid size input + geometry in/out
size_socket = tree.interface.new_socket(
    name="Grid Size", in_out='INPUT', socket_type='NodeSocketInt')
size_socket.default_value = GRID_SIZE
size_socket.min_value = 1
size_socket.max_value = 100
size_identifier = size_socket.identifier

tree.interface.new_socket(
    name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
tree.interface.new_socket(
    name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = tree.nodes
links = tree.links

group_in = nodes.new('NodeGroupInput')
group_in.location = (-900, 0)
group_out = nodes.new('NodeGroupOutput')
group_out.location = (900, 0)

# Compute grid extent: (N - 1) * spacing so cube centers are spaced evenly
sub = nodes.new('ShaderNodeMath')
sub.operation = 'SUBTRACT'
sub.inputs[1].default_value = 1.0
sub.location = (-650, 200)

mul = nodes.new('ShaderNodeMath')
mul.operation = 'MULTIPLY'
mul.inputs[1].default_value = SPACING
mul.location = (-450, 200)

grid = nodes.new('GeometryNodeMeshGrid')
grid.location = (-250, 0)

to_points = nodes.new('GeometryNodeMeshToPoints')
to_points.location = (-50, 0)

cube = nodes.new('GeometryNodeMeshCube')
cube.location = (-250, -300)

cube_move = nodes.new('GeometryNodeTransform')
cube_move.location = (-50, -300)
cube_move.inputs['Translation'].default_value = (0.0, 0.0, 0.5)

inst = nodes.new('GeometryNodeInstanceOnPoints')
inst.location = (150, 0)

realize = nodes.new('GeometryNodeRealizeInstances')
realize.location = (350, 0)

# Wiring
links.new(group_in.outputs[size_identifier], sub.inputs[0])
links.new(sub.outputs[0], mul.inputs[0])

links.new(group_in.outputs[size_identifier], grid.inputs['Vertices X'])
links.new(group_in.outputs[size_identifier], grid.inputs['Vertices Y'])
links.new(mul.outputs[0], grid.inputs['Size X'])
links.new(mul.outputs[0], grid.inputs['Size Y'])

links.new(grid.outputs['Mesh'], to_points.inputs['Mesh'])

links.new(cube.outputs['Mesh'], cube_move.inputs['Geometry'])

links.new(to_points.outputs['Points'], inst.inputs['Points'])
links.new(cube_move.outputs['Geometry'], inst.inputs['Instance'])

links.new(inst.outputs['Instances'], realize.inputs['Geometry'])
links.new(realize.outputs['Geometry'], group_out.inputs['Geometry'])

# ---------- Material ----------
mat = bpy.data.materials.new("CubeMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.2, 0.55, 0.9, 1.0)
bsdf.inputs["Roughness"].default_value = 0.35

# ---------- Object with GN modifier ----------
mesh = bpy.data.meshes.new("CubeGridMesh")
obj = bpy.data.objects.new("CubeGrid", mesh)
bpy.context.scene.collection.objects.link(obj)
obj.data.materials.append(mat)

mod = obj.modifiers.new(name="CubeGridModifier", type='NODES')
mod.node_group = tree
mod[size_identifier] = GRID_SIZE

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.scene.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.0, 0.6)

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 800.0
fill_data.size = 10.0
fill = bpy.data.objects.new("Fill", fill_data)
bpy.context.scene.collection.objects.link(fill)
fill.location = (-15.0, -15.0, 15.0)
fill.rotation_euler = (0.8, 0.0, -0.8)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam)

half_extent = (GRID_SIZE - 1) * SPACING * 0.5
cam.location = (0.0, -half_extent * 1.9, half_extent * 1.6)

target = mathutils.Vector((0.0, 0.0, 0.0))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam

# ---------- Frame range (static scene) ----------
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 1
