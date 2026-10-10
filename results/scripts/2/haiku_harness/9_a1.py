import bpy
import bmesh
import math
import random
from mathutils import Vector

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

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
collection = scene.collection


# ---------- Helpers ----------
def make_mat(name, color, rough=0.5, metallic=0.0, specular=0.5):
    mat = bpy.data.materials.new(name)  # node tree is created automatically
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat


def link_object(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    for poly in me.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new(name, me)
    collection.objects.link(obj)
    return obj


def box_bm(sx, sy, sz, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel,
                        affect='EDGES', segments=2)
    return bm


def point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


# ---------- Materials ----------
book_colors = [
    (0.80, 0.14, 0.14),  # red
    (0.12, 0.35, 0.78),  # blue
    (0.95, 0.72, 0.10),  # yellow
    (0.18, 0.62, 0.30),  # green
    (0.55, 0.20, 0.70),  # purple
    (0.95, 0.45, 0.12),  # orange
]
random.shuffle(book_colors)

apple_mat = make_mat("AppleRed", (0.75, 0.04, 0.03), rough=0.18, specular=0.6)
stem_mat = make_mat("Stem", (0.25, 0.15, 0.06), rough=0.7)
leaf_mat = make_mat("Leaf", (0.15, 0.50, 0.12), rough=0.45)
ground_mat = make_mat("Ground", (0.72, 0.70, 0.66), rough=0.9, specular=0.2)

# ---------- Ground ----------
ground = link_object("Ground", box_bm(20.0, 20.0, 0.02), ground_mat)
ground.location = (0.0, 0.0, -0.01)

# ---------- Book stack ----------
z_top = 0.0
for i in range(6):
    thickness = random.uniform(0.16, 0.26)
    width = random.uniform(2.0, 2.5)
    depth = random.uniform(1.4, 1.8)
    color = book_colors[i % len(book_colors)]
    mat = make_mat(f"Book_{i}", color, rough=0.55, specular=0.35)

    book = link_object(f"Book_{i}", box_bm(width, depth, thickness, bevel=0.012), mat)
    book.location = (
        random.uniform(-0.08, 0.08),
        random.uniform(-0.08, 0.08),
        z_top + thickness / 2.0,
    )
    book.rotation_euler = (0.0, 0.0, random.uniform(-0.12, 0.12))
    z_top += thickness

# Pages-style cream inset on the front of the top-most book for detail
page_mat = make_mat("Pages", (0.93, 0.90, 0.80), rough=0.8, specular=0.2)
top_book = bpy.data.objects[f"Book_{5}"]
pages = link_object(
    "Pages",
    box_bm(top_book.dimensions.x * 0.92, top_book.dimensions.y * 0.92, 0.04),
    page_mat,
)
pages.location = (top_book.location.x, top_book.location.y, z_top - 0.012)
pages.rotation_euler = top_book.rotation_euler

# ---------- Apple ----------
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=0.5)
for v in bm.verts:
    x, y, z = v.co
    r = math.hypot(x, y)
    z *= 0.92
    if z > 0.0:
        # Dimple at the top
        z -= 0.12 * math.exp(-((r / 0.18) ** 2))
    # Slight bulge in the middle, narrower at the top
    x *= 1.02
    y *= 1.02
    v.co = (x, y, z)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
apple = link_object("Apple", bm, apple_mat)
apple.location = (0.05, -0.02, z_top + 0.46)

# Stem
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8,
                      radius1=0.025, radius2=0.018, depth=0.22)
stem = link_object("Stem", bm, stem_mat)
stem.location = (apple.location.x, apple.location.y, apple.location.z + 0.42)
stem.rotation_euler = (math.radians(8), 0.0, 0.0)

# Leaf
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.12)
bmesh.ops.scale(bm, vec=(1.0, 0.4, 0.05), verts=bm.verts)
leaf = link_object("Leaf", bm, leaf_mat)
leaf.location = (apple.location.x + 0.12, apple.location.y, apple.location.z + 0.50)
leaf.rotation_euler = (0.0, math.radians(-20), math.radians(35))

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("KeySun", sun_data)
collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(35))

area_data = bpy.data.lights.new("FillArea", 'AREA')
area_data.energy = 400.0
area_data.size = 4.0
area_data.color = (1.0, 0.97, 0.92)
fill = bpy.data.objects.new("FillArea", area_data)
collection.objects.link(fill)
fill.location = (-4.5, -4.0, 4.5)
point_at(fill, (0.0, 0.0, 1.2))

# ---------- World ----------
world = bpy.data.worlds.new("StudioWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.85, 0.88, 0.92, 1.0)
bg.inputs["Strength"].default_value = 0.6

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 55
cam = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam)
cam.location = (5.2, -6.6, 3.8)
point_at(cam, (0.0, 0.0, 1.5))
scene.camera = cam
