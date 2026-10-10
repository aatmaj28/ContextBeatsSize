import bpy
import math
import random

random.seed(7)
scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

def make_mat(name, color, rough=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

# Floor / table
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(make_mat("Table", (0.35, 0.22, 0.12), 0.6))

# Books
page_mat = make_mat("Pages", (0.92, 0.88, 0.78), 0.8)
colors = [(0.8, 0.1, 0.1), (0.1, 0.3, 0.75), (0.1, 0.55, 0.25),
          (0.9, 0.7, 0.1), (0.5, 0.15, 0.6), (0.95, 0.45, 0.1)]
z = 0.0
for i, col in enumerate(colors):
    w = random.uniform(1.6, 2.1)
    d = random.uniform(1.2, 1.5)
    h = random.uniform(0.18, 0.32)
    rot = random.uniform(-0.25, 0.25)
    ox, oy = random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)
    cover = make_mat(f"Cover{i}", col, 0.45)
    # cover
    bpy.ops.mesh.primitive_cube_add(size=1, location=(ox, oy, z + h / 2))
    c = bpy.context.active_object
    c.scale = (w, d, h)
    c.rotation_euler.z = rot
    c.data.materials.append(cover)
    bev = c.modifiers.new("Bevel", 'BEVEL')
    bev.width = 0.02
    bev.segments = 3
    # pages (inset slightly, protruding on three sides)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(ox, oy, z + h / 2))
    p = bpy.context.active_object
    p.scale = (w - 0.06, d + 0.01, h * 0.82)
    p.location.x += 0.04 * math.cos(rot)
    p.location.y += 0.04 * math.sin(rot)
    p.rotation_euler.z = rot
    p.data.materials.append(page_mat)
    z += h

# Apple
apple_mat = make_mat("Apple", (0.7, 0.03, 0.03), 0.3)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, segments=48, ring_count=24,
                                     location=(0, 0, z + 0.32))
apple = bpy.context.active_object
apple.scale = (1.0, 1.0, 0.9)
bpy.ops.object.shade_smooth()
apple.data.materials.append(apple_mat)
# dimple top/bottom
for v in apple.data.vertices:
    r = math.sqrt(v.co.x ** 2 + v.co.y ** 2)
    if r < 0.12:
        f = (0.12 - r) / 0.12
        if v.co.z > 0:
            v.co.z -= 0.08 * f
        else:
            v.co.z += 0.04 * f
# Stem
stem_mat = make_mat("Stem", (0.25, 0.15, 0.05), 0.8)
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.18,
                                    location=(0.01, 0, z + 0.32 + 0.3))
stem = bpy.context.active_object
stem.rotation_euler = (0, 0.25, 0)
stem.data.materials.append(stem_mat)
# Leaf
leaf_mat = make_mat("Leaf", (0.15, 0.5, 0.1), 0.5)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0.1, 0, z + 0.32 + 0.33))
leaf = bpy.context.active_object
leaf.scale = (1.0, 0.45, 0.08)
leaf.rotation_euler = (0, -0.4, 0.3)
bpy.ops.object.shade_smooth()
leaf.data.materials.append(leaf_mat)

# Lights
bpy.ops.object.light_add(type='AREA', location=(3, -3, 5))
key = bpy.context.active_object
key.data.energy = 800
key.data.size = 3
key.rotation_euler = (math.radians(45), 0, math.radians(45))
bpy.ops.object.light_add(type='AREA', location=(-4, -1, 3))
fill = bpy.context.active_object
fill.data.energy = 250
fill.data.size = 4
fill.rotation_euler = (math.radians(60), 0, math.radians(-75))
bpy.ops.object.light_add(type='POINT', location=(-1, 3, 4))
bpy.context.active_object.data.energy = 300

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.6, 0.65, 0.75, 1)
bg.inputs["Strength"].default_value = 0.4

# Camera
bpy.ops.object.camera_add(location=(4.5, -5.0, 3.6))
cam = bpy.context.active_object
target_z = z * 0.55
import mathutils
direction = mathutils.Vector((0, 0, target_z)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
