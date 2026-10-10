import bpy
import bmesh
import math
import random
from mathutils import Vector, Euler
import mathutils

random.seed(7)

# ---------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

scene = bpy.context.scene


def link_object(obj):
    scene.collection.link(obj)
    return obj


def bmesh_to_object(name, bm, material):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    mesh.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return link_object(bpy.data.objects.new(name, mesh))


# ---------------------------------------------------------------
# World: orange-to-purple sunset gradient built with nodes
# ---------------------------------------------------------------
world = bpy.data.worlds.new("SunsetWorld")
scene.world = world
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()

tex_coord = wn.new("ShaderNodeTexCoord")
separate = wn.new("ShaderNodeSeparateXYZ")
map_range = wn.new("ShaderNodeMapRange")
ramp_node = wn.new("ShaderNodeValToRGB")
background = wn.new("ShaderNodeBackground")
world_out = wn.new("ShaderNodeOutputWorld")

tex_coord.location = (-800, 0)
separate.location = (-600, 0)
map_range.location = (-400, 0)
ramp_node.location = (-180, 0)
background.location = (80, 0)
world_out.location = (300, 0)

# Generated coordinates in a world shader are the view direction.
# Z ranges roughly -1 (down) .. 1 (up); remap so the horizon sits mid-ramp.
map_range.inputs["From Min"].default_value = -0.1
map_range.inputs["From Max"].default_value = 0.6
map_range.inputs["To Min"].default_value = 0.0
map_range.inputs["To Max"].default_value = 1.0

ramp = ramp_node.color_ramp
stops = [
    (0.00, (0.10, 0.03, 0.18)),   # deep purple (below horizon)
    (0.42, (0.95, 0.38, 0.12)),   # orange near horizon
    (0.50, (1.00, 0.72, 0.35)),   # warm gold at horizon
    (0.72, (0.62, 0.22, 0.48)),   # magenta-purple
    (1.00, (0.22, 0.08, 0.36)),   # deep purple top
]
ramp.elements[0].position = stops[0][0]
ramp.elements[0].color = (*stops[0][1], 1.0)
ramp.elements[1].position = stops[-1][0]
ramp.elements[1].color = (*stops[-1][1], 1.0)
for pos, col in stops[1:-1]:
    el = ramp.elements.new(pos)
    el.color = (*col, 1.0)
ramp.elements[0].position = stops[0][0]

background.inputs["Strength"].default_value = 1.0

wl.new(tex_coord.outputs["Generated"], separate.inputs["Vector"])
wl.new(separate.outputs["Z"], map_range.inputs["Value"])
wl.new(map_range.outputs["Result"], ramp_node.inputs["Fac"])
wl.new(ramp_node.outputs["Color"], background.inputs["Color"])
wl.new(background.outputs["Background"], world_out.inputs["Surface"])

# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
# Sand: noisy two-tone granular look
sand_mat = bpy.data.materials.new("Sand")
sn = sand_mat.node_tree.nodes
sl = sand_mat.node_tree.links
sn.clear()
sand_out = sn.new("ShaderNodeOutputMaterial")
sand_bsdf = sn.new("ShaderNodeBsdfPrincipled")
sand_noise = sn.new("ShaderNodeTexNoise")
sand_ramp = sn.new("ShaderNodeValToRGB")
sand_noise.inputs["Scale"].default_value = 90.0
sand_noise.inputs["Detail"].default_value = 8.0
sand_noise.inputs["Roughness"].default_value = 0.6
sand_out.location = (400, 0)
sand_bsdf.location = (100, 0)
sand_ramp.location = (-150, 0)
sand_noise.location = (-400, 0)
sand_ramp.color_ramp.elements[0].color = (0.62, 0.50, 0.32, 1.0)
sand_ramp.color_ramp.elements[1].color = (0.86, 0.78, 0.58, 1.0)
sand_bsdf.inputs["Roughness"].default_value = 0.92
sand_bsdf.inputs["Specular IOR Level"].default_value = 0.2
sl.new(sand_noise.outputs["Fac"], sand_ramp.inputs["Fac"])
sl.new(sand_ramp.outputs["Color"], sand_bsdf.inputs["Base Color"])
sl.new(sand_bsdf.outputs["BSDF"], sand_out.inputs["Surface"])

