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
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m

mat_step = make_mat("StepWood", (0.45, 0.25, 0.12), 0.45)
mat_col = make_mat("ColumnStone", (0.7, 0.7, 0.68), 0.6)
mat_metal = make_mat("RailMetal", (0.15, 0.15, 0.17), 0.3, 1.0)
mat_floor = make_mat("Floor", (0.35, 0.35, 0.38), 0.8)

# ---------- Geometry node group ----------
ng = bpy.data.node_groups.new("SpiralStaircase", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
steps_item = ng.interface.new_socket("Steps", in_out="INPUT", socket_type="NodeSocketInt")
steps_item.default_value = 16
steps_item.min_value = 1
steps_item.max_value = 500
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

N = ng.nodes
L = ng.links
gin = N.new("NodeGroupInput"); gin.location = (-1400, 0)
gout = N.new("NodeGroupOutput"); gout.location = (1200, 0)

RISE = 0.18
ANG = math.radians(15.0)
RAIL_R = 1.55
RAIL_H = 0.9

def math_node(op, a=None, b=None, loc=(0, 0)):
    n = N.new("ShaderNodeMath"); n.operation = op; n.location = loc
    if a is not None:
        if isinstance(a, (int, float)): n.inputs[0].default_value = a
        else: L.new(a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)): n.inputs[1].default_value = b
        else: L.new(b, n.inputs[1])
    return n

steps_out = gin.outputs["Steps"]

# Points along Z (one per step)
line = N.new("GeometryNodeMeshLine"); line.location = (-1100, 300)
L.new(steps_out, line.inputs["Count"])
line.inputs["Offset"].default_value = (0, 0, RISE)

# Rotation per index
idx = N.new("GeometryNodeInputIndex"); idx.location = (-1100, 0)
angle = math_node("MULTIPLY", idx.outputs[0], ANG, (-900, 0))
eul = N.new("ShaderNodeCombineXYZ"); eul.location = (-700, 0)
L.new(angle.outputs[0], eul.inputs["Z"])
e2r = N.new("FunctionNodeEulerToRotation"); e2r.location = (-500, 0)
L.new(eul.outputs[0], e2r.inputs["Euler"])

# Step tread
cube = N.new("GeometryNodeMeshCube"); cube.location = (-900, 500)
cube.inputs["Size"].default_value = (1.4, 0.5, 0.08)
tcube = N.new("GeometryNodeTransform"); tcube.location = (-700, 500)
L.new(cube.outputs["Mesh"], tcube.inputs["Geometry"])
tcube.inputs["Translation"].default_value = (0.95, 0, 0.04)
smat_step = N.new("GeometryNodeSetMaterial"); smat_step.location = (-500, 500)
smat_step.inputs["Material"].default_value = mat_step
L.new(tcube.outputs[0], smat_step.inputs["Geometry"])

inst_steps = N.new("GeometryNodeInstanceOnPoints"); inst_steps.location = (-250, 400)
L.new(line.outputs["Mesh"], inst_steps.inputs["Points"])
L.new(smat_step.outputs[0], inst_steps.inputs["Instance"])
L.new(e2r.outputs[0], inst_steps.inputs["Rotation"])

# Balusters
bal = N.new("GeometryNodeMeshCylinder"); bal.location = (-900, 800)
bal.inputs["Vertices"].default_value = 12
bal.inputs["Radius"].default_value = 0.02
bal.inputs["Depth"].default_value = RAIL_H
tbal = N.new("GeometryNodeTransform"); tbal.location = (-700, 800)
L.new(bal.outputs["Mesh"], tbal.inputs["Geometry"])
tbal.inputs["Translation"].default_value = (RAIL_R, 0, 0.08 + RAIL_H / 2)
smat_bal = N.new("GeometryNodeSetMaterial"); smat_bal.location = (-500, 800)
smat_bal.inputs["Material"].default_value = mat_metal
L.new(tbal.outputs[0], smat_bal.inputs["Geometry"])
inst_bal = N.new("GeometryNodeInstanceOnPoints"); inst_bal.location = (-250, 750)
L.new(line.outputs["Mesh"], inst_bal.inputs["Points"])
L.new(smat_bal.outputs[0], inst_bal.inputs["Instance"])
L.new(e2r.outputs[0], inst_bal.inputs["Rotation"])

