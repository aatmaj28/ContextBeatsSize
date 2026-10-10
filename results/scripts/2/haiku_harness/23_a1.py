import bpy
import math
from mathutils import Vector

# ---------------------------------------------------------------------------
# Clean scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene

# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def make_principled(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

soil_mat = make_principled("Soil", (0.25, 0.18, 0.09), 0.95)
grass_mat = make_principled("Grass", (0.12, 0.42, 0.06), 0.6)

# ---------------------------------------------------------------------------
# Ground plane
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0.0, 0.0, 0.0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(soil_mat)

# ---------------------------------------------------------------------------
# Geometry Nodes group: scatter cones (grass blades) on the ground
# ---------------------------------------------------------------------------
tree = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")
iface = tree.interface

iface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
density_item = iface.new_socket(name="Density", in_out="INPUT", socket_type="NodeSocketFloat")
density_item.default_value = 250.0
density_item.min_value = 0.0
density_item.max_value = 5000.0

iface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = tree.nodes
links = tree.links

group_in = nodes.new("NodeGroupInput")
group_in.location = (-900, 0)
group_out = nodes.new("NodeGroupOutput")
group_out.location = (800, 0)

# Scatter points on the surface
distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
distribute.location = (-600, 0)

# Blade shape: a thin cone
cone = nodes.new("GeometryNodeMeshCone")
cone.location = (-600, -350)
cone.inputs["Vertices"].default_value = 5
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Radius Bottom"].default_value = 0.012
cone.inputs["Depth"].default_value = 0.18

# Instance cones on the scattered points
inst = nodes.new("GeometryNodeInstanceOnPoints")
inst.location = (-300, 0)

# Realize so the material can be applied to the blades
realize = nodes.new("GeometryNodeRealizeInstances")
realize.location = (-100, 0)

# Apply grass material
set_mat = nodes.new("GeometryNodeSetMaterial")
set_mat.location = (100, 0)
set_mat.inputs["Material"].default_value = grass_mat

# Combine ground and grass
join = nodes.new("GeometryNodeJoinGeometry")
join.location = (450, 0)

# Wiring
links.new(distribute.inputs["Mesh"], group_in.outputs["Geometry"])
links.new(distribute.inputs["Density"], group_in.outputs["Density"])

links.new(inst.inputs["Points"], distribute.outputs["Points"])
links.new(inst.inputs["Instance"], cone.outputs["Mesh"])

links.new(realize.inputs["Geometry"], inst.outputs["Instances"])
links.new(set_mat.inputs["Geometry"], realize.outputs["Geometry"])

links.new(join.inputs["Geometry"], group_in.outputs["Geometry"])
links.new(join.inputs["Geometry"], set_mat.outputs["Geometry"])
links.new(group_out.inputs["Geometry"], join.outputs["Geometry"])

# ---------------------------------------------------------------------------
# Geometry Nodes modifier with exposed density input
# ---------------------------------------------------------------------------
mod = ground.modifiers.new("GrassScatter", "NODES")
mod.node_group = tree

# Set the exposed Density input from the script
density_identifier = density_item.identifier
getattr(mod.properties.inputs, density_identifier).value = 300.0

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(3.0)
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(35))

world = bpy.data.worlds.new("GrassWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)

cam_loc = Vector((7.0, -8.5, 3.6))
target = Vector((0.0, 0.0, 0.2))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam

# ---------------------------------------------------------------------------
# Scene settings (single frame, no animation)
# ---------------------------------------------------------------------------
scene.frame_start = 1
scene.frame_end = 1
