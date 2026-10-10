import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ---------- Clean up any existing objects ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1


def make_sphere_object(name, radius, segments=96, rings=48):
    """Create a smooth UV sphere object using bmesh."""
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm, u_segments=segments, v_segments=rings, radius=radius
    )
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    return obj


# ---------- Planet surface material ----------
planet_mat = bpy.data.materials.new("PlanetSurface")
nt = planet_mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()

out = nodes.new("ShaderNodeOutputMaterial")
out.location = (900, 0)
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
bsdf.location = (600, 0)
bsdf.inputs["Roughness"].default_value = 0.8
links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

texcoord = nodes.new("ShaderNodeTexCoord")
texcoord.location = (-900, 0)

noise = nodes.new("ShaderNodeTexNoise")
noise.location = (-500, 0)
noise.inputs["Scale"].default_value = 3.0
noise.inputs["Detail"].default_value = 8.0
noise.inputs["Roughness"].default_value = 0.55
links.new(texcoord.outputs["Object"], noise.inputs["Vector"])

ramp = nodes.new("ShaderNodeValToRGB")
ramp.location = (-200, 100)
cr = ramp.color_ramp
# Deep ocean -> land -> highlands -> ice
cr.elements[0].position = 0.38
cr.elements[0].color = (0.02, 0.10, 0.35, 1.0)
cr.elements[1].position = 0.62
cr.elements[1].color = (0.25, 0.42, 0.14, 1.0)
highland = cr.elements.new(0.78)
highland.color = (0.45, 0.36, 0.25, 1.0)
links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

bump = nodes.new("ShaderNodeBump")
bump.location = (-200, -250)
bump.inputs["Strength"].default_value = 0.15
bump.inputs["Distance"].default_value = 0.05
links.new(noise.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

planet = make_sphere_object("Planet", 1.0)
planet.data.materials.append(planet_mat)

# ---------- Atmosphere shell material ----------
atmo_mat = bpy.data.materials.new("AtmosphereGlow")
at = atmo_mat.node_tree
an = at.nodes
al = at.links
an.clear()

a_out = an.new("ShaderNodeOutputMaterial")
a_out.location = (800, 0)
mix = an.new("ShaderNodeMixShader")
mix.location = (550, 0)
transp = an.new("ShaderNodeBsdfTransparent")
transp.location = (300, 150)
emit = an.new("ShaderNodeEmission")
emit.location = (300, -150)
emit.inputs["Color"].default_value = (0.35, 0.65, 1.0, 1.0)
emit.inputs["Strength"].default_value = 3.0
fresnel = an.new("ShaderNodeFresnel")
fresnel.location = (300, -350)
fresnel.inputs["IOR"].default_value = 1.35

# Fresnel is high at grazing angles (the limb), so the rim gets the glow
al.new(fresnel.outputs["Fac"], mix.inputs["Fac"])
al.new(transp.outputs["BSDF"], mix.inputs[1])
al.new(emit.outputs["Emission"], mix.inputs[2])
al.new(mix.outputs["Shader"], a_out.inputs["Surface"])

atmo_mat.surface_render_method = 'BLENDED'

atmo = make_sphere_object("Atmosphere", 1.06, segments=96, rings=48)
atmo.data.materials.append(atmo_mat)
atmo.visible_shadow = False

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("SunLight", type='SUN')
sun_data.energy = 4.0
sun_data.angle = math.radians(0.5)
sun = bpy.data.objects.new("SunLight", sun_data)
scene.collection.objects.link(sun)
sun.location = (4, -5, 4)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(35))

rim_data = bpy.data.lights.new("RimLight", type='AREA')
rim_data.energy = 300.0
rim_data.color = (0.5, 0.7, 1.0)
rim_data.size = 3.0
rim = bpy.data.objects.new("RimLight", rim_data)
scene.collection.objects.link(rim)
rim.location = (-4, 4, 1.5)
rim.rotation_euler = (math.radians(70), 0.0, math.radians(-135))

# ---------- World ----------
world = bpy.data.worlds.new("SpaceWorld")
scene.world = world
wn = world.node_tree.nodes
bg = wn.get("Background")
if bg is None:
    bg = next(n for n in wn if n.type == 'BACKGROUND')
bg.inputs["Color"].default_value = (0.005, 0.006, 0.012, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("PlanetCamera")
cam_data.lens = 85.0
cam = bpy.data.objects.new("PlanetCamera", cam_data)
scene.collection.objects.link(cam)

cam_loc = Vector((0.0, -4.6, 1.1))
cam.location = cam_loc
# Point the camera's -Z axis toward the planet center
direction = (Vector((0.0, 0.0, 0.0)) - cam_loc).normalized()
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
