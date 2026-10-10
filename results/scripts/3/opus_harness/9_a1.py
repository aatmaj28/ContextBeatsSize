import bpy, math, random

random.seed(3)
scene = bpy.context.scene

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, spec=0.5):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

def bevel(obj, w=0.01, seg=3):
    md = obj.modifiers.new("Bevel", 'BEVEL')
    md.width = w
    md.segments = seg

# Table
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
table = bpy.context.object
table.data.materials.append(mat("Wood", (0.35, 0.2, 0.1), 0.4))

page_mat = mat("Pages", (0.92, 0.88, 0.75), 0.8)
colors = [(0.8, 0.1, 0.1), (0.1, 0.3, 0.8), (0.1, 0.6, 0.25), (0.9, 0.7, 0.1),
          (0.5, 0.15, 0.6), (0.9, 0.4, 0.1), (0.1, 0.55, 0.6)]

z = 0.0
for i, c in enumerate(colors):
    w = random.uniform(1.2, 1.6)
    d = random.uniform(0.9, 1.15)
    t = random.uniform(0.12, 0.22)
    rot = random.uniform(-0.25, 0.25)
    ox, oy = random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08)
    # cover
    bpy.ops.mesh.primitive_cube_add(location=(ox, oy, z + t / 2), rotation=(0, 0, rot))
    cov = bpy.context.object
    cov.scale = (w / 2, d / 2, t / 2)
    bevel(cov, 0.015)
    cov.data.materials.append(mat(f"Cover{i}", c, 0.45))
    # pages (slightly inset, sticking out on the open side)
    import mathutils
    off = mathutils.Matrix.Rotation(rot, 3, 'Z') @ mathutils.Vector((0.03, 0, 0))
    bpy.ops.mesh.primitive_cube_add(location=(ox + off.x, oy + off.y, z + t / 2), rotation=(0, 0, rot))
    pg = bpy.context.object
    pg.scale = (w / 2 - 0.01, d / 2 - 0.03, t / 2 - 0.02)
    pg.data.materials.append(page_mat)
    z += t

# Apple
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=0.35, location=(0, 0, z + 0.32))
apple = bpy.context.object
apple.scale = (1, 1, 0.9)
for v in apple.data.vertices:
    r = math.hypot(v.co.x, v.co.y)
    # dimples at top and bottom
    dent = 0.12 * math.exp(-(r / 0.12) ** 2)
    if v.co.z > 0:
        v.co.z -= dent
    else:
        v.co.z += dent * 0.6
bpy.ops.object.shade_smooth()
apple.data.materials.append(mat("Apple", (0.65, 0.02, 0.02), 0.25))

# Stem
bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=0.18, location=(0.01, 0, z + 0.6), rotation=(0.2, 0.15, 0))
bpy.context.object.data.materials.append(mat("Stem", (0.2, 0.1, 0.03), 0.8))
# Leaf
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0.1, 0, z + 0.64))
leaf = bpy.context.object
leaf.scale = (1, 0.4, 0.06)
leaf.rotation_euler = (0, -0.4, 0.3)
bpy.ops.object.shade_smooth()
leaf.data.materials.append(mat("Leaf", (0.1, 0.45, 0.08), 0.5))

# World
scene.world = bpy.data.worlds.new("World")
bg = scene.world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)
bg.inputs["Strength"].default_value = 0.5

# Lights
bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
key = bpy.context.object
key.data.energy = 600
key.data.size = 3
key.rotation_euler = (math.radians(50), 0, math.radians(45))
bpy.ops.object.light_add(type='AREA', location=(-3, -1, 2.5))
fill = bpy.context.object
fill.data.energy = 200
fill.data.size = 3
fill.rotation_euler = (math.radians(60), 0, math.radians(-70))
bpy.ops.object.light_add(type='SPOT', location=(-1, 3, 3.5))
rim = bpy.context.object
rim.data.energy = 300
rim.rotation_euler = (math.radians(-40), 0, math.radians(180))

# Camera
target_z = z * 0.55
bpy.ops.object.camera_add(location=(3.6, -4.2, 2.6))
cam = bpy.context.object
cam.data.lens = 50
bpy.ops.object.empty_add(location=(0, 0, target_z))
tgt = bpy.context.object
c = cam.constraints.new('TRACK_TO')
c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1280
scene.render.resolution_y = 1280
