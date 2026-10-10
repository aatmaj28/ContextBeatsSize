import bpy
import math
from mathutils import Vector

# ---------- Clean the scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ---------- Materials ----------
def make_principled_material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

ground_mat = make_principled_material("SoilMat", (0.22, 0.16, 0.08), 0.95)
grass_mat = make_principled_material("GrassMat", (0.12, 0.45, 0.08), 0.7)

# ---------- Ground plane ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "GroundPlane"
ground.data.materials.append(ground_mat)

# ---------- Geometry Nodes group ----------
ng = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")
iface = ng.interface
iface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
density_socket = iface.new_socket(name="Density", in_out='INPUT', socket_type='NodeSocketFloat')
density_socket.default_value = 200.0
density_socket.min_value = 0.0
density_socket.max_value = 5000.0
iface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = ng.nodes
links = ng.links

group_in = nodes.new("NodeGroupInput")
group_in.location = (-900, 0)
group_out = nodes.new("NodeGroupOutput")
group_out.location = (700, 0)

# Scatter points on faces
distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
distribute.location = (-600, 0)
distribute.distribute_method = 'RANDOM'

# Cone instance mesh
cone = nodes.new("GeometryNodeMeshCone")
cone.location = (-600, -300)
cone.inputs["Vertices"].default_value = 5
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Radius Bottom"].default_value = 0.035
cone.inputs["Depth"].default_value = 0.22

# Instance cones on points
instance = nodes.new("GeometryNodeInstanceOnPoints")
instance.location = (-300, 0)

# Make instances real geometry
realize = nodes.new("GeometryNodeRealizeInstances")
realize.location = (-100, 0)

# Assign grass material
set_mat = nodes.new("GeometryNodeSetMaterial")
set_mat.location = (100, 0)
set_mat.inputs["Material"].default_value = grass_mat

# Links
links.new(group_in.outputs["Geometry"], distribute.inputs["Mesh"])
links.new(group_in.outputs["Density"], distribute.inputs["Density"])

links.new(distribute.outputs["Points"], instance.inputs["Points"])
links.new(cone.outputs["Mesh"], instance.inputs["Instance"])

links.new(instance.outputs["Instances"], realize.inputs["Geometry"])
links.new(realize.outputs["Geometry"], set_mat.inputs["Geometry"])
links.new(set_mat.outputs["Geometry"], group_out.inputs["Geometry"])

# ---------- Modifier ----------
mod = ground.modifiers.new(name="GrassScatter", type='NODES')
mod.node_group = ng

# Find the exposed density identifier and set its value from the script
density_id = None
for item in ng.interface.items_tree:
    if getattr(item, "item_type", None) == 'SOCKET' and item.name == "Density":
        density_id = item.identifier
        break

DENSITY_VALUE = 1500.0
if density_id is not None:
    mod[density_id] = DENSITY_VALUE

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))

bpy.ops.object.light_add(type='AREA', location=(-6, -6, 8))
area = bpy.context.active_object
area.data.energy = 300.0
area.data.size = 8.0
area.rotation_euler = (math.radians(55), 0, math.radians(-45))

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(0, -9, 3.5))
cam = bpy.context.active_object
cam.name = "GrassCamera"
target = Vector((0, 0, 0.3))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 35
bpy.context.scene.camera = cam

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
