import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, Euler

random.seed(7)
scene = bpy.context.scene
coll = scene.collection

# ---------- clear anything present ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- helpers ----------
SEG = 24
SQUARE_TOP = 0.06  # top surface height of the squares


def make_mat(name, rgba, rough):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    return m


def add_box(bm, loc, size, rot=(0.0, 0.0, 0.0)):
    M = Matrix.Translation(Vector(loc)) @ Euler(rot, 'XYZ').to_matrix().to_4x4()
    sx, sy, sz = [s * 0.5 for s in size]
    corners = [Vector((x, y, z)) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]
    verts = [bm.verts.new(M @ c) for c in corners]
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
             (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return [bm.faces.new([verts[i] for i in q]) for q in quads]


def add_revolve(bm, profile, cx=0.0, cy=0.0, cz=0.0, seg=SEG):
    """Lathe a (radius, height) profile ordered bottom to top around Z."""
    angles = [2.0 * math.pi * k / seg for k in range(seg)]
    rings = []
    for r, z in profile:
        ring = [bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), cz + z))
                for a in angles]
        rings.append(ring)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(seg):
            k2 = (k + 1) % seg
            bm.faces.new((a[k], a[k2], b[k2], b[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])


def sphere_profile(r, n=10):
    pts = []
    for i in range(1, n):
        t = math.pi * i / n
        pts.append((r * math.sin(t), -r * math.cos(t)))
    return pts


def add_sphere(bm, cx, cy, cz, r):
    add_revolve(bm, sphere_profile(r), cx, cy, cz)


# ---------- piece geometry builders ----------
def build_pawn(bm):
    add_revolve(bm, [(0.34, 0.0), (0.34, 0.05), (0.22, 0.12),
                     (0.13, 0.24), (0.15, 0.32), (0.10, 0.36)])
    add_sphere(bm, 0, 0, 0.50, 0.14)


def build_rook(bm):
    add_revolve(bm, [(0.32, 0.0), (0.32, 0.05), (0.26, 0.10),
                     (0.26, 0.66), (0.30, 0.70), (0.30, 0.74)])
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(bm, (0.16 * sx, 0.16 * sy, 0.81), (0.14, 0.14, 0.14))


def build_knight(bm):
    add_revolve(bm, [(0.34, 0.0), (0.34, 0.05), (0.24, 0.12),
                     (0.20, 0.22), (0.20, 0.30)])
    add_box(bm, (0.0, 0.02, 0.50), (0.24, 0.30, 0.42), (-0.35, 0.0, 0.0))
    add_box(bm, (0.0, 0.12, 0.78), (0.22, 0.46, 0.30), (-0.60, 0.0, 0.0))
    add_box(bm, (0.0, 0.30, 0.84), (0.18, 0.20, 0.22), (-0.70, 0.0, 0.0))


def build_bishop(bm):
    add_revolve(bm, [(0.32, 0.0), (0.32, 0.05), (0.20, 0.12), (0.12, 0.30),
                     (0.20, 0.50), (0.22, 0.60), (0.12, 0.70), (0.10, 0.80)])
    add_sphere(bm, 0, 0, 0.85, 0.10)


def build_queen(bm):
    add_revolve(bm, [(0.34, 0.0), (0.34, 0.06), (0.22, 0.14), (0.14, 0.30),
                     (0.24, 0.50), (0.26, 0.60), (0.16, 0.70), (0.14, 0.84)])
    add_sphere(bm, 0, 0, 0.90, 0.15)
    add_sphere(bm, 0, 0, 1.06, 0.08)


def build_king(bm):
    add_revolve(bm, [(0.32, 0.0), (0.32, 0.06), (0.22, 0.14), (0.14, 0.30),
                     (0.24, 0.50), (0.26, 0.60), (0.15, 0.72), (0.13, 0.88)])
    add_sphere(bm, 0, 0, 0.94, 0.13)
    add_box(bm, (0, 0, 1.20), (0.06, 0.06, 0.30))
    add_box(bm, (0, 0, 1.26), (0.22, 0.06, 0.06))


BUILDERS = {
    'pawn': build_pawn, 'rook': build_rook, 'knight': build_knight,
    'bishop': build_bishop, 'queen': build_queen, 'king': build_king,
}

# ---------- materials ----------
mat_white = make_mat("IvoryPiece", (0.88, 0.85, 0.78, 1.0), 0.35)
mat_black = make_mat("EbonyPiece", (0.035, 0.03, 0.03, 1.0), 0.30)
mat_frame = make_mat("BoardFrame", (0.22, 0.10, 0.05, 1.0), 0.45)
mat_light = make_mat("LightSquare", (0.72, 0.56, 0.36, 1.0), 0.50)
mat_dark = make_mat("DarkSquare", (0.16, 0.07, 0.035, 1.0), 0.50)
mat_felt = make_mat("Felt", (0.05, 0.11, 0.08, 1.0), 0.95)
PIECE_MATS = {'white': mat_white, 'black': mat_black}

# ---------- board ----------
bm = bmesh.new()
for f in add_box(bm, (0, 0, -0.12), (9.2, 9.2, 0.3)):
    f.material_index = 0
for fi in range(8):
    for ri in range(8):
        idx = 2 if (fi + ri) % 2 == 0 else 1  # a1 is a dark square
        for f in add_box(bm, (fi - 3.5, ri - 3.5, 0.03), (1.0, 1.0, 0.06)):
            f.material_index = idx
board_me = bpy.data.meshes.new("BoardMesh")
bm.to_mesh(board_me)
bm.free()
for m in (mat_frame, mat_light, mat_dark):
    board_me.materials.append(m)
board_obj = bpy.data.objects.new("Board", board_me)
coll.objects.link(board_obj)

# Felt table under the board
bm = bmesh.new()
for f in add_box(bm, (0, 0, -0.27), (40.0, 40.0, 0.2)):
    f.material_index = 0
felt_me = bpy.data.meshes.new("FeltMesh")
bm.to_mesh(felt_me)
bm.free()
felt_me.materials.append(mat_felt)
coll.objects.link(bpy.data.objects.new("Table", felt_me))

# ---------- piece meshes (one per kind and colour, shared by objects) ----------
mesh_cache = {}


def get_piece_mesh(kind, color):
    key = (kind, color)
    if key in mesh_cache:
        return mesh_cache[key]
    bm = bmesh.new()
    BUILDERS[kind](bm)
    me = bpy.data.meshes.new(f"{color}_{kind}")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(PIECE_MATS[color])
    for p in me.polygons:
        p.use_smooth = True
    mesh_cache[key] = me
    return me


def square_to_xy(sq):
    f = ord(sq[0].lower()) - ord('a')
    r = int(sq[1]) - 1
    return f - 3.5, r - 3.5


def place_piece(kind, color, sq):
    x, y = square_to_xy(sq)
    me = get_piece_mesh(kind, color)
    obj = bpy.data.objects.new(f"{color.title()}{kind.title()}_{sq}", me)
    obj.location = (x, y, SQUARE_TOP)
    obj.rotation_euler = (0.0, 0.0, random.uniform(0.0, 2.0 * math.pi))
    coll.objects.link(obj)
    return obj


# ---------- mid-game position (sparse, Ruy Lopez-style) ----------
WHITE = [
    ('king', 'g1'), ('queen', 'd2'), ('rook', 'a1'), ('rook', 'e1'),
    ('bishop', 'c4'), ('knight', 'f3'), ('knight', 'c3'),
    ('pawn', 'e4'), ('pawn', 'd4'), ('pawn', 'a2'), ('pawn', 'b2'),
    ('pawn', 'f2'), ('pawn', 'g2'), ('pawn', 'h2'),
]
BLACK = [
    ('king', 'g8'), ('queen', 'd8'), ('rook', 'f8'), ('rook', 'd7'),
    ('bishop', 'c5'), ('knight', 'f6'), ('knight', 'c6'),
    ('pawn', 'e5'), ('pawn', 'd6'), ('pawn', 'a7'), ('pawn', 'b7'),
    ('pawn', 'f7'), ('pawn', 'g7