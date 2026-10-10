import bpy
import bmesh
import math
from mathutils import Vector

# ---------- Clear default scene contents ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
collection = scene.collection

# ---------- Materials ----------
def make_principled_material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
    return mat

mat_soil = make_principled_material("SoilMat", (0.22, 0.14, 0.07), 0.95)
mat_grass = make_principled_material("GrassBladeMat", (0.10, 0.45, 0.08), 0.6)

# ---------- Ground plane ----------
ground_mesh = bpy.data.meshes.new("GroundMesh")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=10.0)
bm.to_mesh(ground_mesh)
bm.free()
ground_mesh.update()

ground = bpy.data.objects.new("Ground", ground_mesh)
collection.objects.link(ground)
ground.data.materials.append(mat_soil)

# ---------- Geometry Nodes group ----------
ng = bpy.data.node_groups.new("GrassScatterGN", "GeometryNodeTree")
iface = ng.interface

iface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
density_socket = iface.new_socket(name="Density", in_out="INPUT", socket_type="NodeSocketFloat")
density_socket.default_value = 30.0
density_socket.min_value = 0.0
density_socket.max_value = 500.0
density_socket.description = "Number of grass blades per square meter"

iface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = ng.nodes
links = ng.links

gin = nodes.new("NodeGroupInput")
gin.location = (-900, 0)
gout = nodes.new("NodeGroupOutput")
gout.location = (700, 0)

dist = nodes.new("GeometryNodeDistributePointsOnFaces")
dist.location = (-600, 0)
dist.distribute_method = 'RANDOM'

setpos = nodes.new("GeometryNodeSetPosition")
setpos.location = (-400, 0)
setpos.inputs["Offset"].default_value = (0.0, 0.0, 0.15)

cone = nodes.new("GeometryNodeMeshCone")
cone.location = (-600, -350)
cone.inputs["Vertices"].default_value = 6
cone.inputs["Radius Bottom"].default_value = 0.05
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Depth"].default_value = 0.3

setmat = nodes.new("GeometryNodeSetMaterial")
setmat.location = (-400, -350)
setmat.inputs["Material"].default_value = mat_grass

inst = nodes.new("GeometryNodeInstanceOnPoints")
inst.location = (-150, 0)

join = nodes.new("GeometryNodeJoinGeometry")
join.location = (450, 0)

links.new(gin.outputs["Geometry"], dist.inputs["Mesh"])
links.new(gin.outputs["Density"], dist.inputs["Density"])
links.new(dist.outputs["Points"], setpos.inputs["Geometry"])
links.new(setpos.outputs["Geometry"], inst.inputs["Points"])
links.new(cone.outputs["Mesh"], setmat.inputs["Geometry"])
links.new(setmat.outputs["Geometry"], inst.inputs["Instance"])
links.new(gin.outputs["Geometry"], join.inputs["Geometry"])
links.new(inst.outputs["Instances"], join.inputs["Geometry"])
links.new(join.outputs["Geometry"], gout.inputs["Geometry"])

# ---------- Modifier with exposed density input ----------
mod = ground.modifiers.new(name="GrassScatter", type="NODES")
mod.node_group = ng
mod[density_socket.identifier] = 40.0  # set density from the script

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="Sun", type="SUN")
sun_data.energy = 3.5
sun = bpy.data.objects.new("Sun", sun_data)
collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(30))

fill_data = bpy.data.lights.new(name="Fill", type="AREA")
fill_data.energy = 300.0
fill_data.size = 6.0
fill = bpy.data.objects.new("Fill", fill_data)
collection.objects.link(fill)
fill.location = (-6.0, 6.0, 5.0)
fill.rotation_euler = (math.radians(60), 0.0, math.radians(-135))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam)
cam.location = (7.5, -7.5, 4.5)

target = Vector((0.0, 0.0, 0.3))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam

# ---------- Render settings (no rendering performed) ----------
scene.frame_start = 1
scene.frame_end = 1
