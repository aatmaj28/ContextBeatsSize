import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Materials ----------
def make_mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

wood = make_mat("Wood", (0.45, 0.25, 0.12), 0.45)
steel = make_mat("Steel", (0.6, 0.6, 0.65), 0.3, 1.0)
floor_mat = make_mat("Floor", (0.35, 0.35, 0.35), 0.8)

# ---------- Geometry Nodes tree ----------
tree = bpy.data.node_groups.new("SpiralStaircase", "GeometryNodeTree")
iface = tree.interface
iface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
steps_sock = iface.new_socket("Steps", in_out='INPUT', socket_type='NodeSocketInt')
steps_sock.default_value = 12
steps_sock.min_value = 1
steps_sock.max_value = 500
iface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

N = tree.nodes
L = tree.links

STEP_H = 0.18
ANGLE = math.radians(15)
RADIUS = 1.6

gin = N.new("NodeGroupInput"); gin.location = (-1200, 0)
gout = N.new("NodeGroupOutput"); gout.location = (900, 0)

# Points along Z
line = N.new("GeometryNodeMeshLine"); line.location = (-900, 200)
line.mode = 'OFFSET'
line.inputs["Start Location"].default_value = (0, 0, STEP_H)
line.inputs["Offset"].default_value = (0, 0, STEP_H)
L.new(gin.outputs["Steps"], line.inputs["Count"])

# Step tread
cube = N.new("GeometryNodeMeshCube"); cube.location = (-900, -100)
cube.inputs["Size"].default_value = (RADIUS, 0.55, 0.06)
xf = N.new("GeometryNodeTransform"); xf.location = (-700, -100)
xf.inputs["Translation"].default_value = (RADIUS / 2 + 0.1, 0, 0)
L.new(cube.outputs["Mesh"], xf.inputs["Geometry"])
smat_step = N.new("GeometryNodeSetMaterial"); smat_step.location = (-500, -100)
smat_step.inputs["Material"].default_value = wood
L.new(xf.outputs["Geometry"], smat_step.inputs["Geometry"])

# Rotation per index
idx = N.new("GeometryNodeInputIndex"); idx.location = (-900, -350)
mul = N.new("ShaderNodeMath"); mul.location = (-700, -350)
mul.operation = 'MULTIPLY'
mul.inputs[1].default_value = ANGLE
L.new(idx.outputs["Index"], mul.inputs[0])
comb = N.new("ShaderNodeCombineXYZ"); comb.location = (-500, -350)
L.new(mul.outputs[0], comb.inputs["Z"])
e2r = N.new("FunctionNodeEulerToRotation"); e2r.location = (-350, -350)
L.new(comb.outputs["Vector"], e2r.inputs[0])

inst = N.new("GeometryNodeInstanceOnPoints"); inst.location = (-150, 150)
L.new(line.outputs["Mesh"], inst.inputs["Points"])
L.new(smat_step.outputs["Geometry"], inst.inputs["Instance"])
L.new(e2r.outputs[0], inst.inputs["Rotation"])

# Central column, height depends on step count
total = N.new("ShaderNodeMath"); total.location = (-900, -600)
total.operation = 'MULTIPLY'
total.inputs[1].default_value = STEP_H
L.new(gin.outputs["Steps"], total.inputs[0])
addtop = N.new("ShaderNodeMath"); addtop.location = (-700, -600)
addtop.operation = 'ADD'
addtop.inputs[1].default_value = 1.0
L.new(total.outputs[0], addtop.inputs[0])
half = N.new("ShaderNodeMath"); half.location = (-500, -700)
half.operation = 'MULTIPLY'
half.inputs[1].default_value = 0.5
L.new(addtop.outputs[0], half.inputs[0])
cz = N.new("ShaderNodeCombineXYZ"); cz.location = (-350, -700)
L.new(half.outputs[0], cz.inputs["Z"])

cyl = N.new("GeometryNodeMeshCylinder"); cyl.location = (-500, -500)
cyl.inputs["Vertices"].default_value = 32
cyl.inputs["Radius"].default_value = 0.14
L.new(addtop.outputs[0], cyl.inputs["Depth"])
cxf = N.new("GeometryNodeTransform"); cxf.location = (-150, -500)
L.new(cyl.outputs["Mesh"], cxf.inputs["Geometry"])
L.new(cz.outputs["Vector"], cxf.inputs["Translation"])
smat_col = N.new("GeometryNodeSetMaterial"); smat_col.location = (50, -500)
smat_col.inputs["Material"].default_value = steel
L.new(cxf.outputs["Geometry"], smat_col.inputs["Geometry"])

realize = N.new("GeometryNodeRealizeInstances"); realize.location = (100, 150)
L.new(inst.outputs["Instances"], realize.inputs["Geometry"])

join = N.new("GeometryNodeJoinGeometry"); join.location = (400, 0)
L.new(realize.outputs["Geometry"], join.inputs["Geometry"])
L.new(smat_col.outputs["Geometry"], join.inputs["Geometry"])
L.new(join.outputs["Geometry"], gout.inputs["Geometry"])

# ---------- Object with modifier ----------
mesh = bpy.data.meshes.new("StairBase")
obj = bpy.data.objects.new("SpiralStaircase", mesh)
scene.collection.objects.link(obj)
obj.data.materials.append(wood)
obj.data.materials.append(steel)
mod = obj.modifiers.new("Staircase", 'NODES')
mod.node_group = tree
mod[steps_sock.identifier] = 24
obj.update_tag()

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(floor_mat)

# ---------- Lighting ----------
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(30))
scene.collection.objects.link(sun)

area = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
area.data.energy = 600
area.data.size = 4
area.location = (-4, -3, 6)
area.rotation_euler = (Vector((0, 0, 2)) - area.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(area)

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
scene.world = world

# ---------- Camera ----------
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (7.5, -7.5, 5.0)
target = Vector((0, 0, 2.2))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 40
scene.collection.objects.link(cam)
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
