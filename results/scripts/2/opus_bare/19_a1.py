import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(42)
scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    pass

# ---------- Materials ----------
def make_mat(name, color, rough=0.8):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*color, 1.0)
    return m

foliage_mats = [
    make_mat("Foliage_A", (0.03, 0.12, 0.05)),
    make_mat("Foliage_B", (0.04, 0.16, 0.06)),
    make_mat("Foliage_C", (0.02, 0.09, 0.05)),
]
trunk_mat = make_mat("Trunk", (0.12, 0.07, 0.04))
ground_mat = make_mat("Ground", (0.08, 0.10, 0.05), 0.95)

# ---------- Shared meshes ----------
def cone_mesh(name, r1, depth, segs=16):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r1, radius2=0.0, depth=depth)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((0, 0, depth / 2)))
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me

def cyl_mesh(name, r, depth, segs=10):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r * 0.8, depth=depth)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((0, 0, depth / 2)))
    bm.to_mesh(me)
    bm.free()
    return me

cone_meshes = []
for i, mat in enumerate(foliage_mats):
    me = cone_mesh(f"TreeCone_{i}", 1.0, 1.0)
    me.materials.append(mat)
    cone_meshes.append(me)
trunk_me = cyl_mesh("Trunk", 0.15, 1.0)
trunk_me.materials.append(trunk_mat)

col = scene.collection

# ---------- Ground ----------
gme = bpy.data.meshes.new("Ground")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=60, y_segments=60, size=60)
for v in bm.verts:
    v.co.z = 0.3 * math.sin(v.co.x * 0.15) * math.cos(v.co.y * 0.12) + random.uniform(-0.05, 0.05)
bm.to_mesh(gme)
bm.free()
for p in gme.polygons:
    p.use_smooth = True
gme.materials.append(ground_mat)
ground = bpy.data.objects.new("Ground", gme)
col.objects.link(ground)

def ground_z(x, y):
    return 0.3 * math.sin(x * 0.15) * math.cos(y * 0.12)

# ---------- Trees ----------
placed = []
attempts = 0
while len(placed) < 160 and attempts < 4000:
    attempts += 1
    x = random.uniform(-45, 45)
    y = random.uniform(-25, 55)
    # keep a clearing path near the camera line
    if abs(x) < 2.5 and y < 30:
        continue
    if any((x - px) ** 2 + (y - py) ** 2 < 6.0 for px, py in placed):
        continue
    placed.append((x, y))
    z0 = ground_z(x, y) - 0.1
    h = random.uniform(5, 11)
    r = h * random.uniform(0.18, 0.25)
    trunk_h = h * 0.2
    t = bpy.data.objects.new("Trunk", trunk_me)
    t.location = (x, y, z0)
    t.scale = (r * 0.6, r * 0.6, trunk_h + 0.3)
    col.objects.link(t)
    # stacked tiers
    tiers = random.choice([1, 2, 3])
    for k in range(tiers):
        f = 1.0 - k * 0.25
        c = bpy.data.objects.new("Foliage", random.choice(cone_meshes))
        c.location = (x, y, z0 + trunk_h + k * h * 0.22)
        c.scale = (r * f, r * f, (h - trunk_h) * (1.0 - k * 0.2))
        c.rotation_euler = (random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03),
                            random.uniform(0, math.tau))
        col.objects.link(c)

# ---------- World with volumetric fog ----------
world = bpy.data.worlds.new("FogWorld")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
nt = world.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new("ShaderNodeOutputWorld")
out.location = (400, 0)
bg = nodes.new("ShaderNodeBackground")
bg.location = (100, 120)
bg.inputs["Color"].default_value = (0.55, 0.62, 0.68, 1.0)
bg.inputs["Strength"].default_value = 0.8
vol = nodes.new("ShaderNodeVolumeScatter")
vol.location = (100, -120)
vol.inputs["Color"].default_value = (0.85, 0.9, 0.95, 1.0)
vol.inputs["Density"].default_value = 0.04
if "Anisotropy" in vol.inputs:
    vol.inputs["Anisotropy"].default_value = 0.3
links.new(bg.outputs["Background"], out.inputs["Surface"])
links.new(vol.outputs["Volume"], out.inputs["Volume"])

# EEVEE volume settings (guarded)
ee = getattr(scene, "eevee", None)
if ee:
    for attr, val in (("volumetric_start", 0.1), ("volumetric_end", 120.0),
                      ("volumetric_tile_size", '4'), ("volumetric_samples", 128),
                      ("use_volumetric_shadows", True)):
        try:
            setattr(ee, attr, val)
        except Exception:
            pass

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.0
sun_data.color = (1.0, 0.92, 0.8)
sun_data.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(60), 0, math.radians(160))
col.objects.link(sun)

fill_data = bpy.data.lights.new("Fill", 'AREA')
fill_data.energy = 800
fill_data.size = 20
fill_data.color = (0.7, 0.8, 1.0)
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = (0, 10, 25)
col.objects.link(fill)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 28
cam_data.clip_end = 300
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -18, 2.2)
col.objects.link(cam)
target = Vector((0, 20, 3.5))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
