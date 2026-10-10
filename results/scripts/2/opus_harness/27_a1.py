import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Material ----------
mat = bpy.data.materials.new("CubeMat")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.1, 0.45, 0.85, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35

# ---------- Geometry Nodes group ----------
ng = bpy.data.node_groups.new("CubeGrid", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
size_item = ng.interface.new_socket("Grid Size", in_out="INPUT", socket_type="NodeSocketInt")
size_item.default_value = 5
size_item.min_value = 1
size_item.max_value = 100
spacing_item = ng.interface.new_socket("Spacing", in_out="INPUT", socket_type="NodeSocketFloat")
spacing_item.default_value = 1.3
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes = ng.nodes
links = ng.links

gin = nodes.new("NodeGroupInput")
gin.location = (-800, 0)
gout = nodes.new("NodeGroupOutput")
gout.location = (800, 0)

# (count - 1) * spacing = total grid extent
sub = nodes.new("ShaderNodeMath")
sub.operation = 'SUBTRACT'
sub.inputs[1].default_value = 1.0
sub.location = (-550, 150)
mul = nodes.new("ShaderNodeMath")
mul.operation = 'MULTIPLY'
mul.location = (-350, 150)

grid = nodes.new("GeometryNodeMeshGrid")
grid.location = (-150, 100)

cube = nodes.new("GeometryNodeMeshCube")
cube.location = (-150, -200)
cube.inputs["Size"].default_value = (1.0, 1.0, 1.0)

inst = nodes.new("GeometryNodeInstanceOnPoints")
inst.location = (100, 0)

realize = nodes.new("GeometryNodeRealizeInstances")
realize.location = (320, 0)

setmat = nodes.new("GeometryNodeSetMaterial")
setmat.location = (550, 0)
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

# ---------- Host object ----------
mesh = bpy.data.meshes.new("GridHostMesh")
obj = bpy.data.objects.new("CubeGrid", mesh)
scene.collection.objects.link(obj)
obj.data.materials.append(mat)
obj.location = (0, 0, 0.5)

mod = obj.modifiers.new("CubeGrid", "NODES")
mod.node_group = ng

def set_input(item, value):
    try:
        getattr(mod.properties.inputs, item.identifier).value = value
    except Exception:
        mod[item.identifier] = value

set_input(size_item, 10)
set_input(spacing_item, 1.3)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("GroundMat")
gb = gmat.node_tree.nodes.get("Principled BSDF")
if gb:
    gb.inputs["Base Color"].default_value = (0.8, 0.8, 0.78, 1.0)
    gb.inputs["Roughness"].default_value = 0.8
ground.data.materials.append(gmat)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(5)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(35))
scene.collection.objects.link(sun)

area_data = bpy.data.lights.new("Fill", 'AREA')
area_data.energy = 1500
area_data.size = 10
area = bpy.data.objects.new("Fill", area_data)
area.location = (-10, -8, 12)
scene.collection.objects.link(area)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 0.5)
scene.collection.objects.link(target)

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (14, -16, 14)
scene.collection.objects.link(cam)
track = cam.constraints.new('TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
