import bpy, bmesh, math, random
from mathutils import Vector

random.seed(42)
scene = bpy.context.scene

# Clean scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- Materials ----------
def make_mat(name, color, rough=0.8):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return m

foliage_mats = [
    make_mat("Foliage_A", (0.02, 0.08, 0.03)),
    make_mat("Foliage_B", (0.03, 0.11, 0.04)),
    make_mat("Foliage_C", (0.015, 0.06, 0.035)),
]
trunk_mat = make_mat("Trunk", (0.08, 0.045, 0.025), 0.9)
ground_mat = make_mat("Ground", (0.05, 0.06, 0.03), 0.95)

# ---------- Meshes ----------
def cone_mesh(name, segs, r1, r2, depth):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r1, radius2=r2, depth=depth)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me

foliage_mesh = cone_mesh("FoliageCone", 20, 1.0, 0.0, 2.0)
trunk_mesh = cone_mesh("TrunkCyl", 10, 0.12, 0.09, 1.0)
trunk_mesh.materials.append(trunk_mat)

# Ground
gme = bpy.data.meshes.new("Ground")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=80)
bm.to_mesh(gme)
bm.free()
gme.materials.append(ground_mat)
ground = bpy.data.objects.new("Ground", gme)
ground.location = (0, 30, 0)
scene.collection.objects.link(ground)

# ---------- Trees ----------
forest = bpy.data.collections.new("Forest")
scene.collection.children.link(forest)

def add_tree(x, y, h):
    trunk_h = h * 0.18
    t = bpy.data.objects.new("Trunk", trunk_mesh)
    t.location = (x, y, trunk_h / 2)
    t.scale = (h / 6, h / 6, trunk_h)
    forest.objects.link(t)
    # stacked cones
    layers = random.choice([2, 3, 3])
    base_r = h * random.uniform(0.22, 0.3)
    cone_h = (h - trunk_h) / layers * 1.6
    for i in range(layers):
        f = bpy.data.objects.new("Foliage", foliage_mesh)
        f.data = foliage_mesh
        frac = i / layers
        r = base_r * (1 - frac * 0.55)
        ch = cone_h * (1 - frac * 0.3)
        z = trunk_h + frac * (h - trunk_h) * 0.8 + ch / 2
        f.location = (x, y, z)
        f.scale = (r, r, ch / 2)
        f.rotation_euler = (0, 0, random.uniform(0, math.pi))
        f.material_slots  # ensure
        forest.objects.link(f)
        f.active_material = None
        if not f.material_slots:
            pass
        mat = random.choice(foliage_mats)
        f.data = foliage_mesh
        # object-level material link
        if len(foliage_mesh.materials) == 0:
            foliage_mesh.materials.append(foliage_mats[0])
        f.material_slots[0].link = 'OBJECT'
        f.material_slots[0].material = mat

placed = []
attempts = 0
while len(placed) < 140 and attempts < 4000:
    attempts += 1
    x = random.uniform(-30, 30)
    y = random.uniform(-2, 65)
    # keep a clearing/path in front of camera
    if abs(x) < 2.0 + y * 0.03 and y < 25:
        continue
    if any((x - px) ** 2 + (y - py) ** 2 < 3.2 ** 2 for px, py in placed):
        continue
    placed.append((x, y))
    add_tree(x, y, random.uniform(6, 13))

# ---------- World with volumetric fog ----------
world = bpy.data.worlds.new("FoggyWorld")
scene.world = world
nt = world.node_tree
bg = nt.nodes.get("Background")
out = nt.nodes.get("World Output")
bg.inputs["Color"].default_value = (0.45, 0.52, 0.6, 1)
bg.inputs["Strength"].default_value = 0.6
vol = nt.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Color"].default_value = (0.75, 0.8, 0.85, 1)
vol.inputs["Density"].default_value = 0.035
vol.inputs["Anisotropy"].default_value = 0.4
vol.location = (0, -200)
nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun_data.color = (1.0, 0.9, 0.75)
sun_data.angle = math.radians(1.5)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(55), 0, math.radians(160))
scene.collection.objects.link(sun)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 28
cam_data.clip_end = 300
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -9, 1.8)
direction = Vector((0, 30, 4)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(cam)
scene.camera = cam

# ---------- Render settings ----------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.volume_bounces = 1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
