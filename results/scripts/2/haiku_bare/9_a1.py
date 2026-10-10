import bpy
import math
import random
import colorsys
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def make_mat(name, color, roughness=0.5, specular=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def link(obj):
    scene.collection.objects.link(obj)
    return obj


clear_scene()

# ---------- Materials ----------
floor_mat = make_mat("Floor", (0.55, 0.52, 0.48), roughness=0.8)
apple_mat = make_mat("Apple", (0.75, 0.04, 0.03), roughness=0.25, specular=0.6)
stem_mat = make_mat("Stem", (0.25, 0.15, 0.05), roughness=0.7)
leaf_mat = make_mat("Leaf", (0.15, 0.45, 0.1), roughness=0.5)

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = link(bpy.context.active_object)
floor.name = "Floor"
assign(floor, floor_mat)

# ---------- Books ----------
book_palette = [
    colorsys.hsv_to_rgb(0.00, 0.70, 0.70),  # red
    colorsys.hsv_to_rgb(0.10, 0.65, 0.85),  # orange-yellow
    colorsys.hsv_to_rgb(0.33, 0.55, 0.60),  # green
    colorsys.hsv_to_rgb(0.58, 0.60, 0.75),  # blue
    colorsys.hsv_to_rgb(0.78, 0.45, 0.65),  # purple
]
random.shuffle(book_palette)

z_cursor = 0.0
book_top = 0.0
for i, col in enumerate(book_palette):
    w = random.uniform(1.3, 1.6)
    d = random.uniform(0.95, 1.1)
    h = random.uniform(0.18, 0.24)
    x_off = random.uniform(-0.12, 0.12)
    y_off = random.uniform(-0.08, 0.08)
    yaw = math.radians(random.uniform(-8, 8))

    bpy.ops.mesh.primitive_cube_add(size=1.0,
                                    location=(x_off, y_off, z_cursor + h / 2))
    book = link(bpy.context.active_object)
    book.name = f"Book_{i}"
    book.scale = (w, d, h)
    book.rotation_euler = (0, 0, yaw)
    bpy.context.view_layer.objects.active = book
    book.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(book, make_mat(f"BookMat_{i}", col, roughness=0.55))

    # Page block: slightly lighter strip along one front edge
    bpy.ops.mesh.primitive_cube_add(size=1.0,
                                    location=(x_off, y_off - d * 0.5 + 0.01,
                                              z_cursor + h / 2))
    pages = link(bpy.context.active_object)
    pages.name = f"Pages_{i}"
    pages.scale = (w * 0.96, 0.02, h * 0.82)
    pages.rotation_euler = (0, 0, yaw)
    bpy.context.view_layer.objects.active = pages
    pages.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(pages, make_mat(f"PagesMat_{i}", (0.93, 0.90, 0.82), roughness=0.9))

    z_cursor += h
    book_top = z_cursor

# ---------- Apple ----------
apple_radius = 0.42
apple_z = book_top + apple_radius * 0.9
bpy.ops.mesh.primitive_uv_sphere_add(radius=apple_radius, segments=48, ring_count=32,
                                     location=(0.0, 0.0, apple_z))
apple = link(bpy.context.active_object)
apple.name = "Apple"
apple.scale = (1.0, 1.0, 0.9)
bpy.context.view_layer.objects.active = apple
apple.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.shade_smooth()
assign(apple, apple_mat)

# Dimple at the top of the apple
top_dimple_z = apple_z + apple_radius * 0.9
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, segments=16, ring_count=8,
                                     location=(0.0, 0.0, top_dimple_z - 0.02))
dimple = link(bpy.context.active_object)
dimple.name = "ApplePitTop"
assign(dimple, apple_mat)
dimple.hide_viewport = False
dimple.hide_render = False
dimple.hide_set(False)
# Pull dimple inside a bit: shrink so it blends in as a soft indent cover
dimple.scale = (1.0, 1.0, 0.25)
dimple.location.z = top_dimple_z - 0.04

# Stem
stem_len = 0.22
stem_base_z = top_dimple_z + 0.02
bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=stem_len,
                                    location=(0.03, 0.0, stem_base_z + stem_len / 2))
stem = link(bpy.context.active_object)
stem.name = "Stem"
stem.rotation_euler = (0, math.radians(12), 0)
assign(stem, stem_mat)

# Leaf
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, segments=16, ring_count=8,
                                     location=(0.16, 0.0, stem_base_z + stem_len * 0.85))
leaf = link(bpy.context.active_object)
leaf.name = "Leaf"
leaf.scale = (1.6, 0.6, 0.12)
leaf.rotation_euler = (0, math.radians(-20), math.radians(25))
assign(leaf, leaf_mat)

# ---------- World ----------
world = bpy.data.worlds.new("World")
world.use_nodes = False
world.color = (0.92, 0.92, 0.95)
scene.world = world

# ---------- Lights ----------
sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(4)
sun = bpy.data.objects.new("KeySun", sun_data)
link(sun)
sun.location = (4, -4, 6)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

fill_data = bpy.data.lights.new(name="FillArea", type='AREA')
fill_data.energy = 400
fill_data.size = 4.0
fill = bpy.data.objects.new("FillArea", fill_data)
link(fill)
fill.location = (-4, -3, 3)
fill.rotation_euler = (math.radians(65), 0, math.radians(-50))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 70
cam_data.dof.use_dof = False
cam = bpy.data.objects.new("Camera", cam_data)
link(cam)
cam.location = (3.6, -4.6, 2.4)
target = Vector((0.0, 0.0, book_top * 0.55 + 0.2))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Render settings (no render performed) ----------
scene.frame_start = 1
scene.frame_end = 1
