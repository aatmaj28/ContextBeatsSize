import bpy
import math
import mathutils

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene

# ---------- Helpers ----------
def smooth_shade(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True

def make_planet_material():
    mat = bpy.data.materials.new("PlanetSurface")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-1100, 0)

    # Large-scale continent noise -> color ramp
    noise_color = nodes.new("ShaderNodeTexNoise")
    noise_color.location = (-800, 200)
    noise_color.inputs["Scale"].default_value = 2.5
    noise_color.inputs["Detail"].default_value = 9.0
    noise_color.inputs["Roughness"].default_value = 0.55
    links.new(tex_coord.outputs["Object"], noise_color.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (-450, 200)
    cr = ramp.color_ramp
    cr.elements[0].position = 0.38
    cr.elements[0].color = (0.05, 0.15, 0.35, 1.0)   # deep ocean-ish
    cr.elements[1].position = 0.62
    cr.elements[1].color = (0.45, 0.32, 0.18, 1.0)   # rocky land
    extra = cr.elements.new(0.80)
    extra.color = (0.85, 0.82, 0.78, 1.0)            # highland / ice tint
    links.new(noise_color.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    # Roughness variation
    noise_rough = nodes.new("ShaderNodeTexNoise")
    noise_rough.location = (-800, -150)
    noise_rough.inputs["Scale"].default_value = 6.0
    noise_rough.inputs["Detail"].default_value = 4.0
    links.new(tex_coord.outputs["Object"], noise_rough.inputs["Vector"])
    rough_map = nodes.new("ShaderNodeMapRange")
    rough_map.location = (-450, -150)
    rough_map.inputs["To Min"].default_value = 0.35
    rough_map.inputs["To Max"].default_value = 0.85
    links.new(noise_rough.outputs["Fac"], rough_map.inputs["Value"])
    links.new(rough_map.outputs["Result"], bsdf.inputs["Roughness"])

    # Fine bump detail
    noise_bump = nodes.new("ShaderNodeTexNoise")
    noise_bump.location = (-800, -450)
    noise_bump.inputs["Scale"].default_value = 18.0
    noise_bump.inputs["Detail"].default_value = 12.0
    links.new(tex_coord.outputs["Object"], noise_bump.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.location = (-450, -450)
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.05
    links.new(noise_bump.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    return mat

def make_atmosphere_material():
    mat = bpy.data.materials.new("AtmosphereGlow")
    mat.use_nodes = True
    try:
        mat.surface_render_method = 'BLENDED'
    except Exception:
        pass
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (700, 0)

    layer = nodes.new("ShaderNodeLayerWeight")
    layer.location = (-300, 0)
    layer.inputs["Blend"].default_value = 0.35

    # Glow: emission concentrated at the limb
    emission = nodes.new("ShaderNodeEmission")
    emission.location = (100, 120)
    emission.inputs["Color"].default_value = (0.35, 0.65, 1.0, 1.0)
    emission.inputs["Strength"].default_value = 6.0

    transparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent.location = (100, -120)

    mix = nodes.new("ShaderNodeMixShader")
    mix.location = (400, 0)

    links.new(layer.outputs["Fresnel"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])

    return mat

# ---------- Planet ----------
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=128, ring_count=64, radius=1.0, location=(0, 0, 0)
)
planet = bpy.context.active_object
planet.name = "Planet"
smooth_shade(planet)
planet.data.materials.append(make_planet_material())

# ---------- Atmosphere shell ----------
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=96, ring_count=48, radius=1.06, location=(0, 0, 0)
)
atmo = bpy.context.active_object
atmo.name = "Atmosphere"
smooth_shade(atmo)
atmo.data.materials.append(make_atmosphere_material())
try:
    atmo.visible_shadow = False
except Exception:
    pass

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(4, -6, 5))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 4.0
sun.data.angle = math.radians(3.0)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(35))

# Soft cool rim light from behind for atmosphere separation
bpy.ops.object.light_add(type='AREA', location=(-4, 5, 2))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 300.0
rim.data.color = (0.5, 0.75, 1.0)
rim.data.size = 4.0
rim.rotation_euler = (math.radians(60), 0, math.radians(-135))

# ---------- World ----------
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1.0)
    bg.inputs["Strength"].default_value = 0.6

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 70.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_loc = mathutils.Vector((0.0, -4.6, 1.2))
cam_obj.location = cam_loc
target = mathutils.Vector((0.0, 0.0, 0.0))
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- Render settings (no rendering performed) ----------
scene.frame_start = 1
scene.frame_end = 1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
