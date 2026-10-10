import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

scene = bpy.context.scene
random.seed(7)

# ---------- clear default scene ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)


# ---------- helpers ----------
def make_mat(name, color, rough=0.5, metal=0.0, emit_color=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit_color is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return m


def f_cube(bm):
    bmesh.ops.create_cube(bm, size=1.0)


def f_cylinder(radius_bottom=1.0, radius_top=1.0, segments=40, cap=True):
    def f(bm):
        bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segments,
                              radius1=radius_bottom, radius2=radius_top, depth=1.0)
    return f


def f_sphere(segments=24, rings=14):
    def f(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0)
    return f


def f_torus(R, r, nu=32, nv=12):
    def f(bm):
        grid = []
        for i in range(nu):
            u = 2 * math.pi * i / nu
            row = []
            for j in range(nv):
                v = 2 * math.pi * j / nv
                rad = R + r * math.cos(v)
                row.append(bm.verts.new((rad * math.cos(u), r * math.sin(v), rad * math.sin(u))))
            grid.append(row)
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((grid[i][j], grid[(i + 1) % nu][j],
                              grid[(i + 1) % nu][(j + 1) % nv], grid[i][(j + 1) % nv]))
    return f


def build(name, fill, material, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), smooth=False):
    bm = bmesh.new()
    fill(bm)
    if smooth:
        for f in bm.faces:
            f.smooth = True
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    obj = bpy.data.objects.new(name, me)
    scene.collection.objects.link(obj)
    obj.location = Vector(loc)
    obj.scale = Vector(scale)
    obj.rotation_euler = rot
    return obj


def rot_offset(local, angle_x):
    return Matrix.Rotation(angle_x, 3, 'X') @ Vector(local)


# ---------- materials ----------
m_wall = make_mat("Wall", (0.82, 0.78, 0.70), rough=0.9)
m_floor = make_mat("Floor", (0.30, 0.28, 0.26), rough=0.8)
m_wood = make_mat("Wood", (0.38, 0.23, 0.12), rough=0.45)
m_silver = make_mat("Silver", (0.65, 0.65, 0.68), rough=0.3, metal=0.9)
m_dark = make_mat("DarkPlastic", (0.03, 0.03, 0.035), rough=0.4)
m_keys = make_mat("Keys", (0.15, 0.15, 0.16), rough=0.6)
m_screen = make_mat("Display", (0.05, 0.1, 0.2), rough=0.1,
                    emit_color=(0.3, 0.6, 1.0), emit_strength=1.2)
m_mug = make_mat("Mug", (0.92, 0.92, 0.90), rough=0.25)
m_coffee = make_mat("Coffee", (0.14, 0.07, 0.03), rough=0.2)
m_pot = make_mat("Terracotta", (0.62, 0.30, 0.16), rough=0.7)
m_soil = make_mat("Soil", (0.08, 0.05, 0.03), rough=1.0)
m_leaf = make_mat("Leaf", (0.10, 0.42, 0.12), rough=0.5)
m_stem = make_mat("Stem", (0.18, 0.35, 0.12), rough=0.6)
m_lampmetal = make_mat("LampMetal", (0.12, 0.12, 0.13), rough=0.35, metal=0.8)
m_shade = make_mat("Shade", (0.92, 0.88, 0.78), rough=0.8)
m_bulb = make_mat("Bulb", (1.0, 0.92, 0.75), rough=0.3,
                  emit_color=(1.0, 0.85, 0.6), emit_strength=6.0)

# ---------- room ----------
build("Floor", f_cube, m_floor, loc=(0, 0, -0.01), scale=(8, 8, 0.02))
build("Wall", f_cube, m_wall, loc=(0, 0.75, 2.0), scale=(8, 0.05, 4.0))

# ---------- desk ----------
DESK_TOP_Z = 0.78
build("DeskTop", f_cube, m_wood, loc=(0, 0, DESK_TOP_Z - 0.02), scale=(1.6, 0.8, 0.04), smooth=False)
for sx in (-0.72, 0.72):
    for sy in (-0.32, 0.32):
        build("DeskLeg", f_cube, m_wood,
              loc=(sx, sy, (DESK_TOP_Z - 0.04) / 2),
              scale=(0.05, 0.05, DESK_TOP_Z - 0.04))

# ---------- laptop ----------
LX, LY = -0.02, 0.02
base_top = DESK_TOP_Z + 0.012
build("LaptopBase", f_cube, m_silver,
      loc=(LX, LY, DESK_TOP_Z + 0.006), scale=(0.32, 0.22, 0.012))
build("LaptopKeys", f_cube, m_keys,
      loc=(LX, LY + 0.01, base_top + 0.0005), scale=(0.26, 0.13, 0.001))

hinge = Vector((LX, LY + 0.11, base_top))
open_angle = math.radians(-20)  # screen leans back (about 110 degrees opening)
screen_center = hinge + rot_offset((0, 0, 0.105), open_angle)
screen_rot = (open_angle, 0, 0)
build("LaptopScreen", f_cube, m_silver,
      loc=screen_center, scale=(0.31, 0.008, 0.21), rot=screen_rot)
display_center = hinge + rot_offset((0, -0.0045, 0.105), open_angle)
build("LaptopDisplay", f_cube, m_screen,
      loc=display_center, scale=(0.28, 0.002, 0.18), rot=screen_rot)

# ---------- coffee mug ----------
MX, MY = 0.30, -0.14
MUG_H = 0.10
MUG_R = 0.04
build("Mug", f_cylinder(1.0, 1.0, 40, True), m_mug,
      loc=(MX, MY, DESK_TOP_Z + MUG_H / 2), scale=(MUG_R, MUG_R, MUG_H), smooth=True)
build("Coffee", f_cylinder(1.0, 1.0, 40, True), m_coffee,
      loc=(MX, MY, DESK_TOP_Z + MUG_H - 0.008), scale=(MUG_R * 0.92, MUG_R * 0.92, 0.003))
build("MugHandle", f_torus(0.030, 0.008, 32, 12), m_mug,
      loc=(MX + 0.065, MY, DESK_TOP_Z + MUG_H * 0.5), smooth=True)

# ---------- potted plant ----------
PX, PY = -0.55, 0.15
POT_H = 0.12
pot_base_z = DESK_TOP_Z
build("Pot", f_cylinder(0.07, 0.09, 40, True), m_pot,
      loc=(PX, PY, pot_base_z + POT_H / 2), scale=(1, 1, POT_H), smooth=True)
soil_z = pot_base_z + POT_H - 0.01
build("Soil", f_cylinder(1.0, 1.0, 40, True), m_soil,
      loc=(PX, PY, soil_z), scale=(0.085, 0.085, 0.01))

# stems
for k in range(5):
    a = random.uniform(0, 2 * math.pi)
    d = random.uniform(0.0, 0.03)
    sx = PX + math.cos(a) * d
    sy = PY + math.sin(a) * d
    h = random.uniform(0.14, 0.22)
    build("Stem", f_cylinder(1.0, 0.8, 8, True), m_stem,
          loc=(sx, sy, soil_z + h / 2), scale=(0.004, 0.004, h))

# leaves
top = soil_z
for k in range(18):
    a = random.uniform(0, 2 * math.pi)
    d = random.uniform(0.02, 0.06)
    h = random.uniform(0.06, 0.20)
    tilt = math.radians(random.uniform(35, 65))
    lx = PX + math.cos(a) * d
    ly = PY + math.sin(a) * d
    lz = top + h
    length = random.uniform(0.06, 0.09)
    build("Leaf", f_sphere(16, 8), m_leaf,
          loc=(lx + math.cos(a) * length * 0.4 * math.sin(tilt),
               ly + math.sin(a) * length * 0.4 * math.sin(tilt),
               lz + length * 0.4 * math.cos(tilt)),
          scale=(0.03, 0.009, length),
          rot=(0, tilt, a),
          smooth=True)

# ---------- desk lamp ----------
LAMP_X, LAMP_Y = 0.62, 0.22
build("LampBase", f_cylinder(1.0, 1.0, 40, True), m_lampmetal,
      loc=(LAMP_X, LAMP_Y, DESK_TOP_Z + 0.01), scale=(0.07, 0.07, 0.02), smooth=True)
POLE_H = 0.46
build("LampPole", f_cylinder(1.0, 1.0, 16, True), m_lampmetal,
      loc=(LAMP_X, LAMP_Y, DESK_TOP_Z + 0.02 + POLE_H / 2),
      scale=(0.01, 0.01, POLE_H))
shade_z = DESK_TOP_Z + 0.02 + POLE_H + 0.02
build("LampArm", f_cylinder(1.0, 1.0, 12, True), m_lampmetal,
      loc=(LAMP_X - 0.06, LAMP_Y, shade_z - 0.02), scale=(0.008, 0.008, 0.12),
      rot=(0, math.radians(90), 0))
build("LampShade", f_cylinder(0.12, 0.04, 48, False), m_shade,
      loc=(LAMP_X - 0.12, LAMP_Y, shade_z), scale=(1, 1, 0.13), smooth=True)
bulb_z = shade_z - 0.04
build("Bulb", f_sphere(20, 10), m_bulb,
      loc=(LAMP_X - 0.12, LAMP_Y, bulb_z), scale=(0.03, 0.03, 0.03), smooth=True)

# soft area light from the lamp shade (opens downward)
lamp_light_data = bpy.data.lights.new(name="LampLight", type='AREA')
lamp_light_data.energy = 90.0
lamp_light_data.size = 0.25
lamp_light_data.color = (1.0, 0.86, 0.66)
lamp_light = bpy.data.objects.new("LampLight", lamp_light_data)
scene.collection.objects.link(lamp_light)
lamp_light.location = (LAMP_X - 0.12, LAMP_Y, bulb_z - 0.03)

# gentle fill from the front so the scene isn't pitch black
fill_data = bpy.data.lights.new(name="FillLight", type='AREA')
fill_data.energy = 25.0
fill_data.size = 2.0
fill_data.color = (0.9, 0.93, 1.0)
fill = bpy.data.objects.new("FillLight", fill_data)
scene.collection.objects.link(fill)
fill.location = (1.2, -2.0, 2.2)
fill.rotation_euler = Vector((0.9, 0.0, 0.5)).normalized() * 0 + (
    Vector((0, 0, -1)).rotation_difference(Vector((-1.2, 2.0, -2.2)).normalized()).to_euler())

# ---------- world ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.03, 0.03, 0.035, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------- camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_loc = Vector((1.35, -1.75, 1.45))
cam_target = Vector((-0.05, 0.0, 0.95))
cam_obj.location = cam_loc
direction = (cam_target - cam_loc).normalized()
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- timeline ----------
scene.frame_start = 1
scene.frame_end = 1
