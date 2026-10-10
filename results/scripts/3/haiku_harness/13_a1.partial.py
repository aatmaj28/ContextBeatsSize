import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene

# ---------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    if m.users == 0:
        bpy.data.meshes.remove(m)

# ---------------------------------------------------------------
# Constants
# ---------------------------------------------------------------
TAU = 2.0 * math.pi
R = 1.0          # donut major radius
r = 0.38         # dough minor radius
PLATE_TOP = 0.14
Z0 = PLATE_TOP + r + 0.02   # donut center height

# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
def set_input(bsdf, name, value):
    try:
        bsdf.inputs[name].default_value = value
    except KeyError:
        pass

def make_mat(name, color, rough, coat=0.0, sss=0.0, spec=0.5):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", (color[0], color[1], color[2], 1.0))
    set_input(bsdf, "Roughness", rough)
    set_input(bsdf, "Coat Weight", coat)
    set_input(bsdf, "Subsurface Weight", sss)
    set_input(bsdf, "Specular IOR Level", spec)
    return mat

dough_mat = make_mat("Donut_Dough", (0.80, 0.52, 0.28), 0.60, sss=0.05)
frosting_mat = make_mat("Donut_PinkFrosting", (1.0, 0.42, 0.62), 0.16, coat=0.35)
plate_mat = make_mat("Plate_White", (0.95, 0.95, 0.95), 0.12, coat=0.1)
floor_mat = make_mat("Floor", (0.55, 0.50, 0.46), 0.85)

SPRINKLE_COLORS = [
    (1.00, 0.15, 0.20),   # red
    (0.20, 0.50, 1.00),   # blue
    (1.00, 0.85, 0.10),   # yellow
    (0.20, 0.90, 0.35),   # green
    (0.70, 0.30, 1.00),   # purple
    (1.00, 1.00, 1.00),   # white
]
sprinkle_mats = [make_mat(f"Sprinkle_{i}", c, 0.30, coat=0.2)
                 for i, c in enumerate(SPRINKLE_COLORS)]

# ---------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------
def base_pt(u, v):
    cu, su = math.cos(u), math.sin(u)
    cv, sv = math.cos(v), math.sin(v)
    n = Vector((cv * cu, cv * su, sv))
    p = Vector(((R + r * cv) * cu, (R + r * cv) * su, r * sv))
    return p, n

def frost_pt(u, v):
    p, n = base_pt(u, v)
    nz = n.z
    # Frosting coverage: thick on top, thin underneath
    f = min(max((nz + 0.25) / 1.1, 0.0), 1.0)
    f = f * f * (3.0 - 2.0 * f)
    wave = 0.010 * math.sin(7.0 * u + 2.0 * math.sin(3.0 * v)) \
         + 0.006 * math.sin(13.0 * u + 5.0 * v)
    thick = 0.02 + 0.075 * f + wave * (0.3 + f)
    q = p + n * thick
    # Drips running down the outer side
    outer = max(0.0, math.cos(v)) ** 2
    lower = min(1.0, max(0.0, 0.4 - nz) * 2.0)
    drip_wave = max(0.0, math.sin(6.0 * u + 1.0)) ** 3
    q.z -= 0.09 * drip_wave * outer * lower
    return q, n

def build_torus_bm(fn, nu=96, nv=48):
    bm = bmesh.new()
    grid = []
    for i in range(nu):
        u = TAU * i / nu
        row = []
        for j in range(nv):
            v = TAU * j / nv
            p, _ = fn(u, v)
            row.append(bm.verts.new(p))
        grid.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(nu):
        for j in range(nv):
            a = grid[i][j]
            b = grid[(i + 1) % nu][j]
            c = grid[(i + 1) % nu][(j + 1) % nv]
            d = grid[i][(j + 1) % nv]
            try:
                bm.faces.new((a, b, c, d))
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm

def make_obj(name, bm, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    if mat is not None:
        me.materials.append(mat)
    me.update()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob

def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------
# Donut dough and frosting
# ---------------------------------------------------------------
dough_bm = build_torus_bm(base_pt)
dough = make_obj("Donut_Dough", dough_bm, dough_mat)
dough.location = (0.0, 0.0, Z0)

frost_bm = build_torus_bm(frost_pt)
frosting = make_obj("Donut_Frosting", frost_bm, frosting_mat)
frosting.location = (0.0, 0.0, Z0)

# ---------------------------------------------------------------
# Sprinkles (one mesh per color)
# ---------------------------------------------------------------
sprinkle_bms = [bmesh.new() for _ in SPRINKLE_COLORS]
placed = []
count = 0
tries = 0
TARGET = 130
while count < TARGET and tries < 8000:
    tries += 1
    u = random.uniform(0.0, TAU)
    v = random.uniform(0.0, TAU)
    _, n_base = base_pt(u, v)
    if n_base.z < 0.5:
        continue
    surf, n = frost_pt(u, v)
    pos = surf + n * 0.004

    if any((pos - q).length < 0.13 for q in placed):
        continue

    rv = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
    t = n.cross(rv)
    if t.length < 1e-6:
        continue
    t.normalize()
    y = n.cross(t).normalized()
    x = y.cross(t).normalized()
    M = Matrix((x, y, t)).transposed().to_4x4()
    world_pos = pos + Vector((0.0, 0.0, Z0))
    T = Matrix.Translation(world_pos)
    mtx = T @ M

    L = random.uniform(0.07, 0.10)
    rad = 0.011
    idx = random.randrange(len(SPRINKLE_COLORS))
    bm = sprinkle_bms[idx]
    bmesh.ops.