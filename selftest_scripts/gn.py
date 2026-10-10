# Known good Blender 5.2 script, category: gn. 10x10 grid of cubes from a Geometry Nodes modifier,
# grid size exposed as a modifier input and set from the script.
import bpy
import math

scene = bpy.context.scene

ng = bpy.data.node_groups.new("CubeGrid", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
size_socket = ng.interface.new_socket("Grid Size", in_out="INPUT", socket_type="NodeSocketInt")
size_socket.default_value = 4
size_socket.min_value = 1
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes, links = ng.nodes, ng.links
gin = nodes.new("NodeGroupInput")
gout = nodes.new("NodeGroupOutput")
grid = nodes.new("GeometryNodeMeshGrid")
grid.inputs["Size X"].default_value = 10.0
grid.inputs["Size Y"].default_value = 10.0
cube = nodes.new("GeometryNodeMeshCube")
cube.inputs["Size"].default_value = (0.6, 0.6, 0.6)
inst = nodes.new("GeometryNodeInstanceOnPoints")
realize = nodes.new("GeometryNodeRealizeInstances")
links.new(gin.outputs["Grid Size"], grid.inputs["Vertices X"])
links.new(gin.outputs["Grid Size"], grid.inputs["Vertices Y"])
links.new(grid.outputs["Mesh"], inst.inputs["Points"])
links.new(cube.outputs["Mesh"], inst.inputs["Instance"])
links.new(inst.outputs["Instances"], realize.inputs["Geometry"])
links.new(realize.outputs["Geometry"], gout.inputs["Geometry"])

obj = bpy.data.objects.new("CubeGrid", bpy.data.meshes.new("CubeGrid"))
scene.collection.objects.link(obj)
mod = obj.modifiers.new("CubeGrid", "NODES")
mod.node_group = ng
# 5.2: modifier inputs are RNA properties now, not custom properties (mod["Socket_1"] raises TypeError).
getattr(mod.properties.inputs, size_socket.identifier).value = 10

mat = bpy.data.materials.new("Blue")
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.3, 0.9, 1.0)
obj.data.materials.append(mat)

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", type="SUN"))
sun.rotation_euler = (math.radians(40), math.radians(10), 0)
scene.collection.objects.link(sun)

cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -14, 11)
cam.rotation_euler = (math.radians(52), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam
