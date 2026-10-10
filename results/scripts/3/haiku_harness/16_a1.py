import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene

# ---------------------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------------------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def make_principled(name, base, roughness=0.5, transmission=0.0, ior=1.45,
                    emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", base)
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "IOR", ior)
    set_input(bsdf, "Transmission Weight", transmission)
    if emission is not None:
        set_input(bsdf, "Emission Color", emission)
        set_input(bsdf, "Emission Strength", emission_strength)
    return mat


def link_obj(ob):
    scene.collection.objects.link(ob)
    return ob


def mesh_object(name, bm, mat=None, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.update()
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        ob.data.materials.append(mat)
    return link_obj(ob)


def look_at(ob, target):
    direction = Vector(target) - ob.location
    ob.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
rock_mat = make_principled("DarkRock", (0.055, 0.05, 0.06, 1.0), roughness=0.88)

ground_mat = make_principled("GroundRock", (0.02, 0.018, 0.022, 1.0), roughness=0.95)

crystal_mat = make_principled(
    "PurpleCrystal",
    (0.55, 0.22, 0.95, 1.0),
    roughness=0.04,
    transmission=1.0,
    ior=1.5,
    emission=(0.6, 0.2, 1.0, 1.0),
    emission_strength=0.15,
)

# ---------------------------------------------------------------------------
# Rock (noisy ellipsoid)
# ---------------------------------------------------------------------------
RX, RY, RZ = 2.0, 1.6, 0.9

bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
for v in bm.verts:
    x, y, z = v.co
    n = (1.0
         + 0.12 * math.sin(3.1 * x + 1.3 * y) * math.cos(2.7 * z)
         + 0.07 * math.sin(6.3 * x - 4.7 * y + 2.1 * z)
         + random.uniform(-0.03, 0.03))
    v.co = v.co * n
bmesh.ops.scale(bm, vec=(RX, RY, RZ), verts=bm.verts)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
rock = mesh_object("Rock", bm, rock_mat, smooth=True)


def surf_z(x, y):
    """Approximate top surface height of the rock at (x, y)."""
    t = 1.0 - (x / RX) ** 2 - (y / RY) ** 2
    return RZ * math.sqrt(max(0.0, t))


# ---------------------------------------------------------------------------
# Ground disc
# ---------------------------------------------------------------------------
bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, radius=7.0, segments=64)
bmesh.ops.translate(bm, vec=(0.0, 0.0, -0.95), verts=bm.verts)
ground = mesh_object("Ground", bm, ground_mat)


# ---------------------------------------------------------------------------
# Crystals
# ---------------------------------------------------------------------------
def build_crystal_bmesh(radius, height, tip_height, sides=6):
    """Hexagonal prism with a pointed tip. Base sits at z = 0."""
    bm = bmesh.new()
    base, mid = [], []
    for i in range(sides):
        a = 2.0 * math.pi * i / sides
        c, s = math.cos(a), math.sin(a)
        base.append(bm.verts.new((radius * c, radius * s, 0.0)))
        mid.append(bm.verts.new((radius * c * 0.98, radius * s * 0.98, height)))
    tip = bm.verts.new((0.0, 0.0, height + tip_height))

    bm.faces.new(list(reversed(base)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((base[i], base[j], mid[j], mid[i]))
        bm.faces.new((mid[i], mid[j], tip))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


placed = []
attempts = 0
target_count = 19
while len(placed) < target_count and attempts < 2000:
    attempts += 1
    # Bias toward the center to form a tight cluster
    x = random.gauss(0.0, 0.55)
    y = random.gauss(0.0, 0.45)
    if (x / RX) ** 2 + (y / RY) ** 2 > 0.42:
        continue
    # Keep crystals reasonably apart
    r = random.uniform(0.11, 0.2)
    ok = True
    for (px, py, pr) in placed:
        if math.hypot(x - px, y - py) < (r + pr) * 0.8:
            ok = False
            break
    if not ok:
        continue
    placed.append((x, y, r))

for idx, (x, y, r) in enumerate(placed):
    # Taller crystals near the center
    center_factor = 1.0 - min(1.0, math.hypot(x, y) / 1.2)
    h = random.uniform(0.35, 0.7) + 0.35 * center_factor
    tip = h * random.uniform(0.35, 0.5)

    bm = build_crystal_bmesh(r, h, tip)
    ob = mesh_object(f"Crystal_{idx:02d}", bm, crystal_mat)

    ob.location = (x, y, surf_z(x, y) - 0.06)
    # Lean outward from the cluster center with some random variation
    phi = math.atan2(y, x) if (x or y) else random.uniform(0, 2 * math.pi)
    lean = random.uniform(0.12, 0.32)
    ob.rotation_euler = (
        lean * math.sin(phi) + random.uniform(-0.08, 0.08),
        -lean * math.cos(phi) + random.uniform(-0.08, 0.08),
        random.uniform(0.0, 2.0 * math.pi),
    )


# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
def add_light(name, light_type, loc, energy, color, size=None):
    ld = bpy.data.lights.new(name, light_type)
    ld.energy = energy
    ld.color = color
    if size is not None and light_type == 'AREA':
        ld.size = size
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    link_obj(ob)
    look_at(ob, (0.0, 0.0, 0.3))
    return ob


add_light("KeyLight", 'AREA', (-4.0, -5.0, 5.0), 900.0, (1.0, 0.95, 0.9), size=3.0)
add_light("PurpleRim", 'AREA', (4.5, 3.5, 3.0), 700.0, (0.7, 0.4, 1.0), size=2.0)
add_light("FillLight", 'POINT', (3.0, -4.0, 1.0), 180.0, (0.9, 0.9, 1.0))
add_light("TopLight", 'AREA', (0.0, 0.5, 6.0), 400.0, (1.0, 1.0, 1.0), size=2.5)

# ---------------------------------------------------------------------------
# World: very dark background
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("DarkWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg is not None:
    set_input(bg, "Color", (0.008, 0.006, 0.012, 1.0))
    set_input(bg, "Strength", 1.0)

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 70.0
cam_ob = bpy.data.objects.new("Camera", cam_data)
cam_ob.location = (4.8, -6.4, 3.0)
link_obj(cam_ob)
look_at(cam_ob, (0.0, 0.0, 0.35))
scene.camera = cam_ob

# Static scene
scene.frame_start = 1
scene.frame_end = 1
