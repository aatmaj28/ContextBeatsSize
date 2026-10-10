import bpy, bmesh, random, math
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene

# Clear scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def make_cone_mesh(name, r1, r2, depth, segs=16):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r1, radius2=r2, depth=depth)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    return me

# Materials
def mat(name, color, rough=0.8):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

leaf_mats = [mat("Pine%d" % i, c) for i, c in enumerate(
    [(0.03, 0.12, 0.05), (0.04, 0.15, 0.07), (0.02, 0.09, 0.05), (0.05, 0.13, 0.04)])]
bark_mat = mat("Bark", (0.12, 0.07, 0.04), 0.9)
ground_mat = mat("Ground", (0.06, 0.08, 0.04), 1.0)

# Meshes
cone_mesh = make_cone_mesh("ConeMesh", 1.0, 0.0, 2.0)
trunk_mesh = make_cone_mesh("TrunkMesh", 0.15, 0.1, 1.0, 8)
trunk_mesh.materials.append(bark_mat)

# Ground
gme = bpy.data.meshes.new("Ground")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=80)
bm.to_mesh(gme); bm.free()
gme.materials.append(ground_mat)
ground = bpy.data.objects.new("Ground", gme)
scene.collection.objects.link(ground)

col = bpy.data.collections.new("Forest")
scene.collection.children.link(col)

# Tree meshes per material (so cones can have varied colors)
cone_variants = []
for m in leaf_mats:
    me = cone_mesh.copy()
    me.materials.append(m)
    cone_variants.append(me)

def add_tree(x, y, s):
    trunk = bpy.data.objects.new("Trunk", trunk_mesh)
    trunk.location = (x, y, 0.5 * s)
    trunk.scale = (s, s, s)
    col.objects.link(trunk)
    tiers = random.randint(2, 4)
    me = random.choice(cone_variants)
    z = 0.8 * s
    r = 1.3 * s
    for t in range(tiers):
        h = r * 1.6
        c = bpy.data.objects.new("Cone", me)
        c.location = (x, y, z + h / 2)
        c.scale = (r, r, h / 2)
        c.rotation_euler = (0, 0, random.uniform(0, math.pi))
        col.objects.link(c)
        z += h * 0.45
        r *= 0.72

placed = []
for i in range(220):
    for _ in range(20):
        x = random.uniform(-35, 35)
        y = random.uniform(-10, 60)
        if abs(x) < 2.5 and y < 8:
            continue
        if all((x - px) ** 2 + (y - py) ** 2 > 4.0 for px, py in placed):
            placed.append((x, y))
            add_tree(x, y, random.uniform(0.9, 2.0))
            break

# World with volumetric fog
world = bpy.data.worlds.new("FogWorld")
scene.world = world
nt = world.node_tree
nodes, links = nt.nodes, nt.links
bg = nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.6, 0.65, 1)
bg.inputs["Strength"].default_value = 0.6
out = nodes.get("World Output")
vol = nodes.new("ShaderNodeVolumePrincipled")
vol.location = (0, -250)
vol.inputs["Color"].default_value = (0.8, 0.85, 0.9, 1)
vol.inputs["Density"].default_value = 0.04
vol.inputs["Anisotropy"].default_value = 0.3
links.new(vol.outputs["Volume"], out.inputs["Volume"])

# Lighting
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun_data.color = (1.0, 0.92, 0.8)
sun_data.angle = math.radians(2)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(65), 0, math.radians(160))
scene.collection.objects.link(sun)

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 30
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -6, 1.7)
cam.rotation_euler = (math.radians(86), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

# Render settings
scene.render.engine = 'BLENDER_EEVEE'
try:
    scene.eevee.volumetric_end = 80
    scene.eevee.volumetric_tile_size = '4'
    scene.eevee.use_volumetric_shadows = True
except Exception:
    pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
