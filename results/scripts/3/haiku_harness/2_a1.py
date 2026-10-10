import bpy
import math
import random
from mathutils import Vector, Euler

random.seed(7)

# ---------------------------------------------------------------------------
# Clear the default scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for light in list(bpy.data.lights):
    if light.users == 0:
        bpy.data.lights.remove(light)
for cam in list(bpy.data.cameras):
    if cam.users == 0:
        bpy.data.cameras.remove(cam)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_mat(name, color, rough=0.5, metal=0.0, emit=None, emit_strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (emit[0], emit[1], emit[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat


def assign(obj, mat, smooth=False):
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def add_box(name, size, loc, mat, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    return assign(o, mat)


def add_cylinder(name, radius, depth, loc, mat, verts=48, rot=(0.0, 0.0, 0.0), smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return assign(o, mat, smooth)


def add_cone(name, r_bottom, r_top, depth, loc, mat, verts=32, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r_bottom, radius2=r_top,
                                    depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return assign(o, mat, True)


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
wood_mat = make_mat("Desk_Wood", (0.42, 0.26, 0.14), rough=0.45)
leg_mat = make_mat("Desk_Metal", (0.08, 0.08, 0.09), rough=0.35, metal=0.9)
floor_mat = make_mat("Floor", (0.55, 0.55, 0.57), rough=0.8)
laptop_mat = make_mat("Laptop_Aluminum", (0.6, 0.6, 0.63), rough=0.3, metal=1.0)
screen_bezel_mat = make_mat("Laptop_Bezel", (0.02, 0.02, 0.02), rough=0.5)
screen_mat = make_mat("Laptop_Screen", (0.05, 0.1, 0.2), rough=0.2,
                      emit=(0.3, 0.6, 1.0), emit_strength=1.5)
mug_mat = make_mat("Mug_Ceramic", (0.85, 0.42, 0.25), rough=0.25)
coffee_mat = make_mat("Coffee", (0.12, 0.05, 0.02), rough=0.15)
pot_mat = make_mat("Pot_Terracotta", (0.7, 0.32, 0.18), rough=0.7)
soil_mat = make_mat("Soil", (0.1, 0.06, 0.04), rough=0.95)
leaf_mats = [
    make_mat("Leaf_A", (0.12, 0.45, 0.14), rough=0.5),
    make_mat("Leaf_B", (0.18, 0.55, 0.2), rough=0.5),
    make_mat("Leaf_C", (0.08, 0.35, 0.12), rough=0.5),
]
notebook_mat = make_mat("Notebook", (0.15, 0.25, 0.55), rough=0.6)
lamp_mat = make_mat("Lamp_Metal", (0.15, 0.15, 0.16), rough=0.3, metal=0.8)
shade_mat = make_mat("Lamp_Shade", (0.9, 0.9, 0.85), rough=0.6)

# ---------------------------------------------------------------------------
# Room: floor
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0.0, 0.0, 0.0))
floor = bpy.context.active_object
floor.name = "Floor"
assign(floor, floor_mat)

# ---------------------------------------------------------------------------
# Desk
# ---------------------------------------------------------------------------
DESK_TOP_Z = 0.74
add_box("Desk_Top", (1.6, 0.8, 0.04), (0.0, 0.0, DESK_TOP_Z), wood_mat)
desk_surface = DESK_TOP_Z + 0.02  # top surface height

for i, (lx, ly) in enumerate([(-0.74, -0.34), (0.74, -0.34), (-0.74, 0.34), (0.74, 0.34)]):
    add_box(f"Desk_Leg_{i}", (0.04, 0.04, 0.72), (lx, ly, 0.36), leg_mat)

# ---------------------------------------------------------------------------
# Laptop (base + tilted lid with screen)
# ---------------------------------------------------------------------------
LAP_Y = 0.02
base_t = 0.012
add_box("Laptop_Base", (0.32, 0.22, base_t), (0.0, LAP_Y, desk_surface + base_t / 2), laptop_mat)

hinge = Vector((0.0, LAP_Y + 0.11, desk_surface + base_t))
lid_tilt = math.radians(-20)          # leans back, away from the viewer
lid_rot = Euler((lid_tilt, 0.0, 0.0), 'XYZ')
lid_half_h = 0.11
off = lid_rot.to_matrix() @ Vector((0.0, 0.0, lid_half_h))
lid_center = hinge + off

add_box("Laptop_Lid", (0.32, 0.008, 0.22), tuple(lid_center), laptop_mat,
        rot=(lid_tilt, 0.0, 0.0))

disp_off = lid_rot.to_matrix() @ Vector((0.0, -0.0045, 0.0))
disp_center = lid_center + disp_off
add_box("Laptop_Display", (0.29, 0.002, 0.18), tuple(disp_center), screen_mat,
        rot=(lid_tilt, 0.0, 0.0))

# ---------------------------------------------------------------------------
# Coffee mug with handle and coffee
# ---------------------------------------------------------------------------
MUG_POS = (0.45, -0.12)
MUG_H = 0.10
mug_z = desk_surface + MUG_H / 2
add_cylinder("Mug_Body", 0.04, MUG_H, (MUG_POS[0], MUG_POS[1], mug_z), mug_mat, verts=48)

bpy.ops.mesh.primitive_torus_add(
    major_radius=0.028, minor_radius=0.008,
    location=(MUG_POS[0] + 0.045, MUG_POS[1], mug_z),
    rotation=(math.radians(90), 0.0, 0.0))
handle = bpy.context.active_object
handle.name = "Mug_Handle"
assign(handle, mug_mat, True)

add_cylinder("Mug_Coffee", 0.037, 0.003,
             (MUG_POS[0], MUG_POS[1], desk_surface + MUG_H - 0.012), coffee_mat, verts=48)

# ---------------------------------------------------------------------------
# Small potted plant
# ---------------------------------------------------------------------------
PLANT_POS = (-0.48, -0.16)
POT_H = 0.14
pot_z = desk_surface + POT_H / 2
add_cone("Pot", 0.07, 0.09, POT_H, (PLANT_POS[0], PLANT_POS[1], pot_z), pot_mat)
soil_z = desk_surface + POT_H - 0.006
add_cylinder("Soil", 0.086, 0.01, (PLANT_POS[0], PLANT_POS[1], soil_z), soil_mat, verts=32)

top_z = desk_surface + POT_H
num_leaves = 14
for i in range(num_leaves):
    a = i * 2.39996  # golden angle
    tilt = math.radians(random.uniform(25, 50))
    length = random.uniform(0.08, 0.11)
    width = random.uniform(0.022, 0.03)
    dirv = Vector((math.sin(tilt) * math.cos(a), math.sin(tilt) * math.sin(a), math.cos(tilt)))
    center = Vector((PLANT_POS[0], PLANT_POS[1], top_z)) + dirv * (length * 0.8)
    center.z += 0.01 * (i % 3)

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=16, ring_count=8, radius=1.0,
        location=tuple(center),
        rotation=(0.0, tilt, a))
    leaf = bpy.context.active_object
    leaf.name = f"Leaf_{i}"
    leaf.scale = (width, width * 0.4, length)
    assign(leaf, random.choice(leaf_mats), True)

# ---------------------------------------------------------------------------
# Notebook, tidy detail
# ---------------------------------------------------------------------------
add_box("Notebook", (0.2, 0.15, 0.012), (-0.12, -0.18, desk_surface + 0.006),
        notebook_mat, rot=(0.0, 0.0, math.radians(8)))

# ---------------------------------------------------------------------------
# Desk lamp (base, arm, shade) with soft area light underneath
# ---------------------------------------------------------------------------
LAMP_X, LAMP_Y = -0.62, 0.22
add_cylinder("Lamp_Base", 0.07, 0.02, (LAMP_X, LAMP_Y, desk_surface + 0.01), lamp_mat, verts=40)

ARM_BOTTOM = desk_surface + 0.02
ARM_TOP = 1.08
arm_len = ARM_TOP - ARM_BOTTOM
add_cylinder("Lamp_Arm", 0.012, arm_len,
             (LAMP_X, LAMP_Y, ARM_BOTTOM + arm_len / 2), lamp_mat, verts=16)

shade_tilt = math.radians(-20)
SHADE_CENTER = (LAMP_X + 0.10, LAMP_Y, ARM_TOP + 0.02)
add_cone("Lamp_Shade", 0.085, 0.03, 0.13, SHADE_CENTER, shade_mat,
         verts=40, rot=(0.0, shade_tilt, 0.0))

# Soft area light pointing down out of the shade
bpy.ops.object.light_add(type='AREA', location=(SHADE_CENTER[0] - 0.02, SHADE_CENTER[1],
                                                 SHADE_CENTER[2] - 0.08))
lamp_light = bpy.context.active_object
lamp_light.name = "Desk_Lamp_Light"
lamp_light.data.name = "Desk_Lamp_Light_Data"
lamp_light.data.energy = 120.0
lamp_light.data.size = 0.18
lamp_light.data.size_y = 0.18
lamp_light.data.color = (1.0, 0.78, 0.52)
lamp_light.rotation_euler = (math.radians(0), 0.0, 0.0)

# Gentle fill light from the camera side so the scene isn't too harsh
bpy.ops.object.light_add(type='AREA', location=(1.6, -1.4, 2.2))
fill = bpy.context.active_object
fill.name = "Fill_Light"
fill.data.energy = 25.0
fill.data.size = 1.5
fill.data.color = (0.85, 0.9, 1.0)
fill.rotation_euler = (math.radians(-50), 0.0, math.radians(45))

# ---------------------------------------------------------------------------
# World: soft neutral background
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.04, 0.045, 0.055, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------------------------------------------------------------------------
# Camera framing the desk
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)

cam_loc = Vector((1.25, -2.0, 1.55))
cam_target = Vector((0.0, 0.0, 0.9))
cam_obj.location = cam_loc
direction = cam_target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam_obj

# ---------------------------------------------------------------------------
# Scene settings
# ---------------------------------------------------------------------------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
