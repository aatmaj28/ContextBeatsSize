import bpy
import math

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene

# ---------- Materials ----------
def make_mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return m

mat_step = make_mat("Steps_Wood", (0.45, 0.25, 0.12), 0.45)
mat_column = make_mat("Column_Metal", (0.6, 0.6, 0.62), 0.3, 1.0)
mat_rail = make_mat("Baluster_Metal", (0.08, 0.08, 0.08), 0.35, 1.0)
mat_floor = make_mat("Floor", (0.75, 0.73, 0.7), 0.8)

# ---------- Geometry Nodes tree ----------
tree = bpy.data.node_groups.new("SpiralStaircase", "GeometryNodeTree")
iface = tree.interface
iface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
steps_sock = iface.new_socket(name="Step Count", in_out='INPUT', socket_type='NodeSocketInt')
steps_sock.default_value = 16
steps_sock.min_value = 1
steps_sock.max_value = 500
iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = tree.nodes
links = tree.links

STEP_H = 0.2
STEP_ANGLE = math.radians(15)

gin = nodes.new("NodeGroupInput"); gin.location = (-1200, 0)
gout = nodes.new("NodeGroupOutput"); gout.location = (1200, 0)

# Points along Z
line = nodes.new("GeometryNodeMeshLine"); line.location = (-900, 200)
line.inputs["Start Location"].default_value = (0, 0, STEP_H)
line.inputs["Offset"].default_value = (0, 0, STEP_H)
links.new(gin.outputs["Step Count"], line.inputs["Count"])

# Rotation per index
idx = nodes.new("GeometryNodeInputIndex"); idx.location = (-1100, -200)
mul = nodes.new("ShaderNodeMath"); mul.location = (-900, -200)
mul.operation = 'MULTIPLY'
mul.inputs[1].default_value = STEP_ANGLE
links.new(idx.outputs["Index"], mul.inputs[0])
comb_rot = nodes.new("ShaderNodeCombineXYZ"); comb_rot.location = (-700, -200)
links.new(mul.outputs["Value"], comb_rot.inputs["Z"])

# Step tread
cube = nodes.new("GeometryNodeMeshCube"); cube.location = (-900, 500)
cube.inputs["Size"].default_value = (1.6, 0.55, 0.08)
cube_tf = nodes.new("GeometryNodeTransform"); cube_tf.location = (-700, 500)
cube_tf.inputs["Translation"].default_value = (0.95, 0, 0)
links.new(cube.outputs["Mesh"], cube_tf.inputs["Geometry"])

inst_steps = nodes.new("GeometryNodeInstanceOnPoints"); inst_steps.location = (-400, 300)
links.new(line.outputs["Mesh"], inst_steps.inputs["Points"])
links.new(cube_tf.outputs["Geometry"], inst_steps.inputs["Instance"])
links.new(comb_rot.outputs["Vector"], inst_steps.inputs["Rotation"])

real_steps = nodes.new("GeometryNodeRealizeInstances"); real_steps.location = (-200, 300)
links.new(inst_steps.outputs["Instances"], real_steps.inputs["Geometry"])
setmat_steps = nodes.new("GeometryNodeSetMaterial"); setmat_steps.location = (0, 300)
setmat_steps.inputs["Material"].default_value = mat_step
links.new(real_steps.outputs["Geometry"], setmat_steps.inputs["Geometry"])

# Balusters
bal = nodes.new("GeometryNodeMeshCylinder"); bal.location = (-900, -500)
bal.inputs["Radius"].default_value = 0.02
bal.inputs["Depth"].default_value = 0.9
bal.inputs["Vertices"].default_value = 8
bal_tf = nodes.new("GeometryNodeTransform"); bal_tf.location = (-700, -500)
bal_tf.inputs["Translation"].default_value = (1.65, 0, 0.49)
links.new(bal.outputs["Mesh"], bal_tf.inputs["Geometry"])

