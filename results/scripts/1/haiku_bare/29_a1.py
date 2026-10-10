import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------
STEP_COUNT = 24
RISE = 0.2            # height per step
ANGLE = 0.26          # radians turned per step (~15 degrees)
RADIUS = 0.9          # distance of step centers from the column axis
STEP_SIZE = (1.2, 0.6, 0.12)
COLUMN_RADIUS = 0.15

# ---------------------------------------------------------------
# Geometry Nodes group: spiral staircase
# ---------------------------------------------------------------
tree = bpy.data.node_groups.new("SpiralStairGN", "GeometryNodeTree")
iface = tree.interface

steps_item = iface.new_socket(name="Steps", in_out='INPUT', socket_type='NodeSocketInt')
steps_item.default_value = STEP_COUNT
steps_item.min_value = 1
steps_item.max_value = 200

iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = tree.nodes
links = tree.links


def add_node(node_type, x, y):
    n = nodes.new(node_type)
    n.location = (x, y)
    return n


gin = add_node("NodeGroupInput", -1200, 0)
gout = add_node("NodeGroupOutput", 1000, 0)

# Points stacked vertically, one per step
line = add_node("GeometryNodeMeshLine", -900, 0)
line.mode = 'OFFSET'
line.inputs["Offset"].default_value = (0.0, 0.0, RISE)
links.new(gin.outputs["Steps"], line.inputs["Count"])

# Angle per step = Index * ANGLE
idx = add_node("GeometryNodeInputIndex", -900, -300)
ang = add_node("ShaderNodeMath", -700, -300)
ang.operation = 'MULTIPLY'
links.new(idx.outputs["Index"], ang.inputs[0])
ang.inputs[1].default_value = ANGLE

# Spiral offset: (cos(a)*R, sin(a)*R, 0)
cos_n = add_node("ShaderNodeMath", -500, -150)
cos_n.operation = 'COSINE'
links.new(ang.outputs[0], cos_n.inputs[0])

sin_n = add_node("ShaderNodeMath", -500, -400)
sin_n.operation = 'SINE'
links.new(ang.outputs[0], sin_n.inputs[0])

cos_r = add_node("ShaderNodeMath", -320, -150)
cos_r.operation = 'MULTIPLY'
links.new(cos_n.outputs[0], cos_r.inputs[0])
cos_r.inputs[1].default_value = RADIUS

sin_r = add_node("ShaderNodeMath", -320, -400)
sin_r.operation = 'MULTIPLY'
links.new(sin_n.outputs[0], sin_r.inputs[0])
sin_r.inputs[1].default_value = RADIUS

off_xyz = add_node("ShaderNodeCombineXYZ", -150, -275)
links.new(cos_r.outputs[0], off_xyz.inputs["X"])
links.new(sin_r.outputs[0], off_xyz.inputs["Y"])

set_pos = add_node("GeometryNodeSetPosition", -100, 0)
links.new(line.outputs["Mesh"], set_pos.inputs["Geometry"])
links.new(off_xyz.outputs[0], set_pos.inputs["Offset"])

# Step instance (box), rotated around Z by the same spiral angle
cube = add_node("GeometryNodeMeshCube", -100, -550)
cube.inputs["Size"].default_value = STEP_SIZE

rot_xyz = add_node("ShaderNodeCombineXYZ", -150, -550)
links.new(ang.outputs[0], rot_xyz.inputs["Z"])

inst = add_node("GeometryNodeInstanceOnPoints", 150, 0)
links.new(set_pos.outputs["Geometry"], inst.inputs["Points"])
links.new(cube.outputs["Mesh"], inst.inputs["Instance"])
links.new(rot_xyz.outputs[0], inst.inputs["Rotation"])

realize = add_node("GeometryNodeRealizeInstances", 350, 0)
links.new(inst.outputs["Instances"], realize.inputs["Geometry"])

# Central column whose height follows the step count
cyl = add_node("GeometryNodeMeshCylinder", 150, -350)
cyl.inputs["Radius"].default_value = COLUMN_RADIUS

depth_mul = add_node("ShaderNodeMath", -100, -700)
depth_mul.operation = 'MULTIPLY'
links.new(gin.outputs["Steps"], depth_mul.inputs[0])
depth_mul.inputs[1].default_value = RISE
links.new(depth_mul.outputs[0], cyl.inputs["Depth"])

half_mul = add_node("ShaderNodeMath", 100, -700)
half_mul.operation = 'MULTIPLY'
links.new(depth_mul.outputs[0], half_mul.inputs[0])
half_mul.inputs[1].default_value = 0.5

half_xyz = add_node("ShaderNodeCombineXYZ", 250, -700)
links.new(half_mul.outputs[0], half_xyz.inputs["Z"])

col_xform = add_node("GeometryNodeTransform", 400, -350)
links.new(cyl.outputs["Mesh"], col_xform.inputs["Geometry"])
links.new(half_xyz.outputs[0], col_xform.inputs["Translation"])

join = add_node("GeometryNodeJoinGeometry", 600, 0)
links.new(realize.outputs["Geometry"], join.inputs["Geometry"])
links.new(col_xform.outputs["Geometry"], join.inputs["Geometry"])
links.new(join.outputs["Geometry"], gout.inputs["Geometry"])

# ---------------------------------------------------------------
# Host object with the Geometry Nodes modifier
# ---------------------------------------------------------------
stair_mesh = bpy.data.meshes.new("SpiralStairBase")
stair_mesh.from_pydata([], [], [])
stair_mesh.update()
stair_obj = bpy.data.objects.new("SpiralStair", stair_mesh)
scene.collection.objects.link(stair_obj)

mod = stair_obj.modifiers.new(name="SpiralStair", type='NODES')
mod.node_group = tree
mod[steps_item.identifier] = STEP_COUNT

# Oak-like material
oak = bpy.data.materials.new("Oak")
oak.use_nodes = True
bsdf = oak.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.55, 0.35, 0.18, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.6
stair_obj.data.materials.append(oak)

# ---------------------------------------------------------------
# Ground plane
# ---------------------------------------------------------------
ground_mesh = bpy.data.meshes.new("Ground")
s = 12.0
ground_mesh.from_pydata(
    [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)],
    [],
    [(0, 1, 2, 3)],
)
ground_mesh.update()
ground_obj = bpy.data.objects.new("Ground", ground_mesh)
scene.collection.objects.link(ground_obj)

ground_mat = bpy.data.materials.new("GroundMat")
ground_mat.use_nodes = True
gb = ground_mat.node_tree.nodes.get("Principled BSDF")
if gb:
    gb.inputs["Base Color"].default_value = (0.25, 0.27, 0.3, 1.0)
    gb.inputs["Roughness"].default_value = 0.9
ground_obj.data.materials.append(ground_mat)

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.5
sun_obj = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), 0.0, math.radians(35))

fill_data = bpy.data.lights.new("Fill", 'AREA')
fill_data.energy = 400.0
fill_data.size = 4.0
fill_obj = bpy.data.objects.new("Fill", fill_data)
scene.collection.objects.link(fill_obj)
fill_obj.location = (-5.0, 5.0, 4.0)
fill_obj.rotation_euler = (math.radians(60), 0.0, math.radians(-45))

# ---------------------------------------------------------------
# Camera framing the staircase
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("StairCam")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("StairCam", cam_data)
scene.collection.objects.link(cam_obj)

cam_loc = Vector((6.5, -8.5, 4.2))
target = Vector((0.0, 0.0, 2.4))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# Static scene: single frame range
scene.frame_start = 1
scene.frame_end = 1
