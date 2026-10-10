import bpy
import bmesh
import mathutils
import math
import random
import colorsys
from bpy_extras import object_utils  # noqa: F401 (allowed import, not required)

random.seed(42)

# ---------------------------------------------------------------------------
# Clean up the default scene
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

scene = bpy.context.scene
collection = scene.collection

# Try to use Cycles (volumes need a path tracer); fall back silently if unavailable
try:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
except Exception:
    pass

scene.frame_start = 1
scene.frame_end = 1

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def add_mesh_object(name, bm, material):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob


def cone_into(bm, radius1, radius2, depth, center, segments=9):
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        matrix=mathutils.Matrix.Translation(mathutils.Vector(center)),
        calc_uvs=False,
    )


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
bark_mat = make_material("Bark", (0.16, 0.10, 0.07), roughness=0.9)
ground_mat = make_material("Forest Floor", (0.05, 0.09, 0.05), roughness=1.0)

foliage_mats = []
for i, hue in enumerate([0.33, 0.36, 0.28]):
    r, g, b = colorsys.hsv_to_rgb(hue, 0.6, 0.22 + 0.05 * i)
    foliage_mats.append(make_material(f"Foliage_{i}", (r, g, b), roughness=0.7))

# ---------------------------------------------------------------------------
# Ground
# ---------------------------------------------------------------------------
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=50.0)
ground = add_mesh_object("Ground", bm, ground_mat)
ground.location = (0, 30, 0)

# ---------------------------------------------------------------------------
# Cone-shaped trees
# ---------------------------------------------------------------------------
TREE_COUNT = 140
placed = 0
attempts = 0
while placed < TREE_COUNT and attempts < TREE_COUNT * 10:
    attempts += 1
    x = random.uniform(-32.0, 32.0)
    y = random.uniform(4.0, 75.0)
    # keep a clearing right in front of the camera
    if abs(x) < 3.0 and y < 14.0:
        continue

    height = random.uniform(7.0, 13.0)
    base_r = random.uniform(1.4, 2.4)
    name = f"Tree_{placed:03d}"

    # Trunk
    trunk_bm = bmesh.new()
    trunk_h = height * 0.4
    cone_into(trunk_bm, 0.18, 0.12, trunk_h, (0, 0, trunk_h * 0.5), segments=6)
    trunk = add_mesh_object(name + "_Trunk", trunk_bm, bark_mat)
    trunk.location = (x, y, 0)

    # Foliage tiers (stacked cones)
    leaves_bm = bmesh.new()
    tiers = random.randint(3, 4)
    for t in range(tiers):
        frac = t / float(tiers)
        tier_h = height * (0.42 - 0.06 * frac)
        tier_r = base_r * (1.0 - 0.22 * frac)
        z_base = trunk_h * 0.6 + frac * height * 0.6
        cone_into(
            leaves_bm,
            tier_r,
            0.0,
            tier_h,
            (0, 0, z_base + tier_h * 0.5),
            segments=random.choice([8, 9, 10]),
        )
    leaves = add_mesh_object(
        name + "_Foliage", leaves_bm, random.choice(foliage_mats)
    )
    leaves.location = (x, y, 0)
    leaves.rotation_euler.z = random.uniform(0, math.tau)

    placed += 1

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
sun_data = bpy.data.lights.new(name="Dawn Sun", type='SUN')
sun_data.energy = 3.0
sun_data.color = (1.0, 0.85, 0.7)
sun_data.angle = math.radians(3.0)
sun = bpy.data.objects.new("Dawn Sun", sun_data)
collection.objects.link(sun)
sun.location = (0, 0, 20)
sun.rotation_euler = (math.radians(72), 0, math.radians(-25))

# Soft fill light deeper in the forest
fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 800.0
fill_data.color = (0.6, 0.75, 1.0)
fill_data.size = 20.0
fill = bpy.data.objects.new("Fill", fill_data)
collection.objects.link(fill)
fill.location = (0, -10, 14)
fill.rotation_euler = (math.radians(60), 0, 0)

# ---------------------------------------------------------------------------
# Volumetric fog in the World shader
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("Foggy Forest World")
scene.world = world
world.use_nodes = True
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links
wnodes.clear()

out = wnodes.new("ShaderNodeOutputWorld")
out.location = (400, 0)

bg = wnodes.new("ShaderNodeBackground")
bg.location = (0, 200)
bg.inputs["Color"].default_value = (0.55, 0.62, 0.66, 1.0)
bg.inputs["Strength"].default_value = 0.4

scatter = wnodes.new("ShaderNodeVolumeScatter")
scatter.location = (0, -150)
scatter.inputs["Color"].default_value = (0.75, 0.82, 0.85, 1.0)
scatter.inputs["Density"].default_value = 0.035
scatter.inputs["Anisotropy"].default_value = 0.35

wlinks.new(bg.outputs["Background"], out.inputs["Surface"])
wlinks.new(scatter.outputs["Volume"], out.inputs["Volume"])

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Forest Camera")
cam_data.lens = 35.0
cam_data.clip_end = 300.0
cam = bpy.data.objects.new("Forest Camera", cam_data)
collection.objects.link(cam)

cam_pos = mathutils.Vector((0.0, -5.0, 3.0))
target = mathutils.Vector((0.0, 22.0, 4.5))
cam.location = cam_pos
direction = (target - cam_pos).normalized()
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
