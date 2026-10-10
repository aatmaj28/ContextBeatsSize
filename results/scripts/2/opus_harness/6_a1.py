import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- clean ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- materials ----------
def make_mat(name, color, rough=0.4, spec=0.5, coat=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    try:
        bsdf.inputs["Coat Weight"].default_value = coat
    except Exception:
        pass
    return m

mat_light_sq = make_mat("LightSquare", (0.78, 0.62, 0.42), 0.35, coat=0.3)
mat_dark_sq = make_mat("DarkSquare", (0.25, 0.13, 0.06), 0.35, coat=0.3)
mat_frame = make_mat("Frame", (0.12, 0.06, 0.03), 0.3, coat=0.5)
mat_white = make_mat("WhitePiece", (0.92, 0.88, 0.78), 0.25, coat=0.4)
mat_black = make_mat("BlackPiece", (0.03, 0.03, 0.035), 0.2, coat=0.6)
mat_table = make_mat("Table", (0.35, 0.33, 0.3), 0.7)

def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

def finish(obj, mat, name, do_smooth=True):
    obj.name = name
    obj.data.materials.append(mat)
    if do_smooth:
        smooth(obj)
    return obj

# ---------- primitives ----------
def cone(r1, r2, depth, loc, mat, name="part"):
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=r1, radius2=r2,
                                    depth=depth, location=loc)
    o = finish(bpy.context.active_object, mat, name)
    return o

def sphere(r, loc, mat, scale=(1, 1, 1), name="part"):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16,
                                         radius=r, location=loc)
    o = bpy.context.active_object
    o.scale = scale
    return finish(o, mat, name)

def box(loc, scale, mat, rot=(0, 0, 0), name="part"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = scale
    return finish(o, mat, name, do_smooth=False)

# ---------- board ----------
for f in range(8):
    for r in range(8):
        x, y = f - 3.5, r - 3.5
        dark = (f + r) % 2 == 0
        box((x, y, -0.05), (1, 1, 0.1), mat_dark_sq if dark else mat_light_sq,
            name=f"Square_{f}{r}")

# frame
box((0, 4.3, -0.075), (9.2, 0.6, 0.15), mat_frame, name="FrameN")
box((0, -4.3, -0.075), (9.2, 0.6, 0.15), mat_frame, name="FrameS")
box((4.3, 0, -0.075), (0.6, 8.0, 0.15), mat_frame, name="FrameE")
box((-4.3, 0, -0.075), (0.6, 8.0, 0.15), mat_frame, name="FrameW")
box((0, 0, -0.2), (9.2, 9.2, 0.1), mat_frame, name="FrameBase")

# table
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.25))
finish(bpy.context.active_object, mat_table, "Table", do_smooth=False)

# ---------- pieces ----------
def sq(name):
    f = "abcdefgh".index(name[0])
    r = int(name[1]) - 1
    return f - 3.5, r - 3.5

def base(x, y, m, tag):
    cone(0.34, 0.3, 0.1, (x, y, 0.05), m, tag + "_base")
    cone(0.3, 0.26, 0.06, (x, y, 0.13), m, tag + "_base2")

def pawn(x, y, m, tag, d):
    base(x, y, m, tag)
    cone(0.22, 0.09, 0.38, (x, y, 0.35), m, tag + "_body")
    cone(0.16, 0.16, 0.04, (x, y, 0.53), m, tag + "_collar")
    sphere(0.14, (x, y, 0.65), m, name=tag + "_head")

def rook(x, y, m, tag, d):
    base(x, y, m, tag)
    cone(0.26, 0.2, 0.5, (x, y, 0.41), m, tag + "_body")
    cone(0.26, 0.26, 0.16, (x, y, 0.74), m, tag + "_top")
    for i in range(4):
        a = math.radians(45 + 90 * i)
        box((x + 0.18 * math.cos(a), y + 0.18 * math.sin(a), 0.86),
            (0.12, 0.12, 0.1), m, rot=(0, 0, a), name=f"{tag}_crenel{i}")

