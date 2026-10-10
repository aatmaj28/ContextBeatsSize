import bpy
import math
import random
import mathutils

random.seed(7)

# ---------------------------------------------------------------
# Clean scene
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
def make_mat(name, color, rough=0.5, metal=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return mat

mat_light_sq = make_mat("LightSquare", (0.82, 0.68, 0.48), rough=0.45)
mat_dark_sq = make_mat("DarkSquare", (0.28, 0.14, 0.07), rough=0.45)
mat_base = make_mat("BoardBase", (0.18, 0.09, 0.04), rough=0.6)
mat_white = make_mat("WhitePiece", (0.90, 0.87, 0.78), rough=0.3)
mat_black = make_mat("BlackPiece", (0.06, 0.055, 0.06), rough=0.25)

# ---------------------------------------------------------------
# Primitive helpers
# ---------------------------------------------------------------
def _finish(obj, mat, rot=(0, 0, 0), scale=None):
    obj.rotation_euler = rot
    if scale is not None:
        obj.scale = scale
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj

def cyl(x, y, z, r, d, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=d, location=(x, y, z))
    return _finish(bpy.context.active_object, mat, rot)

def cone(x, y, z, r1, r2, d, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r1, radius2=r2, depth=d, location=(x, y, z))
    return _finish(bpy.context.active_object, mat)

def sph(x, y, z, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r, location=(x, y, z))
    return _finish(bpy.context.active_object, mat)

def box(x, y, z, sx, sy, sz, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z))
    return _finish(bpy.context.active_object, mat, rot, scale=(sx, sy, sz))

# ---------------------------------------------------------------
# Board
# ---------------------------------------------------------------
board_root = bpy.data.objects.new("Board", None)
bpy.context.collection.objects.link(board_root)

base = box(0, 0, -0.1, 8.8, 8.8, 0.2, mat_base)
base.parent = board_root

for f in range(8):
    for r in range(8):
        x = f - 3.5
        y = r - 3.5
        mat = mat_dark_sq if (f + r) % 2 == 0 else mat_light_sq
        tile = box(x, y, 0.05, 1.0, 1.0, 0.1, mat)
        tile.name = f"Tile_{chr(97 + f)}{r + 1}"
        tile.parent = board_root

# ---------------------------------------------------------------
# Pieces
# ---------------------------------------------------------------
def square_xy(name):
    f = ord(name[0]) - 97
    r = int(name[1]) - 1
    return f - 3.5, r - 3.5

def build_piece(kind, x, y, mat):
    z = 0.1
    parts = []
    # common base
    parts.append(cyl(x, y, z + 0.04, 0.30, 0.08, mat))

    if kind == 'P':
        parts.append(cyl(x, y, z + 0.19, 0.18, 0.26, mat))
        parts.append(cyl(x, y, z + 0.34, 0.11, 0.05, mat))
        parts.append(sph(x, y, z + 0.50, 0.16, mat))

    elif kind == 'R':
        parts.append(cyl(x, y, z + 0.33, 0.22, 0.50, mat))
        parts.append(cyl(x, y, z + 0.62, 0.30, 0.12, mat))
        for dx in (-1, 1):
            for dy in (-1, 1):
                parts.append(box(x + dx * 0.19, y + dy * 0.19, z + 0.78,
                                 0.12, 0.12, 0.20, mat))

    elif kind == 'B':
        parts.append(cone(x, y, z + 0.38, 0.24, 0.10, 0.60, mat))
        parts.append(cyl(x, y, z + 0.70, 0.14, 0.05, mat))
        parts.append(sph(x, y, z + 0.82, 0.12, mat))
        parts.append(sph(x, y, z + 0.96, 0.04, mat))

    elif kind == 'N':
        parts.append(cyl(x, y, z + 0.23, 0.24, 0.30, mat))
        parts.append(box(x, y, z + 0.55, 0.16, 0.22, 0.36, mat, rot=(-0.4, 0, 0)))
        parts.append(box(x, y + 0.10, z + 0.80, 0.14, 0.28, 0.20, mat, rot=(-0.4, 0, 0)))
        parts.append(box(x, y + 0.24, z + 0.72, 0.10, 0.14, 0.10, mat))

    elif kind == 'Q':
        parts.append(cone(x, y, z + 0.40, 0.26, 0.12, 0.70, mat))
        parts.append(cyl(x, y, z + 0.76, 0.20, 0.06, mat))
        parts.append(sph(x, y, z + 0.90, 0.14, mat))
        for i in range(5):
            a = 2 * math.pi * i / 5
            parts.append(sph(x + 0.13 * math.cos(a), y + 0.13 * math.sin(a),
                             z + 1.04, 0.05, mat))

    elif kind == 'K':
        parts.append(cone(x, y, z + 0.40, 0.26, 0.13, 0.70, mat))
        parts.append(cyl(x, y, z + 0.76, 0.20, 0.06, mat))
        parts.append(sph(x, y, z + 0.90, 0.14, mat))
        parts.append(box(x, y, z + 1.12, 0.035, 0.035, 0.12, mat))
        parts.append(box(x, y, z + 1.14, 0.09, 0.035, 0.035, mat))

    # group under an empty for tidiness
    grp = bpy.data.objects.new(f"{kind}_{mat.name}_{x:.1f}_{y:.1f}", None)
    bpy.context.collection.objects.link(grp)
    for p in parts:
        p.parent = grp
    return grp

