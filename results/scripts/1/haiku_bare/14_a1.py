import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------------------------------------------------------------------------
# Clean up default scene content
# ---------------------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
              bpy.data.cameras, bpy.data.worlds):
    for item in list(block):
        if item.users == 0:
            block.remove(item)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def set_input(node, name, value):
    """Set a node input default safely (names vary slightly across versions)."""
    try:
        node.inputs[name].default_value = value
    except (KeyError, TypeError):
        pass


def make_principled(name, base_color, roughness=0.5, specular=0.5,
                    metallic=0.0, ior=1.45):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    set_input(bsdf, "Base Color", (*base_color, 1.0))
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "Metallic", metallic)
    set_input(bsdf, "Specular IOR Level", specular)
    set_input(bsdf, "IOR", ior)
    return mat, nt, bsdf


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def sand_height(x, y):
    """Beach profile: deep sea floor on -Y, dry sand rising on +Y."""
    t = (y + 3.0) / 6.0
    s = smoothstep(t)
    base = -1.2 + 1.5 * s
    # gentle dunes and ripples on land
    dunes = 0.25 * math.sin(x * 0.18) * math.cos(y * 0.12) * max(0.0, s)
    bumps = 0.04 * math.sin(x * 1.3 + y * 0.7) * math.cos(y * 1.1 - x * 0.4)
    return base + dunes + bumps


def make_object(name, bm, location=(0, 0, 0)):
    me = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return obj


def shade_smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


# ---------------------------------------------------------------------------
# Sand ground (displaced grid with a shoreline slope)
# ---------------------------------------------------------------------------
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=140, y_segments=140, size=60.0)
for v in bm.verts:
    v.co.z = sand_height(v.co.x, v.co.y)
sand_obj = make_object("Sand", bm)
shade_smooth(sand_obj)

sand_mat, snt, sbsdf = make_principled("SandMat", (0.8, 0.7, 0.5),
                                       roughness=0.9, specular=0.3)
noise = snt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 45.0
noise.inputs["Detail"].default_value = 8.0
noise.inputs["Roughness"].default_value = 0.6
ramp = snt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = (0.62, 0.48, 0.30, 1.0)
ramp.color_ramp.elements[1].position = 0.75
ramp.color_ramp.elements[1].color = (0.92, 0.84, 0.66, 1.0)
snt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
snt.links.new(ramp.outputs["Color"], sbsdf.inputs["Base Color"])
sand_obj.data.materials.append(sand_mat)


# ---------------------------------------------------------------------------
# Ocean plane (gentle waves, slightly reflective blue)
# ---------------------------------------------------------------------------
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=90, y_segments=90, size=60.0)
for v in bm.verts:
    v.co.z = (0.035 * math.sin(v.co.x * 0.6 + 1.3) * math.cos(v.co.y * 0.45)
              + 0.015 * math.sin(v.co.x * 1.7 - v.co.y * 1.1))
ocean_obj = make_object("Ocean", bm, location=(0, 0, 0))
shade_smooth(ocean_obj)

ocean_mat, ont, obsdf = make_principled("OceanMat", (0.02, 0.13, 0.28),
                                        roughness=0.06, specular=0.85,
                                        ior=1.33)
set_input(obsdf, "Coat Weight", 0.15)
set_input(obsdf, "Coat Roughness", 0.05)
ocean_obj.data.materials.append(ocean_mat)


# ---------------------------------------------------------------------------
# Scattered beach rocks near the waterline
# ---------------------------------------------------------------------------
rock_mat, rnt, rbsdf = make_principled("RockMat", (0.28, 0.25, 0.23),
                                       roughness=0.75, specular=0.4)
rock_noise = rnt.nodes.new("ShaderNodeTexNoise")
rock_noise.inputs["Scale"].default_value = 12.0
rock_noise.inputs["Detail"].default_value = 5.0
rock_ramp = rnt.nodes.new("ShaderNodeValToRGB")
rock_ramp.color_ramp.elements[0].color = (0.12, 0.11, 0.10, 1.0)
rock_ramp.color_ramp.elements[1].color = (0.42, 0.38, 0.34, 1.0)
rnt.links.new(rock_noise.outputs["Fac"], rock_ramp.inputs["Fac"])
rnt.links.new(rock_ramp.outputs["Color"], rbsdf.inputs["Base Color"])

