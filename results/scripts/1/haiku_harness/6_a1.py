import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene

# ---------------------------------------------------------------------------
# Clear the default scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)


# ---------------------------------------------------------------------------
# Materials (node-based by default in 5.x)
# ---------------------------------------------------------------------------
def make_mat(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


mat_light_sq = make_mat("LightSquare", (0.90, 0.84, 0.70), 0.45)
mat_dark_sq = make_mat("DarkSquare", (0.30, 0.18, 0.11), 0.45)
mat_board = make_mat("BoardWood", (0.22, 0.12, 0.07), 0.40)
mat_white = make_mat("WhitePiece", (0.95, 0.93, 0.86), 0.30)
mat_black = make_mat("BlackPiece", (0.07, 0.06, 0.06), 0.30)
mat_floor = make_mat("Floor", (0.10, 0.10, 0.12), 0.85)
piece_mats = {"w": mat_white, "b": mat_black}


# ---------------------------------------------------------------------------
# Mesh helpers
# ---------------------------------------------------------------------------
def finish_mesh(bm, name, mat):
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    me.update()
    return me


def box(bm, center, size, rot_x=0.0):
    m = (Matrix.Translation(Vector(center))
         @ Matrix.Rotation(rot_x, 4, 'X')
         @ Matrix.Diagonal(Vector((size[0], size[1], size[2], 1.0))))
    bmesh.ops.create_cube(bm, size=1.0, matrix=m)


def ball(bm, center, radius):
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius,
                               matrix=Matrix.Translation(Vector(center)))


def lathe(bm, profile, segs=36):
    """Revolve a (radius, height) profile around the Z axis."""
    rings = []
    for r, z in profile:
        ring = []
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for j in range(segs):
            k = (j + 1) % segs
            try:
                bm.faces.new((A[j], A[k], B[k], B[j]))
            except ValueError:
                pass
    for ring in (rings[0], rings[-1]):
        try:
            bm.faces.new(ring)
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# Piece profiles and builders
# ---------------------------------------------------------------------------
PAWN_PROFILE = [(0.30, 0.0), (0.30, 0.05), (0.20, 0.10), (0.12, 0.25),
                (0.10, 0.40), (0.18, 0.48), (0.18, 0.52), (0.08, 0.62)]

ROOK_PROFILE = [(0.32, 0.0), (0.32, 0.06), (0.22, 0.12), (0.19, 0.20),
                (0.19, 0.78), (0.25, 0.82), (0.25, 0.95)]

BISHOP_PROFILE = [(0.28, 0.0), (0.28, 0.06), (0.18, 0.12), (0.12, 0.30),
                  (0.10, 0.50), (0.17, 0.60), (0.15, 0.72), (0.07, 0.88),
                  (0.04, 0.95)]

QUEEN_PROFILE = [(0.30, 0.0), (0.30, 0.06), (0.20, 0.12), (0.12, 0.30),
                 (0.10, 0.55), (0.22, 0.70), (0.20, 0.80), (0.14, 0.88),
                 (0.08, 0.95)]

KING_PROFILE = QUEEN_PROFILE


def build_pawn(bm):
    lathe(bm, PAWN_PROFILE)
    ball(bm, (0, 0, 0.66), 0.11)


def build_rook(bm):
    lathe(bm, ROOK_PROFILE)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        box(bm, (sx * 0.15, sy * 0.15, 1.02), (0.12, 0.12, 0.14))


def build_bishop(bm):
    lathe(bm, BISHOP_PROFILE)
    ball(bm, (0, 0, 0.98), 0.07)
    box(bm, (0, 0, 0.80), (0.05, 0.20, 0.05), 0.0)  # slit (decorative)


def build_queen(bm):
    lathe(bm, QUEEN_PROFILE)
    for i in range(8):
        a = 2.0 * math.pi * i / 8
        ball(bm, (0.14 * math.cos(a), 0.14 * math.sin(a), 0.92), 0.045)
    ball(bm, (0, 0, 1.02), 0.08)


def build_king(bm):
    lathe(bm, KING_PROFILE)
    box(bm, (0, 0, 1.10), (0.05, 0.05, 0.22))
    box(bm, (0, 0, 1.16), (0.16, 0.05, 0.05))


def build_knight(bm):
    lathe(bm, [(0.30, 0.0), (0.30, 0.06), (0.20, 0.12), (0.18, 0.20),
               (0.16, 0.30)])
    box(bm, (0, -0.02, 0.45), (0.22, 0.26, 0.34), rot_x=0.35)   # neck
    box(bm, (0, 0.10, 0.70), (0.20, 0.30, 0.28), rot_x=-0.45)   # head
    box(bm, (0, 0.30, 0.62), (0.16, 0.22, 0.16), rot_x=-0.25)   # snout
    box(bm, (0, -0.12, 0.66), (0.06, 0.20, 0.22), rot_x=0.35)   # mane


PIECE_BUILDERS = {
    "P": build_pawn, "R": build_rook, "B": build_bishop,
    "N": build_knight, "Q": build_queen, "K": build_king,
}

PIECE_NAMES = {"P": "Pawn", "R": "Rook", "B": "Bishop",
               "N": "Knight", "Q": "Queen", "K": "King"}

# Build each piece mesh once and share it between instances.
mesh_cache = {}


