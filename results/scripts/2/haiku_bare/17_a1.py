import bpy
import math
from mathutils import Vector

# ---------- Clean scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for item in list(block):
        if item.users == 0:
            block.remove(item)


def smooth_object(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


# ---------- Planet ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.0, location=(0, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
smooth_object(planet)

planet_mat = bpy.data.materials.new("PlanetSurface")
planet_mat.use_nodes = True
pn = planet_mat.node_tree.nodes
pl = planet_mat.node_tree.links
pn.clear()

out = pn.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
bsdf = pn.new("ShaderNodeBsdfPrincipled"); bsdf.location = (600, 0)
texcoord = pn.new("ShaderNodeTexCoord"); texcoord.location = (-900, 0)
noise = pn.new("ShaderNodeTexNoise"); noise.location = (-600, 0)
noise.inputs["Scale"].default_value = 2.2
noise.inputs["Detail"].default_value = 9.0
noise.inputs["Roughness"].default_value = 0.6

ramp = pn.new("ShaderNodeValToRGB"); ramp.location = (-300, 150)
stops = [
    (0.00, (0.02, 0.10, 0.30, 1.0)),   # deep ocean
    (0.42, (0.05, 0.25, 0.45, 1.0)),   # shallow water
    (0.48, (0.76, 0.70, 0.45, 1.0)),   # sand
    (0.60, (0.18, 0.42, 0.14, 1.0)),   # vegetation
    (0.78, (0.40, 0.36, 0.32, 1.0)),   # rock
    (1.00, (0.95, 0.95, 0.97, 1.0)),   # snow
]
els = ramp.color_ramp.elements
els[0].position, els[0].color = stops[0][0], stops[0][1]
for pos, col in stops[1:]:
    e = els.new(pos)
    e.color = col

# Bump for extra surface relief from the same noise field
bump = pn.new("ShaderNodeBump"); bump.location = (-300, -250)
bump.inputs["Strength"].default_value = 0.25
bump.inputs["Distance"].default_value = 0.05

pl.new(texcoord.outputs["Object"], noise.inputs["Vector"])
pl.new(noise.outputs["Fac"], ramp.inputs["Fac"])
pl.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
pl.new(noise.outputs["Fac"], bump.inputs["Height"])
pl.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Roughness"].default_value = 0.72
pl.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

planet.data.materials.append(planet_mat)

# ---------- Atmosphere shell ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.06, location=(0, 0, 0))
atmo = bpy.context.active_object
atmo.name = "Atmosphere"
smooth_object(atmo)
atmo.visible_shadow = False

atmo_mat = bpy.data.materials.new("AtmosphereGlow")
atmo_mat.use_nodes = True
an = atmo_mat.node_tree.nodes
al = atmo_mat.node_tree.links
an.clear()

a_out = an.new("ShaderNodeOutputMaterial"); a_out.location = (800, 0)
mix = an.new("ShaderNodeMixShader"); mix.location = (550, 0)
transp = an.new("ShaderNodeBsdfTransparent"); transp.location = (300, 120)
emit = an.new("ShaderNodeEmission"); emit.location = (300, -120)
emit.inputs["Color"].default_value = (0.35, 0.65, 1.0, 1.0)
emit.inputs["Strength"].default_value = 2.5

layer = an.new("ShaderNodeLayerWeight"); layer.location = (-200, 0)
layer.inputs["Blend"].default_value = 0.35
power = an.new("ShaderNodeMath"); power.location = (0, 0)
power.operation = 'POWER'
power.inputs[1].default_value = 3.5

al.new(layer.outputs["Fresnel"], power.inputs[0])
al.new(power.outputs["Value"], mix.inputs["Fac"])
al.new(transp.outputs["BSDF"], mix.inputs[1])
al.new(emit.outputs["Emission"], mix.inputs[2])
al.new(mix.outputs["Shader"], a_out.inputs["Surface"])

if hasattr(atmo_mat, "surface_render_method"):
    atmo_mat.surface_render_method = 'BLENDED'
if hasattr(atmo_mat, "blend_method"):
    atmo_mat.blend_method = 'BLEND'

atmo.data.materials.append(atmo_mat)

# ---------- World ----------
world = bpy.data.worlds.new("Space")
bpy.context.scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
bg = wn.get("Background") or wn.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.005, 0.007, 0.02, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(4, -5, 3))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 4.5
sun.data.angle = math.radians(1.5)
sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-4, 3, -1))
rim = bpy.context.active_object
rim.name = "RimFill"
rim.data.energy = 300
rim.data.size = 4
rim.data.color = (0.5, 0.7, 1.0)
rim.rotation_euler = (math.radians(70), 0, math.radians(-130))

# ---------- Camera ----------
cam_loc = Vector((0.0, -4.6, 1.0))
bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.active_object
cam.name = "Camera"
cam.data.lens = 50
direction = (Vector((0, 0, 0)) - cam_loc).normalized()
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
