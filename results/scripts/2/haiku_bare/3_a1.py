import bpy
import bmesh
import mathutils
import math
import random

random.seed(7)

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)


# ---------- Helpers ----------
def make_mat(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def assign(obj, mat):
    obj.data.materials.append(mat)


def add_sphere(name, loc, radius, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24,
                                         radius=radius, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    smooth(obj)
    assign(obj, mat)
    return obj


def add_cylinder(name, loc, radius, depth, mat, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius,
                                        depth=depth, location=loc,
                                        rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    smooth(obj)
    assign(obj, mat)
    return obj


# ---------- Materials ----------
snow_mat = make_mat("Snow", (0.95, 0.96, 0.98), roughness=0.55)
ground_mat = make_mat("GroundSnow", (0.88, 0.90, 0.94), roughness=0.7)
carrot_mat = make_mat("Carrot", (1.0, 0.45, 0.05), roughness=0.4)
coal_mat = make_mat("Coal", (0.02, 0.02, 0.02), roughness=0.35)
wood_mat = make_mat("Wood", (0.35, 0.22, 0.10), roughness=0.8)
hat_mat = make_mat("HatBlack", (0.015, 0.015, 0.02), roughness=0.3)
band_mat = make_mat("RedBand", (0.6, 0.02, 0.02), roughness=0.5)
scarf_mat = make_mat("Scarf", (0.7, 0.05, 0.06), roughness=0.85)

# ---------- Ground ----------
bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=80, size=14,
                                location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
me = ground.data
bm = bmesh.new()
bm.from_mesh(me)
for v in bm.verts:
    x, y = v.co.x, v.co.y
    dist = math.hypot(x, y)
    bump = (math.sin(x * 1.3) * math.cos(y * 1.1) * 0.02
            + random.uniform(-0.008, 0.008))
    # flatten near the snowman so it stands cleanly
    falloff = min(1.0, max(0.0, (dist - 1.0) / 1.5))
    v.co.z = bump * falloff
bm.to_mesh(me)
bm.free()
smooth(ground)
assign(ground, ground_mat)

# ---------- Snowman body ----------
bottom = add_sphere("BottomBall", (0, 0, 0.6), 0.6, snow_mat)
middle = add_sphere("MiddleBall", (0, 0, 1.52), 0.42, snow_mat)
head = add_sphere("Head", (0, 0, 2.2), 0.3, snow_mat)

# ---------- Eyes ----------
for sx, nm in [(-0.1, "EyeL"), (0.1, "EyeR")]:
    add_sphere(nm, (sx, -0.27, 2.28), 0.04, coal_mat)

# ---------- Carrot nose ----------
bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.05, radius2=0.0,
                                depth=0.5, location=(0, -0.52, 2.2),
                                rotation=(math.radians(90), 0, 0))
nose = bpy.context.active_object
nose.name = "CarrotNose"
smooth(nose)
assign(nose, carrot_mat)

# ---------- Coal buttons ----------
for i, z in enumerate([1.66, 1.52, 1.38]):
    add_sphere(f"Button{i}", (0, -0.415, z), 0.04, coal_mat)

# ---------- Stick arms ----------
arm_len = 0.9
add_cylinder("ArmR", (0.6, 0, 1.75), 0.025, arm_len, wood_mat,
             rot=(0, math.radians(55), 0), verts=12)
add_cylinder("ArmL", (-0.6, 0, 1.75), 0.025, arm_len, wood_mat,
             rot=(0, math.radians(-55), 0), verts=12)

# Small twig fingers
for sign, nm in [(1, "TwigR"), (-1, "TwigL")]:
    tip_x = sign * (0.6 + 0.37 * 0.82)
    tip_z = 1.75 + 0.37 * 0.57
    add_cylinder(nm, (tip_x + sign * 0.03, 0, tip_z + 0.05), 0.012, 0.14,
                 wood_mat, rot=(math.radians(20), math.radians(sign * 40), 0),
                 verts=8)

# ---------- Scarf ----------
bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.06,
                                 major_segments=48, minor_segments=16,
                                 location=(0, 0, 1.92))
scarf = bpy.context.active_object
scarf.name = "Scarf"
smooth(scarf)
assign(scarf, scarf_mat)

# Scarf tail hanging down the front
add_cylinder("ScarfTail", (0.12, -0.36, 1.7), 0.05, 0.3, scarf_mat,
             rot=(math.radians(10), 0, math.radians(-10)), verts=16)

# ---------- Top hat ----------
hat_z = 2.5
add_cylinder("HatBrim", (0, 0, hat_z + 0.02), 0.42, 0.03, hat_mat, verts=48)
add_cylinder("HatCrown", (0, 0, hat_z + 0.25), 0.27, 0.5, hat_mat, verts=48)
add_cylinder("HatBand", (0, 0, hat_z + 0.07), 0.275, 0.07, band_mat, verts=48)

# Tilt the hat slightly for character
hat_parts = [o for o in bpy.data.objects if o.name.startswith("Hat")]
hat_pivot = mathutils.Vector((0, 0, hat_z))
for o in hat_parts:
    rel = o.location - hat_pivot
    rot_mat = mathutils.Euler((math.radians(-6), 0, math.radians(8)), 'XYZ').to_matrix()
    o.location = hat_pivot + rot_mat @ rel
    o.rotation_euler = (math.radians(-6), 0, math.radians(8))

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(4, -4, 6))
sun = bpy.context.active_object
sun.name = "KeySun"
sun.data.energy = 3.5
sun.data.angle = math.radians(4)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-3.5, -4.5, 3.5))
fill = bpy.context.active_object
fill.name = "FillArea"
fill.data.energy = 250
fill.data.size = 5
fill.rotation_euler = (math.radians(60), 0, math.radians(-30))

bpy.ops.object.light_add(type='AREA', location=(0, 4, 3))
rim = bpy.context.active_object
rim.name = "RimArea"
rim.data.energy = 150
rim.data.size = 3
rim.rotation_euler = (math.radians(-60), 0, math.radians(180))

# ---------- World ----------
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.65, 0.78, 1.0)
bg.inputs["Strength"].default_value = 0.6

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("SnowmanCam")
cam_data.lens = 55
cam_obj = bpy.data.objects.new("SnowmanCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = (3.0, -5.6, 2.2)

target = mathutils.Vector((0, 0, 1.45))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam_obj

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
