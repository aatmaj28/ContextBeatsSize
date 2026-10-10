import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene

# ---------------------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_material(name, color, roughness=0.8, emit_strength=0.0):
    """Create a node-based material. Emissive if emit_strength > 0."""
    mat = bpy.data.materials.new(name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    if emit_strength > 0.0:
        em = nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)
        em.inputs["Strength"].default_value = emit_strength
        links.new(em.outputs["Emission"], out.inputs["Surface"])
    else:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def add_object(name, bm, mat, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)):
    """Convert a bmesh into a linked scene object."""
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    return obj


def normalize_radius(bm, radius):
    """Scale a bmesh (centered at origin) so its farthest vertex is 'radius'."""
    maxd = max(v.co.length for v in bm.verts) or 1.0
    for v in bm.verts:
        v.co *= radius / maxd


def make_cone(radius_base, radius_top, depth, segments):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius_base,
        radius2=radius_top,
        depth=depth,
    )
    return bm


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
mat_ground = make_material("Ground", (0.035, 0.03, 0.025), roughness=0.95)
mat_stone = make_material("Stone", (0.24, 0.23, 0.22), roughness=0.9)
mat_log = make_material("Log", (0.20, 0.12, 0.06), roughness=0.75)
mat_char = make_material("CharredLog", (0.06, 0.04, 0.03), roughness=0.85)
mat_flame_outer = make_material("FlameOuter", (1.0, 0.33, 0.05), emit_strength=6.0)
mat_flame_inner = make_material("FlameInner", (1.0, 0.78, 0.25), emit_strength=10.0)
mat_ember = make_material("Ember", (1.0, 0.5, 0.1), emit_strength=25.0)

# ---------------------------------------------------------------------------
# Ground: a dark patch of earth
# ---------------------------------------------------------------------------
bm = bmesh.new()
s = 4.0
corners = [
    bm.verts.new((-s, -s, 0.0)),
    bm.verts.new((s, -s, 0.0)),
    bm.verts.new((s, s, 0.0)),
    bm.verts.new((-s, s, 0.0)),
]
bm.faces.new(corners)
add_object("Ground", bm, mat_ground)

# ---------------------------------------------------------------------------
# Logs: crossed base pair plus a leaning log on top
# ---------------------------------------------------------------------------
LOG_R = 0.075
LOG_L = 1.3


def log_object(name, pos, rot_matrix, mat):
    bm = make_cone(LOG_R, LOG_R * 0.92, LOG_L, 7)
    obj = add_object(name, bm, mat)
    obj.matrix_world = Matrix.Translation(pos) @ rot_matrix
    return obj


rot_along_x = Matrix.Rotation(math.radians(90), 4, 'Y')
rot_along_y = Matrix.Rotation(math.radians(90), 4, 'X')

log_objects = []
log_objects.append(log_object("LogBottomX", Vector((0.0, 0.0, LOG_R)),
                              Matrix.Rotation(math.radians(4), 4, 'Z') @ rot_along_x, mat_log))
log_objects.append(log_object("LogBottomY", Vector((0.0, 0.0, LOG_R * 2.6)),
                              Matrix.Rotation(math.radians(-6), 4, 'Z') @ rot_along_y, mat_char))
log_objects.append(log_object("LogTopX", Vector((0.05, 0.02, LOG_R * 4.2)),
                              Matrix.Rotation(math.radians(12), 4, 'Z') @ rot_along_x, mat_char))

# Leaning log resting across the pile
lean = Matrix.Rotation(math.radians(38), 4, 'X') @ rot_along_y
log_objects.append(log_object("LogLean", Vector((0.0, -0.45, 0.42)),
                              Matrix.Rotation(math.radians(20), 4, 'Z') @ lean, mat_log))

# ---------------------------------------------------------------------------
# Ring of stones
# ---------------------------------------------------------------------------
STONE_COUNT = 12
RING_RADIUS = 0.95
for i in range(STONE_COUNT):
    angle = (i / STONE_COUNT) * math.tau + random.uniform(-0.12, 0.12)
    r = RING_RADIUS + random.uniform(-0.08, 0.08)
    x, y = math.cos(angle) * r, math.sin(angle) * r

    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, calc_uvs=False)
    for v in bm.verts:
        v.co += Vector((random.uniform(-0.12, 0.12),
                        random.uniform(-0.12, 0.12),
                        random.uniform(-0.08, 0.08)))
    normalize_radius(bm, random.uniform(0.17, 0.26))

    add_object(
        f"Stone_{i:02d}", bm, mat_stone,
        location=(x, y, 0.04),
        rotation=(random.uniform(0, math.tau),
                  random.uniform(0, math.tau),
                  random.uniform(0, math.tau)),
        scale=(1.0, 1.0, random.uniform(0.55, 0.75)),
    )

