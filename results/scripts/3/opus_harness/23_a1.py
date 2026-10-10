import bpy
import math

scene = bpy.context.scene

# --- Ground plane ---
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"

ground_mat = bpy.data.materials.new("GroundMat")
bsdf = ground_mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.12, 0.08, 0.04, 1.0)
bsdf.inputs["Roughness"].default_value = 0.95
ground.data.materials.append(ground_mat)

grass_mat = bpy.data.materials.new("GrassMat")
gb = grass_mat.node_tree.nodes.get("Principled BSDF")
gb.inputs["Base Color"].default_value = (0.08, 0.45, 0.06, 1.0)
gb.inputs["Roughness"].default_value = 0.6

# --- Geometry Nodes tree ---
tree = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")
tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
dens_item = tree.interface.new_socket("Density", in_out="INPUT", socket_type="NodeSocketFloat")
dens_item.default_value = 100.0
dens_item.min_value = 0.0
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = tree.nodes
links = tree.links

gin = nodes.new("NodeGroupInput")
gin.location = (-800, 0)
gout = nodes.new("NodeGroupOutput")
gout.location = (800, 0)

dist = nodes.new("GeometryNodeDistributePointsOnFaces")
dist.location = (-500, 100)
dist.inputs["Seed"].default_value = 7

cone = nodes.new("GeometryNodeMeshCone")
cone.location = (-700, -300)
cone.inputs["Vertices"].default_value = 6
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Radius Bottom"].default_value = 0.025
cone.inputs["Depth"].default_value = 0.3

xform = nodes.new("GeometryNodeTransform")
xform.location = (-500, -300)
xform.inputs["Translation"].default_value = (0, 0, 0.15)

setmat = nodes.new("GeometryNodeSetMaterial")
setmat.location = (-300, -300)
setmat.inputs["Material"].default_value = grass_mat

# Scale variation via noise
pos = nodes.new("GeometryNodeInputPosition")
pos.location = (-700, -600)
noise = nodes.new("ShaderNodeTexNoise")
noise.location = (-500, -600)
noise.inputs["Scale"].default_value = 3.0
madd = nodes.new("ShaderNodeMath")
madd.location = (-300, -600)
madd.operation = 'MULTIPLY_ADD'
madd.inputs[1].default_value = 1.6
madd.inputs[2].default_value = 0.2

inst = nodes.new("GeometryNodeInstanceOnPoints")
inst.location = (0, 0)

join = nodes.new("GeometryNodeJoinGeometry")
join.location = (400, 0)

links.new(gin.outputs[0], dist.inputs["Mesh"])
links.new(gin.outputs[1], dist.inputs["Density"])
links.new(cone.outputs["Mesh"], xform.inputs["Geometry"])
links.new(xform.outputs["Geometry"], setmat.inputs["Geometry"])
links.new(dist.outputs["Points"], inst.inputs["Points"])
links.new(setmat.outputs["Geometry"], inst.inputs["Instance"])
links.new(dist.outputs["Rotation"], inst.inputs["Rotation"])
links.new(pos.outputs["Position"], noise.inputs["Vector"])
links.new(noise.outputs["Fac"], madd.inputs[0])
links.new(madd.outputs["Value"], inst.inputs["Scale"])
links.new(gin.outputs[0], join.inputs["Geometry"])
links.new(inst.outputs["Instances"], join.inputs["Geometry"])
links.new(join.outputs["Geometry"], gout.inputs[0])

mod = ground.modifiers.new("GrassScatter", "NODES")
mod.node_group = tree

# Set density from script
density_value = 250.0
try:
    getattr(mod.properties.inputs, dens_item.identifier).value = density_value
except Exception:
    try:
        mod[dens_item.identifier] = density_value
    except Exception:
        pass

# --- World ---
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# --- Light ---
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(40))

# --- Camera ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (7.5, -7.5, 4.0)
cam.rotation_euler = (math.radians(68), 0, math.radians(45))
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