for i in range(14):
    x = random.uniform(-22, 22)
    y = random.uniform(1.0, 7.0)
    scale = random.uniform(0.4, 1.3)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
    for v in bm.verts:
        v.co *= 1.0 + random.uniform(-0.25, 0.25)
        v.co.z *= 0.6
    z = sand_height(x, y)
    rock = make_object("Rock%02d" % i, bm,
                       location=(x, y, z + 0.15 * scale))
    rock.scale = (scale, scale * random.uniform(0.8, 1.2), scale * 0.7)
    rock.rotation_euler = (random.uniform(0, 0.4),
                           random.uniform(0, 0.4),
                           random.uniform(0, math.tau))
    shade_smooth(rock)
    rock.data.materials.append(rock_mat)


# ---------------------------------------------------------------------------
# Sunset sky: world shader gradient (orange horizon -> purple zenith)
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("SunsetSky")
bpy.context.scene.world = world
world.use_nodes = True
wnt = world.node_tree
for node in list(wnt.nodes):
    wnt.nodes.remove(node)

texcoord = wnt.nodes.new("ShaderNodeTexCoord")
separate = wnt.nodes.new("ShaderNodeSeparateXYZ")
sky_ramp = wnt.nodes.new("ShaderNodeValToRGB")
background = wnt.nodes.new("ShaderNodeBackground")
world_out = wnt.nodes.new("ShaderNodeOutputWorld")

wnt.links.new(texcoord.outputs["Generated"], separate.inputs["Vector"])
wnt.links.new(separate.outputs["Z"], sky_ramp.inputs["Fac"])
wnt.links.new(sky_ramp.outputs["Color"], background.inputs["Color"])
wnt.links.new(background.outputs["Background"], world_out.inputs["Surface"])

# Build colour stops along generated Z (-1 bottom .. 1 top, horizon ~0.5)
elements = sky_ramp.color_ramp.elements
elements[0].position = 0.0
elements[0].color = (0.05, 0.03, 0.12, 1.0)
elements[1].position = 1.0
elements[1].color = (0.12, 0.05, 0.25, 1.0)

stops = [
    (0.36, (0.30, 0.10, 0.40)),   # purple band
    (0.47, (0.85, 0.30, 0.35)),   # rose just above horizon
    (0.51, (1.00, 0.55, 0.22)),   # hot orange at horizon
    (0.60, (0.75, 0.25, 0.35)),   # fading into magenta
    (0.80, (0.35, 0.12, 0.42)),   # violet
]
for pos, col in stops:
    el = elements.new(pos)
    el.color = (*col, 1.0)
elements.sort(key=lambda e: e.position) if hasattr(elements, "sort") else None

background.inputs["Strength"].default_value = 1.1


# ---------------------------------------------------------------------------
# Sun light (low, warm, behind the ocean)
# ---------------------------------------------------------------------------
sun_data = bpy.data.lights.new("SunsetSun", type='SUN')
sun_data.energy = 4.5
sun_data.color = (1.0, 0.62, 0.35)
sun_data.angle = math.radians(1.5)
sun_obj = bpy.data.objects.new("SunsetSun", sun_data)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(-75), 0.0, math.radians(8))

# Soft fill from the sky so shadows are not pitch black
fill_data = bpy.data.lights.new("SkyFill", type='AREA')
fill_data.energy = 120.0
fill_data.color = (0.7, 0.6, 0.9)
fill_data.size = 30.0
fill_obj = bpy.data.objects.new("SkyFill", fill_data)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = (0.0, 20.0, 25.0)
fill_obj.rotation_euler = (math.radians(-35), 0.0, math.radians(180))


# ---------------------------------------------------------------------------
# Camera framing the shoreline and the sunset
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("BeachCam")
cam_data.lens = 35.0
cam_data.clip_end = 500.0
cam_obj = bpy.data.objects.new("BeachCam", cam_data)
bpy.context.collection.objects.link(cam_obj)

cam_loc = Vector((5.0, 12.0, 2.4))
target = Vector((0.0, -8.0, 1.2))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam_obj


# ---------------------------------------------------------------------------
# Scene settings (no rendering / saving)
# ---------------------------------------------------------------------------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