# Ocean: deep blue, slightly reflective
ocean_mat = bpy.data.materials.new("Ocean")
on = ocean_mat.node_tree.nodes
ol = ocean_mat.node_tree.links
on.clear()
ocean_out = on.new("ShaderNodeOutputMaterial")
ocean_bsdf = on.new("ShaderNodeBsdfPrincipled")
ocean_out.location = (300, 0)
ocean_bsdf.location = (0, 0)
ocean_bsdf.inputs["Base Color"].default_value = (0.02, 0.12, 0.30, 1.0)
ocean_bsdf.inputs["Metallic"].default_value = 0.0
ocean_bsdf.inputs["Roughness"].default_value = 0.06
ocean_bsdf.inputs["Specular IOR Level"].default_value = 0.8
ol.new(ocean_bsdf.outputs["BSDF"], ocean_out.inputs["Surface"])

# ---------------------------------------------------------------
# Sand ground with gentle dunes that slope into the water
# ---------------------------------------------------------------
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=120, y_segments=120, size=60.0)
for v in bm.verts:
    x, y = v.co.x, v.co.y
    n1 = mathutils.noise.noise(Vector((x * 0.04, y * 0.04, 0.0)))
    n2 = mathutils.noise.noise(Vector((x * 0.12, y * 0.12, 1.7)))
    dune = 0.9 + 0.8 * n1 + 0.15 * n2
    if y < 0.0:
        h = dune
    else:
        # Slope down into the sea; becomes submerged past the shoreline
        h = dune - y * 0.22
    v.co.z = h
bm.normal_update()
sand_obj = bmesh_to_object("Sand", bm, sand_mat)

# ---------------------------------------------------------------
# Ocean plane (sits at sea level, extends toward the horizon)
# ---------------------------------------------------------------
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=4, y_segments=4, size=100.0)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0.0, 100.0, 0.0))
ocean_obj = bmesh_to_object("Ocean", bm, ocean_mat)

# ---------------------------------------------------------------
# Lighting: low sun behind the ocean, warm colour
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new("SunsetSun", "SUN")
sun_data.energy = 5.0
sun_data.color = (1.0, 0.55, 0.25)
sun_data.angle = math.radians(1.5)
sun_obj = link_object(bpy.data.objects.new("SunsetSun", sun_data))
# Sun direction points toward -Y (toward camera) and slightly downward
sun_obj.rotation_euler = Euler((math.radians(-80), 0.0, math.radians(15)), 'XYZ')
sun_obj.location = (0.0, 40.0, 10.0)

# Soft warm fill light from the sky side
fill_data = bpy.data.lights.new("SkyFill", "AREA")
fill_data.energy = 300.0
fill_data.color = (0.8, 0.6, 0.9)
fill_data.size = 40.0
fill_obj = link_object(bpy.data.objects.new("SkyFill", fill_data))
fill_obj.location = (0.0, -20.0, 25.0)
fill_obj.rotation_euler = Euler((math.radians(20), 0.0, 0.0), 'XYZ')

# ---------------------------------------------------------------
# Camera framing the sunset over the water
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("BeachCamera")
cam_data.lens = 35.0
cam_obj = link_object(bpy.data.objects.new("BeachCamera", cam_data))
cam_location = Vector((0.0, -35.0, 4.0))
cam_target = Vector((0.0, 45.0, 3.0))
cam_obj.location = cam_location
direction = (cam_target - cam_location).normalized()
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------------------------------------------------------------
# Scene settings (single frame still)
# ---------------------------------------------------------------
scene.frame_start = 1
scene.frame_end = 1
