import bpy
import math
import random
import colorsys
from mathutils import Vector

random.seed(7)

# ---------- Clean up ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


# ---------- Helpers ----------
def make_mat(name, color, roughness=0.5, specular=0.3):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def add_box(name, loc, dims, rot_z, mat, bevel=0.012):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = dims
    o.rotation_euler = (0.0, 0.0, rot_z)
    o.data.materials.append(mat)
    if bevel > 0:
        m = o.modifiers.new("Bevel", 'BEVEL')
        m.width = bevel
        m.segments = 3
        m.limit_method = 'ANGLE'
    smooth(o)
    return o


def add_sphere(name, loc, radius, scale, mat, segments=64, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    smooth(o)
    return o


def add_cylinder(name, loc, radius, depth, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16, radius=radius, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = rot
    o.data.materials.append(mat)
    smooth(o)
    return o


# ---------- Materials ----------
table_mat = make_mat("TableWood", (0.42, 0.28, 0.16), roughness=0.55, specular=0.35)
apple_mat = make_mat("AppleRed", (0.75, 0.04, 0.03), roughness=0.25, specular=0.6)
stem_mat = make_mat("Stem", (0.25, 0.14, 0.05), roughness=0.8, specular=0.2)
leaf_mat = make_mat("Leaf", (0.12, 0.45, 0.1), roughness=0.5, specular=0.4)

# ---------- Table / surface ----------
bpy.ops.mesh.primitive_plane_add(size=30.0, location=(0, 0, 0))
table = bpy.context.active_object
table.name = "Table"
table.data.materials.append(table_mat)

# ---------- Books ----------
palette_hues = [0.00, 0.58, 0.12, 0.33, 0.78, 0.05, 0.47]
num_books = 6
z = 0.0
top_books_x = 0.0
top_books_y = 0.0

for i in range(num_books):
    hue = palette_hues[i % len(palette_hues)] + random.uniform(-0.03, 0.03)
    sat = random.uniform(0.55, 0.8)
    val = random.uniform(0.55, 0.85)
    r, g, b = colorsys.hsv_to_rgb(hue % 1.0, sat, val)
    cover = make_mat(f"BookCover{i}", (r, g, b), roughness=random.uniform(0.45, 0.7))

    # Accent label/band on the cover
    ar, ag, ab = colorsys.hsv_to_rgb((hue + 0.5) % 1.0, 0.3, 0.92)
    label = make_mat(f"BookLabel{i}", (ar, ag, ab), roughness=0.6)

    w = random.uniform(1.6, 2.0)
    d = random.uniform(1.2, 1.45)
    h = random.uniform(0.16, 0.24)
    rot = math.radians(random.uniform(-14, 14))
    ox = random.uniform(-0.07, 0.07)
    oy = random.uniform(-0.06, 0.06)

    loc = (ox, oy, z + h / 2.0)
    add_box(f"Book{i}", loc, (w, d, h), rot, cover)

    # Cream page edge strip on the front face, rotated with the book
    cos_r, sin_r = math.cos(rot), math.sin(rot)
    local = Vector((0.0, -d / 2.0 - 0.003, 0.0))
    world_off = Vector((local.x * cos_r - local.y * sin_r,
                        local.x * sin_r + local.y * cos_r, 0.0))
    pages_mat = make_mat(f"Pages{i}", (0.93, 0.9, 0.8), roughness=0.8, specular=0.1)
    add_box(f"Pages{i}",
            (loc[0] + world_off.x, loc[1] + world_off.y, loc[2]),
            (w * 0.9, 0.012, h * 0.7), rot, pages_mat, bevel=0.0)

    # Label on the spine-facing side
    lab_local = Vector((w * 0.22, -d / 2.0 - 0.006, 0.0))
    lab_off = Vector((lab_local.x * cos_r - lab_local.y * sin_r,
                      lab_local.x * sin_r + lab_local.y * cos_r, 0.0))
    add_box(f"Label{i}",
            (loc[0] + lab_off.x, loc[1] + lab_off.y, loc[2]),
            (w * 0.3, 0.01, h * 0.4), rot, label, bevel=0.0)

    z += h
    top_books_x = ox
    top_books_y = oy

stack_top = z

# ---------- Apple ----------
apple_r = 0.5
apple_sq = 0.92
apple_center = (top_books_x * 0.5, top_books_y * 0.5, stack_top + apple_r * apple_sq)

apple = add_sphere("Apple", apple_center, apple_r, (1.0, 1.0, apple_sq), apple_mat)

# Dimple at top of apple: small dark cap pressed in
dimple_z = apple_center[2] + apple_r * apple_sq * 0.92
add_sphere("AppleDimple", (apple_center[0], apple_center[1], dimple_z),
           0.12, (1.0, 1.0, 0.35), stem_mat, segments=24, rings=12)

# Stem
stem_len = 0.42
stem_base_z = apple_center[2] + apple_r * apple_sq * 0.95
add_cylinder("Stem",
             (apple_center[0] + 0.02, apple_center[1], stem_base_z + stem_len / 2.0),
             0.035, stem_len, stem_mat,
             rot=(math.radians(8), 0, 0))

# Leaf
leaf = add_sphere("Leaf",
                  (apple_center[0] + 0.22, apple_center[1] - 0.02,
                   stem_base_z + 0.3),
                  0.22, (1.0, 0.45, 0.12), leaf_mat, segments=24, rings=12)
leaf.rotation_euler = (math.radians(15), math.radians(-20), math.radians(35))

# ---------- World ----------
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
    bg.inputs["Strength"].default_value = 0.6

# ---------- Lights ----------
bpy.ops.object.light_add(type='SUN', location=(4, -4, 8))
sun = bpy.context.active_object
sun.name = "KeySun"
sun.data.energy = 3.0
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-4, -5, 4))
fill = bpy.context.active_object
fill.name = "FillArea"
fill.data.energy = 350
fill.data.size = 4.0
fill.rotation_euler = (math.radians(65), 0, math.radians(-30))

bpy.ops.object.light_add(type='AREA', location=(0, 5, 3))
rim = bpy.context.active_object
rim.name = "RimArea"
rim.data.energy = 250
rim.data.size = 3.0
rim.rotation_euler = (math.radians(-60), 0, 0)

# ---------- Camera ----------
focus = Vector((0.0, 0.0, stack_top + 0.5))
bpy.ops.object.camera_add(location=(4.6, -5.8, stack_top + 1.8))
cam = bpy.context.active_object
cam.name = "Camera"
cam.data.lens = 60
cam.data.dof.use_dof = True
cam.data.dof.focus_object = apple

# Aim camera at the stack
empty = bpy.data.objects.new("CameraTarget", None)
empty.location = focus
bpy.context.collection.objects.link(empty)

con = cam.constraints.new(type='TRACK_TO')
con.target = empty
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'

bpy.context.scene.camera = cam

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
