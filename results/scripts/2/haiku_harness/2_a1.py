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
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

COLL = bpy.data.collections.new("DeskScene")
scene.collection.children.link(COLL)

TOP = 0.775  # desk surface height

# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def make_mat(name, color, rough=0.5, metal=0.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)  # default node tree is created here
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return m

mat_wood = make_mat("Desk_Wood", (0.35, 0.22, 0.12), rough=0.45)
mat_wall = make_mat("Wall", (0.82, 0.80, 0.76), rough=0.9)
mat_floor = make_mat("Floor", (0.55, 0.45, 0.35), rough=0.6)
mat_metal = make_mat("Dark_Metal", (0.08, 0.08, 0.09), rough=0.35, metal=0.9)
mat_silver = make_mat("Laptop_Aluminum", (0.7, 0.7, 0.72), rough=0.3, metal=1.0)
mat_keys = make_mat("Keyboard", (0.05, 0.05, 0.06), rough=0.6)
mat_screen = make_mat("Screen_Glow", (0.2, 0.4, 0.8), rough=0.2,
                      emit=(0.3, 0.6, 1.0), emit_strength=2.0)
mat_ceramic = make_mat("Mug_Ceramic", (0.9, 0.35, 0.25), rough=0.25)
mat_coffee = make_mat("Coffee", (0.12, 0.06, 0.03), rough=0.1)
mat_pot = make_mat("Pot_Terracotta", (0.65, 0.3, 0.18), rough=0.8)
mat_soil = make_mat("Soil", (0.1, 0.07, 0.05), rough=1.0)
mat_leaf_a = make_mat("Leaf_A", (0.1, 0.45, 0.12), rough=0.5)
mat_leaf_b = make_mat("Leaf_B", (0.15, 0.55, 0.18), rough=0.45)
mat_bulb = make_mat("Bulb", (1.0, 0.9, 0.7), rough=0.3,
                    emit=(1.0, 0.85, 0.6), emit_strength=12.0)

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def new_object(name, builder, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
               mat=None, smooth=False):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    builder(bm)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.update()
    if mat is not None:
        me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    obj.location = loc
    obj.rotation_euler = rot
    obj.scale = scale
    COLL.objects.link(obj)
    return obj

def box_builder(bm):
    bmesh.ops.create_cube(bm, size=1.0)

def sphere_builder(bm):
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=1.0)

def cone_builder(r1, r2, depth, segments=32):
    def build(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                              segments=segments, radius1=r1, radius2=r2,
                              depth=depth)
    return build

def torus_builder(R, r, nu=32, nv=12):
    def build(bm):
        verts = []
        for i in range(nu):
            u = 2 * math.pi * i / nu
            row = []
            for j in range(nv):
                v = 2 * math.pi * j / nv
                x = (R + r * math.cos(v)) * math.cos(u)
                y = (R + r * math.cos(v)) * math.sin(u)
                z = r * math.sin(v)
                row.append(bm.verts.new((x, y, z)))
            verts.append(row)
        for i in range(nu):
            for j in range(nv):
                a = verts[i][j]
                b = verts[(i + 1) % nu][j]
                c = verts[(i + 1) % nu][(j + 1) % nv]
                d = verts[i][(j + 1) % nv]
                bm.faces.new((a, b, c, d))
    return build

def box(name, size, loc, mat, rot=(0, 0, 0)):
    return new_object(name, box_builder, loc=loc, rot=rot, scale=size, mat=mat)

# ---------------------------------------------------------------------------
# Room: floor and back wall
# ---------------------------------------------------------------------------
box("Floor", (5.0, 5.0, 0.05), (0, 0, -0.025), mat_floor)
box("Wall", (5.0, 0.06, 3.0), (0, 0.95, 1.5), mat_wall)

# ---------------------------------------------------------------------------
# Desk
# ---------------------------------------------------------------------------
box("Desk_Top", (2.0, 1.0, 0.05), (0, 0, TOP - 0.025), mat_wood)
for sx in (-0.9, 0.9):
    for sy in (-0.4, 0.4):
        box("Desk_Leg", (0.05, 0.05, TOP - 0.05), (sx, sy, (TOP - 0.05) / 2), mat_wood)

# ---------------------------------------------------------------------------
# Laptop
# ---------------------------------------------------------------------------
LX, LY = -0.1, 0.0
base_h = 0.016
box("Laptop_Base", (0.34, 0.24, base_h), (LX, LY, TOP + base_h / 2), mat_silver)
box("Laptop_Keys", (0.28, 0.13, 0.002), (LX, LY - 0.02, TOP + base_h + 0.001), mat_keys)

hinge_y = LY + 0.12
hinge_z = TOP + base_h
tilt = math.radians(-15)  # lid leans back, away from the viewer
half_h = 0.115
center_y = hinge_y - half_h * math.sin(tilt)
center_z = hinge_z + half_h * math.cos(tilt)
rot_lid = (tilt, 0, 0)

lid = box("Laptop_Lid", (0.34, 0.012, 0.23), (LX, center_y, center_z),
          mat_silver, rot=rot_lid)

