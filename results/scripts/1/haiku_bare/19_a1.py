import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

# ---------- Helpers ----------
def make_material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

def add_cone(bm, cx, cy, z0, radius, height, seg, mat_idx):
    ring = []
    for i in range(seg):
        a = 2.0 * math.pi * i / seg
        ring.append(bm.verts.new((cx + radius * math.cos(a),
                                  cy + radius * math.sin(a), z0)))
    apex = bm.verts.new((cx, cy, z0 + height))
    for i in range(seg):
        f = bm.faces.new((ring[i], ring[(i + 1) % seg], apex))
        f.material_index = mat_idx
    base = bm.faces.new(list(reversed(ring)))
    base.material_index = mat_idx

def add_trunk(bm, cx, cy, z0, z1, r, seg, mat_idx):
    bottom = []
    top = []
    for i in range(seg):
        a = 2.0 * math.pi * i / seg
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        bottom.append(bm.verts.new((x, y, z0)))
        top.append(bm.verts.new((x, y, z1)))
    for i in range(seg):
        j = (i + 1) % seg
        f = bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
        f.material_index = mat_idx

def build_tree_mesh(name, tiers, base_radius, tier_height, foliage_mat, trunk_mat, seg=9):
    bm = bmesh.new()
    trunk_h = 1.6
    add_trunk(bm, 0, 0, 0.0, trunk_h + 0.4, 0.22, 6, 1)
    for t in range(tiers):
        z0 = 1.0 + t * tier_height * 0.55
        radius = base_radius * (1.0 - t * 0.22)
        add_cone(bm, 0, 0, z0, radius, tier_height, seg, 0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(foliage_mat)
    me.materials.append(trunk_mat)
    me.update()
    return me

def link_object(obj):
    scene.collection.objects.link(obj)
    return obj

# ---------- Materials ----------
trunk_mat = make_material("Bark", (0.14, 0.09, 0.06), 0.9)
ground_mat = make_material("ForestFloor", (0.07, 0.09, 0.05), 1.0)
foliage_colors = [
    (0.05, 0.22, 0.10),
    (0.04, 0.17, 0.12),
    (0.08, 0.24, 0.08),
    (0.06, 0.15, 0.14),
]
foliage_mats = [make_material(f"Pine_{i}", c, 0.7) for i, c in enumerate(foliage_colors)]

# ---------- Tree variants ----------
variants = []
variant_params = [
    (3, 2.4, 2.8),
    (4, 2.0, 2.4),
    (3, 2.8, 3.2),
    (2, 1.9, 3.0),
]
for i, (tiers, rad, th) in enumerate(variant_params):
    me = build_tree_mesh(f"TreeMesh_{i}", tiers, rad, th, foliage_mats[i], trunk_mat)
    variants.append(me)

# ---------- Ground ----------
gbm = bmesh.new()
bmesh.ops.create_grid(gbm, x_segments=40, y_segments=40, size=60.0)
for v in gbm.verts:
    v.co.z = 0.35 * math.sin(v.co.x * 0.31) * math.cos(v.co.y * 0.27) \
             + random.uniform(-0.08, 0.08)
gbm.faces.ensure_lookup_table()
for f in gbm.faces:
    f.material_index = 0
gme = bpy.data.meshes.new("ForestFloorMesh")
gbm.to_mesh(gme)
gbm.free()
gme.materials.append(ground_mat)
ground = link_object(bpy.data.objects.new("ForestFloor", gme))

# ---------- Scatter trees ----------
cam_pos = Vector((0.0, -28.0, 3.5))
placed = 0
attempts = 0
while placed < 130 and attempts < 5000:
    attempts += 1
    x = random.uniform(-45, 45)
    y = random.uniform(-40, 45)
    # keep a clear lane in front of the camera
    if abs(x) < 4.5 and y < -6:
        continue
    if math.hypot(x, y - cam_pos.y) < 8:
        continue
    s = random.uniform(0.7, 1.6)
    obj = bpy.data.objects.new(f"Tree_{placed}", random.choice(variants))
    obj.location = (x, y, 0.0)
    obj.rotation_euler = (0.0, 0.0, random.uniform(0, 2 * math.pi))
    obj.scale = (s * random.uniform(0.9, 1.1), s * random.uniform(0.9, 1.1), s * random.uniform(0.95, 1.2))
    link_object(obj)
    placed += 1

# ---------- Lights ----------
sun_data = bpy.data.lights.new("MistSun", type='SUN')
sun_data.energy = 2.5
sun_data.color = (1.0, 0.92, 0.78)
sun_data.angle = math.radians(4.0)
sun = link_object(bpy.data.objects.new("MistSun", sun_data))
sun.rotation_euler = (math.radians(68), 0.0, math.radians(35))

spot_data = bpy.data.lights.new("ShaftSpot", type='SPOT')
spot_data.energy = 4000.0
spot_data.color = (0.8, 0.95, 1.0)
spot_data.spot_size = math.radians(45)
spot_data.spot_blend = 0.6
spot = link_object(bpy.data.objects.new("ShaftSpot", spot_data))
spot.location = (6.0, 8.0, 14.0)
spot.rotation_euler = (math.radians(0), 0.0, 0.0)
spot.rotation_euler = (Vector((0, 0, 0)) - spot.location).to_track_quat('-Z', 'Y').to_euler()

# ---------- Volumetric fog in world shader ----------
world = bpy.data.worlds.new("ForestWorld")
scene.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()

bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.05, 0.07, 0.08, 1.0)
bg.inputs["Strength"].default_value = 0.4

vol = nt.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.03
vol.inputs["Color"].default_value = (0.62, 0.72, 0.76, 1.0)
vol.inputs["Anisotropy"].default_value = 0.45

wout = nt.nodes.new("ShaderNodeOutputWorld")
wout.is_active_output = True

nt.links.new(bg.outputs["Background"], wout.inputs["Surface"])
nt.links.new(vol.outputs["Volume"], wout.inputs["Volume"])

# ---------- Render settings (no render performed) ----------
try:
    scene.render.engine = 'CYCLES'
    scene.cycles.volume_step_rate = 0.5
except Exception:
    pass

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("ForestCam")
cam_data.lens = 35.0
cam_data.clip_end = 300.0
cam = link_object(bpy.data.objects.new("ForestCam", cam_data))
cam.location = cam_pos
target = Vector((0.0, 6.0, 4.0))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Frame range ----------
scene.frame_start = 1
scene.frame_end = 1
