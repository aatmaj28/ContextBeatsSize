import bpy
import bmesh
import math
import random
import colorsys
from mathutils import Vector, Matrix

random.seed(7)

# ---------------------------------------------------------------------------
# Clear scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for light in list(bpy.data.lights):
    bpy.data.lights.remove(light)
for cam in list(bpy.data.cameras):
    bpy.data.cameras.remove(cam)

scene = bpy.context.scene
collection = scene.collection


def link(obj):
    collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def make_mat(name, rgb, roughness=0.8):
    # Materials always use nodes in Blender 5.x; the default tree is created here.
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


bark_mat = make_mat("Bark", (0.07, 0.05, 0.035), 0.95)

foliage_mats = []
for i in range(6):
    h = random.uniform(0.27, 0.40)
    s = random.uniform(0.45, 0.70)
    v = random.uniform(0.10, 0.28)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    foliage_mats.append(make_mat(f"Foliage_{i}", (r, g, b), 0.7))

ground_mat = make_mat("ForestFloor", (0.04, 0.05, 0.03), 1.0)

# ---------------------------------------------------------------------------
# Ground
# ---------------------------------------------------------------------------
gbm = bmesh.new()
half = 90.0
gverts = [
    gbm.verts.new((-half, -half + 40, 0.0)),
    gbm.verts.new((half, -half + 40, 0.0)),
    gbm.verts.new((half, half + 40, 0.0)),
    gbm.verts.new((-half, half + 40, 0.0)),
]
gbm.faces.new(gverts)
gmesh = bpy.data.meshes.new("GroundMesh")
gbm.to_mesh(gmesh)
gbm.free()
gmesh.materials.append(ground_mat)
ground = link(bpy.data.objects.new("Ground", gmesh))


# ---------------------------------------------------------------------------
# Cone-shaped trees
# ---------------------------------------------------------------------------
def build_tree(name, height, base_radius, foliage_mat):
    bm = bmesh.new()
    trunk_h = height * 0.3

    # Trunk (cone frustum, acts as a cylinder)
    res = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=6,
        radius1=0.16, radius2=0.09, depth=trunk_h,
    )
    bmesh.ops.translate(bm, vec=(0, 0, trunk_h / 2), verts=res["verts"])
    trunk_face_count = len(bm.faces)

    # Stacked foliage cones
    tiers = 4
    depth = height * 0.36
    for i in range(tiers):
        base_z = trunk_h * 0.7 + i * height * 0.16
        center_z = base_z + depth / 2
        rad = base_radius * (1.0 - 0.2 * i) * random.uniform(0.9, 1.1)
        res = bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=False,
            segments=random.choice([7, 8, 9]),
            radius1=max(rad, 0.2), radius2=0.0, depth=depth,
        )
        bmesh.ops.translate(bm, vec=(0, 0, center_z), verts=res["verts"])

    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(bark_mat)
    mesh.materials.append(foliage_mat)
    for p in mesh.polygons:
        p.material_index = 0 if p.index < trunk_face_count else 1
        p.use_smooth = True

    obj = bpy.data.objects.new(name, mesh)
    link(obj)
    return obj


# Place trees with minimum spacing
positions = []
attempts = 0
while len(positions) < 85 and attempts < 8000:
    attempts += 1
    x = random.uniform(-34, 34)
    y = random.uniform(3, 55)
    if all((Vector((x, y)) - Vector(p)).length > 3.2 for p in positions):
        positions.append((x, y))

for idx, (x, y) in enumerate(positions):
    height = random.uniform(6.0, 13.0)
    base_r = random.uniform(1.4, 2.6) * (height / 9.0)
    mat = random.choice(foliage_mats)
    tree = build_tree(f"Tree_{idx:03d}", height, base_r, mat)
    tree.location = (x, y, 0.0)
    tree.rotation_euler = (
        random.uniform(-0.04, 0.04),
        random.uniform(-0.04, 0.04),
        random.uniform(0, math.tau),
    )
    s = random.uniform(0.85, 1.15)
    tree.scale = (s, s, random.uniform(0.9, 1.1))


# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
# Dim cold moonlight
moon_data = bpy.data.lights.new("Moonlight", type='SUN')
moon_data.energy = 2.0
moon_data.color = (0.6, 0.72, 1.0)
moon_data.angle = math.radians(4)
moon = link(bpy.data.objects.new("Moonlight", moon_data))
moon.rotation_euler = (math.radians(58), 0.0, math.radians(-35))

# Warm glowing lanterns scattered among the trees (visible through the fog)
for i in range(7):
    pl_data = bpy.data.lights.new(f"Lantern_{i}", type='POINT')
    pl_data.energy = random.uniform(250, 500)
    pl_data.color = (1.0, 0.65, 0.35)
    pl_data.shadow_soft_size = 0.5
    pl = link(bpy.data.objects.new(f"Lantern_{i}", pl_data))
    pl.location = (random.uniform(-14, 14), random.uniform(6, 34), random.uniform(1.8, 3.8))


# ---------------------------------------------------------------------------
# World: dim ambient background + volumetric fog
# ---------------------------------------------------------------------------
world = scene.world
if world is None:
    world = bpy.data.worlds.new("ForestWorld")
    scene.world = world

wtree = world.node_tree
wnodes = wtree.nodes
wlinks = wtree.links

out_node = wnodes.get("World Output")
if out_node is None:
    out_node = wnodes.new("ShaderNodeOutputWorld")
bg_node = wnodes.get("Background")
if bg_node is None:
    bg_node = wnodes.new("ShaderNodeBackground")

bg_node.inputs["Color"].default_value = (0.20, 0.26, 0.32, 1.0)
bg_node.inputs["Strength"].default_value = 0.25

# Noise drives density so the fog is patchy rather than uniform
noise = wnodes.new("ShaderNodeTexNoise")
noise.location = (-600, -200)
noise.inputs["Scale"].default_value = 0.12
noise.inputs["Detail"].default_value = 5.0
noise.inputs["Roughness"].default_value = 0.6

map_range = wnodes.new("ShaderNodeMapRange")
map_range.location = (-350, -200)
map_range.inputs["From Min"].default_value = 0.0
map_range.inputs["From Max"].default_value = 1.0
map_range.inputs["To Min"].default_value = 0.012
map_range.inputs["To Max"].default_value = 0.055

scatter = wnodes.new("ShaderNodeVolumeScatter")
scatter.location = (-100, -200)
scatter.inputs["Color"].default_value = (0.66, 0.74, 0.80, 1.0)
scatter.inputs["Anisotropy"].default_value = 0.35

wlinks.new(noise.outputs["Fac"], map_range.inputs["Value"])
wlinks.new(map_range.outputs["Result"], scatter.inputs["Density"])
wlinks.new(scatter.outputs["Volume"], out_node.inputs["Volume"])


# ---------------------------------------------------------------------------
# Render engine (Cycles handles world volumes well); no rendering performed
# ---------------------------------------------------------------------------
scene.render.engine = 'CYCLES'
try:
    scene.cycles.samples = 128
    scene.cycles.volume_step_rate = 0.5
except Exception:
    pass


# ---------------------------------------------------------------------------
# Camera framing the forest
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("ForestCamera")
cam_data.lens = 35
cam_data.clip_end = 300
cam = link(bpy.data.objects.new("ForestCamera", cam_data))

cam_loc = Vector((1.5, -24.0, 3.2))
target = Vector((0.0, 14.0, 4.5))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam

# Still scene
scene.frame_start = 1
scene.frame_end = 1