# Handrail: points on helix -> curve -> tube
line2 = N.new("GeometryNodeMeshLine"); line2.location = (-1100, -400)
L.new(steps_out, line2.inputs["Count"])
idx2 = N.new("GeometryNodeInputIndex"); idx2.location = (-1100, -650)
ang2 = math_node("MULTIPLY", idx2.outputs[0], ANG, (-900, -600))
cosn = math_node("COSINE", ang2.outputs[0], None, (-750, -550))
sinn = math_node("SINE", ang2.outputs[0], None, (-750, -700))
xr = math_node("MULTIPLY", cosn.outputs[0], RAIL_R, (-600, -550))
yr = math_node("MULTIPLY", sinn.outputs[0], RAIL_R, (-600, -700))
zr = math_node("MULTIPLY_ADD", idx2.outputs[0], RISE, (-600, -850))
zr.inputs[2].default_value = 0.08 + RAIL_H
cxyz = N.new("ShaderNodeCombineXYZ"); cxyz.location = (-400, -650)
L.new(xr.outputs[0], cxyz.inputs["X"])
L.new(yr.outputs[0], cxyz.inputs["Y"])
L.new(zr.outputs[0], cxyz.inputs["Z"])
setpos = N.new("GeometryNodeSetPosition"); setpos.location = (-250, -400)
L.new(line2.outputs["Mesh"], setpos.inputs["Geometry"])
L.new(cxyz.outputs[0], setpos.inputs["Position"])
m2c = N.new("GeometryNodeMeshToCurve"); m2c.location = (-50, -400)
L.new(setpos.outputs[0], m2c.inputs["Mesh"])
prof = N.new("GeometryNodeCurvePrimitiveCircle"); prof.location = (-50, -600)
prof.inputs["Resolution"].default_value = 12
prof.inputs["Radius"].default_value = 0.035
c2m = N.new("GeometryNodeCurveToMesh"); c2m.location = (150, -450)
L.new(m2c.outputs[0], c2m.inputs["Curve"])
L.new(prof.outputs[0], c2m.inputs["Profile Curve"])
smat_rail = N.new("GeometryNodeSetMaterial"); smat_rail.location = (350, -450)
smat_rail.inputs["Material"].default_value = mat_metal
L.new(c2m.outputs[0], smat_rail.inputs["Geometry"])

# Central column, height driven by step count
depth = math_node("MULTIPLY_ADD", steps_out, RISE, (-900, -1100))
depth.inputs[2].default_value = 0.3
half = math_node("MULTIPLY", depth.outputs[0], 0.5, (-700, -1200))
zoff = math_node("SUBTRACT", half.outputs[0], 0.05, (-550, -1200))
col = N.new("GeometryNodeMeshCylinder"); col.location = (-550, -1000)
col.inputs["Vertices"].default_value = 32
col.inputs["Radius"].default_value = 0.25
L.new(depth.outputs[0], col.inputs["Depth"])
ctr = N.new("ShaderNodeCombineXYZ"); ctr.location = (-400, -1200)
L.new(zoff.outputs[0], ctr.inputs["Z"])
tcol = N.new("GeometryNodeTransform"); tcol.location = (-250, -1000)
L.new(col.outputs["Mesh"], tcol.inputs["Geometry"])
L.new(ctr.outputs[0], tcol.inputs["Translation"])
smat_col = N.new("GeometryNodeSetMaterial"); smat_col.location = (-50, -1000)
smat_col.inputs["Material"].default_value = mat_col
L.new(tcol.outputs[0], smat_col.inputs["Geometry"])

# Join
join = N.new("GeometryNodeJoinGeometry"); join.location = (800, 0)
for s in (inst_steps, inst_bal, smat_rail, smat_col):
    L.new(s.outputs[0], join.inputs["Geometry"])
L.new(join.outputs[0], gout.inputs["Geometry"])

# ---------- Host object ----------
mesh = bpy.data.meshes.new("StairBase")
obj = bpy.data.objects.new("SpiralStaircase", mesh)
scene.collection.objects.link(obj)
mod = obj.modifiers.new("SpiralStaircase", "NODES")
mod.node_group = ng
getattr(mod.properties.inputs, steps_item.identifier).value = 24

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(mat_floor)

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
bg.inputs["Strength"].default_value = 1.0

# ---------- Lights ----------
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))
scene.collection.objects.link(sun)

area = bpy.data.objects.new("Area", bpy.data.lights.new("Area", "AREA"))
area.data.energy = 800
area.data.size = 4
area.location = (-4, -4, 6)
area.rotation_euler = (math.radians(50), 0, math.radians(-45))
scene.collection.objects.link(area)

# ---------- Camera ----------
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.lens = 35
cam.location = (7.5, -7.5, 4.5)
scene.collection.objects.link(cam)
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 2.1)
scene.collection.objects.link(target)
tc = cam.constraints.new("TRACK_TO")
tc.target = target
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
