import bpy
import bmesh
import mathutils
import math
import random

random.seed(7)

# ---------- Clear scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
collection = scene.collection


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def assign(obj, mat, smooth=True):
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def add_sphere(name, radius, location, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location,
                                         segments=48, ring_count=24)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return assign(obj, mat)


def add_cylinder(name, radius, depth, location, rotation, mat, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=location, rotation=rotation,
                                        vertices=vertices)
    obj = bpy.context.active_object
    obj.name = name
    return assign(obj, mat)


# ---------- Materials ----------
snow_mat = make_material("Snow", (0.93, 0.95, 1.0), roughness=0.85)
ground_mat = make_material("GroundSnow", (0.86, 0.90, 0.96), roughness=0.95)
carrot_mat = make_material("Carrot", (1.0, 0.45, 0.05), roughness=0.45)
hat_mat = make_material("HatBlack", (0.02, 0.02, 0.025), roughness=0.35)
stick_mat = make_material("Stick", (0.28, 0.16, 0.07), roughness=0.8)
coal_mat = make_material("Coal", (0.01, 0.01, 0.01), roughness=0.3)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
assign(ground, ground_mat, smooth=False)

# Scattered snow mounds for ground detail
for i in range(40):
    x = random.uniform(-7, 7)
    y = random.uniform(-5, 5)
    if abs(x) < 1.5 and abs(y) < 1.5:
        continue
    r = random.uniform(0.15, 0.5)
    add_sphere(f"SnowMound_{i}", r, (x, y, -r * 0.4), ground_mat,
               scale=(1, 1, 0.35))

# ---------- Snowman body ----------
bottom = add_sphere("BodyBottom", 0.6, (0, 0, 0.6), snow_mat)
middle = add_sphere("BodyMiddle", 0.45, (0, 0, 1.65), snow_mat)
head = add_sphere("Head", 0.3, (0, 0, 2.45), snow_mat)

# Coal eyes
for side, x in (("L", -0.1), ("R", 0.1)):
    add_sphere(f"Eye_{side}", 0.035, (x, -0.27, 2.52), coal_mat)

# Coal buttons
for i, z in enumerate((1.8, 1.65, 1.5)):
    add_sphere(f"Button_{i}", 0.035, (0, -0.44, z), coal_mat)

# ---------- Carrot nose ----------
bpy.ops.mesh.primitive_cone_add(radius1=0.045, radius2=0.0, depth=0.45,
                                location=(0, -0.36, 2.45),
                                rotation=(math.pi / 2, 0, 0), vertices=24)
nose = bpy.context.active_object
nose.name = "CarrotNose"
assign(nose, carrot_mat)

# ---------- Stick arms ----------
tilt = 0.4
right_arm = add_cylinder("ArmR", 0.03, 0.9, (0.8 * math.cos(tilt), 0, 1.95 + 0.8 * math.sin(tilt) * 0.0 + 0.4 * math.sin(tilt)),
                         (0, math.pi / 2 - tilt, 0), stick_mat, vertices=10)
left_arm = add_cylinder("ArmL", 0.03, 0.9, (-0.8 * math.cos(tilt), 0, 1.95 + 0.4 * math.sin(tilt)),
                        (0, -(math.pi / 2 - tilt), 0), stick_mat, vertices=10)

# Small twig fingers
for side, sx in (("R", 1), ("L", -1)):
    for k, ang in enumerate((-0.5, 0.5)):
        base_x = sx * (0.8 + 0.4 * math.cos(tilt))
        add_cylinder(f"Twig_{side}{k}", 0.012, 0.22,
                     (base_x + sx * 0.05, 0.02 * (k * 2 - 1), 1.95 + 0.4 * math.sin(tilt) + 0.1),
                     (ang, 0, sx * 0.9), stick_mat, vertices=8)

# ---------- Top hat ----------
brim = add_cylinder("HatBrim", 0.42, 0.04, (0, 0, 2.74), (0, 0, 0), hat_mat, vertices=48)
crown = add_cylinder("HatCrown", 0.26, 0.45, (0, 0, 2.99), (0, 0, 0), hat_mat, vertices=48)
band = add_cylinder("HatBand", 0.265, 0.06, (0, 0, 2.84), (0, 0, 0), hat_mat, vertices=48)
hat_tilt = -0.12
for obj in (brim, crown, band):
    obj.rotation_euler = (0.0, hat_tilt, 0.0)
    obj.location.x += 0.02

# ---------- Lighting ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.65, 0.8, 1.0)
bg.inputs["Strength"].default_value = 0.8
scene.world = world

sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(4)
sun_obj = bpy.data.objects.new("KeySun", sun_data)
collection.objects.link(sun_obj)
sun_obj.location = (4, -5, 8)
sun_obj.rotation_euler = (math.radians(50), 0, math.radians(35))

fill_data = bpy.data.lights.new(name="FillArea", type='AREA')
fill_data.energy = 250
fill_data.size = 4.0
fill_obj = bpy.data.objects.new("FillArea", fill_data)
collection.objects.link(fill_obj)
fill_obj.location = (-5, -4, 3)
fill_obj.rotation_euler = (math.radians(70), 0, math.radians(-40))

# ---------- Camera ----------
cam_target = mathutils.Vector((0, 0, 1.55))
cam_location = mathutils.Vector((0.8, -7.8, 2.3))
cam_data = bpy.data.cameras.new("SnowmanCam")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("SnowmanCam", cam_data)
collection.objects.link(cam_obj)
cam_obj.location = cam_location
direction = cam_target - cam_location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- Scene settings ----------
scene.frame_start = 1
scene.frame_end = 1
