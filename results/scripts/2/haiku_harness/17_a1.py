import bpy
import math
from mathutils import Vector


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def new_node(nodes, node_type, location):
    node = nodes.new(type=node_type)
    node.location = location
    return node


def build_planet_material():
    mat = bpy.data.materials.new("PlanetSurface")
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = new_node(nodes, "ShaderNodeOutputMaterial", (900, 0))
    bsdf = new_node(nodes, "ShaderNodeBsdfPrincipled", (600, 0))
    bsdf.inputs["Roughness"].default_value = 0.65
    bsdf.inputs["Specular IOR Level"].default_value = 0.4

    coords = new_node(nodes, "ShaderNodeTexCoord", (-900, 0))

    # Continental / terrain color noise
    noise_color = new_node(nodes, "ShaderNodeTexNoise", (-500, 200))
    noise_color.inputs["Scale"].default_value = 3.2
    noise_color.inputs["Detail"].default_value = 9.0
    noise_color.inputs["Roughness"].default_value = 0.55

    ramp = new_node(nodes, "ShaderNodeValToRGB", (-200, 200))
    cr = ramp.color_ramp
    cr.elements[0].position = 0.42
    cr.elements[0].color = (0.02, 0.10, 0.30, 1.0)   # deep ocean
    cr.elements[1].position = 0.52
    cr.elements[1].color = (0.12, 0.38, 0.12, 1.0)   # lowland green
    e = cr.elements.new(0.66)
    e.color = (0.42, 0.33, 0.20, 1.0)                # highland brown
    e = cr.elements.new(0.84)
    e.color = (0.85, 0.85, 0.88, 1.0)                # snowy peaks

    # Fine bump noise for surface relief
    noise_bump = new_node(nodes, "ShaderNodeTexNoise", (-500, -250))
    noise_bump.inputs["Scale"].default_value = 14.0
    noise_bump.inputs["Detail"].default_value = 6.0
    noise_bump.inputs["Roughness"].default_value = 0.6

    bump = new_node(nodes, "ShaderNodeBump", (-200, -250))
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.04

    links.new(coords.outputs["Object"], noise_color.inputs["Vector"])
    links.new(noise_color.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    links.new(coords.outputs["Object"], noise_bump.inputs["Vector"])
    links.new(noise_bump.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def build_atmosphere_material():
    mat = bpy.data.materials.new("AtmosphereGlow")
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = new_node(nodes, "ShaderNodeOutputMaterial", (700, 0))
    mix = new_node(nodes, "ShaderNodeMixShader", (450, 0))
    transparent = new_node(nodes, "ShaderNodeBsdfTransparent", (250, 120))
    emission = new_node(nodes, "ShaderNodeEmission", (250, -120))
    emission.inputs["Color"].default_value = (0.35, 0.65, 1.0, 1.0)
    emission.inputs["Strength"].default_value = 3.5

    fresnel = new_node(nodes, "ShaderNodeLayerWeight", (-250, 0))
    fresnel.inputs["Blend"].default_value = 0.0

    power = new_node(nodes, "ShaderNodeMath", (-50, 0))
    power.operation = "POWER"
    power.inputs[1].default_value = 3.0

    links.new(fresnel.outputs["Fresnel"], power.inputs[0])
    links.new(power.outputs["Value"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])

    mat.blend_method = "BLEND" if hasattr(mat, "blend_method") else mat.blend_method
    return mat


def setup_world():
    world = bpy.data.worlds.new("DeepSpace")
    bpy.context.scene.world = world
    nt = world.node_tree
    bg = None
    for node in nt.nodes:
        if node.type == "BACKGROUND":
            bg = node
            break
    if bg is None:
        bg = nt.nodes.new("ShaderNodeBackground")
        out = nt.nodes.get("World Output") or nt.nodes.new("ShaderNodeOutputWorld")
        nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs["Color"].default_value = (0.004, 0.005, 0.012, 1.0)
    bg.inputs["Strength"].default_value = 1.0


def add_lights():
    sun_data = bpy.data.lights.new(name="SunLight", type="SUN")
    sun_data.energy = 4.0
    sun_data.angle = math.radians(1.5)
    sun = bpy.data.objects.new("SunLight", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), 0.0, math.radians(-35))

    fill_data = bpy.data.lights.new(name="FillLight", type="AREA")
    fill_data.energy = 60.0
    fill_data.size = 6.0
    fill_data.color = (0.6, 0.75, 1.0)
    fill = bpy.data.objects.new("FillLight", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (-5.0, -3.0, 2.5)
    fill.rotation_euler = (math.radians(65), 0.0, math.radians(-120))


def add_camera(target):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 65.0
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (0.0, -5.6, 1.1)
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def main():
    clear_scene()
    setup_world()

    planet_mat = build_planet_material()
    atmo_mat = build_atmosphere_material()

    bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.0, location=(0, 0, 0))
    planet = bpy.context.active_object
    planet.name = "Planet"
    bpy.ops.object.shade_smooth()
    planet.data.materials.append(planet_mat)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.06, location=(0, 0, 0))
    atmo = bpy.context.active_object
    atmo.name = "Atmosphere"
    bpy.ops.object.shade_smooth()
    atmo.data.materials.append(atmo_mat)
    atmo.visible_shadow = False

    add_lights()
    add_camera((0.0, 0.0, 0.0))

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 1


main()
