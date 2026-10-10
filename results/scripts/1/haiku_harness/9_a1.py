import bpy
import bmesh
import math
import random
import colorsys
from mathutils import Vector, Matrix, Euler

random.seed(7)

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
collection = bpy.context.collection


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0, specular=0.5):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat


def new_object(name, bm, mat, location=(0, 0, 0), rotation=(0, 0, 0), smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    ob.location = location
    ob.rotation_euler = rotation
    return ob


def box_bm(sx, sy, sz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    return bm


# ---------- Materials ----------
book_colors = []
for i in range(7):
    hue = random.random()
    sat = random.uniform(0.5, 0.8)
    val = random.uniform(0.5, 0.85)
    book_colors.append(colorsys.hsv_to_rgb(hue, sat, val))

cream_mat = make_material("PageCream", (0.92, 0.88, 0.75), roughness=0.8)
apple_mat = make_material("AppleRed", (0.75, 0.04, 0.03), roughness=0.25, specular=0.6)
leaf_mat = make_material("LeafGreen", (0.15, 0.45, 0.08), roughness=0.5)
stem_mat = make_material("StemBrown", (0.20, 0.12, 0.05), roughness=0.7)
floor_mat = make_material("Floor", (0.55, 0.52, 0.48), roughness=0.9)

# ---------- Floor ----------
floor = new_object("Floor", box_bm(12.0, 12.0, 0.1), floor_mat, location=(0, 0, -0.05))

# ---------- Book stack ----------
z = 0.0
book_count = len(book_colors)
for i, col in enumerate(book_colors):
    mat = make_material(f"Book_{i}", col, roughness=random.uniform(0.4, 0.7))
    h = random.uniform(0.07, 0.12)
    w = random.uniform(1.1, 1.4)
    d = random.uniform(0.8, 1.0)
    rz = random.uniform(-0.12, 0.12)
    ox = random.uniform(-0.05, 0.05)
    oy = random.uniform(-0.05, 0.05)
    center = Vector((ox, oy, z + h / 2))

    book = new_object(f"Book_{i}", box_bm(w, d, h), mat,
                      location=tuple(center), rotation=(0, 0, rz))

    # Cream page label on the front face, rotated with the book
    rot_mat = Euler((0, 0, rz)).to_matrix()
    label_offset = rot_mat @ Vector((0, -d / 2 - 0.004, 0))
    label_pos = center + label_offset
    label = new_object(f"Label_{i}", box_bm(w * 0.5, 0.008, h * 0.45), cream_mat,
                       location=tuple(label_pos), rotation=(0, 0, rz))
    z += h

stack_top = z

# ---------- Apple ----------
apple_r = 0.4
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=apple_r)
for v in bm.verts:
    v.co.z *= 0.9
    # Dent at the top pole
    if v.co.z > 0.2:
        t = min((v.co.z - 0.2) / 0.16, 1.0)
        v.co.z -= 0.07 * t
        v.co.x *= (1.0 - 0.05 * t)
        v.co.y *= (1.0 - 0.05 * t)
    # Slight organic bottom bulge variation
    v.co.x *= 1.0 + 0.03 * math.sin(v.co.z * 9.0)

apple_center = Vector((0.05, -0.03, stack_top + apple_r * 0.9 - 0.02))
apple = new_object("Apple", bm, apple_mat, location=tuple(apple_center),
                   rotation=(0, 0, 0.4), smooth=True)

# Stem
stem_base_z = apple_center.z + apple_r * 0.9 - 0.07 - 0.02
stem_len = 0.18
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12,
                      radius1=0.02, radius2=0.015, depth=stem_len)
stem = new_object("Stem", bm, stem_mat,
                  location=(apple_center.x - 0.01, apple_center.y, stem_base_z + stem_len / 2),
                  rotation=(math.radians(8), 0, 0), smooth=True)

# Leaf
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.12)
bmesh.ops.scale(bm, vec=(1.6, 0.6, 0.12), verts=bm.verts)
leaf = new_object("Leaf", bm, leaf_mat,
                  location=(apple_center.x + 0.1, apple_center.y + 0.05, stem_base_z + 0.14),
                  rotation=(0, math.radians(15), 0.5), smooth=True)

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.055, 0.065, 1.0)
    bg.inputs["Strength"].default_value = 0.6

# ---------- Lights ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.0
sun_data.angle = math.radians(5)
sun = bpy.data.objects.new("Sun", sun_data)
collection.objects.link(sun)
sun.location = (4, -4, 6)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

area_data = bpy.data.lights.new(name="Fill", type='AREA')
area_data.energy = 250.0
area_data.size = 4.0
area = bpy.data.objects.new("Fill", area_data)
collection.objects.link(area)
area.location = (-3.5, -3.0, 3.5)
area.rotation_euler = (math.radians(60), 0, math.radians(-40))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 65
cam = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam)

target = Vector((0.0, 0.0, stack_top * 0.55 + 0.2))
cam_loc = Vector((3.8, -5.2, stack_top + 1.6))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
