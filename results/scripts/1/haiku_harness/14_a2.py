import bpy
import bmesh
import math
import random
from mathutils import Vector, Euler
from mathutils import noise as mnoise

random.seed(7)

# ---------------------------------------------------------------
# Clear default scene
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
coll = scene.collection


def link(obj):
    coll.objects.link(obj)
    return obj


def ground_height(x, y):
    """Beach profile: water below ~y=0, rising inland, with dune noise."""
    base = -0.5 + 0.07 * max(y, 0.0)
    dunes = 0.35 * mnoise.noise(Vector((x * 0.06, y * 0.06, 0.0)))
    fine = 0.06 * mnoise.noise(Vector((x * 0.6, y * 0.6, 1.0)))
    return base + dunes * (0.3 + 0.7 * min(max(y, 0.0) / 20.0, 1.0)) + fine


# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
def make_principled_material(name, base_color, roughness=0.5, metallic=0.0,
                             specular=0.5, ior=1.45):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat, nt, bsdf


# Sand: warm, slightly bumpy from procedural noise
sand_mat, sand_nt, sand_bsdf = make_principled_material(
    "Sand", (0.80, 0.66, 0.45), roughness=0.85, specular=0.35)
sand_noise = sand_nt.nodes.new("ShaderNodeTexNoise")
sand_noise.inputs["Scale"].default_value = 220.0
sand_noise.inputs["Detail"].default_value = 8.0
sand_bump = sand_nt.nodes.new("ShaderNodeBump")
sand_bump.inputs["Strength"].default_value = 0.08
sand_nt.links.new(sand_noise.outputs["Fac"], sand_bump.inputs["Height"])
sand_nt.links.new(sand_bump.outputs["Normal"], sand_bsdf.inputs["Normal"])

# Ocean: deep blue, glossy and reflective
ocean_mat, ocean_nt, ocean_bsdf = make_principled_material(
    "Ocean", (0.02, 0.10, 0.22), roughness=0.04, specular=1.0, ior=1.33)
ocean_bsdf.inputs["Coat Weight"].default_value = 0.6
ocean_bsdf.inputs["Coat Roughness"].default_value = 0.02

# Rocks: grey stone
rock_mat, _, _ = make_principled_material(
    "Rock", (0.28, 0.26, 0.25), roughness=0.7, specular=0.4)


# ---------------------------------------------------------------
# Mesh helper
# ---------------------------------------------------------------
def build_grid_mesh(name, size, segments, height_fn, material):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=segments, y_segments=segments,
                          size=size)
    for v in bm.verts:
        v.co.z = height_fn(v.co.x, v.co.y)
    bm.normal_update()
    me = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(material)
    me.update()
    obj = bpy.data.objects.new(name, me)
    return link(obj)


# ---------------------------------------------------------------
# Sand ground
# ---------------------------------------------------------------
ground = build_grid_mesh(
    "Sand", size=80.0, segments=160,
    height_fn=ground_height, material=sand_mat)


# ---------------------------------------------------------------
# Ocean plane (seaward of the beach, centred on the waterline at z = 0)
# ---------------------------------------------------------------
ocean = build_grid_mesh(
    "Ocean", size=120.0, segments=4,
    height_fn=lambda x, y: 0.0, material=ocean_mat)
ocean.location = (0.0, -50.0, 0.0)
ocean_bm = bmesh.new()
ocean_bm.from_mesh(ocean.data)
for v in ocean_bm.verts:
    v.co.z = 0.02 * mnoise.noise(Vector((v.co.x * 0.08, v.co.y * 0.08, 3.0)))
ocean_bm.normal_update()
ocean_bm.to_mesh(ocean.data)
ocean_bm.free()
ocean.data.update()