inst_bal = nodes.new("GeometryNodeInstanceOnPoints"); inst_bal.location = (-400, -400)
links.new(line.outputs["Mesh"], inst_bal.inputs["Points"])
links.new(bal_tf.outputs["Geometry"], inst_bal.inputs["Instance"])
links.new(comb_rot.outputs["Vector"], inst_bal.inputs["Rotation"])
real_bal = nodes.new("GeometryNodeRealizeInstances"); real_bal.location = (-200, -400)
links.new(inst_bal.outputs["Instances"], real_bal.inputs["Geometry"])
setmat_bal = nodes.new("GeometryNodeSetMaterial"); setmat_bal.location = (0, -400)
setmat_bal.inputs["Material"].default_value = mat_rail
links.new(real_bal.outputs["Geometry"], setmat_bal.inputs["Geometry"])

# Central column, height scales with step count
h_mul = nodes.new("ShaderNodeMath"); h_mul.location = (-900, -900)
h_mul.operation = 'MULTIPLY'
h_mul.inputs[1].default_value = STEP_H
links.new(gin.outputs["Step Count"], h_mul.inputs[0])
h_add = nodes.new("ShaderNodeMath"); h_add.location = (-700, -900)
h_add.operation = 'ADD'
h_add.inputs[1].default_value = 1.0
links.new(h_mul.outputs["Value"], h_add.inputs[0])
h_half = nodes.new("ShaderNodeMath"); h_half.location = (-500, -1000)
h_half.operation = 'MULTIPLY'
h_half.inputs[1].default_value = 0.5
links.new(h_add.outputs["Value"], h_half.inputs[0])

col = nodes.new("GeometryNodeMeshCylinder"); col.location = (-500, -800)
col.inputs["Radius"].default_value = 0.15
col.inputs["Vertices"].default_value = 32
links.new(h_add.outputs["Value"], col.inputs["Depth"])
col_off = nodes.new("ShaderNodeCombineXYZ"); col_off.location = (-300, -1000)
links.new(h_half.outputs["Value"], col_off.inputs["Z"])
col_tf = nodes.new("GeometryNodeTransform"); col_tf.location = (-200, -800)
links.new(col.outputs["Mesh"], col_tf.inputs["Geometry"])
links.new(col_off.outputs["Vector"], col_tf.inputs["Translation"])
setmat_col = nodes.new("GeometryNodeSetMaterial"); setmat_col.location = (0, -800)
setmat_col.inputs["Material"].default_value = mat_column
links.new(col_tf.outputs["Geometry"], setmat_col.inputs["Geometry"])

join = nodes.new("GeometryNodeJoinGeometry"); join.location = (400, 0)
links.new(setmat_steps.outputs["Geometry"], join.inputs["Geometry"])
links.new(setmat_bal.outputs["Geometry"], join.inputs["Geometry"])
links.new(setmat_col.outputs["Geometry"], join.inputs["Geometry"])
links.new(join.outputs["Geometry"], gout.inputs["Geometry"])

# ---------- Host object ----------
mesh = bpy.data.meshes.new("StairHost")
stairs = bpy.data.objects.new("SpiralStaircase", mesh)
scene.collection.objects.link(stairs)
for m in (mat_step, mat_rail, mat_column):
    mesh.materials.append(m)
mod = stairs.modifiers.new("SpiralStairs", 'NODES')
mod.node_group = tree
mod[steps_sock.identifier] = 24
stairs.update_tag()

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(mat_floor)

# ---------- Lighting ----------
sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun)
sun_obj.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
scene.collection.objects.link(sun_obj)

area = bpy.data.lights.new("Fill", 'AREA')
area.energy = 600
area.size = 5
area_obj = bpy.data.objects.new("Fill", area)
area_obj.location = (-5, -4, 6)
scene.collection.objects.link(area_obj)
c = area_obj.constraints.new('TRACK_TO')

target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 2.4)
scene.collection.objects.link(target)
c.target = target

if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.6, 0.7, 0.85, 1)
    bg.inputs["Strength"].default_value = 0.6

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (7.5, -7.5, 4.5)
scene.collection.objects.link(cam)
tc = cam.constraints.new('TRACK_TO')
tc.target = target
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
