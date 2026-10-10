import bpy
import math

# Clean scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

scene = bpy.context.scene

# Materials
def make_mat(name, color, rough, metal=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m

mat_wood = make_mat("StepWood", (0.45, 0.25, 0.12), 0.45)
mat_metal = make_mat("Metal", (0.6, 0.6, 0.65), 0.3, 1.0)
mat_floor = make_mat("Floor", (0.3, 0.3, 0.32), 0.8)

# Parameters
STEP_H = 0.2
ANGLE = math.radians(15)
INNER = 0.15
LENGTH = 1.6
WIDTH = 0.45
THICK = 0.06

# Geometry node group
ng = bpy.data.node_groups.new("SpiralStaircase", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
steps_item = ng.interface.new_socket("Steps", in_out="INPUT", socket_type="NodeSocketInt")
steps_item.default_value = 12
steps_item.min_value = 1
steps_item.max_value = 500

N = ng.nodes
L = ng.links

gin = N.new("NodeGroupInput"); gin.location = (-1200, 0)
gout = N.new("NodeGroupOutput"); gout.location = (1200, 0)

# Points along Z
line = N.new("GeometryNodeMeshLine"); line.location = (-900, 200)
line.inputs["Offset"].default_value = (0, 0, STEP_H)
line.inputs["Start Location"].default_value = (0, 0, STEP_H)
L.new(gin.outputs["Steps"], line.inputs["Count"])

# Rotation per index
idx = N.new("GeometryNodeInputIndex"); idx.location = (-900, -100)
mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.location = (-700, -100)
mul.inputs[1].default_value = ANGLE
L.new(idx.outputs["Index"], mul.inputs[0])
rot = N.new("ShaderNodeCombineXYZ"); rot.location = (-500, -100)
L.new(mul.outputs[0], rot.inputs["Z"])

# Step tread
cube = N.new("GeometryNodeMeshCube"); cube.location = (-900, 500)
cube.inputs["Size"].default_value = (LENGTH, WIDTH, THICK)
tr_step = N.new("GeometryNodeTransform"); tr_step.location = (-700, 500)
tr_step.inputs["Translation"].default_value = (INNER + LENGTH / 2, 0, -THICK / 2)
L.new(cube.outputs["Mesh"], tr_step.inputs["Geometry"])

inst_steps = N.new("GeometryNodeInstanceOnPoints"); inst_steps.location = (-300, 400)
L.new(line.outputs["Mesh"], inst_steps.inputs["Points"])
L.new(tr_step.outputs["Geometry"], inst_steps.inputs["Instance"])
L.new(rot.outputs["Vector"], inst_steps.inputs["Rotation"])

# Baluster
bal = N.new("GeometryNodeMeshCylinder"); bal.location = (-900, -400)
bal.inputs["Vertices"].default_value = 12
bal.inputs["Radius"].default_value = 0.02
bal.inputs["Depth"].default_value = 0.9
tr_bal = N.new("GeometryNodeTransform"); tr_bal.location = (-700, -400)
tr_bal.inputs["Translation"].default_value = (INNER + LENGTH - 0.08, 0, 0.45)
L.new(bal.outputs["Mesh"], tr_bal.inputs["Geometry"])

inst_bal = N.new("GeometryNodeInstanceOnPoints"); inst_bal.location = (-300, -300)
L.new(line.outputs["Mesh"], inst_bal.inputs["Points"])
L.new(tr_bal.outputs["Geometry"], inst_bal.inputs["Instance"])
L.new(rot.outputs["Vector"], inst_bal.inputs["Rotation"])

# Central column, height = steps * step height + extra
hmul = N.new("ShaderNodeMath"); hmul.operation = 'MULTIPLY'; hmul.location = (-900, -700)
hmul.inputs[1].default_value = STEP_H
L.new(gin.outputs["Steps"], hmul.inputs[0])
hadd = N.new("ShaderNodeMath"); hadd.operation = 'ADD'; hadd.location = (-700, -700)
hadd.inputs[1].default_value = 1.0
L.new(hmul.outputs[0], hadd.inputs[0])
half = N.new("ShaderNodeMath"); half.operation = 'MULTIPLY'; half.location = (-500, -800)
half.inputs[1].default_value = 0.5
L.new(hadd.outputs[0], half.inputs[0])
col_pos = N.new("ShaderNodeCombineXYZ"); col_pos.location = (-300, -800)
L.new(half.outputs[0], col_pos.inputs["Z"])

col = N.new("GeometryNodeMeshCylinder"); col.location = (-500, -600)
col.inputs["Vertices"].default_value = 32
col.inputs["Radius"].default_value = INNER + 0.02
L.new(hadd.outputs[0], col.inputs["Depth"])
tr_col = N.new("GeometryNodeTransform"); tr_col.location = (-100, -650)
L.new(col.outputs["Mesh"], tr_col.inputs["Geometry"])
L.new(col_pos.outputs["Vector"], tr_col.inputs["Translation"])

# Realize + materials
real_steps = N.new("GeometryNodeRealizeInstances"); real_steps.location = (0, 400)
L.new(inst_steps.outputs["Instances"], real_steps.inputs["Geometry"])
sm_wood = N.new("GeometryNodeSetMaterial"); sm_wood.location = (250, 400)
sm_wood.inputs["Material"].default_value = mat_wood
L.new(real_steps.outputs["Geometry"], sm_wood.inputs["Geometry"])

real_bal = N.new("GeometryNodeRealizeInstances"); real_bal.location = (0, -300)
L.new(inst_bal.outputs["Instances"], real_bal.inputs["Geometry"])
join_metal = N.new("GeometryNodeJoinGeometry"); join_metal.location = (200, -400)
L.new(tr_col.outputs["Geometry"], join_metal.inputs["Geometry"])
L.new(real_bal.outputs["Geometry"], join_metal.inputs["Geometry"])
sm_metal = N.new("GeometryNodeSetMaterial"); sm_metal.location = (400, -400)
sm_metal.inputs["Material"].default_value = mat_metal
L.new(join_metal.outputs["Geometry"], sm_metal.inputs["Geometry"])

join = N.new("GeometryNodeJoinGeometry"); join.location = (800, 0)
L.new(sm_wood.outputs["Geometry"], join.inputs["Geometry"])
L.new(sm_metal.outputs["Geometry"], join.inputs["Geometry"])
smooth = N.new("GeometryNodeSetShadeSmooth"); smooth.location = (1000, 0)
smooth.inputs["Shade Smooth"].default_value = False
L.new(join.outputs["Geometry"], smooth.inputs["Geometry"])
L.new(smooth.outputs["Geometry"], gout.inputs["Geometry"])

# Host object
mesh = bpy.data.meshes.new("StaircaseMesh")
obj = bpy.data.objects.new("SpiralStaircase", mesh)
scene.collection.objects.link(obj)
obj.data.materials.append(mat_wood)
obj.data.materials.append(mat_metal)
mod = obj.modifiers.new("SpiralStaircase", "NODES")
mod.node_group = ng

# Set Steps = 24
try:
    getattr(mod.properties.inputs, steps_item.identifier).value = 24
except Exception:
    mod[steps_item.identifier] = 24

# Floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(mat_floor)

# Lights
sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 3.0
sun_ob = bpy.data.objects.new("Sun", sun)
sun_ob.rotation_euler = (math.radians(45), math.radians(10), math.radians(30))
scene.collection.objects.link(sun_ob)

area = bpy.data.lights.new("Fill", 'AREA')
area.energy = 800
area.size = 5
area_ob = bpy.data.objects.new("Fill", area)
area_ob.location = (-5, -4, 6)
scene.collection.objects.link(area_ob)

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
    bg.inputs["Strength"].default_value = 1.0

# Camera
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 2.4)
scene.collection.objects.link(target)
cam = bpy.data.cameras.new("Camera")
cam.lens = 35
cam_ob = bpy.data.objects.new("Camera", cam)
cam_ob.location = (7.5, -7.5, 4.5)
scene.collection.objects.link(cam_ob)
c = cam_ob.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam_ob

scene.render.resolution_x = 1080
scene.render.resolution_y = 1350