# ---------------------------------------------------------------
# Scattered rocks along the beach
# ---------------------------------------------------------------
rock_objs = []
for i in range(14):
    x = random.uniform(-22.0, 22.0)
    y = random.uniform(8.0, 32.0)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        n = mnoise.noise(v.co * 1.7 + Vector((i, i, i)))
        v.co *= (1.0 + 0.25 * n)
    bm.normal_update()
    me = bpy.data.meshes.new(f"RockMesh{i}")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(rock_mat)
    rock = bpy.data.objects.new(f"Rock{i}", me)
    link(rock)
    s = random.uniform(0.4, 1.4)
    rock.scale = (s * random.uniform(0.8, 1.3),
                  s * random.uniform(0.8, 1.3),
                  s * random.uniform(0.4, 0.7))
    rock.location = (x, y, ground_height(x, y) + 0.1)
    rock.rotation_euler = (random.uniform(0, 0.3),
                           random.uniform(0, 0.3),
                           random.uniform(0, math.tau))
    rock_objs.append(rock)


# ---------------------------------------------------------------
# Sky: orange-to-purple gradient via world shader nodes
# ---------------------------------------------------------------
world = bpy.data.worlds.new("SunsetSky")
scene.world = world
wnt = world.node_tree
wnt.nodes.clear()

tex_coord = wnt.nodes.new("ShaderNodeTexCoord")
sep = wnt.nodes.new("ShaderNodeSeparateXYZ")
map_range = wnt.nodes.new("ShaderNodeMapRange")
ramp = wnt.nodes.new("ShaderNodeValToRGB")
bg = wnt.nodes.new("ShaderNodeBackground")
out = wnt.nodes.new("ShaderNodeOutputWorld")

tex_coord.location = (-900, 0)
sep.location = (-700, 0)
map_range.location = (-480, 0)
ramp.location = (-240, 0)
bg.location = (0, 0)
out.location = (220, 0)

# TexCoord has no "Position" socket; for the world, "Generated" gives the
# view-direction-based coordinates used for the sky gradient.
wnt.links.new(tex_coord.outputs["Generated"], sep.inputs["Vector"])
wnt.links.new(sep.outputs["Z"], map_range.inputs["Value"])
map_range.clamp = True
map_range.inputs["From Min"].default_value = -0.2
map_range.inputs["From Max"].default_value = 0.6
map_range.inputs["To Min"].default_value = 0.0
map_range.inputs["To Max"].default_value = 1.0
wnt.links.new(map_range.outputs["Result"], ramp.inputs["Fac"])

# Gradient stops, kept in ascending order
stops = [
    (0.00, (0.90, 0.35, 0.10)),   # deep orange below horizon
    (0.25, (1.00, 0.60, 0.20)),   # bright horizon glow
    (0.40, (0.90, 0.30, 0.38)),   # rose transition
    (0.65, (0.40, 0.12, 0.45)),   # violet
    (1.00, (0.10, 0.03, 0.22)),   # deep purple zenith
]
els = ramp.color_ramp.elements
els[0].position = stops[0][0]
els[0].color = (*stops[0][1], 1.0)
els[1].position = stops[1][0]
els[1].color = (*stops[1][1], 1.0)
for pos, col in stops[2:]:
    e = els.new(pos)
    e.color = (*col, 1.0)

wnt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.2
wnt.links.new(bg.outputs["Background"], out.inputs["Surface"])


# ---------------------------------------------------------------
# Lighting: low warm sun behind the ocean, plus soft fill
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new("SunsetSun", "SUN")
sun_data.energy = 4.5
sun_data.color = (1.0, 0.62, 0.35)
sun_data.angle = math.radians(1.5)
sun = bpy.data.objects.new("SunsetSun", sun_data)
link(sun)
sun.rotation_euler = Euler((math.radians(-80), 0.0, math.radians(20)), 'XYZ')

fill_data = bpy.data.lights.new("SkyFill", "AREA")
fill_data.energy = 150.0
fill_data.color = (0.6, 0.5, 0.8)
fill_data.size = 30.0
fill = bpy.data.objects.new("SkyFill", fill_data)
link(fill)
fill.location = (0.0, -20.0, 25.0)
fill.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')


# ---------------------------------------------------------------
# Camera: low on the sand, looking out over the water toward the sun
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("BeachCamera")
cam_data.lens = 35.0
cam_data.dof.use_dof = False
cam = bpy.data.objects.new("BeachCamera", cam_data)
link(cam)

cam_loc = Vector((0.0, -26.0, 3.5))
target = Vector((0.0, 14.0, 1.0))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam


# ---------------------------------------------------------------
# Render settings (no render or save)
# ---------------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.frame_start = 1
scene.frame_end = 1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
