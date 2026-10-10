import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for item in list(block):
        if item.users == 0:
            block.remove(item)


# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
def make_material(name, color, roughness=0.5, metallic=0.0, emission=None):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.0
    return mat

snow_mat = make_material("Snow", (0.94, 0.96, 1.0), roughness=0.55)
ground_mat = make_material("GroundSnow", (0.90, 0.93, 0.98), roughness=0.7)
carrot_mat = make_material("Carrot", (1.0, 0.45, 0.05), roughness=0.4)
stick_mat = make_material("Twig", (0.30, 0.18, 0.08), roughness=0.9)
black_mat = make_material("Black", (0.02, 0.02, 0.025), roughness=0.35)
hat_mat = make_material("HatBlack", (0.015, 0.015, 0.02), roughness=0.25)
scarf_mat = make_material("Scarf", (0.7, 0.05, 0.08), roughness=0.6)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj

def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj

def add_sphere(name, radius, loc, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=48, ring_count=24, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    smooth(obj)
    return assign(obj, mat)

def add_cylinder(name, radius, depth, loc, mat, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    smooth(obj)
    return assign(obj, mat)

def add_cone(name, r1, r2, depth, loc, mat, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth,
                                    location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    smooth(obj)
    return assign(obj, mat)


# ---------------------------------------------------------------
# Ground: gently undulating snow field
# ---------------------------------------------------------------
bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=80, size=30, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "SnowGround"
phase_a, phase_b = random.uniform(0, 6.28), random.uniform(0, 6.28)
bm = bmesh.new()
bm.from_mesh(ground.data)
for v in bm.verts:
    h = (0.06 * math.sin(v.co.x * 0.7 + phase_a) * math.cos(v.co.y * 0.5 + phase_b)
         + 0.03 * math.sin(v.co.x * 2.3 + v.co.y * 1.9))
    # keep the area under the snowman flat
    d = math.hypot(v.co.x, v.co.y)
    h *= min(1.0, max(0.0, (d - 2.0) / 2.5))
    v.co.z += h
bm.to_mesh(ground.data)
bm.free()
smooth(ground)
assign(ground, ground_mat)

# A few snow mounds scattered around
for i in range(9):
    ang = random.uniform(0, math.tau)
    dist = random.uniform(3.5, 7.0)
    r = random.uniform(0.4, 1.1)
    x, y = math.cos(ang) * dist, math.sin(ang) * dist
    add_sphere(f"SnowMound{i}", r, (x, y, r * 0.25), snow_mat, scale=(1.0, 1.0, 0.45))


# ---------------------------------------------------------------
# Snowman body
# ---------------------------------------------------------------
bottom = add_sphere("BodyBottom", 1.0, (0, 0, 1.0), snow_mat)
middle = add_sphere("BodyMiddle", 0.7, (0, 0, 2.55), snow_mat)
head = add_sphere("Head", 0.5, (0, 0, 3.55), snow_mat)

# Buttons on the torso (facing -Y, toward the camera)
for i, z in enumerate((2.25, 2.55, 2.85)):
    add_sphere(f"Button{i}", 0.065, (0, -0.70, z), black_mat)

# Coal eyes
for side, sx in (("L", -1), ("R", 1)):
    add_sphere(f"Eye{side}", 0.06, (sx * 0.18, -0.44, 3.68), black_mat)

# Coal smile: small dots along an arc
for i in range(7):
    t = math.radians(-60 + i * 20)
    x = math.sin(t) * 0.26
    z = 3.45 - (1 - math.cos(t)) * 0.12
    add_sphere(f"Mouth{i}", 0.035, (x, -0.44, z), black_mat)

# Carrot nose: cone pointing toward -Y
add_cone("CarrotNose", 0.075, 0.0, 0.65, (0, -0.83, 3.55),
         carrot_mat, rot=(math.radians(90), 0, 0), verts=24)

# Scarf wrapped around the neck
bpy.ops.mesh.primitive_torus_add(major_radius=0.46, minor_radius=0.09,
                                 major_segments=48, minor_segments=16,
                                 location=(0, 0, 3.12))
scarf = bpy.context.active_object
scarf.name = "Scarf"
scarf.scale = (1.0, 1.0, 1.0)
smooth(scarf)
assign(scarf, scarf_mat)
# Scarf tail hanging down the front
add_cylinder("ScarfTail", 0.09, 0.7, (0.18, -0.52, 2.78), scarf_mat,
             rot=(math.radians(12), 0, math.radians(-8)))


# ---------------------------------------------------------------
# Stick arms
# ---------------------------------------------------------------
def make_arm(side):
    sx = -1 if side == "L" else 1
    # Cylinder along X, angled upward slightly
    loc = (sx * 1.25, 0.0, 2.95)
    rot = (0, math.radians(90), math.radians(-sx * 25))
    arm = add_cylinder(f"Arm{side}", 0.045, 1.9, loc, stick_mat, rot=rot, verts=12)
    # Little twig branches at the tips
    for j, (dx, dz, ang) in enumerate(((0.0, 0.0, 35), (0.0, 0.0, -30))):
        tip_x = sx * (1.25 + 0.85 * 0.97)
        tip_z = 2.95 + 0.85 * 0.25 * sx * sx * (-1 if sx < 0 else 1) * 0.0 + 0.2
        add_cylinder(f"Twig{side}{j}", 0.025, 0.35,
                     (tip_x + sx * 0.05 * j, 0.05 * j, tip_z + 0.05 * j), stick_mat,
                     rot=(math.radians(ang), math.radians(60 * sx), 0), verts=8)
    return arm

make_arm("L")
make_arm("R")


# ---------------------------------------------------------------
# Black top hat, tilted slightly
# ---------------------------------------------------------------
hat_tilt = (math.radians(-6), 0, math.radians(10))
brim = add_cylinder("HatBrim", 0.72, 0.06, (0, 0, 4.12), hat_mat, rot=hat_tilt, verts=48)
crown = add_cylinder("HatCrown", 0.44, 0.75, (0, 0, 4.12 + 0.40), hat_mat, rot=hat_tilt, verts=48)
band = add_cylinder("HatBand", 0.445, 0.11, (0, 0, 4.12 + 0.12), scarf_mat, rot=hat_tilt, verts=48)


# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
# Soft sky/environment
world = bpy.data.worlds.new("WinterSky")
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.68, 0.9, 1.0)
bg.inputs["Strength"].default_value = 0.9
bpy.context.scene.world = world

# Key sun light, low angle for soft shadows
sun_data = bpy.data.lights.new("KeySun", type='SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(6)
sun = bpy.data.objects.new("KeySun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(-35))

# Cool fill area light from the opposite side
fill_data = bpy.data.lights.new("FillArea", type='AREA')
fill_data.energy = 250
fill_data.size = 6
fill_data.color = (0.8, 0.9, 1.0)
fill = bpy.data.objects.new("FillArea", fill_data)
bpy.context.collection.objects.link(fill)
fill.location = (-5, 4, 4)
fill.rotation_euler = (math.radians(65), 0, math.radians(-130))


# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("SnowmanCam")
cam_data.lens = 55
cam_data.dof.use_dof = False
cam = bpy.data.objects.new("SnowmanCam", cam_data)
bpy.context.collection.objects.link(cam)

cam_loc = Vector((4.2, -8.6, 3.0))
target = Vector((0.0, 0.0, 2.25))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam
