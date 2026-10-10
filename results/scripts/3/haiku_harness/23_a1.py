import bpy
import math
from mathutils import Vector

# ---------------------------------------------------------------------------
# Clean scene (background mode, start from empty)
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def make_principled(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)  # default node tree is created here
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

ground_mat = make_principled("GroundMat", (0.22, 0.16, 0.08), 0.95)
grass_mat = make_principled("GrassMat", (0.12, 0.45, 0.08), 0.7)

# ---------------------------------------------------------------------------
# Ground plane
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=20.0, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(ground_mat)

# ---------------------------------------------------------------------------
# Geometry Nodes tree: scatter cones on the surface
# ---------------------------------------------------------------------------
gn = bpy.data.node_groups.new("GrassScatter", "GeometryNodeTree")
iface = gn.interface
iface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
density_item = iface.new_socket(name="Density", in_out="INPUT", socket_type="NodeSocketFloat")
density_item.default_value = 25.0
density_item.min_value = 0.0
density_item.max_value = 500.0
iface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = gn.nodes
links = gn.links

group_in = nodes.new("NodeGroupInput")
group_in.location = (-900, 0)
group_out = nodes.new("NodeGroupOutput")
group_out.location = (900, 0)

distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
distribute.location = (-600, 0)  # default method is Random

cone = nodes.new("GeometryNodeMeshCone")
cone.location = (-600, -350)
cone.inputs["Vertices"].default_value = 5
cone.inputs["Radius Top"].default_value = 0.0
cone.inputs["Radius Bottom"].default_value = 0.03
cone.inputs["Depth"].default_value = 0.35

# Lift cone so its base sits on the ground
lift = nodes.new("GeometryNodeTransform")
lift.location = (-380, -350)
lift.inputs["Translation"].default_value = (0.0, 0.0, 0.175)

instance = nodes.new("GeometryNodeInstanceOnPoints")
instance.location = (-150, 0)

grass_material_node = nodes.new("GeometryNodeSetMaterial")
grass_material_node.location = (80, 0)
grass_material_node.inputs["Material"].default_value = grass_mat

join = nodes.new("GeometryNodeJoinGeometry")
join.location = (450, 0)

# Links
links.new(distribute.inputs["Mesh"], group_in.outputs["Geometry"])
links.new(distribute.inputs["Density"], group_in.outputs["Density"])

links.new(lift.inputs["Geometry"], cone.outputs["Mesh"])
links.new(instance.inputs["Points"], distribute.outputs["Points"])
links.new(instance.inputs["Instance"], lift.outputs["Geometry"])

links.new(grass_material_node.inputs["Geometry"], instance.outputs["Instances"])

links.new(join.inputs["Geometry"], group_in.outputs["Geometry"])
links.new(join.inputs["Geometry"], grass_material_node.outputs["Geometry"])
links.new(group_out.inputs["Geometry"], join.outputs["Geometry"])

# ---------------------------------------------------------------------------
# Modifier, with density exposed as a modifier input
# ---------------------------------------------------------------------------
mod = ground.modifiers.new("Grass", "NODES")
mod.node_group = gn

# Set density through the modifier's input properties
getattr(mod.properties.inputs, density_item.identifier).value = 45.0

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
bpy.ops.object.light_add(type='SUN', location=(4, -6, 10))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0.0, math.radians(30))

# Soft sky world
world = bpy.data.worlds.new("World")  # default nodes are created here
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.7, 0.9, 1.0)
bg.inputs["Strength"].default_value = 1.0
bpy.context.scene.world = world

# ---------------------------------------------------------------------------
# Camera framing the field
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam)

cam_loc = Vector((7.0, -11.0, 5.5))
target = Vector((0.0, 1.0, 0.0))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam

# ---------------------------------------------------------------------------
# Scene settings (single still frame)
# ---------------------------------------------------------------------------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
