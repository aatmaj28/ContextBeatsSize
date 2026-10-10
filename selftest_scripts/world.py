# Known good Blender 5.2 script, category: world. Glass and gold spheres, checker floor, Sky Texture world.
import bpy
import math

scene = bpy.context.scene

glass = bpy.data.materials.new("Glass")
g = glass.node_tree.nodes["Principled BSDF"]
g.inputs["Transmission Weight"].default_value = 1.0
g.inputs["Roughness"].default_value = 0.0
g.inputs["IOR"].default_value = 1.45

gold = bpy.data.materials.new("Gold")
au = gold.node_tree.nodes["Principled BSDF"]
au.inputs["Base Color"].default_value = (1.0, 0.77, 0.34, 1.0)
au.inputs["Metallic"].default_value = 1.0
au.inputs["Roughness"].default_value = 0.2

floor = bpy.data.materials.new("Checker")
nt = floor.node_tree
checker = nt.nodes.new("ShaderNodeTexChecker")
checker.inputs["Scale"].default_value = 8.0
nt.links.new(checker.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])

bpy.ops.mesh.primitive_plane_add(size=10)
bpy.context.active_object.data.materials.append(floor)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(-1, 0, 0.8))
bpy.ops.object.shade_smooth()
bpy.context.active_object.data.materials.append(glass)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(1, 0, 0.8))
bpy.ops.object.shade_smooth()
bpy.context.active_object.data.materials.append(gold)

world = bpy.data.worlds.new("Sky")  # Background + World Output already exist in 5.x
wnt = world.node_tree
sky = wnt.nodes.new("ShaderNodeTexSky")
sky.sky_type = "MULTIPLE_SCATTERING"
sky.sun_elevation = math.radians(25)
wnt.links.new(sky.outputs["Color"], wnt.nodes["Background"].inputs["Color"])
wnt.nodes["Background"].inputs["Strength"].default_value = 0.3
scene.world = world

cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -6, 2.2)
cam.rotation_euler = (math.radians(78), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam
