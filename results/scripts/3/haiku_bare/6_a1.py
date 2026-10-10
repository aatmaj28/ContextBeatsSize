import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene

# ---------------------------------------------------------------- clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

# ---------------------------------------------------------------- materials
def make_mat(name, color, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return m

MAT_LIGHT = make_mat("LightWood", (0.80, 0.62, 0.42), 0.45)
MAT_DARK = make_mat("DarkWood", (0.28, 0.14, 0.07), 0.45)
MAT_BASE = make_mat("WalnutBase", (0.15, 0.08, 0.04), 0.55)
MAT_WHITE = make_mat("IvoryPiece", (0.92, 0.89, 0.82), 0.30)
MAT_BLACK = make_mat("EbonyPiece", (0.05, 0.05, 0.06), 0.22)

# ---------------------------------------------------------------- geometry helpers
def box_geo(sx, sy, sz, cx=0.0, cy=0.0, cz=0.0):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    corners = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
               (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    V = [(cx + x, cy + y, cz + z) for x, y, z in corners]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return V, F


def lathe_geo(profile, seg=28, ox=0.0, oy=0.0, oz=0.0):
    """Surface of revolution. profile = list of (radius, z) from bottom to top."""
    V = []
    idx = []
    for r, z in profile:
        if r < 1e-6:
            V.append((ox, oy, oz + z))
            idx.append([len(V) - 1] * seg)
        else:
            row = []
            for s in range(seg):
                a = 2 * math.pi * s / seg
                V.append((ox + r * math.cos(a), oy + r * math.sin(a), oz + z))
                row.append(len(V) - 1)
            idx.append(row)
    F = []
    for i in range(len(idx) - 1):
        for s in range(seg):
            q = (idx[i][s], idx[i][(s + 1) % seg],
                 idx[i + 1][(s + 1) % seg], idx[i + 1][s])
            f = tuple(dict.fromkeys(q))
            if len(f) >= 3:
                F.append(f)
    return V, F


def sphere_geo(r, cx, cy, cz, seg=20, rings=10):
    prof = []
    for k in range(rings):
        t = math.pi - math.pi * k / (rings - 1)
        prof.append((r * math.sin(t), r * math.cos(t)))
    return lathe_geo(prof, seg, cx, cy, cz)


def merge(parts):
    V, F = [], []
    for v, f in parts:
        off = len(V)
        V.extend(v)
        F.extend([tuple(i + off for i in face) for face in f])
    return V, F


def add_obj(name, V, F, mat, loc=(0, 0, 0), rz=0.0, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = (0.0, 0.0, rz)
    scene.collection.objects.link(ob)
    return ob

# ---------------------------------------------------------------- board
SQ = 1.0
BOARD_TOP = 0.06

light_parts, dark_parts = [], []
for f in range(8):
    for r in range(8):
        x = f - 3.5
        y = r - 3.5
        part = box_geo(SQ * 0.99, SQ * 0.99, BOARD_TOP, x, y, BOARD_TOP / 2)
        if (f + r) % 2 == 0:
            dark_parts.append(part)
        else:
            light_parts.append(part)

V, F = merge(light_parts)
add_obj("SquaresLight", V, F, MAT_LIGHT, smooth=False)
V, F = merge(dark_parts)
add_obj("SquaresDark", V, F, MAT_DARK, smooth=False)

rim = [
    box_geo(8.8, 0.4, 0.10, 0, 4.2, 0.05),
    box_geo(8.8, 0.4, 0.10, 0, -4.2, 0.05),
    box_geo(0.4, 8.0, 0.10, 4.2, 0, 0.05),
    box_geo(0.4, 8.0, 0.10, -4.2, 0, 0.05),
]
V, F = merge(rim)
add_obj("BoardRim", V, F, MAT_BASE, smooth=False)

V, F = box_geo(9.2, 9.2, 0.4, 0, 0, -0.2)
add_obj("BoardBase", V, F, MAT_BASE, smooth=False)

# ---------------------------------------------------------------- piece builders
PAWN_BODY = [(0, 0), (0.32, 0), (0.32, 0.05), (0.22, 0.12), (0.13, 0.25),
             (0.10, 0.36), (0.17, 0.42), (0.13, 0.48), (0, 0.48)]
ROOK_BODY = [(0, 0), (0.33, 0), (0.33, 0.06), (0.25, 0.14), (0.21, 0.24),
             (0.23, 0.60), (0.28, 0.66), (0, 0.66)]
BISHOP_BODY = [(0, 0), (0.32, 0), (0.32, 0.06), (0.20, 0.14), (0.12, 0.28),
               (0.15, 0.42), (0.10, 0.55), (0.12, 0.62), (0.06, 0.70), (0, 0.74)]
QUEEN_BODY = [(0, 0), (0.34, 0), (0.34, 0.07), (0.22, 0.15), (0.13, 0.30),
              (0.14, 0.45), (0.26, 0.70), (0.22, 0.78), (0.12, 0.80), (0, 0.80)]
KING_BODY = [(0, 0), (0.34, 0), (0.34, 0.07), (0.22, 0.15), (0.13, 0.30),
             (0.14, 0.46), (0.25, 0.72), (0.20, 0.80), (0.10, 0.82), (0, 0.82)]
KNIGHT_BASE = [(0, 0), (0.30, 0), (0.30, 0.06), (0.20, 0.14), (0.16, 0.25), (0, 0.25)]


def pawn_parts():
    return [lathe_geo(PAWN_BODY), sphere_geo(0.15, 0, 0, 0.60)]


def rook_parts():
    parts = [lathe_geo(ROOK_BODY)]
    for dx, dy in [(0.16, 0), (-0.16, 0), (0, 0.16), (0, -0.16)]:
        parts.append(box_geo(0.13, 0.13, 0.16, dx, dy, 0.74))
    return parts


def bishop_parts():
    return [lathe_geo(BISHOP_BODY), sphere_geo(0.065, 0, 0, 0.80)]


def queen_parts():
    parts = [lathe_geo(QUEEN_BODY)]
    for k in range(6):
        a = 2 * math.pi * k / 6
        parts.append(sphere_geo(0.07, 0.19 * math.cos(a), 0.19 * math.sin(a), 0.82))
    parts.append(sphere_geo(0.09, 0, 0, 0.90))
    return parts


def king_parts():
    return [
        lathe_geo(KING_BODY),
        box_geo(0.07, 0.07, 0.30, 0, 0, 0.97),
        box_geo(0.22, 0.07, 0.07, 0, 0, 1.02),
    ]


def knight_parts():
    return [
        lathe_geo(KNIGHT_BASE),
        box_geo(0.24, 0.24, 0.42, 0, 0, 0.45),      # neck
        box_geo(0.20, 0.44, 0.24, 0, 0.06, 0.76),   # head
        box_geo(0.16, 0.18, 0.20, 0, 0.30, 0.70),   # muzzle
        box_geo(0.08, 0.12, 0.12, 0, -0.12, 1.00),  # ear
    ]


BUILDERS = {
    'P': pawn_parts, 'R': rook_parts, 'B': bishop_parts,
    'Q': queen_parts, 'K': king_parts, 'N': knight_parts,
}

# ---------------------------------------------------------------- mid-game position
# (kind, color, file 0-7, rank 0-7)
POSITION = [
    # White
    ('K', 'w', 6, 0), ('Q', 'w', 4, 1), ('R', 'w', 3, 0), ('R', 'w', 5, 0),
    ('B', 'w', 2, 3), ('N', 'w', 5, 2), ('N', 'w', 2, 2),
    ('P', 'w', 0, 1), ('P', 'w', 1, 1), ('P', 'w', 5, 1), ('P', 'w', 6, 1),
    ('P', 'w', 7, 1), ('P', 'w', 3, 3), ('P', 'w', 4, 3),
    # Black
    ('K', 'b', 6, 7), ('Q', 'b', 3, 6), ('R', 'b', 0, 7), ('R', 'b', 5, 7),
    ('B', 'b', 2, 4), ('N', 'b', 2, 5), ('N', 'b', 5, 5),
    ('P', 'b', 0, 6), ('P', 'b', 1, 6), ('P', 'b', 6, 6), ('P', 'b', 7, 6),
    ('P', 'b', 3, 4), ('P', 'b', 4, 4),
]

for kind, color, f, r in POSITION:
    x = f - 3.5
    y = r - 3.5
    is_white = color == 'w'
    mat = MAT_WHITE if is_white else MAT_BLACK
    rz = 0.0 if is_white else math.pi
    V, F = merge(BUILDERS[kind]())
    name = f"{'W' if is_white else 'B'}{kind}_{'abcdefgh'[f]}{r + 1}"
    add_obj(name, V, F, mat, loc=(x, y, BOARD_TOP), rz=rz)

# ---------------------------------------------------------------- world & lighting
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.03, 0.03, 0.04, 1.0)
bg.inputs[1].default_value = 1.0
scene.world = world

key_data = bpy.data.lights.new("KeyArea", 'AREA')
key_data.energy = 350.0
key_data.size = 6.0
key = bpy.data.objects.new("KeyArea", key_data)
key.location = (2.5, -4.5, 9.0)
key.rotation_euler = (math.radians(10), math.radians(-15), 0.0)
scene.collection.objects.link(key)

sun_data = bpy.data.lights.new("WarmSun", 'SUN')
sun_data.energy = 2.5
sun_data.color = (1.0, 0.92, 0.80)
sun = bpy.data.objects.new("WarmSun", sun_data)
sun.rotation_euler = (math.radians(55), 0.0, math.radians(35))
scene.collection.objects.link(sun)

fill_data = bpy.data.lights.new("Fill", 'AREA')
fill_data.energy = 80.0
fill_data.size = 8.0
fill_data.color = (0.8, 0.9, 1.0)
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = (-7.0, 6.0, 6.0)
fill.rotation_euler = (math.radians(60), 0.0, math.radians(-135))
scene.collection.objects.link(fill)

# ---------------------------------------------------------------- camera
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 50.0
cam_data.dof.use_dof = False
cam = bpy.data.objects.new("MainCamera", cam_data)
cam_loc = Vector((0.0, -13.0, 11.0))
cam.location = cam_loc
target = Vector((0.0, 0.0, 0.0))
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(cam)
scene.camera = cam
