import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene

# ---------- Clean the default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)


def link_object(name, mesh):
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    return obj


def make_grid(size, segs, center_y):
    """Grid of given half-size centered at (0, center_y, 0), returned as a BMesh."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=segs, y_segments=segs, size=size)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0.0, center_y, 0.0))
    return bm


# ---------- Materials ----------
def set_input(node, names, value):
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return True
    return False


def make_principled_material(name, base_color, roughness, metallic=0.0, specular=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    set_input(bsdf, ["Base Color"], base_color)
    set_input(bsdf, ["Roughness"], roughness)
    set_input(bsdf, ["Metallic"], metallic)
    set_input(bsdf, ["Specular IOR Level", "Specular"], specular)
    return mat, bsdf


# Sand material with noise-driven bump for grain
sand_mat, sand_bsdf = make_principled_material(
    "Sand", (0.78, 0.67, 0.46, 1.0), roughness=0.92, specular=0.3
)
s_nodes = sand_mat.node_tree.nodes
s_links = sand_mat.node_tree.links
noise = s_nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 90.0
noise.inputs["Detail"].default_value = 8.0
bump = s_nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.15
s_links.new(noise.outputs["Fac"], bump.inputs["Height"])
s_links.new(bump.outputs["Normal"], sand_bsdf.inputs["Normal"])

# Ocean material: deep blue, glossy and reflective
ocean_mat, ocean_bsdf = make_principled_material(
    "Ocean", (0.02, 0.18, 0.32, 1.0), roughness=0.06, metallic=0.0, specular=0.8
)
set_input(ocean_bsdf, ["Coat Weight", "Clearcoat"], 0.4)
set_input(ocean_bsdf, ["Coat Roughness", "Clearcoat Roughness"], 0.05)

# ---------- Sand ground with gentle dunes ----------
sand_bm = make_grid(size=100.0, segs=70, center_y=100.0)
for v in sand_bm.verts:
    x, y = v.co.x, v.co.y
    height = (0.9 * math.sin(x * 0.045 + 1.3) * math.cos(y * 0.031)
              + 0.35 * math.sin(x * 0.13 + y * 0.09))
    falloff = max(0.0, min(1.0, (y - 4.0) / 25.0))  # flat near the shoreline
    v.co.z = height * falloff
sand_mesh = bpy.data.meshes.new("SandMesh")
sand_bm.to_mesh(sand_mesh)
sand_bm.free()
sand_mesh.update()
sand_obj = link_object("SandGround", sand_mesh)
sand_obj.data.materials.append(sand_mat)
sand_mesh.polygons.foreach_set("use_smooth", [True] * len(sand_mesh.polygons))

# ---------- Ocean plane (slightly below sand level) ----------
ocean_bm = make_grid(size=200.0, segs=40, center_y=-100.0)
for v in ocean_bm.verts:
    v.co.z = -0.05
ocean_mesh = bpy.data.meshes.new("OceanMesh")
ocean_bm.to_mesh(ocean_mesh)
ocean_bm.free()
ocean_mesh.update()
ocean_obj = link_object("Ocean", ocean_mesh)
ocean_obj.data.materials.append(ocean_mat)

# ---------- Sky: orange-to-purple gradient via world nodes ----------
world = bpy.data.worlds.new("SunsetWorld")
scene.world = world
world.use_nodes = True
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links
wnodes.clear()

tex_coord = wnodes.new("ShaderNodeTexCoord")
separate = wnodes.new("ShaderNodeSeparateXYZ")
map_range = wnodes.new("ShaderNodeMapRange")
ramp = wnodes.new("ShaderNodeValToRGB")
background = wnodes.new("ShaderNodeBackground")
world_out = wnodes.new("ShaderNodeOutputWorld")

wlinks.new(tex_coord.outputs["Generated"], separate.inputs["Vector"])
wlinks.new(separate.outputs["Z"], map_range.inputs[0])  # Value
map_range.inputs[1].default_value = -0.1                 # From Min
map_range.inputs[2].default_value = 1.0                  # From Max
map_range.inputs[3].default_value = 0.0                  # To Min
map_range.inputs[4].default_value = 1.0                  # To Max
map_range.clamp = True
wlinks.new(map_range.outputs["Result"], ramp.inputs["Fac"])
wlinks.new(ramp.outputs["Color"], background.inputs["Color"])
background.inputs["Strength"].default_value = 1.0
wlinks.new(background.outputs["Background"], world_out.inputs["Surface"])

cr = ramp.color_ramp
# Clear to a known state, then build stops: horizon orange -> pink -> purple -> deep violet
cr.elements[0].position = 0.0
cr.elements[0].color = (1.0, 0.55, 0.12, 1.0)
cr.elements[1].position = 1.0
cr.elements[1].color = (0.10, 0.03, 0.22, 1.0)
pink = cr.elements.new(0.22)
pink.color = (0.95, 0.30, 0.35, 1.0)
purple = cr.elements.new(0.50)
purple.color = (0.45, 0.13, 0.48, 1.0)

# ---------- Sun light (low, warm, sunset) ----------
sun_data = bpy.data.lights.new(name="SunsetSun", type='SUN')
sun_data.energy = 4.0
sun_data.color = (1.0, 0.62, 0.34)
sun_data.angle = math.radians(1.5)
sun_obj = link_object("SunsetSun", sun_data)
# Light travels from the sea toward the beach, angled downward
light_dir = Vector((0.15, 0.85, -0.22)).normalized()
sun_obj.rotation_mode = 'QUATERNION'
sun_obj.rotation_quaternion = light_dir.to_track_quat('-Z', 'Y')

# Soft fill light from the sky
fill_data = bpy.data.lights.new(name="SkyFill", type='AREA')
fill_data.energy = 60.0
fill_data.color = (0.6, 0.5, 0.8)
fill_data.size = 20.0
fill_obj = link_object("SkyFill", fill_data)
fill_obj.location = (0.0, 30.0, 25.0)
fill_obj.rotation_mode = 'QUATERNION'
fill_obj.rotation_quaternion = (Vector((0, 0, 0)) - fill_obj.location).normalized().to_track_quat('-Z', 'Y')

# ---------- Camera framing the shoreline and sunset ----------
cam_data = bpy.data.cameras.new("BeachCamera")
cam_data.lens = 35.0
cam_data.clip_end = 1000.0
cam_obj = link_object("BeachCamera", cam_data)
cam_obj.location = Vector((0.0, 18.0, 3.2))
target = Vector((0.0, -45.0, 2.0))
direction = (target - cam_obj.location).normalized()
cam_obj.rotation_mode = 'QUATERNION'
cam_obj.rotation_quaternion = direction.to_track_quat('-Z', 'Y')
scene.camera = cam_obj

# ---------- Render-agnostic scene settings ----------
scene.frame_start = 1
scene.frame_end = 1
