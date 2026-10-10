import bpy
import math

# Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- Ground plane ----------
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "GrassField"

# ---------- Materials ----------
def make_mat(name, color, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = color
    return m

soil_mat = make_mat("Soil", (0.15, 0.09, 0.04, 1.0), 0.95)
grass_mat = make_mat("Grass", (0.08, 0.45, 0.06, 1.0), 0.6)
ground.data.materials.append(soil_mat)

# ---------- Geometry Nodes ----------
ng = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")
ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
dens_sock = ng.interface.new_socket(name="Density", in_out='INPUT', socket_type='NodeSocketFloat')
dens_sock.default_value = 100.0
dens_sock.min_value = 0.0
dens_sock.max_value = 10000.0
ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = ng.nodes
links = ng.links

def sock(collection, name, stype=None):
    for s in collection:
        if s.name == name and s.enabled and (stype is None or s.type == stype):
            return s
    for s in collection:
        if s.name == name:
            return s
    return None

def first_out(node, stype):
    for s in node.outputs:
        if s.enabled and s.type == stype:
            return s
    return node.outputs[0]

gin = nodes.new("NodeGroupInput"); gin.location = (-900, 0)
gout = nodes.new("NodeGroupOutput"); gout.location = (700, 0)

dist = nodes.new("GeometryNodeDistributePointsOnFaces"); dist.location = (-600, 100)
dist.distribute_method = 'RANDOM'
links.new(gin.outputs[0], dist.inputs["Mesh"])
links.new(gin.outputs[1], dist.inputs["Density"])

cone = nodes.new("GeometryNodeMeshCone"); cone.location = (-600, -250)
cone.inputs["Vertices"].default_value = 5
cone.inputs["Radius Bottom"].default_value = 0.02
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Depth"].default_value = 0.3

xform = nodes.new("GeometryNodeTransform"); xform.location = (-400, -250)
links.new(sock(cone.outputs, "Mesh"), xform.inputs["Geometry"])
xform.inputs["Translation"].default_value = (0, 0, 0.15)

setmat = nodes.new("GeometryNodeSetMaterial"); setmat.location = (-200, -250)
setmat.inputs["Material"].default_value = grass_mat
links.new(xform.outputs[0], setmat.inputs["Geometry"])

# Random rotation (vector)
rrot = nodes.new("FunctionNodeRandomValue"); rrot.location = (-400, 300)
rrot.data_type = 'FLOAT_VECTOR'
sock(rrot.inputs, "Min", 'VECTOR').default_value = (-0.25, -0.25, 0.0)
sock(rrot.inputs, "Max", 'VECTOR').default_value = (0.25, 0.25, math.tau)
rrot.inputs["Seed"].default_value = 3 if "Seed" in rrot.inputs else 0

# Random scale (float)
rscale = nodes.new("FunctionNodeRandomValue"); rscale.location = (-400, 500)
rscale.data_type = 'FLOAT'
sock(rscale.inputs, "Min", 'VALUE').default_value = 0.6
sock(rscale.inputs, "Max", 'VALUE').default_value = 1.6

inst = nodes.new("GeometryNodeInstanceOnPoints"); inst.location = (100, 100)
links.new(dist.outputs["Points"], inst.inputs["Points"])
links.new(setmat.outputs[0], inst.inputs["Instance"])
links.new(first_out(rrot, 'VECTOR'), inst.inputs["Rotation"])
links.new(first_out(rscale, 'VALUE'), inst.inputs["Scale"])

realize = nodes.new("GeometryNodeRealizeInstances"); realize.location = (300, 100)
links.new(inst.outputs[0], realize.inputs[0])

join = nodes.new("GeometryNodeJoinGeometry"); join.location = (500, 0)
links.new(realize.outputs[0], join.inputs[0])
links.new(gin.outputs[0], join.inputs[0])
links.new(join.outputs[0], gout.inputs[0])

mod = ground.modifiers.new("GrassScatter", 'NODES')
mod.node_group = ng
# Set density from the script via the exposed modifier input
mod[dens_sock.identifier] = 400.0
ground.data.update()

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (7.5, -7.5, 4.0)
target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
target.location = (0, 0, 0)
tc = cam.constraints.new('TRACK_TO')
tc.target = target
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
