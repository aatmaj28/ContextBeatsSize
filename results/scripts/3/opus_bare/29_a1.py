import bpy
import math

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene

# ---------- Materials ----------
def make_mat(name, color, rough, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return m

mat_step = make_mat("StepWood", (0.45, 0.25, 0.12), 0.45)
mat_col = make_mat("ColumnMetal", (0.6, 0.6, 0.65), 0.3, 1.0)
mat_floor = make_mat("Floor", (0.35, 0.35, 0.38), 0.8)

# ---------- Geometry node group ----------
ng = bpy.data.node_groups.new("SpiralStaircase", 'GeometryNodeTree')
iface = ng.interface
iface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
s_steps = iface.new_socket(name="Steps", in_out='INPUT', socket_type='NodeSocketInt')
s_steps.default_value = 12
s_steps.min_value = 1
s_steps.max_value = 500
s_h = iface.new_socket(name="Step Height", in_out='INPUT', socket_type='NodeSocketFloat')
s_h.default_value = 0.2
s_a = iface.new_socket(name="Angle Per Step", in_out='INPUT', socket_type='NodeSocketFloat')
s_a.default_value = math.radians(15)
iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

N = ng.nodes
L = ng.links

gin = N.new('NodeGroupInput'); gin.location = (-900, 0)
gout = N.new('NodeGroupOutput'); gout.location = (900, 0)

# Line of points going up
off = N.new('ShaderNodeCombineXYZ'); off.location = (-650, 200)
L.new(gin.outputs["Step Height"], off.inputs["Z"])
line = N.new('GeometryNodeMeshLine'); line.location = (-450, 200)
L.new(gin.outputs["Steps"], line.inputs["Count"])
line.inputs["Start Location"].default_value = (0, 0, 0.2)
L.new(off.outputs["Vector"], line.inputs["Offset"])

# Step shape
cube = N.new('GeometryNodeMeshCube'); cube.location = (-650, -100)
cube.inputs["Size"].default_value = (1.4, 0.45, 0.06)
xf = N.new('GeometryNodeTransform'); xf.location = (-450, -100)
xf.inputs["Translation"].default_value = (0.75, 0, 0)
L.new(cube.outputs["Mesh"], xf.inputs["Geometry"])

# Rotation = index * angle
idx = N.new('GeometryNodeInputIndex'); idx.location = (-650, -300)
mul = N.new('ShaderNodeMath'); mul.location = (-450, -300)
mul.operation = 'MULTIPLY'
L.new(idx.outputs["Index"], mul.inputs[0])
L.new(gin.outputs["Angle Per Step"], mul.inputs[1])
rot = N.new('ShaderNodeCombineXYZ'); rot.location = (-250, -300)
L.new(mul.outputs["Value"], rot.inputs["Z"])

inst = N.new('GeometryNodeInstanceOnPoints'); inst.location = (-50, 100)
L.new(line.outputs["Mesh"], inst.inputs["Points"])
L.new(xf.outputs["Geometry"], inst.inputs["Instance"])
L.new(rot.outputs["Vector"], inst.inputs["Rotation"])

real = N.new('GeometryNodeRealizeInstances'); real.location = (150, 100)
L.new(inst.outputs["Instances"], real.inputs["Geometry"])
smat1 = N.new('GeometryNodeSetMaterial'); smat1.location = (350, 100)
smat1.inputs["Material"].default_value = mat_step
L.new(real.outputs["Geometry"], smat1.inputs["Geometry"])

# Central column
depth = N.new('ShaderNodeMath'); depth.location = (-450, -500)
depth.operation = 'MULTIPLY'
L.new(gin.outputs["Steps"], depth.inputs[0])
L.new(gin.outputs["Step Height"], depth.inputs[1])
depth2 = N.new('ShaderNodeMath'); depth2.location = (-250, -500)
depth2.operation = 'ADD'
L.new(depth.outputs["Value"], depth2.inputs[0])
depth2.inputs[1].default_value = 0.6
half = N.new('ShaderNodeMath'); half.location = (-50, -600)
half.operation = 'MULTIPLY'
L.new(depth2.outputs["Value"], half.inputs[0])
half.inputs[1].default_value = 0.5
cyl = N.new('GeometryNodeMeshCylinder'); cyl.location = (-50, -400)
cyl.inputs["Vertices"].default_value = 32
cyl.inputs["Radius"].default_value = 0.12
L.new(depth2.outputs["Value"], cyl.inputs["Depth"])
cpos = N.new('ShaderNodeCombineXYZ'); cpos.location = (150, -600)
L.new(half.outputs["Value"], cpos.inputs["Z"])
cxf = N.new('GeometryNodeTransform'); cxf.location = (350, -400)
L.new(cyl.outputs["Mesh"], cxf.inputs["Geometry"])
L.new(cpos.outputs["Vector"], cxf.inputs["Translation"])
smat2 = N.new('GeometryNodeSetMaterial'); smat2.location = (550, -400)
smat2.inputs["Material"].default_value = mat_col
L.new(cxf.outputs["Geometry"], smat2.inputs["Geometry"])

join = N.new('GeometryNodeJoinGeometry'); join.location = (700, 0)
L.new(smat2.outputs["Geometry"], join.inputs["Geometry"])
L.new(smat1.outputs["Geometry"], join.inputs["Geometry"])
L.new(join.outputs["Geometry"], gout.inputs["Geometry"])

# ---------- Object with modifier ----------
mesh = bpy.data.meshes.new("StairBase")
obj = bpy.data.objects.new("SpiralStaircase", mesh)
scene.collection.objects.link(obj)
obj.data.materials.append(mat_step)
obj.data.materials.append(mat_col)
mod = obj.modifiers.new("Staircase", 'NODES')
mod.node_group = ng
mod[s_steps.identifier] = 24
obj.update_tag()

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(mat_floor)

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Lights ----------
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))
scene.collection.objects.link(sun)

area = bpy.data.objects.new("Area", bpy.data.lights.new("Area", 'AREA'))
area.data.energy = 800
area.data.size = 4
area.location = (-4, -4, 7)
scene.collection.objects.link(area)
area.rotation_euler = (math.radians(45), 0, math.radians(-45))

# ---------- Camera ----------
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.lens = 35
cam.location = (7.5, -7.5, 5.0)
scene.collection.objects.link(cam)
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 2.4)
scene.collection.objects.link(target)
tc = cam.constraints.new('TRACK_TO')
tc.target = target
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
