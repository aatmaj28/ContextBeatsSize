import bpy
import bmesh
import math
import random
import mathutils

random.seed(7)

scene = bpy.context.scene
master_collection = scene.collection

# ---------------------------------------------------------------------------
# Clear default scene contents
# ---------------------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh)
for light in list(bpy.data.lights):
    bpy.data.lights.remove(light)
for cam in list(bpy.data.cameras):
    bpy.data.cameras.remove(cam)

# ---------------------------------------------------------------------------
# Render settings (Cycles handles world volumes well)
# ---------------------------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.frame_start = 1
scene.frame_end = 1

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def link_to_scene(obj):
    master_collection.objects.link(obj)
    return obj

def make_material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

def make_object(name, bm, mat, location=(0, 0, 0), rot_z=0.0, scale=(1, 1, 1)):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    for poly in mesh.polygons:
        poly.use_smooth = False
    obj = bpy.data.objects.new(name, mesh)
    link_to_scene(obj)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, rot_z)
    obj.scale = scale
    return obj

# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
ground_mat = make_material("ForestFloor", (0.08, 0.10, 0.06), roughness=0.95)
trunk_mat = make_material("Bark", (0.16, 0.10, 0.06), roughness=0.9)
leaf_mats = [
    make_material("PineDark", (0.03, 0.12, 0.05), roughness=0.7),
    make_material("PineMid", (0.05, 0.17, 0.07), roughness=0.7),
    make_material("PineBlue", (0.04, 0.14, 0.12), roughness=0.7),
]

# ---------------------------------------------------------------------------
# Ground
# ---------------------------------------------------------------------------
ground_mesh = bpy.data.meshes.new("Ground")
ground_bm = bmesh.new()
half = 80.0
verts = [
    ground_bm.verts.new((-half, 30.0 - half, 0.0)),
    ground_bm.verts.new((half, 30.0 - half, 0.0)),
    ground_bm.verts.new((half, 30.0 + half, 0.0)),
    ground_bm.verts.new((-half, 30.0 + half, 0.0)),
]
ground_bm.faces.new(verts)
ground_bm.to_mesh(ground_mesh)
ground_bm.free()
ground_mesh.materials.append(ground_mat)
ground = bpy.data.objects.new("Ground", ground_mesh)
link_to_scene(ground)

# ---------------------------------------------------------------------------
# Trees: stacked cones on a cylinder trunk
# ---------------------------------------------------------------------------
def build_tree(x, y, height, base_radius):
    trunk_h = height * 0.25
    # Trunk
    bm_t = bmesh.new()
    bmesh.ops.create_cone(
        bm_t,
        cap_ends=True,
        cap_tris=False,
        segments=6,
        radius1=0.12 * base_radius / 1.5,
        radius2=0.12 * base_radius / 1.5,
        depth=trunk_h,
        matrix=mathutils.Matrix.Translation((0, 0, trunk_h / 2.0)),
    )
    make_object(f"Trunk_{x:.1f}_{y:.1f}", bm_t, trunk_mat,
                location=(x, y, 0.0), rot_z=random.uniform(0, math.tau))

    # Foliage tiers (cones stacked upward, shrinking)
    leaf_mat = random.choice(leaf_mats)
    tiers = 3
    for i in range(tiers):
        frac = i / tiers
        tier_h = height * (0.55 - 0.1 * frac)
        tier_r = base_radius * (1.0 - 0.28 * frac)
        base_z = trunk_h * 0.6 + frac * height * 0.45
        bm_f = bmesh.new()
        bmesh.ops.create_cone(
            bm_f,
            cap_ends=True,
            cap_tris=False,
            segments=9,
            radius1=tier_r,
            radius2=0.0,
            depth=tier_h,
            matrix=mathutils.Matrix.Translation((0, 0, base_z + tier_h / 2.0)),
        )
        make_object(f"Foliage_{x:.1f}_{y:.1f}_{i}", bm_f, leaf_mat,
                    location=(x, y, 0.0), rot_z=random.uniform(0, math.tau))

# Scatter trees, keeping a clearing in front of the camera
placed = 0
attempts = 0
while placed < 110 and attempts < 2000:
    attempts += 1
    x = random.uniform(-26, 26)
    y = random.uniform(-4, 48)
    # Keep a small clearing near the camera
    if abs(x) < 3.5 and y < 6:
        continue
    height = random.uniform(7.0, 16.0)
    base_radius = random.uniform(1.4, 2.8) * (height / 11.0)
    build_tree(x, y, height, base_radius)
    placed += 1

# ---------------------------------------------------------------------------
# Lighting: dim key sun + soft fill
# ---------------------------------------------------------------------------
sun_data = bpy.data.lights.new(name="MoonSun", type='SUN')
sun_data.energy = 2.5
sun_data.angle = math.radians(4.0)
sun_data.color = (0.75, 0.85, 1.0)
sun_obj = bpy.data.objects.new("MoonSun", sun_data)
link_to_scene(sun_obj)
sun_obj.rotation_euler = (math.radians(55), math.radians(-10), math.radians(35))

fill_data = bpy.data.lights.new(name="FillArea", type='AREA')
fill_data.energy = 300.0
fill_data.size = 20.0
fill_data.color = (0.6, 0.75, 1.0)
fill_obj = bpy.data.objects.new("FillArea", fill_data)
link_to_scene(fill_obj)
fill_obj.location = (0.0, -15.0, 22.0)
fill_obj.rotation_euler = (math.radians(70), 0.0, 0.0)

# ---------------------------------------------------------------------------
# World: dark sky background + volumetric fog (Volume Scatter)
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("ForestFogWorld")
scene.world = world
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links

bg = wnodes.get("Background")
bg.inputs["Color"].default_value = (0.02, 0.03, 0.05, 1.0)
bg.inputs["Strength"].default_value = 0.2

world_output = next(n for n in wnodes if n.type == 'OUTPUT_WORLD')

fog = wnodes.new("ShaderNodeVolumeScatter")
fog.location = (-300, -200)
fog.inputs["Color"].default_value = (0.62, 0.72, 0.80, 1.0)
fog.inputs["Density"].default_value = 0.035
fog.inputs["Anisotropy"].default_value = 0.35
wlinks.new(fog.outputs["Volume"], world_output.inputs["Volume"])

# ---------------------------------------------------------------------------
# Camera framing the forest
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("ForestCamera")
cam_data.lens = 35.0
cam_data.clip_end = 300.0
cam_obj = bpy.data.objects.new("ForestCamera", cam_data)
link_to_scene(cam_obj)

cam_loc = mathutils.Vector((0.0, -22.0, 4.5))
target = mathutils.Vector((0.0, 14.0, 5.0))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj
