import bpy, math, random
from mathutils import Vector

random.seed(4)
scene = bpy.context.scene

# Clear scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

def bevel(obj, w=0.01, seg=3):
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = w
    mod.segments = seg

# Ground / table
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
table = bpy.context.object
table.data.materials.append(mat("Table", (0.35, 0.22, 0.12), 0.6))

# Books
colors = [(0.8, 0.1, 0.1), (0.1, 0.3, 0.75), (0.95, 0.7, 0.1),
          (0.1, 0.55, 0.25), (0.5, 0.15, 0.6), (0.9, 0.4, 0.1)]
page_mat = mat("Pages", (0.93, 0.9, 0.8), 0.8)
z = 0.0
for i, c in enumerate(colors):
    w = random.uniform(1.4, 1.8)
    d = random.uniform(1.0, 1.3)
    h = random.uniform(0.18, 0.32)
    rot = random.uniform(-0.25, 0.25)
    ox, oy = random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08)
    # cover
    bpy.ops.mesh.primitive_cube_add(location=(ox, oy, z + h / 2))
    cover = bpy.context.object
    cover.scale = (w / 2, d / 2, h / 2)
    cover.rotation_euler.z = rot
    cover.data.materials.append(mat(f"Cover{i}", c, 0.45))
    bevel(cover, 0.015)
    # pages (inset slightly, protruding on 3 sides from spine side)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    pages = bpy.context.object
    pages.scale = ((w - 0.06) / 2, (d - 0.04) / 2 + 0.005, (h - 0.05) / 2)
    pages.location = (0.035, 0, 0)
    pages.parent = cover
    pages.matrix_parent_inverse.identity()
    pages.scale = ((w - 0.06) / w * 1.0 + 0.0, (d - 0.04) / d + 0.012, (h - 0.05) / h)
    pages.location = (0.04 / (w / 2), 0, 0)
    pages.data.materials.append(page_mat)
    z += h

# Apple
apple_mat = mat("Apple", (0.7, 0.03, 0.03), 0.3)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=0.35, location=(0, 0, z + 0.32))
apple = bpy.context.object
apple.scale = (1, 1, 0.9)
bm_mesh = apple.data
for v in bm_mesh.vertices:
    r = math.sqrt(v.co.x ** 2 + v.co.y ** 2) / 0.35
    # dimple top and bottom
    if v.co.z > 0:
        v.co.z -= 0.08 * (1 - r) ** 3
    else:
        v.co.z += 0.05 * (1 - r) ** 3
    v.co.x *= 1 + 0.08 * (v.co.z / 0.35)
    v.co.y *= 1 + 0.08 * (v.co.z / 0.35)
bpy.ops.object.shade_smooth()
apple.data.materials.append(apple_mat)

# Stem
bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=0.18, location=(0.01, 0, z + 0.32 + 0.3))
stem = bpy.context.object
stem.rotation_euler = (0.2, 0.15, 0)
stem.data.materials.append(mat("Stem", (0.25, 0.15, 0.05), 0.8))

# Leaf
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0.1, 0, z + 0.32 + 0.33))
leaf = bpy.context.object
leaf.scale = (1, 0.45, 0.08)
leaf.rotation_euler = (0, -0.4, 0.3)
bpy.ops.object.shade_smooth()
leaf.data.materials.append(mat("Leaf", (0.15, 0.5, 0.1), 0.5))

# Lighting
bpy.ops.object.light_add(type='AREA', location=(3, -3, 5))
key = bpy.context.object
key.data.energy = 800
key.data.size = 3
key.rotation_euler = (math.radians(45), 0, math.radians(45))
bpy.ops.object.light_add(type='AREA', location=(-4, -1, 3))
fill = bpy.context.object
fill.data.energy = 250
fill.data.size = 4
fill.rotation_euler = (math.radians(60), 0, math.radians(-75))
bpy.ops.object.light_add(type='POINT', location=(-1, 3, 4))
bpy.context.object.data.energy = 300

world = bpy.data.worlds.new("World") if not scene.world else scene.world
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.6, 0.65, 0.75, 1)
    bg.inputs[1].default_value = 0.4

# Camera
bpy.ops.object.camera_add(location=(4.2, -4.8, 3.2))
cam = bpy.context.object
target = Vector((0, 0, z * 0.6))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 50
scene.camera = cam
