import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clean the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

collection = bpy.context.collection


def link(obj):
    collection.objects.link(obj)
    return obj


def make_material(name, color, roughness=0.5, specular=0.5):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat


def make_box(name, dims, location, rot_z, material, bevel=0.01):
    me = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    me.materials.append(material)

    obj = bpy.data.objects.new(name, me)
    link(obj)
    obj.scale = dims
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, rot_z)

    if bevel > 0:
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        mod.limit_method = 'ANGLE'
    return obj


# ---------- Materials ----------
book_colors = [
    ("Book_Teal", (0.05, 0.45, 0.45)),
    ("Book_Mustard", (0.85, 0.65, 0.12)),
    ("Book_Navy", (0.08, 0.14, 0.42)),
    ("Book_Plum", (0.42, 0.14, 0.38)),
    ("Book_Olive", (0.36, 0.42, 0.14)),
]
book_mats = [make_material(n, c, roughness=0.55) for n, c in book_colors]

apple_mat = make_material("Apple_Red", (0.75, 0.04, 0.03), roughness=0.25, specular=0.6)
stem_mat = make_material("Stem_Brown", (0.25, 0.14, 0.05), roughness=0.8)
leaf_mat = make_material("Leaf_Green", (0.12, 0.45, 0.08), roughness=0.4)
floor_mat = make_material("Floor", (0.55, 0.52, 0.48), roughness=0.9)

# ---------- Floor ----------
floor_me = bpy.data.meshes.new("Floor_mesh")
floor_bm = bmesh.new()
bmesh.ops.create_grid(floor_bm, x_segments=1, y_segments=1, size=6.0)
floor_bm.to_mesh(floor_me)
floor_bm.free()
floor_me.materials.append(floor_mat)
floor = link(bpy.data.objects.new("Floor", floor_me))

# ---------- Stack of books ----------
book_specs = [
    # (width, depth, height)
    (1.70, 1.25, 0.22),
    (1.45, 1.05, 0.18),
    (1.60, 1.15, 0.26),
    (1.25, 0.95, 0.16),
    (1.40, 1.05, 0.21),
]

current_z = 0.0
for i, (w, d, h) in enumerate(book_specs):
    jitter_x = random.uniform(-0.06, 0.06)
    jitter_y = random.uniform(-0.06, 0.06)
    rot = random.uniform(-0.18, 0.18)
    loc = Vector((jitter_x, jitter_y, current_z + h / 2.0))
    make_box(
        f"Book_{i}",
        Vector((w, d, h)),
        loc,
        rot,
        book_mats[i % len(book_mats)],
        bevel=0.012,
    )
    current_z += h

stack_top = current_z

# ---------- Apple ----------
apple_radius = 0.42
apple_scale_z = 0.9
apple_center = Vector((0.05, -0.03, stack_top + apple_radius * apple_scale_z * 0.95))

apple_me = bpy.data.meshes.new("Apple_mesh")
apple_bm = bmesh.new()
bmesh.ops.create_uvsphere(apple_bm, u_segments=48, v_segments=32, radius=apple_radius)

# Shape: slight dimples at top and bottom, slight widening at shoulders
for v in apple_bm.verts:
    x, y, z = v.co.x, v.co.y, v.co.z
    r2 = x * x + y * y
    if z > 0:
        dimple = math.exp(-r2 / 0.02)
        v.co.z -= 0.09 * dimple * (z / apple_radius)
    else:
        dimple = math.exp(-r2 / 0.03)
        v.co.z += 0.04 * dimple * (-z / apple_radius)
    v.co.z *= apple_scale_z
    # Slight waist to make it look more like an apple
    v.co.x *= 1.0 + 0.04 * (1 - (z / apple_radius) ** 2)
    v.co.y *= 1.0 + 0.04 * (1 - (z / apple_radius) ** 2)

apple_bm.to_mesh(apple_me)
apple_bm.free()

for p in apple_me.polygons:
    p.use_smooth = True
apple_me.materials.append(apple_mat)

apple = link(bpy.data.objects.new("Apple", apple_me))
apple.location = apple_center
apple.rotation_euler = (0.0, 0.0, random.uniform(0, math.tau))

sub = apple.modifiers.new("Subsurf", 'SUBSURF')
sub.levels = 1
sub.render_levels = 2

# ---------- Stem ----------
stem_me = bpy.data.meshes.new("Stem_mesh")
stem_bm = bmesh.new()
bmesh.ops.create_cone(
    stem_bm,
    cap_ends=True,
    cap_tris=False,
    segments=8,
    radius1=0.022,
    radius2=0.016,
    depth=0.22,
)
stem_bm.to_mesh(stem_me)
stem_bm.free()
stem_me.materials.append(stem_mat)

stem = link(bpy.data.objects.new("Stem", stem_me))
stem.location = apple_center + Vector((0.0, 0.0, apple_radius * apple_scale_z * 0.82 + 0.08))
stem.rotation_euler = (math.radians(8), 0.0, 0.0)

# ---------- Leaf ----------
leaf_me = bpy.data.meshes.new("Leaf_mesh")
leaf_bm = bmesh.new()
bmesh.ops.create_uvsphere(leaf_bm, u_segments=16, v_segments=8, radius=1.0)
for v in leaf_bm.verts:
    v.co.x *= 0.16
    v.co.y *= 0.07
    v.co.z *= 0.035
    # Bend the leaf slightly
    v.co.z += 0.02 * (v.co.x / 0.16) ** 2
leaf_bm.to_mesh(leaf_me)
leaf_bm.free()
for p in leaf_me.polygons:
    p.use_smooth = True
leaf_me.materials.append(leaf_mat)

leaf = link(bpy.data.objects.new("Leaf", leaf_me))
leaf.location = stem.location + Vector((0.09, 0.0, 0.03))
leaf.rotation_euler = (0.0, math.radians(-20), math.radians(25))

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.0
sun_data.angle = math.radians(4)
sun = link(bpy.data.objects.new("KeySun", sun_data))
sun.location = (4, -4, 6)
sun.rotation_euler = (math.radians(55), 0.0, math.radians(40))

fill_data = bpy.data.lights.new("FillArea", 'AREA')
fill_data.energy = 250
fill_data.size = 3.0
fill = link(bpy.data.objects.new("FillArea", fill_data))
fill.location = (-4, -3, 3.5)
fill.rotation_euler = (math.radians(65), 0.0, math.radians(-50))

# ---------- World ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.82, 0.86, 0.92, 1.0)
bg.inputs["Strength"].default_value = 0.6
bpy.context.scene.world = world

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 65
cam = link(bpy.data.objects.new("Camera", cam_data))
cam_pos = Vector((4.2, -5.6, stack_top + 1.6))
target = Vector((0.0, 0.0, stack_top * 0.55 + 0.3))
cam.location = cam_pos
direction = target - cam_pos
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam
