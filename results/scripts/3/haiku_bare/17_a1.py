import bpy
import bmesh
import mathutils
import math
import random
import colorsys
import bpy_extras

random.seed(7)

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

scene = bpy.context.scene


def make_smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def new_sphere(name, radius, segments=128, rings=64):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    make_smooth(obj)
    return obj


# ---------- Planet material (procedural noise surface) ----------
planet_mat = bpy.data.materials.new("PlanetSurface")
planet_mat.use_nodes = True
pnt = planet_mat.node_tree
pnt.nodes.clear()

p_out = pnt.nodes.new("ShaderNodeOutputMaterial")
p_out.location = (900, 0)
p_bsdf = pnt.nodes.new("ShaderNodeBsdfPrincipled")
p_bsdf.location = (600, 0)
p_bsdf.inputs["Roughness"].default_value = 0.85
pnt.links.new(p_bsdf.outputs["BSDF"], p_out.inputs["Surface"])

coord = pnt.nodes.new("ShaderNodeTexCoord")
coord.location = (-1100, 0)

mapping = pnt.nodes.new("ShaderNodeMapping")
mapping.location = (-900, 0)
pnt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])

noise_big = pnt.nodes.new("ShaderNodeTexNoise")
noise_big.location = (-600, 200)
noise_big.inputs["Scale"].default_value = 2.5
noise_big.inputs["Detail"].default_value = 9.0
noise_big.inputs["Roughness"].default_value = 0.6
pnt.links.new(mapping.outputs["Vector"], noise_big.inputs["Vector"])

noise_fine = pnt.nodes.new("ShaderNodeTexNoise")
noise_fine.location = (-600, -250)
noise_fine.inputs["Scale"].default_value = 18.0
noise_fine.inputs["Detail"].default_value = 6.0
pnt.links.new(mapping.outputs["Vector"], noise_fine.inputs["Vector"])

# Mix big and fine noise for terrain-like detail
mix_noise = pnt.nodes.new("ShaderNodeMix")
mix_noise.data_type = "FLOAT"
mix_noise.location = (-350, 0)
mix_noise.inputs["Factor"].default_value = 0.35
pnt.links.new(noise_big.outputs["Fac"], mix_noise.inputs["A"])
pnt.links.new(noise_fine.outputs["Fac"], mix_noise.inputs["B"])
height_src = mix_noise.outputs["Result"]

ramp = pnt.nodes.new("ShaderNodeValToRGB")
ramp.location = (-100, 150)
cr = ramp.color_ramp
cr.elements[0].position = 0.0
cr.elements[0].color = (0.05, 0.12, 0.25, 1.0)  # deep ocean/lowlands
cr.elements[1].position = 1.0
cr.elements[1].color = (0.85, 0.75, 0.55, 1.0)  # highland tan
mid = cr.elements.new(0.45)
mid.color = (0.18, 0.38, 0.22, 1.0)            # green plains
hi = cr.elements.new(0.75)
hi.color = (0.45, 0.42, 0.40, 1.0)             # rocky peaks
pnt.links.new(height_src, ramp.inputs["Fac"])
pnt.links.new(ramp.outputs["Color"], p_bsdf.inputs["Base Color"])

bump = pnt.nodes.new("ShaderNodeBump")
bump.location = (100, -250)
bump.inputs["Strength"].default_value = 0.35
bump.inputs["Distance"].default_value = 0.05
pnt.links.new(height_src, bump.inputs["Height"])
pnt.links.new(bump.outputs["Normal"], p_bsdf.inputs["Normal"])

# ---------- Planet ----------
planet_radius = 1.0
planet = new_sphere("Planet", planet_radius)
planet.data.materials.append(planet_mat)
planet.rotation_euler = (math.radians(12), 0.0, math.radians(-25))

# ---------- Atmosphere shell material (fresnel glow) ----------
atmo_mat = bpy.data.materials.new("AtmosphereGlow")
atmo_mat.use_nodes = True
ant = atmo_mat.node_tree
ant.nodes.clear()

a_out = ant.nodes.new("ShaderNodeOutputMaterial")
a_out.location = (700, 0)
a_mix = ant.nodes.new("ShaderNodeMixShader")
a_mix.location = (450, 0)
a_transp = ant.nodes.new("ShaderNodeBsdfTransparent")
a_transp.location = (250, 120)
a_emit = ant.nodes.new("ShaderNodeEmission")
a_emit.location = (250, -120)
a_emit.inputs["Color"].default_value = (0.35, 0.65, 1.0, 1.0)
a_emit.inputs["Strength"].default_value = 6.0

fresnel = ant.nodes.new("ShaderNodeFresnel")
fresnel.location = (0, 0)
fresnel.inputs["IOR"].default_value = 1.6

ramp_a = ant.nodes.new("ShaderNodeValToRGB")
ramp_a.location = (0, -250)
ramp_a.color_ramp.elements[0].position = 0.55
ramp_a.color_ramp.elements[0].color = (0, 0, 0, 1)
ramp_a.color_ramp.elements[1].position = 1.0
ramp_a.color_ramp.elements[1].color = (1, 1, 1, 1)

ant.links.new(fresnel.outputs["Fac"], ramp_a.inputs["Fac"])
ant.links.new(ramp_a.outputs["Color"], a_mix.inputs["Fac"])
ant.links.new(a_transp.outputs["BSDF"], a_mix.inputs[1])
ant.links.new(a_emit.outputs["Emission"], a_mix.inputs[2])
ant.links.new(a_mix.outputs["Shader"], a_out.inputs["Surface"])

if hasattr(atmo_mat, "surface_render_method"):
    atmo_mat.surface_render_method = "BLENDED"
if hasattr(atmo_mat, "blend_method"):
    try:
        atmo_mat.blend_method = "BLEND"
    except Exception:
        pass
if hasattr(atmo_mat, "use_backface_culling"):
    atmo_mat.use_backface_culling = True

atmo = new_sphere("Atmosphere", planet_radius * 1.06, segments=128, rings=64)
atmo.data.materials.append(atmo_mat)
atmo.visible_shadow = False if hasattr(atmo, "visible_shadow") else None

# ---------- Starfield-like world ----------
world = bpy.data.worlds.new("SpaceWorld")
scene.world = world
world.use_nodes = True
wnt = world.node_tree
bg = wnt.nodes.get("Background")
if bg is None:
    bg = wnt.nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.005, 0.008, 0.02, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="SunLight", type="SUN")
sun_data.energy = 4.0
sun_data.color = (1.0, 0.96, 0.9)
sun = bpy.data.objects.new("SunLight", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0.0, math.radians(35))

rim_data = bpy.data.lights.new(name="RimLight", type="AREA")
rim_data.energy = 300.0
rim_data.color = (0.5, 0.7, 1.0)
rim_data.size = 4.0
rim = bpy.data.objects.new("RimLight", rim_data)
scene.collection.objects.link(rim)
rim.location = (-4.0, 4.0, 2.5)
rim.rotation_euler = (math.radians(60), 0.0, math.radians(-135))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 70.0
cam_data.clip_end = 200.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.0, -4.6, 1.1)

target_pos = mathutils.Vector((0.0, 0.0, 0.0))
direction = target_pos - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

# ---------- Animation range (static scene) ----------
scene.frame_start = 1
scene.frame_end = 1
