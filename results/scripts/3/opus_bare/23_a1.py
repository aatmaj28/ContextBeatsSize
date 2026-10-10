import bpy
import math

# Clean scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

scene = bpy.context.scene

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "GrassField"

# Materials
soil = bpy.data.materials.new("Soil")
soil.use_nodes = True
soil.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.11, 0.05, 1)
soil.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
ground.data.materials.append(soil)

grass_mat = bpy.data.materials.new("Grass")
grass_mat.use_nodes = True
grass_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.08, 0.45, 0.06, 1)
grass_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6

# Geometry node group
ng = bpy.data.node_groups.new("GrassScatter", 'GeometryNodeTree')
iface = ng.interface
iface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
dens_sock = iface.new_socket(name="Density", in_out='INPUT', socket_type='NodeSocketFloat')
dens_sock.default_value = 50.0
dens_sock.min_value = 0.0
dens_sock.max_value = 10000.0
iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = ng.nodes
links = ng.links

gin = nodes.new('NodeGroupInput'); gin.location = (-900, 0)
gout = nodes.new('NodeGroupOutput'); gout.location = (700, 0)

dist = nodes.new('GeometryNodeDistributePointsOnFaces'); dist.location = (-600, 100)
links.new(gin.outputs["Geometry"], dist.inputs["Mesh"])
links.new(gin.outputs["Density"], dist.inputs["Density"])

cone = nodes.new('GeometryNodeMeshCone'); cone.location = (-600, -250)
cone.inputs["Vertices"].default_value = 5
cone.inputs["Radius Bottom"].default_value = 0.025
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Depth"].default_value = 0.3

xform = nodes.new('GeometryNodeTransform'); xform.location = (-400, -250)
xform.inputs["Translation"].default_value = (0, 0, 0.15)
links.new(cone.outputs["Mesh"], xform.inputs["Geometry"])

setmat = nodes.new('GeometryNodeSetMaterial'); setmat.location = (-200, -250)
setmat.inputs["Material"].default_value = grass_mat
links.new(xform.outputs["Geometry"], setmat.inputs["Geometry"])

def sock(sockets, name, stype):
    for s in sockets:
        if s.name == name and s.type == stype:
            return s
    return None

# Random scale
rscale = nodes.new('FunctionNodeRandomValue'); rscale.location = (-400, -500)
rscale.data_type = 'FLOAT'
sock(rscale.inputs, "Min", 'VALUE').default_value = 0.6
sock(rscale.inputs, "Max", 'VALUE').default_value = 1.6
rscale.inputs["Seed"].default_value = 3

# Random tilt/rotation
rrot = nodes.new('FunctionNodeRandomValue'); rrot.location = (-400, -750)
rrot.data_type = 'FLOAT_VECTOR'
sock(rrot.inputs, "Min", 'VECTOR').default_value = (-0.25, -0.25, 0.0)
sock(rrot.inputs, "Max", 'VECTOR').default_value = (0.25, 0.25, 6.283)
rrot.inputs["Seed"].default_value = 7

inst = nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (100, 0)
links.new(dist.outputs["Points"], inst.inputs["Points"])
links.new(setmat.outputs["Geometry"], inst.inputs["Instance"])
links.new(sock(rscale.outputs, "Value", 'VALUE'), inst.inputs["Scale"])
links.new(sock(rrot.outputs, "Value", 'VECTOR'), inst.inputs["Rotation"])

join = nodes.new('GeometryNodeJoinGeometry'); join.location = (400, 0)
links.new(gin.outputs["Geometry"], join.inputs["Geometry"])
links.new(inst.outputs["Instances"], join.inputs["Geometry"])
links.new(join.outputs["Geometry"], gout.inputs["Geometry"])

# Modifier
mod = ground.modifiers.new("GrassScatter", 'NODES')
mod.node_group = ng
mod[dens_sock.identifier] = 300.0

# World
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1)
    bg.inputs["Strength"].default_value = 0.8

# Light
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun_data.angle = math.radians(5)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (7.5, -7.5, 4.0)
cam.rotation_euler = (math.radians(68), 0, math.radians(45))
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
