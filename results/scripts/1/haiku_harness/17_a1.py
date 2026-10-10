import bpy
import bmesh
import math
import random
from mathutils import Vector, Euler

random.seed(7)

# ---------- Clean the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    pass

# ---------- World ----------
world = bpy.data.worlds.new("SpaceWorld")
scene.world = world
wnodes = world.node_tree.nodes
wbg = wnodes.get("Background")
if wbg:
    wbg.inputs["Color"].default_value = (0.01, 0.012, 0.025, 1.0)
    wbg.inputs["Strength"].default_value = 0.5

# ---------- Planet surface material (procedural noise) ----------
planet_mat = bpy.data.materials.new("PlanetSurface")
pn = planet_mat.node_tree.nodes
pl = planet_mat.node_tree.links
pn.clear()

texcoord = pn.new("ShaderNodeTexCoord")
texcoord.location = (-900, 0)

noise_color = pn.new("ShaderNodeTexNoise")
noise_color.location = (-650, 200)
noise_color.inputs["Scale"].default_value = 3.0
noise_color.inputs["Detail"].default_value = 8.0
noise_color.inputs["Roughness"].default_value = 0.6

ramp = pn.new("ShaderNodeValToRGB")
ramp.location = (-400, 200)
cr = ramp.color_ramp
cr.elements[0].position = 0.35
cr.elements[0].color = (0.05, 0.22, 0.06, 1.0)     # deep green lowlands
cr.elements[1].position = 0.75
cr.elements[1].color = (0.45, 0.36, 0.22, 1.0)     # brown highlands
mid = cr.elements.new(0.55)
mid.color = (0.14, 0.32, 0.10, 1.0)                 # grassland

noise_bump = pn.new("ShaderNodeTexNoise")
noise_bump.location = (-650, -200)
noise_bump.inputs["Scale"].default_value = 9.0
noise_bump.inputs["Detail"].default_value = 12.0
noise_bump.inputs["Roughness"].default_value = 0.55

bump = pn.new("ShaderNodeBump")
bump.location = (-300, -250)
bump.inputs["Strength"].default_value = 0.25
bump.inputs["Distance"].default_value = 0.02

principled_p = pn.get("Principled BSDF") or pn.new("ShaderNodeBsdfPrincipled")
principled_p.location = (0, 0)
principled_p.inputs["Roughness"].default_value = 0.85
principled_p.inputs["Specular IOR Level"].default_value = 0.35

out_p = pn.get("Material Output") or pn.new("ShaderNodeOutputMaterial")
out_p.location = (250, 0)

pl.new(texcoord.outputs["Object"], noise_color.inputs["Vector"])
pl.new(noise_color.outputs["Fac"], ramp.inputs["Fac"])
pl.new(ramp.outputs["Color"], principled_p.inputs["Base Color"])
pl.new(texcoord.outputs["Object"], noise_bump.inputs["Vector"])
pl.new(noise_bump.outputs["Fac"], bump.inputs["Height"])
pl.new(bump.outputs["Normal"], principled_p.inputs["Normal"])
pl.new(principled_p.outputs["BSDF"], out_p.inputs["Surface"])

# ---------- Atmosphere material (thin glowing rim) ----------
atmo_mat = bpy.data.materials.new("AtmosphereGlow")
an = atmo_mat.node_tree.nodes
al = atmo_mat.node_tree.links
an.clear()

layer = an.new("ShaderNodeLayerWeight")
layer.location = (-400, 0)
layer.inputs["Blend"].default_value = 0.25

transp = an.new("ShaderNodeBsdfTransparent")
transp.location = (-100, 120)

emit = an.new("ShaderNodeEmission")
emit.location = (-100, -120)
emit.inputs["Color"].default_value = (0.35, 0.65, 1.0, 1.0)
emit.inputs["Strength"].default_value = 4.0

mix = an.new("ShaderNodeMixShader")
mix.location = (120, 0)

out_a = an.new("ShaderNodeOutputMaterial")
out_a.location = (330, 0)

al.new(layer.outputs["Fresnel"], mix.inputs["Fac"])
al.new(transp.outputs["BSDF"], mix.inputs[1])
al.new(emit.outputs["Emission"], mix.inputs[2])
al.new(mix.outputs["Shader"], out_a.inputs["Surface"])

try:
    atmo_mat.surface_render_method = 'BLENDED'
except Exception:
    pass

# ---------- Geometry ----------
def add_sphere(name, radius, segments=128, rings=64):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = name
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj

planet = add_sphere("Planet", 1.0)
planet.data.materials.append(planet_mat)
planet.rotation_euler = Euler((math.radians(12), 0, math.radians(-20)), 'XYZ')

atmo = add_sphere("Atmosphere", 1.06, segments=128, rings=64)
atmo.data.materials.append(atmo_mat)
atmo.rotation_euler = planet.rotation_euler

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 4.0
sun_data.angle = math.radians(3)
sun = bpy.data.objects.new("KeySun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = Euler((math.radians(55), 0, math.radians(35)), 'XYZ')

rim_data = bpy.data.lights.new("RimFill", 'AREA')
rim_data.energy = 300.0
rim_data.size = 4.0
rim = bpy.data.objects.new("RimFill", rim_data)
scene.collection.objects.link(rim)
rim.location = (-4.0, 4.0, 2.0)
rim.rotation_euler = Euler((math.radians(60), 0, math.radians(-135)), 'XYZ')

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 70
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((0.0, -4.6, 1.2))

target = Vector((0.0, 0.0, 0.0))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Output settings ----------
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
