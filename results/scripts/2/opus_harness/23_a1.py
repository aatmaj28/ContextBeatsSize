import bpy
import math

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "GrassField"

# Materials
soil = bpy.data.materials.new("Soil")
bsdf = soil.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.12, 0.07, 0.03, 1)
bsdf.inputs["Roughness"].default_value = 0.95

grass_mat = bpy.data.materials.new("Grass")
gb = grass_mat.node_tree.nodes.get("Principled BSDF")
gb.inputs["Base Color"].default_value = (0.08, 0.35, 0.05, 1)
gb.inputs["Roughness"].default_value = 0.6
ground.data.materials.append(soil)

# Geometry nodes tree
tree = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")
tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
dens_item = tree.interface.new_socket("Density", in_out="INPUT", socket_type="NodeSocketFloat")
dens_item.default_value = 10.0
dens_item.min_value = 0.0
dens_item.max_value = 1000.0
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

N = tree.nodes
L = tree.links
gin = N.new("NodeGroupInput"); gin.location = (-800, 0)
gout = N.new("NodeGroupOutput"); gout.location = (800, 0)

dist = N.new("GeometryNodeDistributePointsOnFaces"); dist.location = (-500, 100)
L.new(gin.outputs[0], dist.inputs["Mesh"])
L.new(gin.outputs[1], dist.inputs["Density"])

cone = N.new("GeometryNodeMeshCone"); cone.location = (-500, -200)
cone.inputs["Vertices"].default_value = 6
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Radius Bottom"].default_value = 0.025
cone.inputs["Depth"].default_value = 0.35

xf = N.new("GeometryNodeTransform"); xf.location = (-300, -200)
xf.inputs["Translation"].default_value = (0, 0, 0.175)
L.new(cone.outputs["Mesh"], xf.inputs["Geometry"])

setmat_g = N.new("GeometryNodeSetMaterial"); setmat_g.location = (-100, -200)
setmat_g.inputs["Material"].default_value = grass_mat
L.new(xf.outputs["Geometry"], setmat_g.inputs["Geometry"])

inst = N.new("GeometryNodeInstanceOnPoints"); inst.location = (100, 100)
L.new(dist.outputs["Points"], inst.inputs["Points"])
L.new(setmat_g.outputs["Geometry"], inst.inputs["Instance"])
L.new(dist.outputs["Rotation"], inst.inputs["Rotation"])

# Random scale (robust socket lookup)
try:
    rnd = N.new("FunctionNodeRandomValue"); rnd.location = (-100, 250)
    rnd.data_type = 'FLOAT'
    mn = [s for s in rnd.inputs if s.name == "Min" and s.type == 'VALUE' and s.enabled][0]
    mx = [s for s in rnd.inputs if s.name == "Max" and s.type == 'VALUE' and s.enabled][0]
    out = [s for s in rnd.outputs if s.name == "Value" and s.type == 'VALUE' and s.enabled][0]
    mn.default_value = 0.6
    mx.default_value = 1.5
    L.new(out, inst.inputs["Scale"])
except Exception:
    pass

realize = N.new("GeometryNodeRealizeInstances"); realize.location = (300, 100)
L.new(inst.outputs["Instances"], realize.inputs["Geometry"])

join = N.new("GeometryNodeJoinGeometry"); join.location = (550, 0)
L.new(realize.outputs["Geometry"], join.inputs["Geometry"])
L.new(gin.outputs[0], join.inputs["Geometry"])
L.new(join.outputs["Geometry"], gout.inputs[0])

mod = ground.modifiers.new("GrassScatter", "NODES")
mod.node_group = tree

# Set density from script
DENSITY = 60.0
try:
    getattr(mod.properties.inputs, dens_item.identifier).value = DENSITY
except Exception:
    try:
        mod[dens_item.identifier] = DENSITY
    except Exception:
        dens_item.default_value = DENSITY

# Lighting
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(sun)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1)
    bg.inputs["Strength"].default_value = 0.8

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (8, -8, 4.5)
scene.collection.objects.link(cam)
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 0)
scene.collection.objects.link(target)
tc = cam.constraints.new('TRACK_TO')
tc.target = target
tc.track_axis = 'TRACK_NEGATIVE_Z'
tc.up_axis = 'UP_Y'
scene.camera = cam
