import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(42)

scene = bpy.context.scene

# ---------------------------------------------------------------
# Clear existing data
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value

def get_or_create_bsdf(mat):
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        out = nodes.get("Material Output") or nodes.new("ShaderNodeOutputMaterial")
        mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return bsdf

def link_material_output_clean(mat):
    # Ensure there is a material output present (default trees already have one)
    if mat.node_tree.nodes.get("Material Output") is None:
        mat.node_tree.nodes.new("ShaderNodeOutputMaterial")

def link_objects(obj):
    scene.collection.objects.link(obj)
    return obj

def smooth_shade(mesh):
    for p in mesh.polygons:
        p.use_smooth = True

def height(x, y):
    """Terrain height: sea floor below y=0, beach slope and dunes above."""
    if y < 0.0:
        return 0.15 * y + 0.02 * math.sin(0.3 * x)
    if y < 12.0:
        base = 0.12 * y
    else:
        base = 1.44 + 0.03 * (y - 12.0)
    amp = min(1.0, y / 15.0)
    dunes = (0.9 * math.sin(0.12 * x + 0.25 * math.sin(0.05 * y)) +
             0.25 * math.sin(0.7 * x + 1.3) * math.cos(0.45 * y)) * amp
    return base + dunes

# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
def make_sand_material():
    mat = bpy.data.materials.new("Sand")
    link_material_output_clean(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = get_or_create_bsdf(mat)

    set_input(bsdf, "Roughness", 0.85)
    set_input(bsdf, "Specular IOR Level", 0.3)

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 60.0
    noise.inputs["Detail"].default_value = 8.0

    ramp = nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position = 0.0
    els[0].color = (0.70, 0.56, 0.36, 1.0)
    els[1].position = 1.0
    els[1].color = (0.92, 0.80, 0.60, 1.0)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def make_ocean_material():
    mat = bpy.data.materials.new("Ocean")
    link_material_output_clean(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = get_or_create_bsdf(mat)

    set_input(bsdf, "Base Color", (0.02, 0.16, 0.34, 1.0))
    set_input(bsdf, "Roughness", 0.06)
    set_input(bsdf, "Specular IOR Level", 0.7)
    set_input(bsdf, "Metallic", 0.0)

    # Gentle ripples through a bump map
    wave = nodes.new("ShaderNodeTexNoise")
    wave.inputs["Scale"].default_value = 10.0
    wave.inputs["Detail"].default_value = 4.0
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    links.new(wave.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def make_rock_material():
    mat = bpy.data.materials.new("Rock")
    link_material_output_clean(mat)
    bsdf = get_or_create_bsdf(mat)
    set_input(bsdf, "Base Color", (0.13, 0.11, 0.10, 1.0))
    set_input(bsdf, "Roughness", 0.7)
    return mat

sand_mat = make_sand_material()
ocean_mat = make_ocean_material()
rock_mat = make_rock_material()

# ---------------------------------------------------------------
# Sand ground (heightfield)
# ---------------------------------------------------------------
nx, ny = 120, 150
xmin, xmax = -60.0, 60.0
ymin, ymax = -80.0, 70.0

verts = []
for j in range(ny + 1):
    y = ymin + (ymax - ymin) * j / ny
    for i in range(nx + 1):
        x = xmin + (xmax - xmin) * i / nx
        verts.append((x, y, height(x, y)))

faces = []
for j in range(ny):
    for i in range(nx):
        a = j * (nx + 1) + i
        b = a + 1
        c = b + nx + 1
        d = a + nx + 1
        faces.append((a, b, c, d))

sand_mesh = bpy.data.meshes.new("SandMesh")
sand_mesh.from_pydata(verts, [], faces)
sand_mesh.update()
smooth_shade(sand_mesh)
sand_obj = bpy.data.objects.new("Sand", sand_mesh)
link_objects(sand_obj)
sand_obj.data.materials.append(sand_mat)

# ---------------------------------------------------------------
# Ocean plane (slightly reflective)
# ---------------------------------------------------------------
ocean_mesh = bpy.data.meshes.new("OceanMesh")
ocean_verts = [
    (-150.0, -150.0, 0.0),
    (150.0, -150.0, 0.0),
    (150.0, 3.0, 0.0),
    (-150.0, 3.0, 0.0),
]
ocean_mesh.from_pydata(ocean_verts, [], [(0, 1, 2, 3)])
ocean_mesh.update()
ocean_obj = bpy.data.objects.new("Ocean", ocean_mesh)
link_objects(ocean_obj)
ocean_obj.data.materials.append(ocean_mat)

# ---------------------------------------------------------------
# Rocks along the shoreline
# ---------------------------------------------------------------
def make_rock(index, x, y, size, stretch):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, diameter=2.0)
    for v in bm.verts:
        v.co *= 1.0 + random.uniform(-0.22, 0.22)
    me = bpy.data.meshes.new(f"RockMesh{index}")
    bm.to_mesh(me)
    bm.free()
    smooth_shade(me)
    me.materials.append(rock_mat)

    obj = bpy.data.objects.new(f"Rock{index}", me)
    link_objects(obj)
    z = height(x, y) + 0.25 * size
    obj.location = (x, y, z)
    obj.scale = (size * stretch[0], size * stretch[1], size * stretch[2])
    obj.rotation_euler = (random.uniform(0, math.pi),
                          random.uniform(0, math.pi),
                          random.uniform(0, math.pi))
    return obj

rock_specs = [
    (-9.0, 4.0, 1.4, (1.0, 0.8, 0.6)),
    (-6.5, 6.5, 0.8, (1.2, 1.0, 0.7)),
    (7.5, 3.0, 1.1, (1.0, 1.2, 0.8)),
    (11.0, 8.5, 1.8, (1.3, 1.0, 0.7)),
    (-14.0, 11.0, 2.2, (1.1, 1.0, 0.6)),
    (16.0, 14.0, 1.5, (1.0, 1.0, 0.9)),
    (3.5, 1.5, 0.6, (1.0, 1.0, 0.8)),
]
for idx, (rx, ry, rs, st) in enumerate(rock_specs):
    make_rock(idx, rx, ry, rs, st)

# ---------------------------------------------------------------
# Sunset sky (world shader nodes)
# ---------------------------------------------------------------
world = bpy.data.worlds.get("SunsetWorld")
if world is None:
    world = bpy.data.worlds.new("SunsetWorld")
scene.world = world

wnodes = world.node_tree.nodes
wlinks = world.node_tree.links
wnodes.clear()

tex_coord = wnodes.new("ShaderNodeTexCoord")
separate = wnodes.new("ShaderNodeSeparateXYZ")
map_range = wnodes.new("ShaderNodeMapRange")
ramp = wnodes.new("ShaderNodeValToRGB")
background = wnodes.new("ShaderNodeBackground")
world_out = wnodes.new("ShaderNodeOutputWorld")

wlinks.new(tex_coord.outputs["Generated"], separate.inputs[0])
wlinks.new(separate.outputs["Z"], map_range.inputs[0])   # Value
map_range.inputs[1].default_value = 0.0    # From Min
map_range.inputs[2].default_value = 0.6    # From Max
map_range.inputs[3].default_value = 0.0    # To Min
map_range.inputs[4].default_value = 1.0    # To Max
wlinks.new(map_range.outputs[0], ramp.inputs["Fac"])

# Horizon orange -> pink -> purple -> deep violet overhead
stops = [
    (0.00, (1.00, 0.45, 0.12, 1.0)),
    (0.12, (0.95, 0.25, 0.35, 1.0)),
    (0.40, (0.45, 0.12, 0.50, 1.0)),
    (1.00, (0.08, 0.03, 0.18, 1.0)),
]
els = ramp.color_ramp.elements
els[0].position = stops[0][0]
els[0].color = stops[0][1]
els[1].position = stops[1][0]
els[1].color = stops[1][1]
for pos, col in stops[2:]:
    e = els.new(pos)
    e.color = col

wlinks.new(ramp.outputs["Color"], background.inputs["Color"])
background.inputs["Strength"].default_value = 1.0
wlinks.new(background.outputs["Background"], world_out.inputs["Surface"])

# ---------------------------------------------------------------
# Low setting sun behind the ocean
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new("SunsetSun", "SUN")
sun_data.energy = 3.5
sun_data.color = (1.0, 0.55, 0.28)
sun_data.angle = math.radians(1.5)
sun_obj = bpy.data.objects.new("SunsetSun", sun_data)
link_objects(sun_obj)
sun_obj.location = (0.0, -40.0, 20.0)

# Light travels from the ocean side toward the camera, slightly downward
sun_dir = Vector((0.25, 1.0, -0.22)).normalized()
sun_obj.rotation_mode = "QUATERNION"
sun_obj.rotation_quaternion = sun_dir.to_track_quat("-Z", "Y")

# Soft warm fill light from the sea side
fill_data = bpy.data.lights.new("WarmFill", "AREA")
fill_data.energy = 300.0
fill_data.color = (1.0, 0.6, 0.4)
fill_data.size = 30.0
fill_obj = bpy.data.objects.new("WarmFill", fill_data)
link_objects(fill_obj)
fill_obj.location = (0.0, -30.0, 12.0)
fill_obj.rotation_mode = "QUATERNION"
fill_obj.rotation_quaternion = Vector((0.0, 0.25, 1.0)).normalized().to_track_quat("-Z", "Y")

# ---------------------------------------------------------------
# Camera framing the shoreline and the sunset
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("BeachCamera")
cam_data.lens = 35.0
cam_obj = bpy.data.objects.new("BeachCamera", cam_data)
link_objects(cam_obj)

cam_loc = Vector((-3.0, 26.0, 3.2))
cam_target = Vector((0.0, -6.0, 0.8))
cam_dir = (cam_target - cam_loc).normalized()
cam_obj.location = cam_loc
cam_obj.rotation_mode = "QUATERNION"
cam_obj.rotation_quaternion = cam_dir.to_track_quat("-Z", "Y")

scene.camera = cam_obj

# ---------------------------------------------------------------
# Render settings (no rendering performed here)
# ---------------------------------------------------------------
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
