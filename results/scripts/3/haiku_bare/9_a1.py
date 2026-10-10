import bpy
import bmesh
import math
import random
import colorsys
from mathutils import Vector

random.seed(7)

# ---------- Clean up any default content ----------
for obj in list(bpy.context.scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------- Helpers ----------
def new_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def make_object(name, build_fn, material, smooth=False):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build_fn(bm)
    bm.to_mesh(mesh)
    bm.free()
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def build_cube(bm):
    bmesh.ops.create_cube(bm, size=1.0)


def build_sphere(bm):
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=1.0)


def build_cylinder(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=10,
                          radius1=1.0, radius2=1.0, depth=1.0)


def place(obj, loc, scale=(1, 1, 1), rot=(0, 0, 0)):
    obj.location = Vector(loc)
    obj.scale = Vector(scale)
    obj.rotation_euler = rot
    return obj


# ---------- Ground ----------
ground_mat = new_material("Ground", (0.75, 0.72, 0.68), roughness=0.9)
ground = make_object("Ground", build_cube, ground_mat)
place(ground, (0, 0, -0.01), scale=(12, 12, 0.02))

# ---------- Book stack ----------
book_count = 6
z = 0.0
book_top = 0.0
for i in range(book_count):
    w = random.uniform(0.70, 0.90)
    d = random.uniform(0.52, 0.64)
    t = random.uniform(0.06, 0.09)

    hue = random.random()
    sat = random.uniform(0.55, 0.85)
    val = random.uniform(0.45, 0.80)
    rgb = colorsys.hsv_to_rgb(hue, sat, val)

    mat = new_material(f"Book_{i}", rgb, roughness=random.uniform(0.45, 0.7))
    book = make_object(f"Book_{i}", build_cube, mat)

    rot_z = random.uniform(-0.15, 0.15)
    off_x = random.uniform(-0.03, 0.03)
    off_y = random.uniform(-0.03, 0.03)
    place(book,
          (off_x, off_y, z + t * 0.5),
          scale=(w, d, t),
          rot=(0, 0, rot_z))

    # Cream page block sitting on the front edge of each book
    page_mat = new_material(f"Pages_{i}", (0.93, 0.90, 0.82), roughness=0.8)
    pages = make_object(f"Pages_{i}", build_cube, page_mat)
    place(pages,
          (off_x, off_y - d * 0.02, z + t * 0.5),
          scale=(w * 0.97, d * 0.92, t * 0.72),
          rot=(0, 0, rot_z))

    z += t
    book_top = z

# ---------- Apple ----------
apple_r = 0.12
apple_mat = new_material("Apple", (0.75, 0.02, 0.02), roughness=0.25)
apple = make_object("Apple", build_sphere, apple_mat, smooth=True)
apple_center_z = book_top + apple_r * 0.9 + 0.005
place(apple, (0.02, -0.01, apple_center_z),
      scale=(apple_r, apple_r, apple_r * 0.9))

# Stem
stem_mat = new_material("Stem", (0.25, 0.14, 0.06), roughness=0.7)
stem = make_object("Stem", build_cylinder, stem_mat)
stem_top = apple_center_z + apple_r * 0.9
place(stem, (0.02, -0.01, stem_top + 0.03),
      scale=(0.007, 0.007, 0.06),
      rot=(math.radians(8), 0, 0))

# Leaf
leaf_mat = new_material("Leaf", (0.15, 0.45, 0.08), roughness=0.5)
leaf = make_object("Leaf", build_sphere, leaf_mat, smooth=True)
place(leaf, (0.065, -0.01, stem_top + 0.035),
      scale=(0.06, 0.025, 0.012),
      rot=(0, math.radians(-15), math.radians(30)))

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.0
sun_data.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

area_data = bpy.data.lights.new(name="KeyArea", type='AREA')
area_data.energy = 600
area_data.size = 2.5
area_data.color = (1.0, 0.97, 0.92)
area = bpy.data.objects.new("KeyArea", area_data)
bpy.context.collection.objects.link(area)
area.location = (1.6, -1.4, 1.8)
area.rotation_euler = (math.radians(55), 0, math.radians(45))

rim_data = bpy.data.lights.new(name="Rim", type='AREA')
rim_data.energy = 250
rim_data.size = 1.5
rim_data.color = (0.8, 0.9, 1.0)
rim = bpy.data.objects.new("Rim", rim_data)
bpy.context.collection.objects.link(rim)
rim.location = (-1.5, 1.5, 1.2)
rim.rotation_euler = (math.radians(60), 0, math.radians(-135))

# ---------- World ----------
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 65
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)

target = Vector((0.0, 0.0, book_top * 0.6 + 0.1))
cam_loc = Vector((1.5, -2.2, book_top + 0.9))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.camera = cam_obj

# ---------- Scene settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1