# Mid-game position: (piece, square, color)
position = [
    # White
    ('K', 'g1', 'w'), ('Q', 'd3', 'w'), ('R', 'e1', 'w'), ('R', 'a1', 'w'),
    ('B', 'c4', 'w'), ('B', 'c1', 'w'), ('N', 'f3', 'w'), ('N', 'c3', 'w'),
    ('P', 'e4', 'w'), ('P', 'd4', 'w'), ('P', 'f2', 'w'), ('P', 'g2', 'w'),
    ('P', 'h2', 'w'), ('P', 'a2', 'w'), ('P', 'b2', 'w'), ('P', 'c2', 'w'),
    # Black
    ('K', 'g8', 'b'), ('Q', 'd7', 'b'), ('R', 'f8', 'b'), ('R', 'a8', 'b'),
    ('B', 'c5', 'b'), ('B', 'e7', 'b'), ('N', 'f6', 'b'), ('N', 'c6', 'b'),
    ('P', 'e5', 'b'), ('P', 'd6', 'b'), ('P', 'f7', 'b'), ('P', 'g7', 'b'),
    ('P', 'h7', 'b'), ('P', 'a7', 'b'), ('P', 'b7', 'b'),
]

for kind, sq, color in position:
    x, y = square_xy(sq)
    mat = mat_white if color == 'w' else mat_black
    build_piece(kind, x, y, mat)

# Captured pieces standing beside the board
build_piece('P', 5.4, -2.5, mat_black)
build_piece('N', 5.4, -1.2, mat_white)
build_piece('P', -5.4, 2.8, mat_white)

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 2.5
sun_data.angle = math.radians(4)
sun = bpy.data.objects.new("KeySun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))

area_data = bpy.data.lights.new(name="SoftFill", type='AREA')
area_data.energy = 600
area_data.size = 6.0
area = bpy.data.objects.new("SoftFill", area_data)
bpy.context.collection.objects.link(area)
area.location = (4.0, -6.0, 7.0)
area.rotation_euler = (math.radians(60), 0, math.radians(30))

rim_data = bpy.data.lights.new(name="RimLight", type='POINT')
rim_data.energy = 250
rim = bpy.data.objects.new("RimLight", rim_data)
bpy.context.collection.objects.link(rim)
rim.location = (-4.5, 5.0, 4.0)

# ---------------------------------------------------------------
# World
# ---------------------------------------------------------------
scene = bpy.context.scene
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.03, 0.03, 0.045, 1.0)
    bg.inputs["Strength"].default_value = 0.6

# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 55
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = 13.0
cam_data.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("MainCamera", cam_data)
bpy.context.collection.objects.link(cam)

cam_pos = mathutils.Vector((-1.2, -11.0, 8.5))
target = mathutils.Vector((0.0, 0.0, 0.4))
direction = target - cam_pos
cam.location = cam_pos
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam

# ---------------------------------------------------------------
# Timeline (static scene)
# ---------------------------------------------------------------
scene.frame_start = 1
scene.frame_end = 1
