import bpy
import math
from mathutils import Vector

# ---------------------------------------------------------------
# Clean default scene objects
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene

# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

wood_mat = make_material("Staircase_Wood", (0.45, 0.27, 0.12), roughness=0.55)
floor_mat = make_material("Floor_Stone", (0.25, 0.25, 0.27), roughness=0.85)

# ---------------------------------------------------------------
# Geometry Nodes tree
# ---------------------------------------------------------------
ng = bpy.data.node_groups.new("SpiralStaircaseGN", "GeometryNodeTree")
iface = ng.interface

s_steps = iface.new_socket(name="Steps", in_out='INPUT', socket_type='NodeSocketInt')
s_steps.default_value = 24
s_steps.min_value = 1
s_steps.max_value = 200

s_radius = iface.new_socket(name="Radius", in_out='INPUT', socket_type='NodeSocketFloat')
s_radius.default_value = 1.0
s_radius.min_value = 0.1
s_radius.max_value = 10.0

iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = ng.nodes
links = ng.links

def node(kind, x, y):
    n = nodes.new(kind)
    n.location = (x, y)
    return n

gin = node('NodeGroupInput', -1400, 0)
gout = node('NodeGroupOutput', 1100, 0)

# Points along a vertical line, one per step
mline = node('GeometryNodeMeshLine', -1100, 0)
mline.mode = 'OFFSET'
mline.inputs['Offset'].default_value = (0.0, 0.0, 0.2)
links.new(gin.outputs['Steps'], mline.inputs['Count'])

# Angle per step: total of 1.5 turns spread over Steps
idx = node('GeometryNodeInputIndex', -1400, -350)

step_ang = node('ShaderNodeMath', -1100, -350)
step_ang.operation = 'DIVIDE'
step_ang.inputs[0].default_value = 3.0 * math.pi
links.new(gin.outputs['Steps'], step_ang.inputs[1])

ang = node('ShaderNodeMath', -900, -350)
ang.operation = 'MULTIPLY'
links.new(idx.outputs['Index'], ang.inputs[0])
links.new(step_ang.outputs[0], ang.inputs[1])

cos_n = node('ShaderNodeMath', -700, -150)
cos_n.operation = 'COSINE'
links.new(ang.outputs[0], cos_n.inputs[0])

sin_n = node('ShaderNodeMath', -700, -450)
sin_n.operation = 'SINE'
links.new(ang.outputs[0], sin_n.inputs[0])

x_r = node('ShaderNodeMath', -500, -150)
x_r.operation = 'MULTIPLY'
links.new(cos_n.outputs[0], x_r.inputs[0])
links.new(gin.outputs['Radius'], x_r.inputs[1])

y_r = node('ShaderNodeMath', -500, -450)
y_r.operation = 'MULTIPLY'
links.new(sin_n.outputs[0], y_r.inputs[0])
links.new(gin.outputs['Radius'], y_r.inputs[1])

pos_n = node('GeometryNodeInputPosition', -900, 100)
sep = node('ShaderNodeSeparateXYZ', -700, 100)
links.new(pos_n.outputs['Position'], sep.inputs['Vector'])

comb_pos = node('ShaderNodeCombineXYZ', -300, -250)
links.new(x_r.outputs[0], comb_pos.inputs['X'])
links.new(y_r.outputs[0], comb_pos.inputs['Y'])
links.new(sep.outputs['Z'], comb_pos.inputs['Z'])

set_pos = node('GeometryNodeSetPosition', -100, 0)
links.new(mline.outputs['Geometry'], set_pos.inputs['Geometry'])
links.new(comb_pos.outputs['Vector'], set_pos.inputs['Position'])

# Tread shape
cube = node('GeometryNodeMeshCube', -100, -400)
cube.inputs['Size'].default_value = (1.2, 0.5, 0.1)

# Rotate each tread about Z to follow the spiral
comb_rot = node('ShaderNodeCombineXYZ', 100, -450)
links.new(ang.outputs[0], comb_rot.inputs['Z'])

inst = node('GeometryNodeInstanceOnPoints', 250, 0)
links.new(set_pos.outputs['Geometry'], inst.inputs['Points'])
links.new(cube.outputs['Mesh'], inst.inputs['Instance'])
links.new(comb_rot.outputs['Vector'], inst.inputs['Rotation'])

realize = node('GeometryNodeRealizeInstances', 500, 0)
links.new(inst.outputs['Instances'], realize.inputs['Geometry'])

set_mat = node('GeometryNodeSetMaterial', 750, 0)
links.new(realize.outputs['Geometry'], set_mat.inputs['Geometry'])
set_mat.inputs['Material'].default_value = wood_mat

links.new(set_mat.outputs['Geometry'], gout.inputs[0])

# ---------------------------------------------------------------
# Staircase object with Geometry Nodes modifier
# ---------------------------------------------------------------
stair_mesh = bpy.data.meshes.new("SpiralStaircaseMesh")
stair_obj = bpy.data.objects.new("SpiralStaircase", stair_mesh)
scene.collection.objects.link(stair_obj)

mod = stair_obj.modifiers.new(name="Staircase", type='NODES')
mod.node_group = ng

# Find the exposed input identifiers and set values
for item in ng.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
        if item.name == "Steps":
            mod[item.identifier] = 24
        elif item.name == "Radius":
            mod[item.identifier] = 1.0

# ---------------------------------------------------------------
# Floor
# ---------------------------------------------------------------
floor_mesh = bpy.data.meshes.new("FloorMesh")
s = 10.0
floor_mesh.from_pydata(
    [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)],
    [],
    [(0, 1, 2, 3)],
)
floor_mesh.update()
floor_mesh.materials.append(floor_mat)
floor_obj = bpy.data.objects.new("Floor", floor_mesh)
scene.collection.objects.link(floor_obj)

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("KeySun", sun_data)
sun_obj.rotation_euler = (math.radians(50), 0, math.radians(35))
scene.collection.objects.link(sun_obj)

area_data = bpy.data.lights.new("FillArea", 'AREA')
area_data.energy = 800.0
area_data.size = 5.0
area_obj = bpy.data.objects.new("FillArea", area_data)
area_obj.location = (4.0, -4.0, 6.0)
scene.collection.objects.link(area_obj)
dir_vec = Vector((0.0, 0.0, 2.4)) - area_obj.location
area_obj.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("StaircaseCam")
cam_data.lens = 40.0
cam_obj = bpy.data.objects.new("StaircaseCam", cam_data)
cam_obj.location = (7.5, -8.5, 5.0)
scene.collection.objects.link(cam_obj)

target = Vector((0.0, 0.0, 2.4))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------------------------------------------------------------
# Frame range (single still frame)
# ---------------------------------------------------------------
scene.frame_start = 1
scene.frame_end = 1
