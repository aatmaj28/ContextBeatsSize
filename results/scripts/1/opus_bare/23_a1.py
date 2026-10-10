import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Materials ----------
def make_mat(name, color, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = rough
    return m

ground_mat = make_mat("Ground", (0.12, 0.07, 0.03, 1.0), 1.0)
grass_mat = make_mat("Grass", (0.08, 0.35, 0.05, 1.0), 0.6)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "GrassField"
ground.data.materials.append(ground_mat)

# ---------- Geometry Nodes ----------
ng = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")
iface = ng.interface
iface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
dens_sock = iface.new_socket(name="Density", in_out='INPUT', socket_type='NodeSocketFloat')
dens_sock.default_value = 100.0
dens_sock.min_value = 0.0
dens_sock.max_value = 10000.0
iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = ng.nodes
links = ng.links

def sock(collection, name, stype=None):
    for s in collection:
        if s.name == name and (stype is None or s.type == stype) and s.enabled:
            return s
    for s in collection:
        if s.name == name and (stype is None or s.type == stype):
            return s
    return collection[name]

gin = nodes.new("NodeGroupInput"); gin.location = (-800, 0)
gout = nodes.new("NodeGroupOutput"); gout.location = (600, 0)

dist = nodes.new("GeometryNodeDistributePointsOnFaces"); dist.location = (-500, 100)
links.new(gin.outputs["Geometry"], dist.inputs["Mesh"])
links.new(gin.outputs["Density"], dist.inputs["Density"])

cone = nodes.new("GeometryNodeMeshCone"); cone.location = (-500, -200)
cone.inputs["Vertices"].default_value = 6
cone.inputs["Radius Bottom"].default_value = 0.02
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Depth"].default_value = 0.3

setmat = nodes.new("GeometryNodeSetMaterial"); setmat.location = (-300, -200)
setmat.inputs["Material"].default_value = grass_mat
links.new(cone.outputs["Mesh"], setmat.inputs["Geometry"])

rot_rand = nodes.new("FunctionNodeRandomValue"); rot_rand.location = (-500, -450)
rot_rand.data_type = 'FLOAT_VECTOR'
sock(rot_rand.inputs, "Min", 'VECTOR').default_value = (-0.25, -0.25, 0.0)
sock(rot_rand.inputs, "Max", 'VECTOR').default_value = (0.25, 0.25, 6.283)

scale_rand = nodes.new("FunctionNodeRandomValue"); scale_rand.location = (-500, -700)
scale_rand.data_type = 'FLOAT'
sock(scale_rand.inputs, "Min", 'VALUE').default_value = 0.6
sock(scale_rand.inputs, "Max", 'VALUE').default_value = 1.5
sock(scale_rand.inputs, "Seed").default_value = 7

inst = nodes.new("GeometryNodeInstanceOnPoints"); inst.location = (0, 0)
links.new(dist.outputs["Points"], inst.inputs["Points"])
links.new(setmat.outputs["Geometry"], inst.inputs["Instance"])
links.new(sock(rot_rand.outputs, "Value", 'VECTOR'), inst.inputs["Rotation"])
links.new(sock(scale_rand.outputs, "Value", 'VALUE'), inst.inputs["Scale"])

join = nodes.new("GeometryNodeJoinGeometry"); join.location = (300, 0)
links.new(gin.outputs["Geometry"], join.inputs["Geometry"])
links.new(inst.outputs["Instances"], join.inputs["Geometry"])
links.new(join.outputs["Geometry"], gout.inputs["Geometry"])

mod = ground.modifiers.new("GrassScatter", "NODES")
mod.node_group = ng

# Set exposed density from script
DENSITY = 250.0
mod[dens_sock.identifier] = DENSITY

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun_data.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (8.5, -8.5, 4.5)
direction = -cam.location.copy()
direction.z += 0.0
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
