import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Ground plane ----------
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "GrassField"

# Materials
soil = bpy.data.materials.new("Soil")
bsdf = soil.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.12, 0.07, 0.03, 1)
bsdf.inputs["Roughness"].default_value = 0.95
ground.data.materials.append(soil)

grass_mat = bpy.data.materials.new("Grass")
gb = grass_mat.node_tree.nodes.get("Principled BSDF")
gb.inputs["Base Color"].default_value = (0.08, 0.45, 0.05, 1)
gb.inputs["Roughness"].default_value = 0.6

# ---------- Geometry nodes ----------
ng = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
dens_item = ng.interface.new_socket("Density", in_out="INPUT", socket_type="NodeSocketFloat")
dens_item.default_value = 50.0
dens_item.min_value = 0.0
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes, links = ng.nodes, ng.links
gin = nodes.new("NodeGroupInput"); gin.location = (-800, 0)
gout = nodes.new("NodeGroupOutput"); gout.location = (800, 0)

dist = nodes.new("GeometryNodeDistributePointsOnFaces"); dist.location = (-500, 0)
links.new(gin.outputs["Geometry"], dist.inputs["Mesh"])
links.new(gin.outputs["Density"], dist.inputs["Density"])

cone = nodes.new("GeometryNodeMeshCone"); cone.location = (-700, -300)
cone.inputs["Vertices"].default_value = 5
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Radius Bottom"].default_value = 0.025
cone.inputs["Depth"].default_value = 0.3

xf = nodes.new("GeometryNodeTransform"); xf.location = (-500, -300)
xf.inputs["Translation"].default_value = (0, 0, 0.15)
links.new(cone.outputs["Mesh"], xf.inputs["Geometry"])

inst = nodes.new("GeometryNodeInstanceOnPoints"); inst.location = (-200, 0)
links.new(dist.outputs["Points"], inst.inputs["Points"])
links.new(xf.outputs["Geometry"], inst.inputs["Instance"])

# Random scale (find sockets by name and type to be robust)
try:
    rnd = nodes.new("FunctionNodeRandomValue"); rnd.location = (-450, -550)
    rnd.data_type = 'FLOAT'
    def find(sockets, name, typ):
        for s in sockets:
            if s.name == name and s.type == typ:
                return s
        return None
    find(rnd.inputs, "Min", 'VALUE').default_value = 0.6
    find(rnd.inputs, "Max", 'VALUE').default_value = 1.5
    links.new(find(rnd.outputs, "Value", 'VALUE'), inst.inputs["Scale"])
except Exception:
    pass

# Slight random tilt via distributed rotation
try:
    links.new(dist.outputs["Rotation"], inst.inputs["Rotation"])
except Exception:
    pass

setmat = nodes.new("GeometryNodeSetMaterial"); setmat.location = (100, 0)
setmat.inputs["Material"].default_value = grass_mat
links.new(inst.outputs["Instances"], setmat.inputs["Geometry"])

join = nodes.new("GeometryNodeJoinGeometry"); join.location = (400, 0)
links.new(setmat.outputs["Geometry"], join.inputs["Geometry"])
links.new(gin.outputs["Geometry"], join.inputs["Geometry"])
links.new(join.outputs["Geometry"], gout.inputs["Geometry"])

mod = ground.modifiers.new("GrassScatter", "NODES")
mod.node_group = ng

DENSITY = 150.0
try:
    getattr(mod.properties.inputs, dens_item.identifier).value = DENSITY
except Exception:
    mod[dens_item.identifier] = DENSITY

# ---------- World & lighting ----------
world = bpy.data.worlds.new("Sky")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1)
bg.inputs["Strength"].default_value = 0.8

sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
scene.collection.objects.link(sun)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (7.5, -7.5, 3.5)
scene.collection.objects.link(cam)
direction = -cam.location.copy()
direction.z += 0.0
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
