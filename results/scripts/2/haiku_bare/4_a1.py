import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Clear existing scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return m

def assign(obj, material, smooth=True):
    obj.data.materials.append(material)
    if smooth and obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj

def add_cylinder(name, radius, depth, loc, material, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    return assign(obj, material)

def add_cone(name, radius1, radius2, depth, loc, material, verts=32):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=radius1, radius2=radius2,
                                    depth=depth, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    return assign(obj, material)

def add_box(name, size, loc, material, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    obj.rotation_euler.z = rot_z
    return assign(obj, material, smooth=False)

# ---------- Materials ----------
mat_rocket_white = make_material("RocketWhite", (0.92, 0.92, 0.93), roughness=0.35, metallic=0.0)
mat_fin_grey = make_material("FinGrey", (0.35, 0.36, 0.38), roughness=0.45, metallic=0.6)
mat_nozzle = make_material("Nozzle", (0.08, 0.07, 0.06), roughness=0.6, metallic=0.8)
mat_concrete = make_material("Concrete", (0.55, 0.55, 0.53), roughness=0.9)
mat_ground = make_material("Ground", (0.28, 0.33, 0.20), roughness=1.0)
mat_steel = make_material("TowerSteel", (0.45, 0.42, 0.40), roughness=0.5, metallic=0.9)
mat_stripe = make_material("Stripe", (0.8, 0.12, 0.08), roughness=0.4)

# ---------- Ground and launch pad ----------
bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
assign(ground, mat_ground, smooth=False)

pad = add_box("LaunchPad", (16, 16, 1.0), (0, 0, 0.5), mat_concrete)

# Flame trench (dark recess in the middle of the pad)
add_box("FlameTrench", (5, 5, 0.3), (0, 0, 0.85), mat_nozzle)

# ---------- Rocket ----------
ROCKET_Z = 1.0  # bottom of nozzle sits on top of pad

# Engine bell (nozzle): wider at bottom
add_cone("Nozzle", radius1=1.4, radius2=1.0, depth=2.5,
         loc=(0, 0, ROCKET_Z + 1.25), material=mat_nozzle)

# Main body
body_bottom = ROCKET_Z + 2.5
body_top = 22.0
body_depth = body_top - body_bottom
add_cylinder("RocketBody", radius=1.5, depth=body_depth,
             loc=(0, 0, body_bottom + body_depth / 2), material=mat_rocket_white)

# Red stripe band near the base
add_cylinder("StripeBand", radius=1.52, depth=1.2,
             loc=(0, 0, 6.0), material=mat_stripe)

# Nose cone
add_cone("NoseCone", radius1=1.5, radius2=0.0, depth=6.0,
         loc=(0, 0, body_top + 3.0), material=mat_rocket_white)

# Four fins
for i in range(4):
    a = i * math.pi / 2
    x = math.cos(a) * 1.6
    y = math.sin(a) * 1.6
    add_box(f"Fin{i}", (0.25, 2.8, 4.0), (x, y, 5.0), mat_fin_grey, rot_z=a)

# Small window ring detail
add_cylinder("WindowRing", radius=1.55, depth=0.4,
             loc=(0, 0, 17.0), material=mat_fin_grey)

# ---------- Support tower ----------
TOWER_X = 8.0
HALF = 1.2
TOWER_H = 32.0
LEG_R = 0.15

# Four legs
for sx in (-1, 1):
    for sy in (-1, 1):
        add_cylinder(f"TowerLeg_{sx}_{sy}", radius=LEG_R, depth=TOWER_H,
                     loc=(TOWER_X + sx * HALF, sy * HALF, TOWER_H / 2), material=mat_steel, verts=8)

# Horizontal cross bracing on each face at several heights
for z in (4.0, 10.0, 16.0, 22.0, 28.0):
    # front and back faces (bars along X)
    for sy in (-1, 1):
        add_box(f"BraceX_{z}_{sy}", (2 * HALF, 0.1, 0.1),
                (TOWER_X, sy * HALF, z), mat_steel)
    # left and right faces (bars along Y)
    for sx in (-1, 1):
        add_box(f"BraceY_{z}_{sx}", (0.1, 2 * HALF, 0.1),
                (TOWER_X + sx * HALF, 0, z), mat_steel)

# Diagonal bracing on the rocket-facing side for visual interest
for z0 in (4.0, 16.0):
    length = math.hypot(HALF * 2, 12.0)
    ang = math.atan2(12.0, 2 * HALF)
    add_box(f"Diag_{z0}", (length, 0.08, 0.08),
            (TOWER_X, -HALF, z0 + 6.0), mat_steel)
    scene.objects[f"Diag_{z0}"].rotation_euler = (0, 0, 0)
    scene.objects[f"Diag_{z0}"].rotation_euler.y = ang

# Top platform
add_box("TowerPlatform", (3.0, 3.0, 0.3), (TOWER_X, 0, TOWER_H), mat_steel)

# Crew arm reaching toward the rocket
ARM_Z = 20.0
arm_start_x = TOWER_X - HALF
arm_end_x = 2.2
arm_len = arm_start_x - arm_end_x
add_box("CrewArm", (arm_len, 0.25, 0.25),
        (arm_start_x - arm_len / 2, 0, ARM_Z), mat_steel)
# Arm platform plate
add_box("CrewArmPlate", (1.2, 1.6, 0.12),
        (arm_end_x + 0.6, 0, ARM_Z - 0.3), mat_steel)

# ---------- World / Sky ----------
world = bpy.data.worlds.new("SkyWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.65, 0.95, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun_data.angle = math.radians(1.5)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(35))

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 600.0
fill_data.size = 12.0
fill = bpy.data.objects.new("Fill", fill_data)
scene.collection.objects.link(fill)
fill.location = (-22, -24, 18)
fill.rotation_euler = (math.radians(60), 0, math.radians(-40))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 50
cam_data.clip_end = 1000
cam_obj = bpy.data.objects.new("MainCamera", cam_data)
scene.collection.objects.link(cam_obj)

cam_loc = Vector((-40.0, -48.0, 17.0))
target = Vector((2.0, 0.0, 14.0))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# ---------- Timeline (still scene) ----------
scene.frame_start = 1
scene.frame_end = 1
