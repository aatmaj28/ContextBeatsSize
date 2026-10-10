import bpy
import math
from mathutils import Vector

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1

# ---------- Materials ----------
def make_mat(name, color, rough=0.5, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m

mat_light_sq = make_mat("LightSquare", (0.85, 0.70, 0.48), rough=0.45)
mat_dark_sq = make_mat("DarkSquare", (0.28, 0.14, 0.07), rough=0.45)
mat_frame = make_mat("BoardFrame", (0.22, 0.10, 0.05), rough=0.4)
mat_floor = make_mat("Floor", (0.06, 0.06, 0.07), rough=0.8)
mat_white = make_mat("WhitePiece", (0.92, 0.89, 0.82), rough=0.3)
mat_black = make_mat("BlackPiece", (0.04, 0.04, 0.05), rough=0.25)

# ---------- Helpers ----------
def assign(obj, mat, smooth=False):
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj

def cube(loc, size, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    return assign(o, mat)

def cyl(loc, r, h, mat, r2=None, verts=40):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=h, location=loc)
    return assign(bpy.context.active_object, mat, smooth=True)

def sph(loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=loc)
    return assign(bpy.context.active_object, mat, smooth=True)

def square_center(f, r):
    return (f - 3.5, r - 3.5)

# ---------- Board ----------
# Base frame and floor
cube((0, 0, -0.28), (9.2, 9.2, 0.36), mat_frame)
cube((0, 0, -0.9), (60, 60, 0.2), mat_floor)

# Squares
for f in range(8):
    for r in range(8):
        x, y = square_center(f, r)
        is_light = (f + r) % 2 == 1
        cube((x, y, -0.05), (1.0, 1.0, 0.1), mat_light_sq if is_light else mat_dark_sq)

# ---------- Pieces ----------
def build_pawn(x, y, m):
    cyl((x, y, 0.04), 0.30, 0.08, m)
    cyl((x, y, 0.28), 0.22, 0.40, m, r2=0.12)
    sph((x, y, 0.62), 0.14, m)

def build_rook(x, y, m):
    cyl((x, y, 0.05), 0.32, 0.10, m)
    cyl((x, y, 0.33), 0.24, 0.46, m, r2=0.20)
    cyl((x, y, 0.66), 0.30, 0.14, m)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        cube((x + 0.22 * math.cos(a), y + 0.22 * math.sin(a), 0.80),
             (0.14, 0.14, 0.16), m)

def build_knight(x, y, m):
    cyl((x, y, 0.05), 0.30, 0.10, m)
    cube((x, y, 0.34), (0.42, 0.28, 0.46), m, rot=(0.25, 0, 0))
    cube((x, y + 0.08, 0.70), (0.26, 0.42, 0.30), m, rot=(-0.6, 0, 0))
    cube((x, y + 0.22, 0.84), (0.20, 0.22, 0.18), m, rot=(-0.9, 0, 0))

def build_bishop(x, y, m):
    cyl((x, y, 0.05), 0.30, 0.10, m)
    cyl((x, y, 0.42), 0.26, 0.64, m, r2=0.10)
    sph((x, y, 0.88), 0.13, m)
    sph((x, y, 1.02), 0.05, m)

def build_queen(x, y, m):
    cyl((x, y, 0.05), 0.32, 0.10, m)
    cyl((x, y, 0.46), 0.28, 0.72, m, r2=0.12)
    cyl((x, y, 0.84), 0.20, 0.06, m)
    sph((x, y, 0.98), 0.16, m)
    for i in range(6):
        a = i * math.pi / 3
        sph((x + 0.17 * math.cos(a), y + 0.17 * math.sin(a), 1.16), 0.06, m)
    sph((x, y, 1.22), 0.07, m)

def build_king(x, y, m):
    cyl((x, y, 0.05), 0.32, 0.10, m)
    cyl((x, y, 0.46), 0.26, 0.72, m, r2=0.12)
    cyl((x, y, 0.84), 0.20, 0.06, m)
    sph((x, y, 0.98), 0.16, m)
    cube((x, y, 1.20), (0.05, 0.05, 0.26), m)
    cube((x, y, 1.26), (0.18, 0.05, 0.05), m)

builders = {
    "pawn": build_pawn, "rook": build_rook, "knight": build_knight,
    "bishop": build_bishop, "queen": build_queen, "king": build_king,
}

# Mid-game placement: (piece, color, file, rank) with file/rank 0..7
placements = [
    # White
    ("rook", "w", 0, 0), ("king", "w", 6, 0), ("knight", "w", 2, 2),
    ("bishop", "w", 5, 2), ("queen", "w", 3, 3), ("pawn", "w", 4, 4),
    ("pawn", "w", 1, 1), ("pawn", "w", 6, 2), ("pawn", "w", 2, 4),
    ("pawn", "w", 5, 5), ("rook", "w", 7, 1),
    # Black
    ("rook", "b", 7, 7), ("king", "b", 1, 7), ("knight", "b", 5, 5),
    ("bishop", "b", 2, 5), ("queen", "b", 4, 6), ("pawn", "b", 3, 4),
    ("pawn", "b", 6, 6), ("pawn", "b", 0, 6), ("pawn", "b", 4, 5),
    ("pawn", "b", 7, 5),
]

for piece, color, f, r in placements:
    x, y = square_center(f, r)
    m = mat_white if color == "w" else mat_black
    builders[piece](x, y, m)
    # Knights face toward the center of the board
    if piece == "knight":
        bpy.context.active_object.rotation_euler.z = math.atan2(-y, -x)

# ---------- Lighting ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.02, 0.025, 0.035, 1.0)
bg.inputs["Strength"].default_value = 0.6
scene.world = world

key_data = bpy.data.lights.new("KeyLight", type='AREA')
key_data.energy = 1800
key_data.size = 6.0
key = bpy.data.objects.new("KeyLight", key_data)
bpy.context.collection.objects.link(key)
key.location = (6, -7, 12)
key.rotation_euler = (math.radians(50), 0, math.radians(35))

rim_data = bpy.data.lights.new("RimLight", type='SPOT')
rim_data.energy = 2500
rim_data.spot_size = math.radians(70)
rim = bpy.data.objects.new("RimLight", rim_data)
bpy.context.collection.objects.link(rim)
rim.location = (-8, 8, 9)
rim.rotation_euler = (math.radians(55), 0, math.radians(-140))

fill_data = bpy.data.lights.new("Fill", type='SUN')
fill_data.energy = 1.5
fill = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(-20))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (9.0, -12.0, 11.0)

target = Vector((0.0, 0.0, 0.5))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