def knight(x, y, m, tag, d):
    base(x, y, m, tag)
    cone(0.25, 0.18, 0.3, (x, y, 0.31), m, tag + "_body")
    box((x, y - 0.03 * d, 0.62), (0.2, 0.3, 0.45), m,
        rot=(-0.3 * d, 0, 0), name=tag + "_neck")
    box((x, y + 0.13 * d, 0.8), (0.19, 0.42, 0.18), m,
        rot=(0.25 * d, 0, 0), name=tag + "_head")
    for s in (-1, 1):
        cone(0.04, 0.0, 0.12, (x + 0.06 * s, y - 0.05 * d, 0.92), m, f"{tag}_ear{s}")
    sphere(0.025, (x + 0.1, y + 0.18 * d, 0.84), mat_frame if m is mat_white else mat_white,
           name=tag + "_eyeR")
    sphere(0.025, (x - 0.1, y + 0.18 * d, 0.84), mat_frame if m is mat_white else mat_white,
           name=tag + "_eyeL")

def bishop(x, y, m, tag, d):
    base(x, y, m, tag)
    cone(0.24, 0.08, 0.6, (x, y, 0.46), m, tag + "_body")
    cone(0.15, 0.15, 0.04, (x, y, 0.74), m, tag + "_collar")
    sphere(0.13, (x, y, 0.9), m, scale=(1, 1, 1.4), name=tag + "_head")
    sphere(0.045, (x, y, 1.1), m, name=tag + "_tip")

def queen(x, y, m, tag, d):
    base(x, y, m, tag)
    cone(0.27, 0.1, 0.75, (x, y, 0.535), m, tag + "_body")
    cone(0.17, 0.17, 0.04, (x, y, 0.92), m, tag + "_collar")
    sphere(0.14, (x, y, 1.0), m, name=tag + "_neck")
    cone(0.1, 0.19, 0.14, (x, y, 1.12), m, tag + "_crown")
    for i in range(8):
        a = math.radians(45 * i)
        sphere(0.03, (x + 0.17 * math.cos(a), y + 0.17 * math.sin(a), 1.2), m,
               name=f"{tag}_jewel{i}")
    sphere(0.05, (x, y, 1.22), m, name=tag + "_tip")

def king(x, y, m, tag, d):
    base(x, y, m, tag)
    cone(0.28, 0.11, 0.85, (x, y, 0.585), m, tag + "_body")
    cone(0.18, 0.18, 0.04, (x, y, 1.02), m, tag + "_collar")
    cone(0.14, 0.2, 0.16, (x, y, 1.12), m, tag + "_crown")
    box((x, y, 1.36), (0.07, 0.07, 0.28), m, name=tag + "_crossV")
    box((x, y, 1.38), (0.2, 0.07, 0.07), m, name=tag + "_crossH")

builders = {"P": pawn, "R": rook, "N": knight, "B": bishop, "Q": queen, "K": king}

# mid-game position (Italian-style middlegame)
white = {"g1": "K", "f1": "R", "a1": "R", "e2": "Q", "c4": "B", "f3": "N",
         "a2": "P", "b2": "P", "c3": "P", "d4": "P", "f2": "P", "g2": "P", "h3": "P"}
black = {"g8": "K", "f8": "R", "a8": "R", "d8": "Q", "e7": "B", "c6": "N",
         "a7": "P", "b7": "P", "c7": "P", "d6": "P", "e5": "P", "f7": "P", "g7": "P", "h6": "P"}

for squ, t in white.items():
    x, y = sq(squ)
    builders[t](x, y, mat_white, f"W{t}_{squ}", 1)
for squ, t in black.items():
    x, y = sq(squ)
    builders[t](x, y, mat_black, f"B{t}_{squ}", -1)

# captured pieces beside the board
pawn(5.3, -2.5, mat_black, "CapB_P1", -1)
knight(5.3, -1.6, mat_black, "CapB_N", -1)
pawn(-5.3, 2.5, mat_white, "CapW_P1", 1)
pawn(-5.3, 1.7, mat_white, "CapW_P2", 1)

# ---------- lighting ----------
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.data.angle = math.radians(5)
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(-6, -4, 7))
area = bpy.context.active_object
area.data.energy = 800
area.data.size = 6
area.rotation_euler = (Vector((0, 0, 0)) - area.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.object.light_add(type='AREA', location=(3, 8, 5))
rim = bpy.context.active_object
rim.data.energy = 400
rim.data.size = 4
rim.rotation_euler = (Vector((0, 0, 0.5)) - rim.location).to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.055, 0.07, 1)
bg.inputs["Strength"].default_value = 0.6

# ---------- camera ----------
bpy.ops.object.camera_add(location=(6.5, -10.0, 8.5))
cam = bpy.context.active_object
cam.data.lens = 42
target = Vector((0, 0.3, 0.2))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (target - cam.location).length
cam.data.dof.aperture_fstop = 4.0
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
