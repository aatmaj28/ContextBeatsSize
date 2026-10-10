import bpy
import math
import mathutils
import bmesh

# ---------------------------------------------------------------------------
# Clean up any existing objects
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

RISE = 0.25  # height gained per step

# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
stair_mat = bpy.data.materials.new("StairMaterial")
bsdf = stair_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.75, 0.6, 0.42, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55

ground_mat = bpy.data.materials.new("GroundMaterial")
gbsdf = ground_mat.node_tree.nodes.get("Principled BSDF")
if gbsdf:
    gbsdf.inputs["Base Color"].default_value = (0.25, 0.27, 0.3, 1.0)
    gbsdf.inputs["Roughness"].default_value = 0.9

# ---------------------------------------------------------------------------
# Geometry Nodes tree: spiral staircase
# ---------------------------------------------------------------------------
tree = bpy.data.node_groups.new("SpiralStaircase", "GeometryNodeTree")

steps_item = tree.interface.new_socket(name="Steps", in_out="INPUT", socket_type="NodeSocketInt")
steps_item.default_value = 24
steps_item.min_value = 3
steps_item.max_value = 64

radius_item = tree.interface.new_socket(name="Radius", in_out="INPUT", socket_type="NodeSocketFloat")
radius_item.default_value = 2.0
radius_item.min_value = 0.5
radius_item.max_value = 10.0

tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

# A new node tree is empty in 5.x: create the group input/output nodes explicitly
gin = tree.nodes.new("NodeGroupInput")
gout = tree.nodes.new("NodeGroupOutput")
L = tree.links


def math_node(op):
    n = tree.nodes.new("ShaderNodeMath")
    n.operation = op
    return n


# Step positions along a line, one vertex per step
mesh_line = tree.nodes.new("GeometryNodeMeshLine")
L.new(gin.outputs["Steps"], mesh_line.inputs["Count"])
mesh_line.inputs["Offset"].default_value = (0.0, 0.0, RISE)

m2p = tree.nodes.new("GeometryNodeMeshToPoints")
L.new(mesh_line.outputs["Mesh"], m2p.inputs["Mesh"])

index = tree.nodes.new("GeometryNodeInputIndex")

# angle = Index * (2*pi / Steps)
inv_angle = math_node('DIVIDE')
inv_angle.inputs[0].default_value = 2.0 * math.pi
L.new(gin.outputs["Steps"], inv_angle.inputs[1])

angle = math_node('MULTIPLY')
L.new(index.outputs["Index"], angle.inputs[0])
L.new(inv_angle.outputs[0], angle.inputs[1])

cos_n = math_node('COSINE')
L.new(angle.outputs[0], cos_n.inputs[0])
sin_n = math_node('SINE')
L.new(angle.outputs[0], sin_n.inputs[0])

x_r = math_node('MULTIPLY')
L.new(cos_n.outputs[0], x_r.inputs[0])
L.new(gin.outputs["Radius"], x_r.inputs[1])

y_r = math_node('MULTIPLY')
L.new(sin_n.outputs[0], y_r.inputs[0])
L.new(gin.outputs["Radius"], y_r.inputs[1])

z_h = math_node('MULTIPLY')
L.new(index.outputs["Index"], z_h.inputs[0])
z_h.inputs[1].default_value = RISE

pos_vec = tree.nodes.new("ShaderNodeCombineXYZ")
L.new(x_r.outputs[0], pos_vec.inputs["X"])
L.new(y_r.outputs[0], pos_vec.inputs["Y"])
L.new(z_h.outputs[0], pos_vec.inputs["Z"])

set_pos = tree.nodes.new("GeometryNodeSetPosition")
L.new(m2p.outputs["Points"], set_pos.inputs["Geometry"])
L.new(pos_vec.outputs["Vector"], set_pos.inputs["Position"])

rot_vec = tree.nodes.new("ShaderNodeCombineXYZ")
L.new(angle.outputs[0], rot_vec.inputs["Z"])

# Each tread is a box, oriented radially
tread = tree.nodes.new("GeometryNodeMeshCube")
tread.inputs["Size"].default_value = (1.8, 1.0, 0.12)

inst = tree.nodes.new("GeometryNodeInstanceOnPoints")
L.new(set_pos.outputs["Geometry"], inst.inputs["Points"])
L.new(tread.outputs["Mesh"], inst.inputs["Instance"])
L.new(rot_vec.outputs["Vector"], inst.inputs["Rotation"])

realize = tree.nodes.new("GeometryNodeRealizeInstances")
L.new(inst.outputs["Instances"], realize.inputs["Geometry"])

# Central pole spanning the full height
pole_depth = math_node('MULTIPLY')
L.new(gin.outputs["Steps"], pole_depth.inputs[0])
pole_depth.inputs[1].default_value = RISE

pole = tree.nodes.new("GeometryNodeMeshCylinder")
pole.inputs["Radius"].default_value = 0.18
L.new(pole_depth.outputs[0], pole.inputs["Depth"])

half_h = math_node('MULTIPLY')
L.new(pole_depth.outputs[0], half_h.inputs[0])
half_h.inputs[1].default_value = 0.5

off_vec = tree.nodes.new("ShaderNodeCombineXYZ")
L.new(half_h.outputs[0], off_vec.inputs["Z"])

pole_set = tree.nodes.new("GeometryNodeSetPosition")
L.new(pole.outputs["Mesh"], pole_set.inputs["Geometry"])
L.new(off_vec.outputs["Vector"], pole_set.inputs["Offset"])

join = tree.nodes.new("GeometryNodeJoinGeometry")
L.new(realize.outputs["Geometry"], join.inputs["Geometry"])
L.new(pole_set.outputs["Geometry"], join.inputs["Geometry"])

L.new(join.outputs["Geometry"], gout.inputs["Geometry"])

# ---------------------------------------------------------------------------
# Host object with Geometry Nodes modifier
# ---------------------------------------------------------------------------
stair_mesh = bpy.data.meshes.new("StaircaseMesh")
stair_obj = bpy.data.objects.new("SpiralStaircase", stair_mesh)
bpy.context.scene.collection.objects.link(stair_obj)
stair_obj.data.materials.append(stair_mat)

mod = stair_obj.modifiers.new("Spiral Staircase", "NODES")
mod.node_group = tree

# Set the exposed inputs (RNA-style modifier properties in 5.2)
getattr(mod.properties.inputs, steps_item.identifier).value = 24
getattr(mod.properties.inputs, radius_item.identifier).value = 2.0

# ---------------------------------------------------------------------------
# Ground plane
# ---------------------------------------------------------------------------
ground_mesh = bpy.data.meshes.new("GroundMesh")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=12.0)
bm.to_mesh(ground_mesh)
bm.free()
ground_mesh.materials.append(ground_mat)
ground_obj = bpy.data.objects.new("Ground", ground_mesh)
bpy.context.scene.collection.objects.link(ground_obj)

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), 0.0, math.radians(35))

fill_data = bpy.data.lights.new("Fill", "AREA")
fill_data.energy = 400.0
fill_data.size = 6.0
fill_obj = bpy.data.objects.new("Fill", fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.location = (-8.0, -6.0, 8.0)
fill_obj.rotation_euler = (math.radians(60), 0.0, math.radians(-50))

# ---------------------------------------------------------------------------
# Camera framing the staircase
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = (12.0, -13.0, 8.5)

target = mathutils.Vector((0.0, 0.0, 3.0))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam_obj
