import bpy
import math
import random
from mathutils import Vector

random.seed(7)

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ---------- Ground plane ----------
bpy.ops.mesh.primitive_plane_add(size=20.0, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "GrassGround"

# Grass ground material
grass_mat = bpy.data.materials.new("GroundGrass")
grass_mat.use_nodes = True
bsdf = grass_mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.12, 0.42, 0.08, 1.0)
bsdf.inputs["Roughness"].default_value = 0.9
ground.data.materials.append(grass_mat)

# ---------- Blade material (applied to cones) ----------
blade_mat = bpy.data.materials.new("BladeGreen")
blade_mat.use_nodes = True
bsdf_b = blade_mat.node_tree.nodes.get("Principled BSDF")
bsdf_b.inputs["Base Color"].default_value = (0.25, 0.65, 0.12, 1.0)
bsdf_b.inputs["Roughness"].default_value = 0.6

# ---------- Geometry Nodes group ----------
ng = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")

# Interface
ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
dens_sock = ng.interface.new_socket(name="Density", in_out='INPUT', socket_type='NodeSocketFloat')
dens_sock.default_value = 25.0
dens_sock.min_value = 0.0
dens_sock.max_value = 500.0
dens_sock.description = "Grass blade points per square unit"
ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

nodes = ng.nodes
links = ng.links

def add_node(type_name, loc):
    n = nodes.new(type_name)
    n.location = loc
    return n

n_in = add_node("NodeGroupInput", (-900, 0))
n_out = add_node("NodeGroupOutput", (700, 0))
n_dist = add_node("GeometryNodeDistributePointsOnFaces", (-600, -200))
n_dist.distribute_method = 'RANDOM'
n_cone = add_node("GeometryNodeMeshCone", (-600, -500))
n_cone.inputs["Vertices"].default_value = 5
n_cone.inputs["Radius Top"].default_value = 0.0
n_cone.inputs["Radius Bottom"].default_value = 0.03
n_cone.inputs["Depth"].default_value = 0.25
n_setmat = add_node("GeometryNodeSetMaterial", (-400, -500))
n_setmat.inputs["Material"].default_value = blade_mat
n_rand = add_node("GeometryNodeRandomValue", (-400, -800))
n_rand.data_type = 'FLOAT_VECTOR'
# Random scale range (vector min/max sockets)
for s in n_rand.inputs:
    if s.name == "Min" and s.type == 'VECTOR':
        s.default_value = (0.7, 0.7, 0.8)
    elif s.name == "Max" and s.type == 'VECTOR':
        s.default_value = (1.3, 1.3, 1.6)
n_inst = add_node("GeometryNodeInstanceOnPoints", (-150, -300))
n_join = add_node("GeometryNodeJoinGeometry", (400, 0))

# Links
links.new(n_in.outputs["Geometry"], n_dist.inputs["Mesh"])
links.new(n_in.outputs["Density"], n_dist.inputs["Density"])
links.new(n_dist.outputs["Points"], n_inst.inputs["Points"])
links.new(n_cone.outputs["Mesh"], n_setmat.inputs["Geometry"])
links.new(n_setmat.outputs["Geometry"], n_inst.inputs["Instance"])
links.new(n_rand.outputs["Value"], n_inst.inputs["Scale"])
links.new(n_in.outputs["Geometry"], n_join.inputs["Geometry"])
links.new(n_inst.outputs["Instances"], n_join.inputs["Geometry"])
links.new(n_join.outputs["Geometry"], n_out.inputs["Geometry"])

# ---------- Modifier ----------
mod = ground.modifiers.new(name="GrassScatter", type='NODES')
mod.node_group = ng

# Find the identifier for the exposed Density input and set its value
density_id = None
for item in ng.interface.items_tree:
    if getattr(item, "item_type", "") == 'SOCKET' and item.name == "Density" and item.in_out == 'INPUT':
        density_id = item.identifier
        break
if density_id is not None:
    mod[density_id] = 60.0  # controls how many blades are scattered

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(4, -4, 8))
sun = bpy.context.active_object
sun.name = "SunLight"
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-5, 5, 5))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 300.0
fill.data.size = 6.0

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(5.5, -6.5, 3.2))
cam = bpy.context.active_object
cam.name = "GrassCamera"
target = Vector((0.0, 0.0, 0.3))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 35
bpy.context.scene.camera = cam

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
