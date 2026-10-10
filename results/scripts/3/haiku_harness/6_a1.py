import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------------------------------------------------------------
# Scene cleanup and collection setup
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

scene = bpy.context.scene
coll = bpy.data.collections.new("ChessSet")
scene.collection.children.link(coll)

S = 0.6          # global piece scale relative to a 1-unit square
BASE_Z = 0.05    # top surface of the squares


# ---------------------------------------------------------------
# Materials (Principled BSDF created by default with new materials)
# ---------------------------------------------------------------
def make_mat(name, color, rough=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


mat_light_sq = make_mat("LightSquare", (0.80, 0.70, 0.52), rough=0.45)
mat_dark_sq = make_mat("DarkSquare", (0.30, 0.15, 0.08), rough=0.45)
mat_frame = make_mat("BoardFrame", (0.22, 0.10, 0.05), rough=0.4)
mat_floor = make_mat("Floor", (0.08, 0.08, 0.09), rough=0.8)
mat_white = make_mat("IvoryPiece", (0.90, 0.87, 0.78), rough=0.35)
mat_black = make_mat("EbonyPiece", (0.04, 0.035, 0.03), rough=0.25)


# ---------------------------------------------------------------
# Mesh helpers using bmesh
# ---------------------------------------------------------------
def build_obj(name, bm, mat, smooth=True):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


def add_frustum(name, rb, rt, h, pos, mat):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=32,
                          radius1=rb, radius2=rt, depth=h)
    bmesh.ops.translate(bm, vec=(pos[0], pos[1], pos[2] + h / 2), verts=bm.verts)
    return build_obj(name, bm, mat, smooth=True)


def add_sphere(name, r, center, mat):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=r)
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    return build_obj(name, bm, mat, smooth=True)


def add_box(name, size, pos, mat, smooth=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.translate(bm, vec=(pos[0], pos[1], pos[2] + size[2] / 2), verts=bm.verts)
    return build_obj(name, bm, mat, smooth=smooth)


# ---------------------------------------------------------------
# Board
# ---------------------------------------------------------------
# Wooden base (top surface at z = 0)
add_box("BoardBase", (8.6, 8.6, 0.2), (0, 0, -0.2), mat_frame)

# Floor
add_box("Floor", (40.0, 40.0, 0.02), (0, 0, -0.22), mat_floor)

# 64 squares
for f in range(8):
    for r in range(8):
        x = f - 3.5
        y = r - 3.5
        is_light = (f + r) % 2 == 1
        mat = mat_light_sq if is_light else mat_dark_sq
        add_box(f"Sq_{f}_{r}", (0.98, 0.98, 0.05), (x, y, 0.0), mat)


# ---------------------------------------------------------------
# Piece definitions (unscaled units)
# ('f', r_bottom, r_top, height, z_bottom, dx, dy)  frustum/cylinder
# ('s', radius, z_center, dx, dy)                   sphere
# ('b', sx, sy, sz, z_bottom, dx, dy)               box
# ---------------------------------------------------------------
PARTS = {
    'pawn': [
        ('f', 0.30, 0.30, 0.06, 0.00, 0, 0),
        ('f', 0.22, 0.12, 0.30, 0.06, 0, 0),
        ('s', 0.17, 0.44, 0, 0),
    ],
    'rook': [
        ('f', 0.30, 0.30, 0.07, 0.00, 0, 0),
        ('f', 0.22, 0.20, 0.40, 0.07, 0, 0),
        ('f', 0.27, 0.27, 0.10, 0.47, 0, 0),
        ('b', 0.12, 0.12, 0.12, 0.57, 0.20, 0.20),
        ('b', 0.12, 0.12, 0.12, 0.57, -0.20, 0.20),
        ('b', 0.12, 0.12, 0.12, 0.57, 0.20, -0.20),
        ('b', 0.12, 0.12, 0.12, 0.57, -0.20, -0.20),
    ],
    'bishop': [
        ('f', 0.30, 0.30, 0.07, 0.00, 0, 0),
        ('f', 0.22, 0.12, 0.42, 0.07, 0, 0),
        ('s', 0.15, 0.58, 0, 0),
        ('s', 0.05, 0.72, 0, 0),
    ],
    'knight': [
        ('f', 0.30, 0.30, 0.07, 0.00, 0, 0),
        ('f', 0.24, 0.16, 0.25, 0.07, 0, 0),
        ('b', 0.20, 0.34, 0.30, 0.30, 0, 0.02),
        ('b', 0.18, 0.20, 0.20, 0.45, 0, 0.14),
    ],
    'queen': [
        ('f', 0.32, 0.32, 0.07, 0.00, 0, 0),
        ('f', 0.25, 0.12, 0.50, 0.07, 0, 0),
        ('f', 0.20, 0.20, 0.06, 0.55, 0, 0),
        ('f', 0.20, 0.30, 0.10, 0.61, 0, 0),
        ('s', 0.09, 0.80, 0, 0),
    ],
    'king': [
        ('f', 0.32, 0.32, 0.07, 0.00, 0, 0),
        ('f', 0.24, 0.14, 0.45, 0.07, 0, 0),
        ('f', 0.20, 0.20, 0.06, 0.52, 0, 0),
        ('f', 0.20, 0.26, 0.08, 0.58, 0, 0),
        ('b', 0.05, 0.05, 0.24, 0.66, 0, 0),
        ('b', 0.16, 0.05, 0.05, 0.80, 0, 0),
    ],
}


def place_piece(kind, color, file_idx, rank_idx):
    x = file_idx - 3.5
    y = rank_idx - 3.5
    mat = mat_white if color == 'w' else mat_black
    tag = f"{'W' if color == 'w' else 'B'}_{kind}_{file_idx}{rank_idx}"

    for i, part in enumerate(PARTS[kind]):
        name = f"{tag}_{i}"
        shape = part[0]
        if shape == 'f':
            _, rb, rt, h, zb, dx, dy = part
            add_frustum(name, rb * S, rt * S, h * S,
                        (x + dx * S, y + dy * S, BASE_Z + zb * S), mat)
        elif shape == 's':
            _, r, zc, dx, dy = part
            add_sphere(name, r * S,
                       (x + dx * S, y + dy * S, BASE_Z + zc * S), mat)
        elif shape == 'b':
            _, sx, sy, sz, zb, dx, dy = part
            add_box(name, (sx * S, sy * S, sz * S),
                    (x + dx * S, y + dy * S, BASE_Z + zb * S), mat, smooth=True)


# ---------------------------------------------------------------
# Mid-game position
# ---------------------------------------------------------------
position = [
    # White
    ('king',   'w', 6, 0),   # Kg1
    ('queen',  'w', 3, 2),   # Qd3
    ('rook',   'w', 5, 0),   # Rf1
    ('rook',   'w', 0, 0),   # Ra1
    ('bishop', 'w', 2, 3),   # Bc4
    ('knight', 'w', 5, 2),   # Nf3
    ('pawn',   'w', 4, 3),   # e4
    ('pawn',   'w', 0, 1),   # a2
    ('pawn',   'w', 1, 1),   # b2
    ('pawn',   'w', 6, 1),   # g2
    ('pawn',   'w', 7, 1),   # h2
    # Black
    ('king',   'b', 6, 7),   # Kg8
    ('queen',  'b', 4, 6),   # Qe7
    ('rook',   'b', 3, 7),   # Rd8
    ('knight', 'b', 2, 5),   # Nc6
    ('bishop', 'b', 5, 4),   # Bf5
    ('pawn',   'b', 0, 6),   # a7
    ('pawn',   'b', 1, 6),   # b7
    ('pawn',   'b', 5, 6),   # f7
    ('pawn',   'b', 3, 4),   # d5
    ('pawn',   'b', 6, 5),   # g6
]

for kind, color, f, r in position:
    place_piece(kind, color, f, r)


# ---------------------------------------------------------------
# World background
# ---------------------------------------------------------------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg is not None:
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.025, 1.0)
    bg.inputs["Strength"].default_value = 1.0


# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
key_data = bpy.data.lights.new("KeyLight", 'AREA')
key_data.energy = 900.0
key_data.size = 5.0
key_data.color = (1.0, 0.95, 0.88)
key = bpy.data.objects.new("KeyLight", key_data)
coll.objects.link(key)
key.location = (-4.0, -5.0, 8.0)
key.rotation_euler = (math.radians(45), 0.0, math.radians(-30))

rim_data = bpy.data.lights.new("RimLight", 'SPOT')
rim_data.energy = 600.0
rim_data.color = (0.7, 0.8, 1.0)
rim_data.spot_size = math.radians(70)
rim = bpy.data.objects.new("RimLight", rim_data)
coll.objects.link(rim)
rim.location = (5.0, 6.0, 5.0)
rim.rotation_euler = (math.radians(60), 0.0, math.radians(140))

sun_data = bpy.data.lights.new("FillSun", 'SUN')
sun_data.energy = 1.5
sun_data.angle = math.radians(10)
sun = bpy.data.objects.new("FillSun", sun_data)
coll.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0.0, math.radians(20))


# ---------------------------------------------------------------
# Camera framing the board from the white side, slightly elevated
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
coll.objects.link(cam)

cam_loc = Vector((-3.0, -8.5, 7.0))
target = Vector((0.0, 0.0, 0.3))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
