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
    md = obj.modifiers.new("Bevel", 'BEVEL')
    md.width = w
    md.segments = seg

# Table
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.05))
table = bpy.context.object
table.scale = (4, 3, 0.1)
table.data.materials.append(mat("Wood", (0.35, 0.2, 0.1), 0.6))

# Books
colors = [(0.8, 0.1, 0.1), (0.1, 0.3, 0.8), (0.1, 0.6, 0.2), (0.9, 0.7, 0.1),
          (0.5, 0.15, 0.6), (0.9, 0.4, 0.1)]
paper = mat("Paper", (0.92, 0.88, 0.78), 0.8)
z = 0.0
for i, c in enumerate(colors):
    w = random.uniform(0.75, 0.95)
    d = random.uniform(0.55, 0.7)
    h = random.uniform(0.1, 0.18)
    rot = random.uniform(-0.25, 0.25)
    off = Vector((random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), 0))
    cover = mat(f"Cover{i}", c, 0.4)
    # cover
    bpy.ops.mesh.primitive_cube_add(size=1, location=(off.x, off.y, z + h / 2))
    b = bpy.context.object
    b.scale = (w, d, h)
    b.rotation_euler.z = rot
    b.data.materials.append(cover)
    bevel(b, 0.008)
    # pages (inset, protruding slightly on front/side edges)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(off.x + 0.012, off.y, z + h / 2))
    p = bpy.context.object
    p.scale = (w - 0.01, d - 0.02, h * 0.82)
    p.rotation_euler.z = rot
    p.data.materials.append(paper)
    # recompute location for rotation offset
    shift = Vector((0.012, 0, 0))
    shift.rotate(b.rotation_euler)
    p.location = Vector((off.x, off.y, z + h / 2)) + shift
    z += h

# Apple
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, segments=48, ring_count=32, location=(0, 0, z + 0.15))
apple = bpy.context.object
apple.scale = (1, 1, 0.92)
for v in apple.data.vertices:
    co = v.co
    r = math.sqrt(co.x ** 2 + co.y ** 2) / 0.16
    # dimples at top and bottom
    co.z -= 0.05 * math.exp(-(r ** 2) / 0.05) * (1 if co.z > 0 else -0.5)
bpy.ops.object.shade_smooth()
apple.data.materials.append(mat("Apple", (0.7, 0.03, 0.03), 0.25))

# Stem
bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.09, location=(0.005, 0, z + 0.15 + 0.13))
stem = bpy.context.object
stem.rotation_euler = (0.15, 0.2, 0)
stem.data.materials.append(mat("Stem", (0.25, 0.15, 0.05), 0.8))

# Leaf
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0.05, 0.01, z + 0.15 + 0.14))
leaf = bpy.context.object
leaf.scale = (1, 0.4, 0.08)
leaf.rotation_euler = (0, -0.4, 0.3)
bpy.ops.object.shade_smooth()
leaf.data.materials.append(mat("Leaf", (0.15, 0.5, 0.1), 0.5))

# Lights
bpy.ops.object.light_add(type='AREA', location=(2.5, -2, 3))
key = bpy.context.object
key.data.energy = 400
key.data.size = 2
key.rotation_euler = (math.radians(50), 0, math.radians(50))
bpy.ops.object.light_add(type='AREA', location=(-2.5, -1.5, 2))
fill = bpy.context.object
fill.data.energy = 120
fill.data.size = 3
fill.rotation_euler = (math.radians(60), 0, math.radians(-60))
bpy.ops.object.light_add(type='SUN', location=(0, 3, 4))
sun = bpy.context.object
sun.data.energy = 1.5
sun.rotation_euler = (math.radians(-40), 0, 0)

# World
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)

# Camera
bpy.ops.object.camera_add(location=(2.6, -2.8, 1.9))
cam = bpy.context.object
cam.data.lens = 50
target = Vector((0, 0, z * 0.6))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
