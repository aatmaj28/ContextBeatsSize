import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Materials ----------
def make_mat(name, color, rough=0.4, metal=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m

mat_light_sq = make_mat("LightSquare", (0.85, 0.75, 0.55), 0.35)
mat_dark_sq = make_mat("DarkSquare", (0.25, 0.13, 0.06), 0.35)
mat_frame = make_mat("Frame", (0.12, 0.06, 0.03), 0.3)
mat_white = make_mat("WhitePiece", (0.92, 0.9, 0.84), 0.25)
mat_black = make_mat("BlackPiece", (0.03, 0.03, 0.035), 0.2)
mat_table = make_mat("Table", (0.3, 0.32, 0.35), 0.7)

def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

# ---------- Board ----------
SQ = 1.0
for f in range(8):
    for r in range(8):
        bpy.ops.mesh.primitive_cube_add(size=1, location=((f - 3.5) * SQ, (r - 3.5) * SQ, 0.05))
        sq = bpy.context.active_object
        sq.scale = (SQ, SQ, 0.1)
        sq.name = f"Square_{f}_{r}"
        assign(sq, mat_dark_sq if (f + r) % 2 == 0 else mat_light_sq)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.0))
frame = bpy.context.active_object
frame.scale = (8.8, 8.8, 0.18)
frame.name = "BoardFrame"
assign(frame, mat_frame)

bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.09))
table = bpy.context.active_object
table.name = "Table"
assign(table, mat_table)

TOP = 0.1  # board surface height

# ---------- Piece builders ----------
def cyl(parts, r, d, z, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=(0, 0, z + d / 2))
    o = bpy.context.active_object; smooth(o); parts.append(o); return o

def cone(parts, r1, r2, d, z):
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r1, radius2=r2, depth=d, location=(0, 0, z + d / 2))
    o = bpy.context.active_object; smooth(o); parts.append(o); return o

def sphere(parts, r, z, scale=(1, 1, 1), loc_xy=(0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r, location=(loc_xy[0], loc_xy[1], z))
    o = bpy.context.active_object; o.scale = scale; smooth(o); parts.append(o); return o

def cube(parts, size, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.scale = size; parts.append(o); return o

def base(parts):
    cyl(parts, 0.36, 0.08, 0)
    cyl(parts, 0.30, 0.06, 0.08)

def build(kind, white):
    p = []
    base(p)
    if kind == "P":
        cone(p, 0.22, 0.09, 0.45, 0.14)
        cyl(p, 0.15, 0.04, 0.55)
        sphere(p, 0.15, 0.72)
    elif kind == "R":
        cyl(p, 0.24, 0.6, 0.14)
        cyl(p, 0.29, 0.14, 0.74)
        for i in range(4):
            a = i * math.pi / 2 + math.pi / 4
            cube(p, (0.12, 0.12, 0.12), (0.21 * math.cos(a), 0.21 * math.sin(a), 0.94), (0, 0, a))
    elif kind == "N":
        cone(p, 0.26, 0.17, 0.4, 0.14)
        cube(p, (0.26, 0.3, 0.5), (0, 0.02, 0.75), (math.radians(-15), 0, 0))
        cube(p, (0.22, 0.42, 0.2), (0, -0.16, 0.92), (math.radians(20), 0, 0))
        cube(p, (0.08, 0.08, 0.14), (0.07, 0.06, 1.08))
        cube(p, (0.08, 0.08, 0.14), (-0.07, 0.06, 1.08))
    elif kind == "B":
        cone(p, 0.24, 0.1, 0.6, 0.14)
        cyl(p, 0.17, 0.04, 0.72)
        sphere(p, 0.16, 0.95, (1, 1, 1.4))
        sphere(p, 0.05, 1.22)
    elif kind == "Q":
        cone(p, 0.27, 0.11, 0.8, 0.14)
        cyl(p, 0.2, 0.05, 0.92)
        cone(p, 0.12, 0.22, 0.2, 0.97)
        for i in range(8):
            a = i * math.pi / 4
            sphere(p, 0.045, 1.2, loc_xy=(0.19 * math.cos(a), 0.19 * math.sin(a)))
        sphere(p, 0.08, 1.22)
    elif kind == "K":
        cone(p, 0.28, 0.12, 0.88, 0.14)
        cyl(p, 0.21, 0.05, 1.0)
        cone(p, 0.13, 0.22, 0.2, 1.05)
        cube(p, (0.07, 0.07, 0.3), (0, 0, 1.4))
        cube(p, (0.22, 0.07, 0.07), (0, 0, 1.44))
    # join parts
    bpy.ops.object.select_all(action='DESELECT')
    for o in p:
        o.select_set(True)
    bpy.context.view_layer.objects.active = p[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.join()
    obj = bpy.context.active_object
    assign(obj, mat_white if white else mat_black)
    return obj

def place(kind, square, white, rot_z=0.0):
    f = "abcdefgh".index(square[0])
    r = int(square[1]) - 1
    obj = build(kind, white)
    obj.location = ((f - 3.5) * SQ, (r - 3.5) * SQ, TOP)
    obj.rotation_euler = (0, 0, rot_z + (0 if white else math.pi))
    obj.name = f"{'W' if white else 'B'}_{kind}_{square}"
    return obj

# ---------- Mid-game position ----------
white = [("K", "g1"), ("R", "f1"), ("R", "a1"), ("Q", "e2"), ("B", "c4"), ("N", "f3"),
         ("P", "a2"), ("P", "b2"), ("P", "c3"), ("P", "e4"), ("P", "f2"), ("P", "g2"), ("P", "h3")]
black = [("K", "g8"), ("R", "f8"), ("R", "d8"), ("Q", "d6"), ("B", "e7"), ("N", "c6"),
         ("P", "a7"), ("P", "b7"), ("P", "e5"), ("P", "f7"), ("P", "g7"), ("P", "h6")]
for k, s in white:
    place(k, s, True)
for k, s in black:
    place(k, s, False)

# A captured piece lying beside the board
cap = build("B", False)
cap.location = (5.2, 1.0, 0.25)
cap.rotation_euler = (math.radians(90), 0, math.radians(30))
cap2 = build("P", True)
cap2.location = (-5.2, -1.5, 0.15)
cap2.rotation_euler = (math.radians(90), 0, math.radians(-50))

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), 0, math.radians(35))
sun.data.angle = math.radians(5)

bpy.ops.object.light_add(type='AREA', location=(-6, -4, 7))
area = bpy.context.active_object
area.data.energy = 800
area.data.size = 5
area.rotation_euler = (Vector((0, 0, 0)) - area.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.object.light_add(type='AREA', location=(4, 8, 5))
rim = bpy.context.active_object
rim.data.energy = 400
rim.data.size = 4
rim.rotation_euler = (Vector((0, 0, 0)) - rim.location).to_track_quat('-Z', 'Y').to_euler()

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(3.5, -11.5, 9.0))
cam = bpy.context.active_object
cam.data.lens = 42
target = Vector((0, -0.3, 0.3))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
