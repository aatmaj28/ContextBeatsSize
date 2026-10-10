import bpy
import math
from mathutils import Vector

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Geometry Nodes tree ----------
tree = bpy.data.node_groups.new("SpiralStaircaseGN", "GeometryNodeTree")
tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
steps_item = tree.interface.new_socket(name="Steps", in_out="INPUT", socket_type="NodeSocketInt")
steps_item.default_value = 12
steps_item.min_value = 3
steps_item.max_value = 200

nodes = tree.nodes
links = tree.links

RISE = 0.2          # height per step
RADIUS = 1.0        # spiral radius
ANGLE = 0.3         # radians between steps
STEP_SIZE = (1.4, 0.5, 0.08)
COLUMN_RADIUS = 0.12

group_in = nodes.new("NodeGroupInput")
group_in.location = (-1000, 0)
group_out = nodes.new("NodeGroupOutput")
group_out.location = (900, 0)

# Step line: points stacked vertically
line = nodes.new("GeometryNodeMeshLine")
line.location = (-750, 200)
line.inputs["Offset"].default_value = (0.0, 0.0, RISE)
links.new(group_in.outputs["Steps"], line.inputs["Count"])

# Single step cube, offset radially
cube = nodes.new("GeometryNodeMeshCube")
cube.location = (-750, -200)
cube.inputs["Size"].default_value = STEP_SIZE

radial = nodes.new("ShaderNodeCombineXYZ")
radial.location = (-950, -350)
radial.inputs["X"].default_value = RADIUS
radial.inputs["Y"].default_value = 0.0
radial.inputs["Z"].default_value = 0.0

step_xf = nodes.new("GeometryNodeTransformGeometry")
step_xf.location = (-550, -200)
links.new(cube.outputs["Mesh"], step_xf.inputs["Geometry"])
links.new(radial.outputs["Vector"], step_xf.inputs["Translation"])

# Rotation per instance: Index * ANGLE around Z
index_node = nodes.new("GeometryNodeInputIndex")
index_node.location = (-750, -500)

angle_mul = nodes.new("ShaderNodeMath")
angle_mul.location = (-550, -500)
angle_mul.operation = 'MULTIPLY'
angle_mul.inputs[1].default_value = ANGLE
links.new(index_node.outputs["Index"], angle_mul.inputs[0])

rot_vec = nodes.new("ShaderNodeCombineXYZ")
rot_vec.location = (-350, -500)
links.new(angle_mul.outputs["Value"], rot_vec.inputs["Z"])

# Instance steps on the points
inst = nodes.new("GeometryNodeInstanceOnPoints")
inst.location = (-300, 100)
links.new(line.outputs["Mesh"], inst.inputs["Points"])
links.new(step_xf.outputs["Geometry"], inst.inputs["Instance"])
links.new(rot_vec.outputs["Vector"], inst.inputs["Rotation"])

# Central column with height = Steps * RISE
height_mul = nodes.new("ShaderNodeMath")
height_mul.location = (-550, 400)
height_mul.operation = 'MULTIPLY'
height_mul.inputs[1].default_value = RISE
links.new(group_in.outputs["Steps"], height_mul.inputs[0])

column = nodes.new("GeometryNodeMeshCylinder")
column.location = (-300, 500)
column.inputs["Radius"].default_value = COLUMN_RADIUS
column.inputs["Vertices"].default_value = 24
links.new(height_mul.outputs["Value"], column.inputs["Depth"])

half_mul = nodes.new("ShaderNodeMath")
half_mul.location = (-550, 600)
half_mul.operation = 'MULTIPLY'
half_mul.inputs[1].default_value = 0.5
links.new(height_mul.outputs["Value"], half_mul.inputs[0])

col_pos = nodes.new("ShaderNodeCombineXYZ")
col_pos.location = (-350, 650)
col_pos.inputs["X"].default_value = 0.0
col_pos.inputs["Y"].default_value = 0.0
links.new(half_mul.outputs["Value"], col_pos.inputs["Z"])

col_xf = nodes.new("GeometryNodeTransformGeometry")
col_xf.location = (-100, 500)
links.new(column.outputs["Mesh"], col_xf.inputs["Geometry"])
links.new(col_pos.outputs["Vector"], col_xf.inputs["Translation"])

# Join steps and column, realize, output
join = nodes.new("GeometryNodeJoinGeometry")
join.location = (300, 200)
links.new(inst.outputs["Instances"], join.inputs["Geometry"])
links.new(col_xf.outputs["Geometry"], join.inputs["Geometry"])

realize = nodes.new("GeometryNodeRealizeInstances")
realize.location = (550, 200)
links.new(join.outputs["Geometry"], realize.inputs["Geometry"])
links.new(realize.outputs["Geometry"], group_out.inputs["Geometry"])

# ---------- Object + modifier ----------
mesh = bpy.data.meshes.new("SpiralStaircaseBase")
mesh.from_pydata([(0.0, 0.0, 0.0)], [], [])
mesh.update()
stair_obj = bpy.data.objects.new("SpiralStaircase", mesh)
bpy.context.scene.collection.objects.link(stair_obj)

mod = stair_obj.modifiers.new("SpiralStaircase", "NODES")
mod.node_group = tree

# Set the exposed Steps input to 24
getattr(mod.properties.inputs, steps_item.identifier).value = 24

# ---------- Material ----------
mat = bpy.data.materials.new("StairMaterial")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.75, 0.6, 0.45, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.45
stair_obj.data.materials.append(mat)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("KeySun", "SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("KeySun", sun_data)
sun.location = (5, -5, 8)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(30))
bpy.context.scene.collection.objects.link(sun)

fill_data = bpy.data.lights.new("FillArea", "AREA")
fill_data.energy = 400.0
fill_data.size = 4.0
fill = bpy.data.objects.new("FillArea", fill_data)
fill.location = (-5, 4, 4)
fill.rotation_euler = (math.radians(65), 0.0, math.radians(-135))
bpy.context.scene.collection.objects.link(fill)

# ---------- World ----------
world = bpy.data.worlds.new("StudioWorld")
bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("StaircaseCam")
cam_data.lens = 50
cam = bpy.data.objects.new("StaircaseCam", cam_data)
cam.location = (7.5, -8.5, 4.5)
bpy.context.scene.collection.objects.link(cam)

target = Vector((0.0, 0.0, 2.4))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
