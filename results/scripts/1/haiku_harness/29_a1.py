import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------------------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------------------------------------------------------------------------
# Geometry Nodes tree for the spiral staircase
# ---------------------------------------------------------------------------
tree = bpy.data.node_groups.new("SpiralStaircaseGN", "GeometryNodeTree")

steps_item = tree.interface.new_socket(
    name="Step Count", in_out="INPUT", socket_type="NodeSocketInt")
steps_item.default_value = 24
steps_item.min_value = 3
steps_item.max_value = 256

tree.interface.new_socket(
    name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = tree.nodes
links = tree.links


def add(node_type, loc):
    n = nodes.new(node_type)
    n.location = loc
    return n


gin = add("NodeGroupInput", (-1000, 0))
gout = add("NodeGroupOutput", (900, 0))

# Step positions on a circle
circle = add("GeometryNodeMeshCircle", (-700, 150))
circle.inputs["Radius"].default_value = 2.0
links.new(gin.outputs["Step Count"], circle.inputs["Vertices"])

idx = add("GeometryNodeInputIndex", (-900, -250))

# Rise per step: index * 0.25
rise_mul = add("ShaderNodeMath", (-700, -100))
rise_mul.operation = 'MULTIPLY'
rise_mul.inputs[1].default_value = 0.25
links.new(idx.outputs["Index"], rise_mul.inputs[0])

rise_xyz = add("ShaderNodeCombineXYZ", (-500, -100))
links.new(rise_mul.outputs["Value"], rise_xyz.inputs["Z"])

setpos = add("GeometryNodeSetPosition", (-500, 150))
links.new(circle.outputs["Mesh"], setpos.inputs["Geometry"])
links.new(rise_xyz.outputs["Vector"], setpos.inputs["Offset"])

# Rotation per step: index * (2*pi / steps)
angle_div = add("ShaderNodeMath", (-900, -500))
angle_div.operation = 'DIVIDE'
angle_div.inputs[0].default_value = 2.0 * math.pi
links.new(gin.outputs["Step Count"], angle_div.inputs[1])

angle_mul = add("ShaderNodeMath", (-700, -450))
angle_mul.operation = 'MULTIPLY'
links.new(idx.outputs["Index"], angle_mul.inputs[0])
links.new(angle_div.outputs["Value"], angle_mul.inputs[1])

rot_xyz = add("ShaderNodeCombineXYZ", (-500, -450))
links.new(angle_mul.outputs["Value"], rot_xyz.inputs["Z"])

# Step box
cube = add("GeometryNodeMeshCube", (-500, -250))
cube.inputs["Size"].default_value = (1.6, 0.9, 0.18)

inst = add("GeometryNodeInstanceOnPoints", (-250, 0))
links.new(setpos.outputs["Geometry"], inst.inputs["Points"])
links.new(cube.outputs["Mesh"], inst.inputs["Instance"])
links.new(rot_xyz.outputs["Vector"], inst.inputs["Rotation"])

realize = add("GeometryNodeRealizeInstances", (0, 0))
links.new(inst.outputs["Instances"], realize.inputs["Geometry"])

# Central column, height = steps * 0.25
depth_mul = add("ShaderNodeMath", (-500, -650))
depth_mul.operation = 'MULTIPLY'
links.new(gin.outputs["Step Count"], depth_mul.inputs[0])
depth_mul.inputs[1].default_value = 0.25

cyl = add("GeometryNodeMeshCylinder", (-250, -650))
cyl.inputs["Vertices"].default_value = 16
cyl.inputs["Radius"].default_value = 0.15
links.new(depth_mul.outputs["Value"], cyl.inputs["Depth"])

half_mul = add("ShaderNodeMath", (-500, -800))
half_mul.operation = 'MULTIPLY'
links.new(gin.outputs["Step Count"], half_mul.inputs[0])
half_mul.inputs[1].default_value = 0.125

half_xyz = add("ShaderNodeCombineXYZ", (-250, -800))
links.new(half_mul.outputs["Value"], half_xyz.inputs["Z"])

cyl_pos = add("GeometryNodeSetPosition", (0, -650))
links.new(cyl.outputs["Mesh"], cyl_pos.inputs["Geometry"])
links.new(half_xyz.outputs["Vector"], cyl_pos.inputs["Offset"])

join = add("GeometryNodeJoinGeometry", (400, 0))
links.new(realize.outputs["Geometry"], join.inputs["Geometry"])
links.new(cyl_pos.outputs["Geometry"], join.inputs["Geometry"])
links.new(join.outputs["Geometry"], gout.inputs["Geometry"])

# ---------------------------------------------------------------------------
# Ground plane
# ---------------------------------------------------------------------------
ground_mesh = bpy.data.meshes.new("GroundMesh")
ground_mesh.from_pydata(
    [(-8, -8, 0), (8, -8, 0), (8, 8, 0), (-8, 8, 0)],
    [],
    [(0, 1, 2, 3)],
)
ground_mesh.update()
ground_obj = bpy.data.objects.new("Ground", ground_mesh)
scene.collection.objects.link(ground_obj)

ground_mat = bpy.data.materials.new("GroundMat")
g_bsdf = ground_mat.node_tree.nodes.get("Principled BSDF")
g_bsdf.inputs["Base Color"].default_value = (0.25, 0.27, 0.3, 1.0)
g_bsdf.inputs["Roughness"].default_value = 0.8
ground_obj.data.materials.append(ground_mat)

# ---------------------------------------------------------------------------
# Staircase object with the Geometry Nodes modifier
# ---------------------------------------------------------------------------
stair_mesh = bpy.data.meshes.new("StaircaseBase")
stair_obj = bpy.data.objects.new("SpiralStaircase", stair_mesh)
scene.collection.objects.link(stair_obj)

stair_mat = bpy.data.materials.new("StairMat")
s_bsdf = stair_mat.node_tree.nodes.get("Principled BSDF")
s_bsdf.inputs["Base Color"].default_value = (0.8, 0.6, 0.4, 1.0)
s_bsdf.inputs["Roughness"].default_value = 0.4
stair_obj.data.materials.append(stair_mat)

mod = stair_obj.modifiers.new(name="Staircase", type="NODES")
mod.node_group = tree
getattr(mod.properties.inputs, steps_item.identifier).value = 24

# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0


# ---------------------------------------------------------------------------
# Lights
# ---------------------------------------------------------------------------
def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun_data)
sun_obj.rotation_euler = (math.radians(50), 0.0, math.radians(30))
scene.collection.objects.link(sun_obj)

area_data = bpy.data.lights.new("KeyArea", "AREA")
area_data.energy = 800.0
area_data.size = 6.0
area_obj = bpy.data.objects.new("KeyArea", area_data)
area_obj.location = (6.0, -7.0, 9.0)
look_at(area_obj, (0.0, 0.0, 3.0))
scene.collection.objects.link(area_obj)

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
cam_obj.location = (11.0, -11.0, 7.0)
look_at(cam_obj, (0.0, 0.0, 3.0))
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

scene.frame_start = 1
scene.frame_end = 1
