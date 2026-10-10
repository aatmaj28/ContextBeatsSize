import bpy
import math
from mathutils import Vector

# ---------- Clean up the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Materials ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

mat_step = make_material("StepWood", (0.55, 0.36, 0.20), roughness=0.45)
mat_column = make_material("ColumnSteel", (0.70, 0.72, 0.75), roughness=0.25, metallic=1.0)
mat_floor = make_material("Floor", (0.80, 0.80, 0.78), roughness=0.9)

# ---------- Geometry Nodes tree ----------
tree = bpy.data.node_groups.new("SpiralStaircaseGN", "GeometryNodeTree")
iface = tree.interface
iface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
step_socket = iface.new_socket(name="Step Count", in_out="INPUT", socket_type="NodeSocketInt")
step_socket.default_value = 24
step_socket.min_value = 3
step_socket.max_value = 200
iface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = tree.nodes
links = tree.links

RADIUS = 1.1
ANGLE_STEP = 0.35
RISE = 0.25

def set_input(node, target, value):
    if isinstance(value, bpy.types.NodeSocket):
        links.new(value, target)
    else:
        target.default_value = value

def math_node(op, a, b=None):
    n = nodes.new("ShaderNodeMath")
    n.operation = op
    set_input(n, n.inputs[0], a)
    if b is not None:
        set_input(n, n.inputs[1], b)
    return n.outputs[0]

def combine(x, y, z):
    n = nodes.new("ShaderNodeCombineXYZ")
    set_input(n, n.inputs["X"], x)
    set_input(n, n.inputs["Y"], y)
    set_input(n, n.inputs["Z"], z)
    return n.outputs[0]

# Group I/O
gin = nodes.new("NodeGroupInput")
gout = nodes.new("NodeGroupOutput")
step_count = gin.outputs["Step Count"]

# Per-step parameters
idx = nodes.new("GeometryNodeInputIndex")
angle = math_node("MULTIPLY", idx.outputs["Index"], ANGLE_STEP)
px = math_node("MULTIPLY", math_node("COSINE", angle), RADIUS)
py = math_node("MULTIPLY", math_node("SINE", angle), RADIUS)
pz = math_node("MULTIPLY", idx.outputs["Index"], RISE)
step_pos = combine(px, py, pz)
step_rot = combine(0.0, 0.0, angle)

# Points, one per step
points = nodes.new("GeometryNodePoints")
set_input(points, points.inputs["Count"], step_count)
set_input(points, points.inputs["Position"], step_pos)

# Step box mesh
cube = nodes.new("GeometryNodeMeshCube")
cube.inputs["Size"].default_value = (1.6, 0.9, 0.15)

# Instance steps on points
iop = nodes.new("GeometryNodeInstanceOnPoints")
links.new(points.outputs["Points"], iop.inputs["Points"])
links.new(cube.outputs["Mesh"], iop.inputs["Instance"])
set_input(iop, iop.inputs["Rotation"], step_rot)

realize = nodes.new("GeometryNodeRealizeInstances")
links.new(iop.outputs["Instances"], realize.inputs["Geometry"])

set_steps_mat = nodes.new("GeometryNodeSetMaterial")
links.new(realize.outputs["Geometry"], set_steps_mat.inputs["Geometry"])
set_steps_mat.inputs["Material"].default_value = mat_step

# Central column, height driven by step count
column = nodes.new("GeometryNodeMeshCylinder")
column.inputs["Vertices"].default_value = 32
column.inputs["Radius"].default_value = 0.18
depth = math_node("ADD", math_node("MULTIPLY", step_count, RISE), 0.3)
set_input(column, column.inputs["Depth"], depth)

col_xform = nodes.new("GeometryNodeTransformGeometry")
links.new(column.outputs["Mesh"], col_xform.inputs["Geometry"])
half_depth = math_node("MULTIPLY", depth, 0.5)
set_input(col_xform, col_xform.inputs["Translation"], combine(0.0, 0.0, half_depth))

set_col_mat = nodes.new("GeometryNodeSetMaterial")
links.new(col_xform.outputs["Geometry"], set_col_mat.inputs["Geometry"])
set_col_mat.inputs["Material"].default_value = mat_column

# Join and output
join = nodes.new("GeometryNodeJoinGeometry")
links.new(set_steps_mat.outputs["Geometry"], join.inputs[0])
links.new(set_col_mat.outputs["Geometry"], join.inputs[0])
links.links.new(join.outputs["Geometry"], gout.inputs["Geometry"]) if False else links.new(join.outputs["Geometry"], gout.inputs["Geometry"])

# ---------- Object carrying the modifier ----------
mesh = bpy.data.meshes.new("SpiralStaircaseMesh")
stair_obj = bpy.data.objects.new("SpiralStaircase", mesh)
bpy.context.scene.collection.objects.link(stair_obj)

mod = stair_obj.modifiers.new(name="SpiralStairs", type="NODES")
mod.node_group = tree

# Set exposed step count input
for item in tree.interface.items_tree:
    if item.item_type == "SOCKET" and item.in_out == "INPUT" and item.name == "Step Count":
        mod[item.identifier] = 24

# ---------- Floor ----------
floor_mesh = bpy.data.meshes.new("Floor")
size = 8.0
verts = [(-size, -size, 0), (size, -size, 0), (size, size, 0), (-size, size, 0)]
floor_mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
floor_mesh.update()
floor_obj = bpy.data.objects.new("Floor", floor_mesh)
bpy.context.scene.collection.objects.link(floor_obj)
floor_obj.data.materials.append(mat_floor)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), 0, math.radians(30))

area_data = bpy.data.lights.new("Fill", type="AREA")
area_data.energy = 400.0
area_data.size = 6.0
area_obj = bpy.data.objects.new("Fill", area_data)
bpy.context.scene.collection.objects.link(area_obj)
area_obj.location = (-6, -6, 8)
area_obj.rotation_euler = (math.radians(55), 0, math.radians(-45))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = Vector((9.0, -11.0, 7.0))
target = Vector((0.0, 0.0, 3.0))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam_obj

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
