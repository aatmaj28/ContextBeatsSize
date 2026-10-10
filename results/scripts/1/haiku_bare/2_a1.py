import bpy
import math
import random
from mathutils import Vector, Euler

random.seed(7)
scene = bpy.context.scene

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for light in list(bpy.data.lights):
    bpy.data.lights.remove(light)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)

# ---------- Helpers ----------
def make_mat(name, color, roughness=0.5, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

def assign(obj, mat, smooth=False):
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj

def add_box(name, loc, dims, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = dims
    o.rotation_euler = Euler(rot, 'XYZ')
    return assign(o, mat)

def add_cyl(name, loc, radius, depth, mat, verts=48, rot=(0, 0, 0), smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = Euler(rot, 'XYZ')
    return assign(o, mat, smooth)

def add_sphere(name, loc, radius, mat, scale=(1, 1, 1), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=radius, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.rotation_euler = Euler(rot, 'XYZ')
    return assign(o, mat, smooth=True)

def add_cone(name, loc, r1, r2, depth, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=r1, radius2=r2, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    return assign(o, mat, smooth=True)

def add_torus(name, loc, major, minor, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, location=loc,
                                     rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return assign(o, mat, smooth=True)

def add_area_light(name, loc, rot, energy, size, color):
    ld = bpy.data.lights.new(name=name, type='AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = Euler(rot, 'XYZ')
    return lo

# ---------- Materials ----------
wall_mat = make_mat("Wall", (0.82, 0.80, 0.76), roughness=0.9)
floor_mat = make_mat("Floor", (0.35, 0.25, 0.18), roughness=0.6)
wood_mat = make_mat("Desk", (0.55, 0.36, 0.20), roughness=0.45)
metal_mat = make_mat("Metal", (0.6, 0.6, 0.62), roughness=0.3, metallic=1.0)
dark_mat = make_mat("DarkPlastic", (0.08, 0.08, 0.09), roughness=0.35)
screen_mat = make_mat("Screen", (0.02, 0.05, 0.08), roughness=0.1,
                      emission=(0.3, 0.6, 0.9), emission_strength=1.5)
ceramic_mat = make_mat("Ceramic", (0.92, 0.90, 0.86), roughness=0.25)
coffee_mat = make_mat("Coffee", (0.18, 0.09, 0.04), roughness=0.2)
terracotta_mat = make_mat("Terracotta", (0.72, 0.38, 0.22), roughness=0.7)
soil_mat = make_mat("Soil", (0.12, 0.07, 0.04), roughness=0.95)
leaf_mat = make_mat("Leaf", (0.12, 0.45, 0.12), roughness=0.5)
lamp_mat = make_mat("LampBrass", (0.75, 0.55, 0.25), roughness=0.3, metallic=1.0)
shade_mat = make_mat("LampShade", (0.95, 0.93, 0.85), roughness=0.6)

# ---------- Room ----------
add_box("Floor", (0, 0, -0.01), (8, 8, 0.02), floor_mat)
add_box("Wall", (0, -0.6, 2.0), (8, 0.05, 4.0), wall_mat)

# ---------- Desk ----------
DESK_TOP_Z = 0.75
add_box("DeskTop", (0, 0, DESK_TOP_Z), (1.2, 0.6, 0.04), wood_mat)
for sx in (-1, 1):
    for sy in (-1, 1):
        add_box("DeskLeg", (sx * 0.55, sy * 0.25, DESK_TOP_Z / 2),
                (0.05, 0.05, DESK_TOP_Z), wood_mat)

surf = DESK_TOP_Z + 0.02  # top surface height

# ---------- Laptop ----------
lap_x = -0.2
add_box("LaptopBase", (lap_x, 0.0, surf + 0.01), (0.34, 0.24, 0.02), metal_mat)
add_box("LaptopKeys", (lap_x, 0.02, surf + 0.0215), (0.28, 0.14, 0.001), dark_mat)
tilt = math.radians(15)
hinge_y = -0.12
hinge_z = surf + 0.02
half_h = 0.115
scr_center = (lap_x,
              hinge_y - half_h * math.sin(tilt),
              hinge_z + half_h * math.cos(tilt))
add_box("LaptopLid", scr_center, (0.34, 0.012, 0.23), metal_mat, rot=(tilt, 0, 0))
add_box("LaptopScreen", (scr_center[0], scr_center[1] - 0.0065 * math.cos(tilt),
                         scr_center[2] + 0.0065 * math.sin(tilt)),
        (0.31, 0.004, 0.20), screen_mat, rot=(tilt, 0, 0))

# ---------- Coffee mug ----------
mug_x, mug_y = 0.38, 0.12
mug_h = 0.10
add_cyl("Mug", (mug_x, mug_y, surf + mug_h / 2), 0.04, mug_h, ceramic_mat)
add_cyl("MugCoffee", (mug_x, mug_y, surf + mug_h - 0.012), 0.037, 0.004, coffee_mat, verts=40)
add_torus("MugHandle", (mug_x + 0.045, mug_y, surf + mug_h / 2), 0.025, 0.007,
          ceramic_mat, rot=(math.pi / 2, 0, 0))

# ---------- Potted plant ----------
pot_x, pot_y = 0.6, -0.12
pot_h = 0.11
add_cyl("PlantPot", (pot_x, pot_y, surf + pot_h / 2), 0.065, pot_h, terracotta_mat)
add_cyl("PlantSoil", (pot_x, pot_y, surf + pot_h - 0.01), 0.058, 0.01, soil_mat, verts=36)

top_z = surf + pot_h
for i in range(9):
    ang = i * (2 * math.pi / 9) + random.uniform(-0.2, 0.2)
    r = random.uniform(0.02, 0.05)
    lx = pot_x + r * math.cos(ang)
    ly = pot_y + r * math.sin(ang)
    lz = top_z + random.uniform(0.05, 0.14)
    tilt_amt = random.uniform(0.3, 0.7)
    add_sphere(f"Leaf{i}", (lx, ly, lz), 0.5, leaf_mat,
               scale=(0.035, 0.012, 0.075),
               rot=(tilt_amt * math.cos(ang), tilt_amt * math.sin(ang), ang))
# central stem tuft
add_sphere("LeafTop", (pot_x, pot_y, top_z + 0.17), 0.5, leaf_mat, scale=(0.05, 0.05, 0.07))

# ---------- Desk lamp ----------
lamp_x, lamp_y = -0.6, 0.18
add_cyl("LampBase", (lamp_x, lamp_y, surf + 0.01), 0.055, 0.02, lamp_mat)
arm_len = 0.42
add_cyl("LampArm", (lamp_x, lamp_y - 0.02, surf + 0.02 + arm_len / 2), 0.008, arm_len, lamp_mat, verts=16)
joint_z = surf + 0.02 + arm_len
add_sphere("LampJoint", (lamp_x, lamp_y - 0.02, joint_z), 0.016, lamp_mat)
head_z = joint_z + 0.04
add_cone("LampShade", (lamp_x, lamp_y - 0.02, head_z), 0.09, 0.03, 0.12, shade_mat)
add_sphere("LampBulb", (lamp_x, lamp_y - 0.02, head_z - 0.05), 0.02,
           make_mat("Bulb", (1, 0.95, 0.85), roughness=0.2, emission=(1, 0.9, 0.7),
                    emission_strength=8.0))

# ---------- Lights ----------
add_area_light("LampKey", (lamp_x, lamp_y - 0.02, head_z - 0.08), (0, 0, 0),
               energy=60.0, size=0.18, color=(1.0, 0.86, 0.68))
add_area_light("SoftFill", (0.3, 1.2, 2.2), (math.radians(50), 0, math.radians(15)),
               energy=40.0, size=1.5, color=(0.9, 0.93, 1.0))

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.04, 0.045, 0.05, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_loc = Vector((0.0, 1.5, 1.45))
target = Vector((0.0, -0.05, 0.95))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- Scene settings ----------
scene.frame_start = 1
scene.frame_end = 1