# Normal pointing toward the viewer (front face of the lid)
n = Vector((0, -math.cos(tilt), -math.sin(tilt)))
display_center = Vector((LX, center_y, center_z)) + n * 0.0065
box("Laptop_Display", (0.31, 0.002, 0.2), tuple(display_center),
    mat_screen, rot=rot_lid)

# ---------------------------------------------------------------------------
# Coffee mug
# ---------------------------------------------------------------------------
MX, MY = 0.35, -0.12
mug_h = 0.1
mug_r = 0.045
new_object("Mug_Body", cone_builder(mug_r, mug_r, mug_h),
           loc=(MX, MY, TOP + mug_h / 2), mat=mat_ceramic, smooth=True)
new_object("Mug_Coffee", cone_builder(mug_r - 0.004, mug_r - 0.004, 0.004),
           loc=(MX, MY, TOP + mug_h - 0.008), mat=mat_coffee)
new_object("Mug_Handle", torus_builder(0.03, 0.008),
           loc=(MX + 0.055, MY, TOP + mug_h / 2),
           rot=(math.pi / 2, 0, 0), mat=mat_ceramic, smooth=True)

# ---------------------------------------------------------------------------
# Potted plant
# ---------------------------------------------------------------------------
PX, PY = 0.62, 0.15
pot_h = 0.11
new_object("Plant_Pot", cone_builder(0.05, 0.065, pot_h),
           loc=(PX, PY, TOP + pot_h / 2), mat=mat_pot, smooth=True)
new_object("Plant_Soil", cone_builder(0.06, 0.06, 0.01),
           loc=(PX, PY, TOP + pot_h - 0.01), mat=mat_soil)

leaf_count = 14
for i in range(leaf_count):
    angle = 2 * math.pi * i / leaf_count + random.uniform(-0.2, 0.2)
    tilt_out = random.uniform(0.4, 0.9)  # radians away from vertical
    height = random.uniform(0.12, 0.22)
    spread = random.uniform(0.03, 0.06)
    lx = PX + math.cos(angle) * spread
    ly = PY + math.sin(angle) * spread
    lz = TOP + pot_h + height * 0.6
    mat = mat_leaf_a if i % 2 == 0 else mat_leaf_b
    obj = new_object(f"Leaf_{i}", sphere_builder,
                     loc=(lx, ly, lz),
                     rot=(math.sin(angle) * tilt_out, -math.cos(angle) * tilt_out, angle),
                     scale=(0.035, 0.02, height),
                     mat=mat, smooth=True)

# ---------------------------------------------------------------------------
# Desk lamp (back-left corner)
# ---------------------------------------------------------------------------
DX, DY = -0.75, 0.25
new_object("Lamp_Base", cone_builder(0.07, 0.07, 0.025),
           loc=(DX, DY, TOP + 0.0125), mat=mat_metal, smooth=True)
new_object("Lamp_Pole", cone_builder(0.011, 0.011, 0.6, segments=16),
           loc=(DX, DY, TOP + 0.025 + 0.3), mat=mat_metal, smooth=True)

head_bottom = TOP + 0.625
head_depth = 0.16
new_object("Lamp_Shade", cone_builder(0.09, 0.035, head_depth),
           loc=(DX, DY, head_bottom + head_depth / 2),
           mat=mat_metal, smooth=True)
new_object("Lamp_Bulb", sphere_builder,
           loc=(DX, DY, head_bottom + 0.02), scale=(0.03, 0.03, 0.03),
           mat=mat_bulb, smooth=True)

# Soft key light from the lamp head
lamp_data = bpy.data.lights.new("Lamp_Light", type='AREA')
lamp_data.energy = 35.0
lamp_data.color = (1.0, 0.85, 0.62)
lamp_data.shape = 'DISK'
lamp_data.size = 0.25
lamp_obj = bpy.data.objects.new("Lamp_Light", lamp_data)
lamp_obj.location = (DX, DY, head_bottom - 0.02)
lamp_obj.rotation_euler = (0, 0, 0)  # area light emits along -Z (downward)
COLL.objects.link(lamp_obj)

# Gentle fill light from the camera side
fill_data = bpy.data.lights.new("Fill_Light", type='AREA')
fill_data.energy = 12.0
fill_data.color = (0.85, 0.9, 1.0)
fill_data.shape = 'RECTANGLE'
fill_data.size = 1.6
fill_data.size_y = 1.0
fill_obj = bpy.data.objects.new("Fill_Light", fill_data)
fill_obj.location = (1.6, -1.8, 2.4)
fill_obj.rotation_euler = (math.radians(55), 0, math.radians(35))
COLL.objects.link(fill_obj)

# ---------------------------------------------------------------------------
# World (soft, dim ambient)
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("Desk_World")  # default nodes are created here
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg is not None:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
    bg.inputs["Strength"].default_value = 0.5

# ---------------------------------------------------------------------------
# Camera framing the desk vignette
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Desk_Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("Desk_Camera", cam_data)
COLL.objects.link(cam_obj)

cam_loc = Vector((0.2, -2.9, 1.75))
target = Vector((0.0, 0.0, 0.95))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# ---------------------------------------------------------------------------
# Scene settings (still frame)
# ---------------------------------------------------------------------------
scene.frame_start = 1
scene.frame_end = 1
