import bpy
import bmesh
import mathutils
import math
import random
import colorsys

random.seed(7)
scene = bpy.context.scene

# ---------- Clear any existing content ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

def link(obj):
    scene.collection.objects.link(obj)
    return obj

def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

def make_material(name, color, roughness, metallic=0.0, clearcoat=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    for key in ("Coat Weight", "Clearcoat"):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = clearcoat
            break
    return mat

# ---------- Materials ----------
dough_mat = make_material("Dough", (0.72, 0.42, 0.18), roughness=0.35, clearcoat=0.2)
frosting_mat = make_material("PinkFrosting", (0.98, 0.42, 0.62), roughness=0.12, clearcoat=0.8)
plate_mat = make_material("WhitePlate", (0.93, 0.93, 0.92), roughness=0.18, clearcoat=0.3)

sprinkle_mats = []
sprinkle_colors = [
    (1.0, 0.95, 0.2), (0.2, 0.7, 1.0), (0.3, 0.9, 0.35),
    (1.0, 0.25, 0.25), (0.6, 0.3, 1.0), (1.0, 1.0, 1.0),
]
for i, c in enumerate(sprinkle_colors):
    sprinkle_mats.append(make_material(f"Sprinkle{i}", c, roughness=0.25, clearcoat=0.5))

# ---------- Plate ----------
bpy.ops.mesh.primitive_cylinder_add(
    vertices=96, radius=2.1, depth=0.12, location=(0, 0, -0.56)
)
plate = bpy.context.active_object
plate.name = "Plate"
plate.data.materials.append(plate_mat)
bev = plate.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.05
bev.segments = 4
smooth(plate)
link(plate)

# ---------- Dough donut ----------
bpy.ops.mesh.primitive_torus_add(
    major_radius=1.0, minor_radius=0.4,
    major_segments=96, minor_segments=40, location=(0, 0, 0)
)
dough = bpy.context.active_object
dough.name = "DonutDough"
dough.data.materials.append(dough_mat)
sub = dough.modifiers.new("Subsurf", 'SUBSURF')
sub.levels = 1
sub.render_levels = 2
smooth(dough)
link(dough)

# ---------- Frosting (top shell with drips) ----------
FROST_R = 0.43
bpy.ops.mesh.primitive_torus_add(
    major_radius=1.0, minor_radius=FROST_R,
    major_segments=96, minor_segments=40, location=(0, 0, 0)
)
frost = bpy.context.active_object
frost.name = "Frosting"
frost.data.materials.append(frosting_mat)

me = frost.data
bm = bmesh.new()
bm.from_mesh(me)
cut_faces = [f for f in bm.faces if all(v.co.z < -0.10 for v in f.verts)]
bmesh.ops.delete(bm, geom=cut_faces, context='FACES')

for v in bm.verts:
    if v.co.z < 0.02:
        # Drips hanging over the sides
        if random.random() < 0.35:
            v.co.z -= random.uniform(0.02, 0.09)
    else:
        # Subtle organic wobble
        v.co += v.co.normalized() * random.uniform(-0.008, 0.008)

bm.to_mesh(me)
bm.free()

frost_sub = frost.modifiers.new("Subsurf", 'SUBSURF')
frost_sub.levels = 1
frost_sub.render_levels = 2
smooth(frost)
link(frost)

# ---------- Sprinkles ----------
R = 1.0
r = FROST_R
count = 0
attempts = 0
while count < 170 and attempts < 2000:
    attempts += 1
    theta = random.uniform(0, 2 * math.pi)
    phi = random.uniform(0.35, math.pi - 0.35)  # top region of the frosting
    cos_p, sin_p = math.cos(phi), math.sin(phi)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    normal = mathutils.Vector((cos_p * cos_t, cos_p * sin_t, sin_p))
    surface = mathutils.Vector(((R + r * cos_p) * cos_t,
                                (R + r * cos_p) * sin_t,
                                r * sin_p))
    # Keep sprinkles off the donut's bottom and too-steep sides
    if normal.z < 0.25:
        continue

    length = random.uniform(0.09, 0.14)
    radius = random.uniform(0.018, 0.026)
    pos = surface + normal * 0.03

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8, radius=radius, depth=length, location=pos
    )
    s = bpy.context.active_object
    s.name = f"Sprinkle_{count:03d}"
    s.data.materials.append(random.choice(sprinkle_mats))

    base = mathutils.Vector((0, 0, 1)).rotation_difference(normal)
    spin = mathutils.Quaternion(normal, random.uniform(0, 2 * math.pi))
    s.rotation_mode = 'QUATERNION'
    s.rotation_quaternion = spin @ base
    link(s)
    count += 1

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(0, 0, 6))
sun = bpy.context.active_object
sun.name = "KeySun"
sun.data.energy = 3.0
sun.data.angle = math.radians(12)
sun.rotation_euler = (math.radians(50), math.radians(0), math.radians(35))
link(sun)

bpy.ops.object.light_add(type='AREA', location=(4.0, -4.5, 5.0))
key = bpy.context.active_object
key.name = "SoftKey"
key.data.energy = 600
key.data.size = 5.0
key.rotation_euler = mathutils.Vector((0, 0, 0)).to_track_quat('Z', 'Y').to_euler()
direction = mathutils.Vector((0, 0, 0)) - key.location
key.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
link(key)

bpy.ops.object.light_add(type='POINT', location=(-4.0, 3.0, 2.5))
fill = bpy.context.active_object
fill.name = "FillPoint"
fill.data.energy = 150
fill.data.shadow_soft_size = 2.0
link(fill)

# ---------- World ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.04, 0.04, 0.05, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 65
cam = bpy.data.objects.new("Camera", cam_data)
link(cam)
cam.location = (4.2, -5.2, 3.6)
target = mathutils.Vector((0, 0, -0.1))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Scene settings ----------
scene.frame_start = 1
scene.frame_end = 1
