import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# --- Clean scene ---
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# --- Material ---
mat = bpy.data.materials.new("CubeMat")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.1, 0.45, 0.85, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35

# --- Geometry node group ---
ng = bpy.data.node_groups.new("CubeGrid", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
size_item = ng.interface.new_socket("Grid Size", in_out="INPUT", socket_type="NodeSocketInt")
size_item.default_value = 5
size_item.min_value = 1
spacing_item = ng.interface.new_socket("Spacing", in_out="INPUT", socket_type="NodeSocketFloat")
spacing_item.default_value = 1.5
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes, links = ng.nodes, ng.links
gin = nodes.new("NodeGroupInput"); gin.location = (-800, 0)
gout = nodes.new("NodeGroupOutput"); gout.location = (800, 0)

sub = nodes.new("ShaderNodeMath"); sub.operation = 'SUBTRACT'
sub.inputs[1].default_value = 1.0; sub.location = (-600, 100)
mul = nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
mul.location = (-400, 100)

grid = nodes.new("GeometryNodeMeshGrid"); grid.location = (-200, 100)
cube = nodes.new("GeometryNodeMeshCube"); cube.location = (-200, -150)
cube.inputs["Size"].default_value = (1.0, 1.0, 1.0)

inst = nodes.new("GeometryNodeInstanceOnPoints"); inst.location = (50, 0)
realize = nodes.new("GeometryNodeRealizeInstances"); realize.location = (300, 0)
setmat = nodes.new("GeometryNodeSetMaterial"); setmat.location = (550, 0)
setmat.inputs["Material"].default_value = mat

links.new(gin.outputs["Grid Size"], sub.inputs[0])
links.new(sub.outputs[0], mul.inputs[0])
links.new(gin.outputs["Spacing"], mul.inputs[1])
links.new(mul.outputs[0], grid.inputs["Size X"])
links.new(mul.outputs[0], grid.inputs["Size Y"])
links.new(gin.outputs["Grid Size"], grid.inputs["Vertices X"])
links.new(gin.outputs["Grid Size"], grid.inputs["Vertices Y"])
links.new(grid.outputs["Mesh"], inst.inputs["Points"])
links.new(cube.outputs["Mesh"], inst.inputs["Instance"])
links.new(inst.outputs["Instances"], realize.inputs["Geometry"])
links.new(realize.outputs["Geometry"], setmat.inputs["Geometry"])
links.new(setmat.outputs["Geometry"], gout.inputs["Geometry"])

# --- Host object ---
mesh = bpy.data.meshes.new("GridHost")
obj = bpy.data.objects.new("CubeGrid", mesh)
scene.collection.objects.link(obj)
obj.data.materials.append(mat)
obj.location.z = 0.5

mod = obj.modifiers.new("CubeGrid", "NODES")
mod.node_group = ng

# Set grid size from script (5.2 API, with fallback)
try:
    getattr(mod.properties.inputs, size_item.identifier).value = 10
except Exception:
    mod[size_item.identifier] = 10

# --- Ground ---
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("Ground")
gb = gmat.node_tree.nodes.get("Principled BSDF")
if gb:
    gb.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
    gb.inputs["Roughness"].default_value = 0.8
ground.data.materials.append(gmat)

# --- Lighting ---
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(5)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(35))
scene.collection.objects.link(sun)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.6, 0.7, 0.85, 1.0)
    bg.inputs["Strength"].default_value = 0.6

# --- Camera ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((17.0, -17.0, 15.0))
direction = Vector((0, 0, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