def get_piece_mesh(kind, color):
    key = (kind, color)
    if key not in mesh_cache:
        bm = bmesh.new()
        PIECE_BUILDERS[kind](bm)
        mesh_cache[key] = finish_mesh(bm, f"{PIECE_NAMES[kind]}_{color}",
                                      piece_mats[color])
    return mesh_cache[key]


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------
BOARD_TOP = 0.02  # top surface of the squares

# Base slab (top at z = 0)
bm = bmesh.new()
box(bm, (0, 0, -0.15), (8.6, 8.6, 0.3))
base_mesh = finish_mesh(bm, "BoardBase", mat_board)
base_obj = bpy.data.objects.new("BoardBase", base_mesh)
scene.collection.objects.link(base_obj)

# Squares: a1 is dark.
bm_dark = bmesh.new()
bm_light = bmesh.new()
for f in range(8):
    for r in range(8):
        x = f - 3.5
        y = r - 3.5
        target = bm_dark if (f + r) % 2 == 0 else bm_light
        box(target, (x, y, 0.0), (0.99, 0.99, 0.04))

dark_obj = bpy.data.objects.new(
    "DarkSquares", finish_mesh(bm_dark, "DarkSquares", mat_dark_sq))
light_obj = bpy.data.objects.new(
    "LightSquares", finish_mesh(bm_light, "LightSquares", mat_light_sq))
scene.collection.objects.link(dark_obj)
scene.collection.objects.link(light_obj)


# ---------------------------------------------------------------------------
# Position: a middlegame with some captured pieces off the board
# (kind, color, square) — square is algebraic or an (x, y) tuple off-board
# ---------------------------------------------------------------------------
PIECES = [
    # White
    ("K", "w", "g1"), ("Q", "w", "d2"), ("R", "w", "a1"), ("R", "w", "f1"),
    ("B", "w", "c4"), ("N", "w", "f3"), ("N", "w", "c3"),
    ("P", "w", "e4"), ("P", "w", "d4"), ("P", "w", "a2"), ("P", "w", "b2"),
    ("P", "w", "f2"), ("P", "w", "g2"), ("P", "w", "h2"),
    # Black
    ("K", "b", "g8"), ("Q", "b", "d8"), ("R", "b", "a8"), ("R", "b", "f8"),
    ("B", "b", "c5"), ("N", "b", "c6"), ("N", "b", "f6"),
    ("P", "b", "e5"), ("P", "b", "a7"), ("P", "b", "b7"), ("P", "b", "d7"),
    ("P", "b", "f7"), ("P", "b", "g7"), ("P", "b", "h7"),
    # Captured pieces beside the board
    ("B", "b", (5.4, -3.2)), ("P", "w", (5.4, -2.2)),
    ("N", "w", (-5.4, 2.6)), ("P", "b", (-5.4, 3.6)),
]


def square_position(sq):
    if isinstance(sq, tuple):
        return Vector((sq[0], sq[1], BOARD_TOP))
    f = ord(sq[0]) - ord("a")
    r = int(sq[1]) - 1
    return Vector((f - 3.5, r - 3.5, BOARD_TOP))


piece_objects = []
for kind, color, sq in PIECES:
    mesh = get_piece_mesh(kind, color)
    name = f"{'White' if color == 'w' else 'Black'}{PIECE_NAMES[kind]}"
    obj = bpy.data.objects.new(name, mesh)
    obj.location = square_position(sq)
    if isinstance(sq, tuple):
        obj.rotation_euler.z = random.uniform(0.0, 2.0 * math.pi)
    else:
        obj.rotation_euler.z = math.pi if color == "b" else 0.0
    scene.collection.objects.link(obj)
    piece_objects.append(obj)


# ---------------------------------------------------------------------------
# Floor
# ---------------------------------------------------------------------------
bm = bmesh.new()
box(bm, (0, 0, -0.5), (40.0, 40.0, 0.2))
floor_obj = bpy.data.objects.new("Floor", finish_mesh(bm, "Floor", mat_floor))
scene.collection.objects.link(floor_obj)


# ---------------------------------------------------------------------------
# World background
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.04, 0.045, 0.06, 1.0)
    bg.inputs["Strength"].default_value = 0.6


# ---------------------------------------------------------------------------
# Lights
# ---------------------------------------------------------------------------
sun_data = bpy.data.lights.new("KeySun", type='SUN')
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("KeySun", sun_data)
sun_obj.rotation_euler = (math.radians(50), 0.0, math.radians(-35))
scene.collection.objects.link(sun_obj)

focus = Vector((0.0, 0.0, 0.5))


def aim_light(name, light_type, energy, size, location):
    data = bpy.data.lights.new(name, type=light_type)
    data.energy = energy
    if light_type == 'AREA':
        data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = Vector(location)
    direction = focus - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(obj)
    return obj


aim_light("FillArea", 'AREA', 450.0, 6.0, (-4.0, -6.0, 6.0))
aim_light("RimArea", 'AREA', 300.0, 5.0, (-3.0, 7.0, 6.0))


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 55.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
cam_obj.location = Vector((0.0, -10.5, 8.0))
target = Vector((0.0, 0.3, 0.4))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Static scene
scene.frame_start = 1
scene.frame_end = 1
