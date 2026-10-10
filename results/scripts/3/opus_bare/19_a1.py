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
    try:
        mat.use_nodes = True
    except Exception:
        pass
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
    mat.diffuse_color = (*color, 1.0)
    return mat

ground_mat = make_mat("Ground", (0.09, 0.07, 0.04), 0.95)
trunk_mat = make_mat("Trunk", (0.12, 0.07, 0.04), 0.9)
leaf_mats = [
    make_mat("Foliage_A", (0.03, 0.12, 0.05)),
    make_mat("Foliage_B", (0.04, 0.16, 0.06)),
    make_mat("Foliage_C", (0.02, 0.10, 0.06)),
]

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(ground_mat)

# ---------- Base meshes ----------
bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=1.0, radius2=0.0, depth=2.0, location=(0, 0, -50))
cone_proto = bpy.context.active_object
cone_mesh = cone_proto.data
bpy.ops.object.shade_smooth()
bpy.data.objects.remove(cone_proto, do_unlink=True)

bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=1.0, depth=2.0, location=(0, 0, -50))
cyl_proto = bpy.context.active_object
cyl_mesh = cyl_proto.data
cyl_mesh.materials.append(trunk_mat)
bpy.data.objects.remove(cyl_proto, do_unlink=True)

cone_meshes = []
for m in leaf_mats:
    cm = cone_mesh.copy()
    cm.materials.append(m)
    cone_meshes.append(cm)

forest = bpy.data.collections.new("Forest")
scene.collection.children.link(forest)

def add_tree(x, y, scale):
    trunk_h = 1.2 * scale
    trunk = bpy.data.objects.new("Trunk", cyl_mesh)
    trunk.scale = (0.18 * scale, 0.18 * scale, trunk_h / 2)
    trunk.location = (x, y, trunk_h / 2)
    forest.objects.link(trunk)
    tiers = random.randint(2, 4)
    base = trunk_h * 0.7
    cm = random.choice(cone_meshes)
    for i in range(tiers):
        r = (1.6 - i * 0.35) * scale
        h = (2.6 - i * 0.4) * scale
        c = bpy.data.objects.new("Foliage", cm)
        c.scale = (r, r, h / 2)
        c.location = (x, y, base + h / 2)
        c.rotation_euler = (0, 0, random.uniform(0, math.tau))
        forest.objects.link(c)
        base += h * 0.5

# Scatter trees, leaving a path clear near the camera
placed = []
attempts = 0
while len(placed) < 140 and attempts < 4000:
    attempts += 1
    x = random.uniform(-35, 35)
    y = random.uniform(-15, 60)
    if abs(x) < 2.5 and y < 20:
        continue
    if any((x - px) ** 2 + (y - py) ** 2 < 6.0 for px, py in placed):
        continue
    placed.append((x, y))
    add_tree(x, y, random.uniform(0.8, 1.6))

# ---------- World with volumetric fog ----------
world = bpy.data.worlds.new("FoggyWorld")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
nt = world.node_tree
nodes = nt.nodes
links = nt.links
for n in list(nodes):
    nodes.remove(n)

out = nodes.new("ShaderNodeOutputWorld")
out.location = (400, 0)
bg = nodes.new("ShaderNodeBackground")
bg.location = (0, 150)
bg.inputs["Color"].default_value = (0.55, 0.6, 0.65, 1.0)
bg.inputs["Strength"].default_value = 0.6
vol = nodes.new("ShaderNodeVolumePrincipled")
vol.location = (0, -150)
vol.inputs["Color"].default_value = (0.8, 0.85, 0.9, 1.0)
vol.inputs["Density"].default_value = 0.04
vol.inputs["Anisotropy"].default_value = 0.3
links.new(bg.outputs["Background"], out.inputs["Surface"])
links.new(vol.outputs["Volume"], out.inputs["Volume"])

# ---------- Lighting ----------
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.0
sun_data.color = (1.0, 0.93, 0.8)
sun_data.angle = math.radians(2)
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(50), math.radians(-20), math.radians(160))
scene.collection.objects.link(sun)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam_data.clip_end = 300
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -12, 2.2)
target = Vector((0, 20, 3.5))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(cam)
scene.camera = cam

# ---------- Render settings ----------
try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        pass
try:
    scene.eevee.volumetric_end = 120.0
    scene.eevee.volumetric_tile_size = '4'
except Exception:
    pass
try:
    scene.cycles.volume_step_rate = 2.0
except Exception:
    pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
