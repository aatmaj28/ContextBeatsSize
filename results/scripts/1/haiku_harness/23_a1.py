import bpy
import bmesh
import math
from mathutils import Vector

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene

# ---------- Materials ----------
def make_principled_material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

ground_mat = make_principled_material("GroundSoil", (0.22, 0.15, 0.08), 0.95)
grass_mat = make_principled_material("GrassBlade", (0.10, 0.42, 0.06), 0.6)

# ---------- Ground plane (bmesh) ----------
mesh = bpy.data.meshes.new("GroundMesh")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6.0)
bm.to_mesh(mesh)
bm.free()
mesh.materials.append(ground_mat)

ground = bpy.data.objects.new("Ground", mesh)
scene.collection.objects.link(ground)

# ---------- Geometry Nodes group ----------
tree = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")

tree.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
density_socket = tree.interface.new_socket(name="Density", in_out="INPUT", socket_type="NodeSocketFloat")
density_socket.default_value = 200.0
density_socket.min_value = 0.0
density_socket.max_value = 2000.0
tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = tree.nodes
links = tree.links

group_in = nodes.new("NodeGroupInput")
group_in.location = (-900, 0)
group_out = nodes.new("NodeGroupOutput")
group_out.location = (700, 0)

distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
distribute.location = (-600, 0)

cone = nodes.new("GeometryNodeMeshCone")
cone.location = (-600, -350)
cone.inputs["Vertices"].default_value = 6
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Radius Bottom"].default_value = 0.02
cone.inputs["Depth"].default_value = 0.14

instance = nodes.new("GeometryNodeInstanceOnPoints")
instance.location = (-300, 0)

realize = nodes.new("GeometryNodeRealizeInstances")
realize.location = (-50, 0)

set_mat = nodes.new("GeometryNodeSetMaterial")
set_mat.location = (250, 0)
set_mat.inputs["Material"].default_value = grass_mat

links.new(group_in.outputs["Geometry"], distribute.inputs["Mesh"])
links.new(group_in.outputs["Density"], distribute.inputs["Density"])
links.new(distribute.outputs["Points"], instance.inputs["Points"])
links.new(cone.outputs["Mesh"], instance.inputs["Instance"])
links.new(instance.outputs["Instances"], realize.inputs["Geometry"])
links.new(realize.outputs["Geometry"], set_mat.inputs["Geometry"])
links.new(set_mat.outputs["Geometry"], group_out.inputs["Geometry"])

# ---------- Modifier ----------
gn_mod = ground.modifiers.new("GrassScatter", "NODES")
gn_mod.node_group = tree

# Find the Density input's identifier and set it
density_id = None
for item in tree.interface.items_tree:
    if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == "Density":
        density_id = item.identifier
        break

if density_id is not None:
    getattr(gn_mod.properties.inputs, density_id).value = 250.0

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 4.0
sun_data.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
scene.collection.objects.link(sun)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((3.2, -4.2, 1.4))
target = Vector((0.0, 0.0, 0.15))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
