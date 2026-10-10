import bpy
import math

# ---------- Clean scene ----------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

scene = bpy.context.scene

# ---------- Materials ----------
def make_mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return m

mat_step = make_mat("StepWood", (0.45, 0.25, 0.12), 0.4)
mat_metal = make_mat("Metal", (0.6, 0.6, 0.62), 0.3, 1.0)
mat_floor = make_mat("Floor", (0.3, 0.3, 0.32), 0.8)

# ---------- Geometry node group ----------
ng = bpy.data.node_groups.new("SpiralStaircase", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
steps_item = ng.interface.new_socket("Steps", in_out="INPUT", socket_type="NodeSocketInt")
steps_item.default_value = 12
steps_item.min_value = 1
steps_item.max_value = 500

N = ng.nodes
L = ng.links

gin = N.new("NodeGroupInput"); gin.location = (-1200, 0)
gout = N.new("NodeGroupOutput"); gout.location = (1000, 0)

RISE = 0.18
ANGLE = math.radians(15.0)

# Points along Z
line = N.new("GeometryNodeMeshLine"); line.location = (-900, 200)
line.inputs["Offset"].default_value = (0.0, 0.0, RISE)
L.new(gin.outputs["Steps"], line.inputs["Count"])

# Step tread
cube = N.new("GeometryNodeMeshCube"); cube.location = (-900, -100)
cube.inputs["Size"].default_value = (1.6, 0.5, 0.06)
tr_cube = N.new("GeometryNodeTransform"); tr_cube.location = (-700, -100)
tr_cube.inputs["Translation"].default_value = (1.0, 0.0, 0.0)
L.new(cube.outputs["Mesh"], tr_cube.inputs["Geometry"])
sm_step = N.new("GeometryNodeSetMaterial"); sm_step.location = (-500, -100)
sm_step.inputs["Material"].default_value = mat_step
L.new(tr_cube.outputs["Geometry"], sm_step.inputs["Geometry"])

# Railing post
post = N.new("GeometryNodeMeshCylinder"); post.location = (-900, -350)
post.inputs["Radius"].default_value = 0.02
post.inputs["Depth"].default_value = 0.9
post.inputs["Vertices"].default_value = 12
tr_post = N.new("GeometryNodeTransform"); tr_post.location = (-700, -350)
tr_post.inputs["Translation"].default_value = (1.7, 0.0, 0.48)
L.new(post.outputs["Mesh"], tr_post.inputs["Geometry"])
sm_post = N.new("GeometryNodeSetMaterial"); sm_post.location = (-500, -350)
sm_post.inputs["Material"].default_value = mat_metal
L.new(tr_post.outputs["Geometry"], sm_post.inputs["Geometry"])

join_inst = N.new("GeometryNodeJoinGeometry"); join_inst.location = (-300, -200)
L.new(sm_post.outputs["Geometry"], join_inst.inputs["Geometry"])
L.new(sm_step.outputs["Geometry"], join_inst.inputs["Geometry"])

# Rotation per index
idx = N.new("GeometryNodeInputIndex"); idx.location = (-900, 450)
mul = N.new("ShaderNodeMath"); mul.location = (-700, 450)
mul.operation = 'MULTIPLY'
mul.inputs[1].default_value = ANGLE
L.new(idx.outputs["Index"], mul.inputs[0])
comb = N.new("ShaderNodeCombineXYZ"); comb.location = (-500, 450)
L.new(mul.outputs["Value"], comb.inputs["Z"])
e2r = N.new("FunctionNodeEulerToRotation"); e2r.location = (-300, 450)
L.new(comb.outputs["Vector"], e2r.inputs["Euler"])

iop = N.new("GeometryNodeInstanceOnPoints"); iop.location = (-50, 200)
L.new(line.outputs["Mesh"], iop.inputs["Points"])
L.new(join_inst.outputs["Geometry"], iop.inputs["Instance"])
L.new(e2r.outputs["Rotation"], iop.inputs["Rotation"])

realize = N.new("GeometryNodeRealizeInstances"); realize.location = (200, 200)
L.new(iop.outputs["Instances"], realize.inputs["Geometry"])

# Central column, height depends on step count
hmul = N.new("ShaderNodeMath"); hmul.location = (-700, -650)
hmul.operation = 'MULTIPLY_ADD'
hmul.inputs[1].default_value = RISE
hmul.inputs[2].default_value = 0.3
L.new(gin.outputs["Steps"], hmul.inputs[0])
col = N.new("GeometryNodeMeshCylinder"); col.location = (-500, -650)
col.inputs["Radius"].default_value = 0.2
col.inputs["Vertices"].default_value = 32
L.new(hmul.outputs["Value"], col.inputs["Depth"])
half = N.new("ShaderNodeMath"); half.location = (-500, -850)
half.operation = 'MULTIPLY'
half.inputs[1].default_value = 0.5
L.new(hmul.outputs["Value"], half.inputs[0])
ctr = N.new("ShaderNodeCombineXYZ"); ctr.location = (-300, -850)
L.new(half.outputs["Value"], ctr.inputs["Z"])
tr_col = N.new("GeometryNodeTransform"); tr_col.location = (-100, -650)
L.new(col.outputs["Mesh"], tr_col.inputs["Geometry"])
L.new(ctr.outputs["Vector"], tr_col.inputs["Translation"])
sm_col = N.new("GeometryNodeSetMaterial"); sm_col.location = (100, -650)
sm_col.inputs["Material"].default_value = mat_metal
L.new(tr_col.outputs["Geometry"], sm_col.inputs["Geometry"])

join_all = N.new("GeometryNodeJoinGeometry"); join_all.location = (500, 0)
L.new(sm_col.outputs["Geometry"], join_all.inputs["Geometry"])
L.new(realize.outputs["Geometry"], join_all.inputs["Geometry"])

shade = N.new("GeometryNodeSetShadeSmooth"); shade.location = (750, 0)
shade.inputs["Shade Smooth"].default_value = False
L.new(join_all.outputs["Geometry"], shade.inputs["Geometry"])
L.new(shade.outputs["Geometry"], gout.inputs["Geometry"])

# ---------- Host object ----------
mesh = bpy.data.meshes.new("StairBase")
obj = bpy.data.objects.new("SpiralStaircase", mesh)
scene.collection.objects.link(obj)
obj.data.materials.append(mat_step)
obj.data.materials.append(mat_metal)

mod = obj.modifiers.new("SpiralStaircase", "NODES")
mod.node_group = ng
try:
    getattr(mod.properties.inputs, steps_item.identifier).value = 24
except Exception:
    mod[steps_item.identifier] = 24

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, -0.03))
floor = bpy.context.active_object
floor.data.materials.append(mat_floor)

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Lights ----------
sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 3.0
sun_ob = bpy.data.objects.new("Sun", sun)
sun_ob.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(sun_ob)

area = bpy.data.lights.new("Fill", 'AREA')
area.energy = 800
area.size = 4
area_ob = bpy.data.objects.new("Fill", area)
area_ob.location = (-5, -4, 6)
scene.collection.objects.link(area_ob)
d = area_ob.location.copy()
area_ob.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()

# ---------- Camera ----------
cam = bpy.data.cameras.new("Camera")
cam.lens = 35
cam_ob = bpy.data.objects.new("Camera", cam)
cam_ob.location = (7.5, -7.5, 5.0)
scene.collection.objects.link(cam_ob)
import mathutils
target = mathutils.Vector((0, 0, 2.2))
cam_ob.rotation_euler = (target - cam_ob.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_ob

scene.frame_start = 1
scene.frame_end = 1
