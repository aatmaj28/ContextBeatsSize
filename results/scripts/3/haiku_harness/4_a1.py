import bpy
import math
from mathutils import Vector

# ---------------------------------------------------------------
# Reset scene
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


mat_white = make_material("RocketWhite", (0.93, 0.93, 0.95), roughness=0.35)
mat_red = make_material("RocketRed", (0.75, 0.12, 0.08), roughness=0.4)
mat_dark = make_material("EngineDark", (0.05, 0.05, 0.06), roughness=0.3, metallic=0.9)
mat_steel = make_material("TowerSteel", (0.55, 0.56, 0.58), roughness=0.45, metallic=0.8)
mat_concrete = make_material("PadConcrete", (0.42, 0.42, 0.40), roughness=0.9)
mat_ground = make_material("Ground", (0.22, 0.30, 0.16), roughness=1.0)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def add_box(name, loc, scale, mat, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.rotation_euler = rot
    o.data.materials.append(mat)
    return o


def add_cyl(name, loc, radius, depth, mat, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius,
                                        depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def add_cone(name, loc, r1, r2, depth, mat, verts=48):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2,
                                    depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


# ---------------------------------------------------------------
# Ground and launch pad
# ---------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, -0.5))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(mat_ground)

# Pad slab: top surface at z = 0
add_box("LaunchPad", (0, 0, -0.25), (8.0, 8.0, 0.5), mat_concrete)

# Flame trench / small detail blocks on the pad
add_box("PadBlockA", (3.2, 3.0, 0.05), (0.8, 0.8, 0.1), mat_concrete)
add_box("PadBlockB", (-3.0, -3.2, 0.05), (0.6, 0.6, 0.1), mat_concrete)

# ---------------------------------------------------------------
# Rocket (base sits on the pad, lifted slightly by base_z)
# ---------------------------------------------------------------
base_z = 0.5
body_h = 8.0
body_r = 0.5

# Main white body
add_cyl("RocketBody", (0, 0, base_z + body_h / 2), body_r, body_h, mat_white)

# Nose cone
add_cone("RocketNose", (0, 0, base_z + body_h + 1.1), body_r, 0.0, 2.2, mat_white)

# Red accent band
add_cyl("RocketBand", (0, 0, base_z + 5.0), body_r + 0.012, 0.4, mat_red)

# Porthole ring
add_cyl("RocketPorthole", (0, 0, base_z + 6.4), body_r + 0.02, 0.12, mat_dark, verts=24)

# Four fins, radially oriented
for i in range(4):
    ang = i * math.pi / 2
    x = math.cos(ang) * 0.9
    y = math.sin(ang) * 0.9
    add_box(f"Fin{i}", (x, y, base_z + 1.4), (0.5, 0.06, 1.4), mat_red,
            rot=(0, 0, ang))

# Engine bell and nozzle
add_cyl("EngineBase", (0, 0, base_z - 0.15), 0.38, 0.5, mat_dark)
add_cone("EngineBell", (0, 0, base_z - 0.55), 0.38, 0.6, 0.6, mat_dark)

# ---------------------------------------------------------------
# Support tower (simple lattice with service arm)
# ---------------------------------------------------------------
tx, ty = -2.4, 0.0
tower_h = 9.0
leg_off = 0.5
leg_w = 0.12

for sx in (-1, 1):
    for sy in (-1, 1):
        add_box(f"TowerLeg_{sx}_{sy}",
                (tx + sx * leg_off, ty + sy * leg_off, base_z * 0 + tower_h / 2),
                (leg_w, leg_w, tower_h), mat_steel)

# Horizontal braces at several heights (both faces, X and Y)
for k, z in enumerate([1.8, 3.8, 5.8, 7.8]):
    add_box(f"TowerBraceX_{k}_a", (tx, ty - leg_off, z), (leg_off * 2, 0.05, 0.05), mat_steel)
    add_box(f"TowerBraceX_{k}_b", (tx, ty + leg_off, z), (leg_off * 2, 0.05, 0.05), mat_steel)
    add_box(f"TowerBraceY_{k}_a", (tx - leg_off, ty, z), (0.05, leg_off * 2, 0.05), mat_steel)
    add_box(f"TowerBraceY_{k}_b", (tx + leg_off, ty, z), (0.05, leg_off * 2, 0.05), mat_steel)

# Diagonal bracing on one face for detail
for k in range(3):
    z0 = 0.5 + k * 2.2 + 1.1
    ang = math.atan2(2.2, leg_off * 2)
    add_box(f"TowerDiag_{k}", (tx, ty - leg_off, z0), (0.04, 0.04, 2.6), mat_steel,
            rot=(ang, 0, 0))

# Service platform and arm reaching toward the rocket
platform_z = 7.0
add_box("TowerPlatform", (tx, ty, platform_z), (1.6, 1.6, 0.12), mat_steel)
arm_len = abs(tx) - body_r - 0.2
add_box("ServiceArm", (tx + arm_len / 2 + 0.3, ty, platform_z + 0.3),
        (arm_len, 0.12, 0.12), mat_steel)
add_box("ArmRail", (tx + arm_len / 2 + 0.3, ty, platform_z + 0.7),
        (arm_len, 0.03, 0.03), mat_steel)

# ---------------------------------------------------------------
# World background
# ---------------------------------------------------------------
world = bpy.data.worlds.new("SkyWorld")
bpy.context.scene.world = world
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs["Color"].default_value = (0.55, 0.72, 0.95, 1.0)
bg_node.inputs["Strength"].default_value = 0.8

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
scene = bpy.context.scene
collection = scene.collection

sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(3.0)
sun = bpy.data.objects.new("KeySun", sun_data)
collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(-35))

fill_data = bpy.data.lights.new(name="FillArea", type='AREA')
fill_data.energy = 350.0
fill_data.size = 6.0
fill = bpy.data.objects.new("FillArea", fill_data)
collection.objects.link(fill)
fill.location = (-7.0, -9.0, 7.0)
fill_dir = Vector((0.0, 0.0, 5.0)) - fill.location
fill.rotation_euler = fill_dir.to_track_quat('-Z', 'Y').to_euler()

rim_data = bpy.data.lights.new(name="RimArea", type='AREA')
rim_data.energy = 200.0
rim_data.size = 4.0
rim = bpy.data.objects.new("RimArea", rim_data)
collection.objects.link(rim)
rim.location = (6.0, 8.0, 9.0)
rim_dir = Vector((0.0, 0.0, 6.0)) - rim.location
rim.rotation_euler = rim_dir.to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("MainCamera", cam_data)
collection.objects.link(cam)

cam_loc = Vector((11.0, -17.0, 6.5))
target = Vector((-0.8, 0.0, 5.0))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam

# ---------------------------------------------------------------
# Frame range (static scene)
# ---------------------------------------------------------------
scene.frame_start = 1
scene.frame_end = 1
