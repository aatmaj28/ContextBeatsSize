import bpy, math, random, colorsys
from mathutils import Vector

random.seed(4)
scene = bpy.context.scene

def mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

# Floor / table
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
table = bpy.context.active_object
table.data.materials.append(mat("Table", (0.35, 0.2, 0.1), 0.4))

page_mat = mat("Pages", (0.92, 0.88, 0.75), 0.8)

# Books
z = 0.0
colors = [(0.7, 0.1, 0.1), (0.1, 0.3, 0.7), (0.15, 0.55, 0.2),
          (0.85, 0.6, 0.1), (0.45, 0.15, 0.55), (0.1, 0.55, 0.6)]
for i, c in enumerate(colors):
    w = random.uniform(1.4, 1.8)
    d = random.uniform(1.0, 1.25)
    h = random.uniform(0.15, 0.28)
    rot = random.uniform(-0.25, 0.25)
    ox, oy = random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08)
    # cover
    bpy.ops.mesh.primitive_cube_add(location=(ox, oy, z + h / 2))
    cov = bpy.context.active_object
    cov.scale = (w / 2, d / 2, h / 2)
    cov.rotation_euler.z = rot
    bev = cov.modifiers.new("Bevel", 'BEVEL')
    bev.width = 0.015
    bev.segments = 2
    cov.data.materials.append(mat(f"Cover{i}", c, 0.45))
    # pages (slightly inset, sticking out on three sides of the cover thickness)
    bpy.ops.mesh.primitive_cube_add(location=(ox, oy, z + h / 2))
    pg = bpy.context.active_object
    pg.scale = (w / 2 + 0.005, d / 2 - 0.04, h / 2 - 0.025)
    pg.rotation_euler.z = rot
    # offset pages toward the front opposite spine
    off = Vector((0.0, 0.0, 0.0))
    pg.data.materials.append(page_mat)
    z += h

# Apple
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=0.32,
                                     location=(0.05, 0, z + 0.29))
apple = bpy.context.active_object
apple.scale = (1, 1, 0.9)
for v in apple.data.vertices:
    co = v.co
    r = math.sqrt(co.x**2 + co.y**2)
    # dimple at top and bottom
    if r < 0.12:
        f = (0.12 - r) / 0.12
        if co.z > 0:
            co.z -= 0.08 * f
        else:
            co.z += 0.04 * f
bpy.ops.object.shade_smooth()
apple.data.materials.append(mat("Apple", (0.65, 0.03, 0.03), 0.3))

# Stem
top = z + 0.29 + 0.32 * 0.9 - 0.07
bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.16,
                                    location=(0.06, 0, top + 0.06))
stem = bpy.context.active_object
stem.rotation_euler = (0.2, 0.25, 0)
stem.data.materials.append(mat("Stem", (0.2, 0.12, 0.05), 0.8))

# Leaf
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0.15, 0.02, top + 0.08))
leaf = bpy.context.active_object
leaf.scale = (1, 0.45, 0.06)
leaf.rotation_euler = (0, -0.4, 0.3)
bpy.ops.object.shade_smooth()
leaf.data.materials.append(mat("Leaf", (0.15, 0.45, 0.08), 0.5))

# Lights
bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
key = bpy.context.active_object
key.data.energy = 600
key.data.size = 2
key.rotation_euler = (math.radians(45), 0, math.radians(45))
bpy.ops.object.light_add(type='AREA', location=(-3, -1, 3))
fill = bpy.context.active_object
fill.data.energy = 200
fill.data.size = 3
fill.rotation_euler = (math.radians(50), 0, math.radians(-70))
bpy.ops.object.light_add(type='SUN', location=(0, 3, 5))
sun = bpy.context.active_object
sun.data.energy = 1.5
sun.rotation_euler = (math.radians(-30), 0, 0)

# World
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)

# Camera
center = Vector((0, 0, (z + 0.6) / 2))
bpy.ops.object.camera_add(location=(3.6, -4.2, 2.6))
cam = bpy.context.active_object
cam.data.lens = 50
d = center - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
