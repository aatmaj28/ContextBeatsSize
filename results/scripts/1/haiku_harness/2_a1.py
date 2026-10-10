import bpy
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def make_mat(name, color, roughness=0.5, metallic=0.0,
             emission_strength=0.0, emission_color=None):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission_strength > 0.0:
        ec = emission_color if emission_color else color
        bsdf.inputs["Emission Color"].default_value = (*ec, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def assign(obj, mat, smooth=True):
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def box(name, loc, size, mat, rot=(0, 0, 0), smooth=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    return assign(o, mat, smooth)


def cyl(name, loc, radius, depth, mat, verts=48, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius,
                                        depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return assign(o, mat, True)


def cone(name, loc, r1, r2, depth, mat, verts=48, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2,
                                    depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return assign(o, mat, True)


def sphere(name, loc, radius, mat, scale=(1, 1, 1), subdiv=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=radius,
                                          location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    return assign(o, mat, True)


def add_light(name, ltype, loc, energy, color=(1, 1, 1), rot=(0, 0, 0)):
    ld = bpy.data.lights.new(name, type=ltype)
    ld.energy = energy
    ld.color = color
    obj = bpy.data.objects.new(name, ld)
    bpy.context.collection.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


clear_scene()

# ---------- Materials ----------
wood = make_mat("Wood", (0.42, 0.26, 0.14), roughness=0.5)
dark_metal = make_mat("DarkMetal", (0.08, 0.08, 0.09), roughness=0.4, metallic=0.5)
wall_mat = make_mat("Wall", (0.82, 0.80, 0.76), roughness=0.9)
floor_mat = make_mat("Floor", (0.25, 0.20, 0.16), roughness=0.8)
silver = make_mat("Laptop", (0.72, 0.72, 0.75), roughness=0.3, metallic=1.0)
screen_dark = make_mat("ScreenBody", (0.02, 0.02, 0.025), roughness=0.2)
screen_glow = make_mat("ScreenDisplay", (0.35, 0.55, 0.85),
                       roughness=0.2, emission_strength=1.5)
ceramic = make_mat("Ceramic", (0.92, 0.91, 0.88), roughness=0.25)
coffee = make_mat("Coffee", (0.12, 0.06, 0.03), roughness=0.15)
terracotta = make_mat("Terracotta", (0.62, 0.32, 0.18), roughness=0.7)
soil = make_mat("Soil", (0.1, 0.07, 0.04), roughness=0.95)
leaf_a = make_mat("LeafA", (0.10, 0.45, 0.12), roughness=0.45)
leaf_b = make_mat("LeafB", (0.16, 0.55, 0.16), roughness=0.45)
lamp_black = make_mat("LampBlack", (0.04, 0.04, 0.05), roughness=0.3, metallic=0.6)

# ---------- Environment ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.04, 0.04, 0.05, 1.0)
    bg.inputs["Strength"].default_value = 0.5

# Floor and back wall
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.scale = (6, 6, 1)
assign(floor, floor_mat, False)

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.5, 1.5),
                                 rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.name = "Wall"
wall.scale = (4, 3, 1)
assign(wall, wall_mat, False)

# ---------- Desk ----------
DESK_TOP = 0.77
box("DeskTop", (0, 0, 0.75), (1.6, 0.8, 0.04), wood)
for i, (x, y) in enumerate([(-0.74, -0.34), (0.74, -0.34),
                            (-0.74, 0.34), (0.74, 0.34)]):
    box(f"DeskLeg{i}", (x, y, 0.365), (0.05, 0.05, 0.73), wood)

# ---------- Laptop ----------
LX, LY = -0.25, 0.0
box("LaptopBase", (LX, LY, DESK_TOP + 0.006), (0.34, 0.24, 0.012), silver)
tilt = math.radians(15)
hinge_y = LY - 0.12
hinge_z = DESK_TOP + 0.012
half = 0.115
scr_cy = hinge_y - math.sin(tilt) * half
scr_cz = hinge_z + math.cos(tilt) * half
box("LaptopScreen", (LX, scr_cy, scr_cz), (0.34, 0.01, 0.23),
    screen_dark, rot=(tilt, 0, 0))
off = 0.0065
box("LaptopDisplay",
    (LX, scr_cy + math.cos(tilt) * off, scr_cz + math.sin(tilt) * off),
    (0.31, 0.002, 0.2), screen_glow, rot=(tilt, 0, 0))

# ---------- Coffee mug ----------
MX, MY = 0.35, -0.05
MUG_H = 0.10
mug_center = DESK_TOP + MUG_H / 2
cyl("Mug", (MX, MY, mug_center), 0.04, MUG_H, ceramic, verts=64)
cyl("MugCoffee", (MX, MY, DESK_TOP + MUG_H - 0.012), 0.036, 0.006, coffee, verts=64)
bpy.ops.mesh.primitive_torus_add(
    location=(MX + 0.045, MY, mug_center),
    rotation=(math.radians(90), 0, 0),
    major_radius=0.026, minor_radius=0.007,
    major_segments=32, minor_segments=12)
handle = bpy.context.active_object
handle.name = "MugHandle"
assign(handle, ceramic, True)

# ---------- Potted plant ----------
PX, PY = -0.62, 0.10
POT_H = 0.13
cone("PlantPot", (PX, PY, DESK_TOP + POT_H / 2), 0.07, 0.058, POT_H,
     terracotta, verts=48)
cyl("PlantSoil", (PX, PY, DESK_TOP + POT_H - 0.012), 0.06, 0.01, soil, verts=40)

base_z = DESK_TOP + POT_H + 0.05
for i in range(16):
    ang = random.uniform(0, 2 * math.pi)
    dist = random.uniform(0.0, 0.085)
    h = base_z + random.uniform(0.0, 0.22)
    r = random.uniform(0.032, 0.055)
    lx = PX + math.cos(ang) * dist
    ly = PY + math.sin(ang) * dist
    mat = leaf_a if i % 2 == 0 else leaf_b
    sphere(f"Leaf{i}", (lx, ly, h), r, mat,
           scale=(1.0, 1.0, random.uniform(0.45, 0.65)), subdiv=2)

# ---------- Desk lamp ----------
DLX, DLY = 0.62, 0.22
cyl("LampBase", (DLX, DLY, DESK_TOP + 0.01), 0.07, 0.02, lamp_black, verts=48)
ARM_BOTTOM = DESK_TOP + 0.02
ARM_TOP = 1.22
arm_len = ARM_TOP - ARM_BOTTOM
box("LampArm", (DLX, DLY, ARM_BOTTOM + arm_len / 2), (0.016, 0.016, arm_len),
    lamp_black, smooth=True)
HEAD_H = 0.12
head_center = 1.27
cone("LampHead", (DLX, DLY, head_center), 0.10, 0.03, HEAD_H, lamp_black, verts=48)
bulb_z = head_center - HEAD_H / 2 - 0.01
sphere("LampBulb", (DLX, DLY, bulb_z), 0.025,
       make_mat("Bulb", (1.0, 0.92, 0.75), roughness=0.3,
                emission_strength=8.0, emission_color=(1.0, 0.9, 0.7)),
       subdiv=2)

# ---------- Lighting ----------
# Soft large key from above/front
add_light("KeyArea", "AREA", (0.0, 1.0, 2.4), 250.0, color=(1.0, 0.97, 0.92),
          rot=(math.radians(15), 0, 0))
bpy.data.lights["KeyArea"].size = 2.0

# Warm desk lamp spot pointing down onto the desk
lamp_light = add_light("DeskLampSpot", "SPOT", (DLX, DLY, bulb_z - 0.02), 120.0,
                       color=(1.0, 0.85, 0.6), rot=(0, 0, 0))
lamp_light.data.spot_size = math.radians(70)
lamp_light.data.spot_blend = 0.6
lamp_light.data.shadow_soft_size = 0.05

# Gentle fill from the left
add_light("FillArea", "AREA", (-1.6, 0.6, 1.4), 40.0, color=(0.85, 0.9, 1.0),
          rot=(math.radians(60), math.radians(-70), 0))
bpy.data.lights["FillArea"].size = 1.5

# ---------- Camera ----------
cam_loc = Vector((0.05, 2.1, 1.35))
cam_target = Vector((0.0, 0.0, 0.92))
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_data.sensor_width = 36
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.link(cam)
cam.location = cam_loc
direction = cam_target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Scene settings ----------
scene.frame_start = 1
scene.frame_end = 1
