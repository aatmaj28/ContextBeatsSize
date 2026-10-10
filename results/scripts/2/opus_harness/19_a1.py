import bpy
import math
import random
from mathutils import Vector

random.seed(42)
scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Materials ----------
def make_mat(name, color, rough=0.8):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return mat

foliage_mats = [
    make_mat("Foliage_A", (0.03, 0.12, 0.05)),
    make_mat("Foliage_B", (0.04, 0.16, 0.06)),
    make_mat("Foliage_C", (0.02, 0.09, 0.04)),
]
trunk_mat = make_mat("Trunk", (0.12, 0.07, 0.04), 0.9)
ground_mat = make_mat("Ground", (0.08, 0.10, 0.05), 1.0)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(ground_mat)

# ---------- Base meshes ----------
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=1.0, radius2=0.0, depth=1.0, location=(0, 0, 0))
cone_proto = bpy.context.active_object
cone_mesh = cone_proto.data
bpy.ops.object.shade_smooth()
bpy.data.objects.remove(cone_proto, do_unlink=True)

bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=1.0, depth=1.0, location=(0, 0, 0))
trunk_proto = bpy.context.active_object
trunk_mesh = trunk_proto.data
trunk_mesh.materials.append(trunk_mat)
bpy.data.objects.remove(trunk_proto, do_unlink=True)

cone_meshes = []
for i, m in enumerate(foliage_mats):
    cm = cone_mesh.copy()
    cm.materials.clear()
    cm.materials.append(m)
    cone_meshes.append(cm)

coll = bpy.data.collections.new("Forest")
scene.collection.children.link(coll)

def add_tree(x, y, h, r):
    trunk_h = h * 0.15
    t = bpy.data.objects.new("Trunk", trunk_mesh)
    t.location = (x, y, trunk_h / 2)
    t.scale = (r * 0.12, r * 0.12, trunk_h)
    coll.objects.link(t)
    mesh = random.choice(cone_meshes)
    tiers = random.choice([1, 2, 3])
    for k in range(tiers):
        f = 1.0 - k * 0.25
        th = (h - trunk_h) * (0.75 if tiers > 1 else 1.0) * f
        base = trunk_h + (h - trunk_h) * 0.28 * k
        c = bpy.data.objects.new("Cone", mesh)
        c.location = (x, y, base + th / 2)
        c.scale = (r * f, r * f, th)
        c.rotation_euler = (0, 0, random.uniform(0, math.pi))
        coll.objects.link(c)

placed = []
count = 0
attempts = 0
while count < 260 and attempts < 5000:
    attempts += 1
    x = random.uniform(-60, 60)
    y = random.uniform(-25, 90)
    # keep a clearing/path in front of camera
    if abs(x) < 2.5 + max(0, (y + 25)) * 0.05 and y < 40:
        continue
    if Vector((x, y)).length < 0 or (abs(x) < 4 and y < -18):
        continue
    r = random.uniform(1.2, 2.6)
    if any((Vector((x, y)) - p).length < (r + pr) * 0.8 for p, pr in placed):
        continue
    h = r * random.uniform(3.5, 5.0)
    add_tree(x, y, h, r)
    placed.append((Vector((x, y)), r))
    count += 1

# ---------- World with volumetric fog ----------
world = bpy.data.worlds.new("FoggyWorld")
scene.world = world
nt = world.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()
out = nodes.new("ShaderNodeOutputWorld")
out.location = (400, 0)
bg = nodes.new("ShaderNodeBackground")
bg.location = (100, 100)
bg.inputs["Color"].default_value = (0.55, 0.62, 0.68, 1.0)
bg.inputs["Strength"].default_value = 0.8
vol = nodes.new("ShaderNodeVolumePrincipled")
vol.location = (100, -150)
vol.inputs["Color"].default_value = (0.8, 0.85, 0.9, 1.0)
vol.inputs["Density"].default_value = 0.035
vol.inputs["Anisotropy"].default_value = 0.3
links.new(bg.outputs["Background"], out.inputs["Surface"])
links.new(vol.outputs["Volume"], out.inputs["Volume"])

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.5
sun_data.color = (1.0, 0.93, 0.8)
sun_data.angle = math.radians(2)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(55), 0, math.radians(150))
scene.collection.objects.link(sun)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 32
cam_data.clip_end = 500
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -28, 2.2)
direction = Vector((0, 20, 4.5)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(cam)
scene.camera = cam

# ---------- Render settings ----------
scene.render.engine = 'BLENDER_EEVEE'
try:
    scene.eevee.volumetric_end = 150
    scene.eevee.volumetric_tile_size = '4'
    scene.eevee.use_volumetric_shadows = True
except Exception:
    pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