# ---------------------------------------------------------------------------
# Flames: stacked cones, outer orange and inner yellow
# ---------------------------------------------------------------------------
FLAME_BASE_Z = 0.2
flame_layers = [
    # (count, base radius, depth, material, spread)
    (5, 0.22, 0.75, mat_flame_outer, 0.12),
    (4, 0.15, 0.95, mat_flame_outer, 0.08),
    (4, 0.09, 0.60, mat_flame_inner, 0.05),
    (3, 0.05, 0.85, mat_flame_inner, 0.03),
]

flame_index = 0
for count, base_r, depth, mat, spread in flame_layers:
    for i in range(count):
        ang = random.uniform(0, math.tau)
        dist = random.uniform(0, spread)
        ox, oy = math.cos(ang) * dist, math.sin(ang) * dist
        r = base_r * random.uniform(0.85, 1.15)
        d = depth * random.uniform(0.85, 1.15)
        bm = make_cone(r, 0.01, d, 6)
        tilt = Matrix.Rotation(math.radians(random.uniform(-14, 14)), 4, 'X') @ \
               Matrix.Rotation(math.radians(random.uniform(-14, 14)), 4, 'Y')
        flame = add_object(f"Flame_{flame_index:02d}", bm, mat)
        flame.matrix_world = Matrix.Translation(Vector((ox, oy, FLAME_BASE_Z + d * 0.5))) @ tilt
        flame_index += 1

# ---------------------------------------------------------------------------
# A few embers drifting above the fire
# ---------------------------------------------------------------------------
for i in range(14):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, calc_uvs=False)
    normalize_radius(bm, 0.014)
    ang = random.uniform(0, math.tau)
    dist = random.uniform(0.0, 0.25)
    z = random.uniform(0.9, 1.7)
    add_object(
        f"Ember_{i:02d}", bm, mat_ember,
        location=(math.cos(ang) * dist, math.sin(ang) * dist, z),
    )

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
# Main warm fire light above the logs
fire_data = bpy.data.lights.new("FireLight", 'POINT')
fire_data.energy = 160.0
fire_data.color = (1.0, 0.5, 0.18)
fire_data.shadow_soft_size = 0.35
fire_obj = bpy.data.objects.new("FireLight", fire_data)
scene.collection.objects.link(fire_obj)
fire_obj.location = (0.0, 0.0, 0.55)

# Low glow lighting the ground and stones
glow_data = bpy.data.lights.new("GroundGlow", 'POINT')
glow_data.energy = 35.0
glow_data.color = (1.0, 0.4, 0.12)
glow_data.shadow_soft_size = 0.5
glow_obj = bpy.data.objects.new("GroundGlow", glow_data)
scene.collection.objects.link(glow_obj)
glow_obj.location = (0.0, 0.0, 0.15)

# Faint cool moonlight for night ambience
moon_data = bpy.data.lights.new("Moon", 'SUN')
moon_data.energy = 0.6
moon_data.color = (0.55, 0.65, 0.95)
moon_data.angle = math.radians(3.0)
moon_obj = bpy.data.objects.new("Moon", moon_data)
scene.collection.objects.link(moon_obj)
moon_obj.rotation_euler = (math.radians(55), 0.0, math.radians(-35))

# ---------------------------------------------------------------------------
# World: very dark night sky
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("NightWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg is None:
    bg = world.node_tree.nodes.new("ShaderNodeBackground")
    out = world.node_tree.nodes.get("World Output") or world.node_tree.nodes.new("ShaderNodeOutputWorld")
    world.node_tree.links.new(bg.outputs["Background"], out.inputs["Surface"])
bg.inputs["Color"].default_value = (0.012, 0.016, 0.03, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------------------------------------------------------------------------
# Camera framing the fire
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("CampfireCamera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("CampfireCamera", cam_data)
scene.collection.objects.link(cam_obj)

cam_location = Vector((3.2, -3.8, 1.5))
target = Vector((0.0, 0.0, 0.45))
direction = target - cam_location
cam_obj.location = cam_location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj
