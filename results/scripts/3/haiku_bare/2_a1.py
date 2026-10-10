import bpy
import math
import random
from mathutils import Vector

random.seed(7)

# ---------------------------------------------------------------------------
# Clean up the scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_mat(name, color, rough=0.5, metal=0.0, emit=0.0, transmission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit > 0.0:
        bsdf.inputs["Emission Color"].default_value = (color[0], color[1], color[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit
    if transmission > 0.0:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    return mat


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def box(name, loc, size, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    return assign(o, mat)


def cyl(name, loc, radius, depth, mat, rot=(0, 0, 0), verts=40):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    smooth(o)
    return assign(o, mat)


def cone(name, loc, r_bottom, r_top, depth, mat, rot=(0, 0, 0), verts=40):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r_bottom, radius2=r_top,
                                    depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    smooth(o)
    return assign(o, mat)


def sphere(name, loc, radius, mat, scale=(1, 1, 1), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=24, ring_count=12,
                                         location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    smooth(o)
    return assign(o, mat)


def torus(name, loc, major, minor, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    smooth(o)
    return assign(o, mat)


def aim(obj, target):
    d = Vector(target) - Vector(obj.location)
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
wood_mat = make_mat("Desk_Wood", (0.42, 0.26, 0.14), rough=0.55)
leg_mat = make_mat("Desk_Legs", (0.12, 0.12, 0.13), rough=0.35, metal=0.6)
wall_mat = make_mat("Wall", (0.78, 0.76, 0.72), rough=0.9)
floor_mat = make_mat("Floor", (0.35, 0.33, 0.30), rough=0.7)

laptop_mat = make_mat("Laptop_Body", (0.55, 0.56, 0.6), rough=0.3, metal=0.8)
keys_mat = make_mat("Laptop_Keys", (0.25, 0.25, 0.27), rough=0.5)
screen_mat = make_mat("Laptop_Screen", (0.3, 0.6, 0.9), rough=0.2, emit=1.2)
bezel_mat = make_mat("Laptop_Bezel", (0.02, 0.02, 0.025), rough=0.4)

mug_mat = make_mat("Mug_Ceramic", (0.9, 0.85, 0.75), rough=0.25)
coffee_mat = make_mat("Mug_Coffee", (0.12, 0.05, 0.02), rough=0.15)

pot_mat = make_mat("Pot_Terracotta", (0.7, 0.36, 0.2), rough=0.8)
soil_mat = make_mat("Pot_Soil", (0.1, 0.07, 0.05), rough=1.0)
stem_mat = make_mat("Plant_Stem", (0.2, 0.35, 0.12), rough=0.6)
leaf_mats = [
    make_mat("Leaf_A", (0.12, 0.45, 0.15), rough=0.5),
    make_mat("Leaf_B", (0.18, 0.55, 0.2), rough=0.5),
    make_mat("Leaf_C", (0.08, 0.35, 0.12), rough=0.5),
]

lamp_base_mat = make_mat("Lamp_Metal", (0.2, 0.2, 0.22), rough=0.3, metal=0.9)
lamp_shade_mat = make_mat("Lamp_Shade", (0.85, 0.2, 0.1), rough=0.4)
bulb_mat = make_mat("Lamp_Bulb", (1.0, 0.85, 0.6), rough=0.2, emit=8.0)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
box("Floor", (0, 0, -0.01), (4, 4, 0.02), floor_mat)
box("Wall", (0, 0.6, 1.5), (4, 0.02, 3.0), wall_mat)

# ---------------------------------------------------------------------------
# Desk
# ---------------------------------------------------------------------------
DESK_TOP_Z = 0.75
box("Desk_Top", (0, 0, DESK_TOP_Z - 0.015), (0.9, 0.5, 0.03), wood_mat)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("Desk_Leg", (sx * 0.42, sy * 0.2, 0.36), (0.04, 0.04, 0.72), leg_mat)

# ---------------------------------------------------------------------------
# Laptop (open, screen tilted slightly back)
# ---------------------------------------------------------------------------
LX, LY = 0.0, 0.03
base_z = DESK_TOP_Z + 0.006
box("Laptop_Base", (LX, LY, base_z), (0.32, 0.22, 0.012), laptop_mat)
box("Laptop_Keyboard", (LX, LY - 0.01, base_z + 0.0065), (0.26, 0.12, 0.002), keys_mat)
box("Laptop_Trackpad", (LX, LY - 0.075, base_z + 0.0065), (0.09, 0.06, 0.002), keys_mat)

hinge_y = LY + 0.11
hinge_z = base_z + 0.006
tilt = math.radians(-20)
panel_len = 0.21
cy = hinge_y + (panel_len / 2) * math.sin(-tilt)
cz = hinge_z + (panel_len / 2) * math.cos(tilt)
box("Laptop_Screen_Frame", (LX, cy, cz), (0.32, 0.012, panel_len), bezel_mat,
    rot=(tilt, 0, 0))
box("Laptop_Display", (LX, cy + 0.0065 * math.sin(-tilt) * 1.0, cz + 0.0), (0.30, 0.004, 0.19),
    screen_mat, rot=(tilt, 0, 0))

# ---------------------------------------------------------------------------
# Coffee mug
# ---------------------------------------------------------------------------
MUG_X, MUG_Y = -0.25, -0.05
MUG_H = 0.10
mug_center_z = DESK_TOP_Z + MUG_H / 2
cyl("Mug_Body", (MUG_X, MUG_Y, mug_center_z), 0.04, MUG_H, mug_mat)
cyl("Mug_Coffee", (MUG_X, MUG_Y, DESK_TOP_Z + MUG_H - 0.012), 0.036, 0.005, coffee_mat)
torus("Mug_Handle", (MUG_X + 0.048, MUG_Y, mug_center_z + 0.005), 0.024, 0.007, mug_mat,
      rot=(math.radians(90), 0, 0))

# ---------------------------------------------------------------------------
# Potted plant
# ---------------------------------------------------------------------------
PX, PY = 0.27, 0.06
pot_h = 0.09
cone("Pot", (PX, PY, DESK_TOP_Z + pot_h / 2), 0.055, 0.045, pot_h, pot_mat)
cyl("Pot_Soil", (PX, PY, DESK_TOP_Z + pot_h - 0.01), 0.046, 0.01, soil_mat)
stem_h = 0.16
cyl("Plant_Stem", (PX, PY, DESK_TOP_Z + pot_h + stem_h / 2), 0.004, stem_h, stem_mat)

for i in range(16):
    ang = random.uniform(0, math.tau)
    dist = random.uniform(0.01, 0.07)
    lx = PX + math.cos(ang) * dist
    ly = PY + math.sin(ang) * dist
    lz = DESK_TOP_Z + pot_h + random.uniform(0.04, 0.2)
    r = random.uniform(0.03, 0.05)
    tilt_x = random.uniform(-0.6, 0.6)
    tilt_y = random.uniform(-0.6, 0.6)
    mat = random.choice(leaf_mats)
    sphere(f"Leaf_{i:02d}", (lx, ly, lz), r, mat,
           scale=(1.0, 1.0, 0.35),
           rot=(tilt_x, tilt_y, ang))

# ---------------------------------------------------------------------------
# Desk lamp (soft warm light, back right)
# ---------------------------------------------------------------------------
LMX, LMY = 0.36, 0.15
cyl("Lamp_Base", (LMX, LMY, DESK_TOP_Z + 0.008), 0.06, 0.016, lamp_base_mat)
pole_h = 0.46
cyl("Lamp_Pole", (LMX, LMY, DESK_TOP_Z + pole_h / 2 + 0.016), 0.008, pole_h, lamp_base_mat)
head_z = DESK_TOP_Z + pole_h + 0.03
cone("Lamp_Shade", (LMX, LMY - 0.02, head_z), 0.07, 0.025, 0.10, lamp_shade_mat,
     rot=(math.radians(-20), 0, 0))
sphere("Lamp_Bulb", (LMX, LMY - 0.02, head_z - 0.03), 0.025, bulb_mat)

lamp_light_data = bpy.data.lights.new("Lamp_Area", 'AREA')
lamp_light_data.energy = 45.0
lamp_light_data.size = 0.18
lamp_light_data.color = (1.0, 0.84, 0.6)
lamp_light = bpy.data.objects.new("Lamp_Area", lamp_light_data)
scene.collection.objects.link(lamp_light)
lamp_light.location = (LMX, LMY - 0.03, head_z - 0.05)
aim(lamp_light, (LMX, LMY - 0.05, DESK_TOP_Z))

# ---------------------------------------------------------------------------
# Soft fill light and ambient world
# ---------------------------------------------------------------------------
fill_data = bpy.data.lights.new("Fill_Area", 'AREA')
fill_data.energy = 30.0
fill_data.size = 1.6
fill_data.color = (0.9, 0.94, 1.0)
fill = bpy.data.objects.new("Fill_Area", fill_data)
scene.collection.objects.link(fill)
fill.location = (-1.0, -1.1, 1.7)
aim(fill, (0.0, 0.0, DESK_TOP_Z + 0.1))

if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.06, 0.06, 0.07, 1.0)
    bg.inputs["Strength"].default_value = 0.6

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = 1.6
cam_data.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.15, -1.45, 1.25)
aim(cam, (0.02, 0.02, 0.88))
scene.camera = cam

# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------
scene.frame_start = 1
scene.frame_end = 1
