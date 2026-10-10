import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clear scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()


# ---------- Helpers ----------
def make_mat(name, color, rough=0.5, metallic=0.0, emission=None, emit_strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (emission[0], emission[1], emission[2], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat


def assign(obj, mat, smooth=True):
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def sphere(name, radius, loc, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=48, ring_count=24)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    return assign(o, mat)


def cylinder(name, radius, depth, loc, rot, mat, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc,
                                        rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    return assign(o, mat)


# ---------- Materials ----------
snow_mat = make_mat("Snow", (0.92, 0.95, 1.0), rough=0.55)
ground_mat = make_mat("SnowGround", (0.86, 0.90, 0.96), rough=0.7)
carrot_mat = make_mat("Carrot", (1.0, 0.45, 0.05), rough=0.4)
coal_mat = make_mat("Coal", (0.02, 0.02, 0.02), rough=0.3)
wood_mat = make_mat("Stick", (0.28, 0.17, 0.08), rough=0.8)
hat_mat = make_mat("HatBlack", (0.015, 0.015, 0.02), rough=0.35)
scarf_mat = make_mat("Scarf", (0.7, 0.05, 0.08), rough=0.6)

# ---------- Ground (gently undulating snowfield) ----------
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=70, y_segments=70, size=15.0)
for v in bm.verts:
    x, y = v.co.x, v.co.y
    r = math.hypot(x, y)
    falloff = min(1.0, max(0.0, (r - 2.5) / 4.0))
    h = (0.12 * math.sin(x * 0.7 + 1.3) * math.cos(y * 0.5)
         + 0.06 * math.sin(x * 1.9 - y * 1.4)
         + random.uniform(-0.01, 0.01))
    v.co.z = h * falloff
bm.normal_update()
me = bpy.data.meshes.new("GroundMesh")
bm.to_mesh(me)
bm.free()
ground = bpy.data.objects.new("Ground", me)
bpy.context.collection.objects.link(ground)
assign(ground, ground_mat)

# ---------- Snowman body ----------
bottom = sphere("BodyBottom", 0.9, (0, 0, 0.9), snow_mat, scale=(1, 1, 0.95))
middle = sphere("BodyMiddle", 0.65, (0, 0, 2.3), snow_mat)
head = sphere("Head", 0.45, (0, 0, 3.5), snow_mat)

# Small snow lumps for texture
for i in range(10):
    a = random.uniform(0, math.tau)
    z = random.uniform(0.3, 1.5)
    rr = 0.9 * math.sqrt(max(0.0, 1 - (z / 0.9 - 1) ** 2)) * 0.98
    lump_loc = (rr * math.cos(a), rr * math.sin(a), z)
    sphere(f"Lump{i}", random.uniform(0.08, 0.14), lump_loc, snow_mat)

# ---------- Carrot nose ----------
bpy.ops.mesh.primitive_cone_add(radius1=0.075, radius2=0.0, depth=0.5,
                                location=(0, -0.65, 3.5),
                                rotation=(math.pi / 2, 0, 0), vertices=24)
nose = bpy.context.active_object
nose.name = "CarrotNose"
assign(nose, carrot_mat)

# ---------- Eyes and coal buttons ----------
for sx, name in [(-0.15, "EyeL"), (0.15, "EyeR")]:
    sphere(name, 0.05, (sx, -0.40, 3.62), coal_mat)

for i, z in enumerate([2.5, 2.3, 2.1]):
    sphere(f"Button{i}", 0.05, (0, -0.63, z), coal_mat)

# Smile: small dark dots arcing under the nose
for i, (x, z) in enumerate([(-0.22, 3.36), (-0.12, 3.30), (0.0, 3.28),
                            (0.12, 3.30), (0.22, 3.36)]):
    sphere(f"Smile{i}", 0.02, (x, -0.43, z), coal_mat)

# ---------- Stick arms ----------
arm_len = 1.4
arm_tilt = math.pi / 2 - 0.35
# Left arm (points toward -X and up)
left_arm = cylinder("ArmL", 0.03, arm_len, (-0.85, 0.0, 2.6),
                    (0, -arm_tilt, 0), wood_mat, verts=12)
# Right arm (points toward +X and up)
right_arm = cylinder("ArmR", 0.03, arm_len, (0.85, 0.0, 2.6),
                     (0, arm_tilt, 0), wood_mat, verts=12)

# Twigs on the arms
cylinder("TwigL1", 0.012, 0.3, (-1.25, -0.05, 2.95),
         (math.radians(40), 0, math.radians(-30)), wood_mat, verts=8)
cylinder("TwigL2", 0.012, 0.25, (-1.35, 0.04, 2.8),
         (math.radians(-35), 0, math.radians(20)), wood_mat, verts=8)
cylinder("TwigR1", 0.012, 0.3, (1.25, -0.05, 2.95),
         (math.radians(40), 0, math.radians(30)), wood_mat, verts=8)
cylinder("TwigR2", 0.012, 0.25, (1.35, 0.04, 2.8),
         (math.radians(-35), 0, math.radians(-20)), wood_mat, verts=8)

# ---------- Scarf ----------
bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.07,
                                 location=(0, 0, 2.95),
                                 major_segments=48, minor_segments=16)
scarf_ring = bpy.context.active_object
scarf_ring.name = "ScarfRing"
scarf_ring.scale = (1.0, 1.0, 0.8)
assign(scarf_ring, scarf_mat)

cylinder("ScarfTail", 0.07, 0.6, (0.28, -0.52, 2.55),
         (math.radians(10), 0, math.radians(-12)), scarf_mat, verts=16)

# ---------- Top hat ----------
hat_z = 3.97
cylinder("HatBrim", 0.55, 0.05, (0, 0, hat_z), (0, 0, 0.12), hat_mat, verts=48)
cylinder("HatCrown", 0.32, 0.55, (0, 0, hat_z + 0.28), (0, 0, 0.12), hat_mat, verts=48)
cylinder("HatBand", 0.33, 0.1, (0, 0, hat_z + 0.1), (0, 0, 0.12), scarf_mat, verts=48)

# ---------- Lighting ----------
# Key sun
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun = bpy.context.active_object
sun.name = "KeySun"
sun.data.energy = 3.5
sun.data.angle = math.radians(4)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))

# Soft fill area light
bpy.ops.object.light_add(type='AREA', location=(-5, -6, 4.5))
fill = bpy.context.active_object
fill.name = "FillArea"
fill.data.energy = 400
fill.data.size = 5.0
fill.rotation_euler = (math.radians(60), 0, math.radians(-40))

# Cool rim light from behind
bpy.ops.object.light_add(type='AREA', location=(4, 5, 4))
rim = bpy.context.active_object
rim.name = "RimArea"
rim.data.energy = 250
rim.data.size = 3.0
rim.data.color = (0.75, 0.85, 1.0)
rim.rotation_euler = (math.radians(-120), 0, math.radians(35))

# ---------- World ----------
world = bpy.data.worlds.new("WinterSky")
bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.45, 0.55, 0.72, 1.0)
bg.inputs["Strength"].default_value = 0.8

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("SnowmanCam")
cam_data.lens = 58
cam_obj = bpy.data.objects.new("SnowmanCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (5.6, -8.2, 3.1)

target = Vector((0.0, 0.0, 2.25))
direction = target - Vector(cam_obj.location)
cam_obj.rotation_mode = 'QUATERNION'
cam_obj.rotation_quaternion = direction.to_track_quat('-Z', 'Y')

bpy.context.scene.camera = cam_obj

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
