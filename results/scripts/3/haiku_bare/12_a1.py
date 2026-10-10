import bpy
import bmesh
import math
import random
from mathutils import Matrix, Vector

random.seed(7)

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene
collection = scene.collection

def link(obj):
    collection.objects.link(obj)
    return obj

# ---------- Materials ----------
def make_brick_material():
    mat = bpy.data.materials.new("DarkBrick")
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 25.0
    noise.inputs["Detail"].default_value = 8.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.05, 0.02, 0.02, 1.0)
    ramp.color_ramp.elements[1].color = (0.16, 0.06, 0.05, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.9
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_emission_material(name, color, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emis = nodes.new("ShaderNodeEmission")
    emis.inputs["Color"].default_value = color
    emis.inputs["Strength"].default_value = strength
    links.new(emis.outputs["Emission"], out.inputs["Surface"])
    return mat

brick_mat = make_brick_material()
pink_mat = make_emission_material("PinkNeon", (1.0, 0.15, 0.55, 1.0), 25.0)

# ---------- Brick wall (single bmesh) ----------
wall_w, wall_h = 12.0, 6.0
brick_w, brick_h = 0.5, 0.25
bm = bmesh.new()
rows = int(wall_h / brick_h)
cols = int(wall_w / brick_w) + 2
for r in range(rows):
    z = r * brick_h + brick_h * 0.5
    offset = 0.25 if r % 2 else 0.0
    for c in range(cols):
        x = -wall_w * 0.5 - brick_w + c * brick_w + offset
        sx = brick_w * random.uniform(0.94, 0.98)
        sz = brick_h * random.uniform(0.90, 0.96)
        sy = random.uniform(0.35, 0.45)
        jx = random.uniform(-0.01, 0.01)
        mtx = Matrix.Translation((x + brick_w * 0.5 + jx, 0.0, z)) @ Matrix.Diagonal((sx, sy, sz, 1.0))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mtx)

wall_mesh = bpy.data.meshes.new("BrickWallMesh")
bm.to_mesh(wall_mesh)
bm.free()
wall_mesh.materials.append(brick_mat)
wall_obj = link(bpy.data.objects.new("BrickWall", wall_mesh))
wall_obj.location = (0.0, 0.0, 0.0)
for p in wall_obj.data.polygons:
    p.use_smooth = False

# Dark mortar backing plane
mortar_mat = bpy.data.materials.new("Mortar")
mortar_mat.use_nodes = True
mortar_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1.0)
mortar_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
bpy.ops.mesh.primitive_plane_add(size=1.0)
mortar = bpy.context.active_object
mortar.name = "MortarBacking"
mortar.scale = (wall_w * 0.5, 1.0, wall_h * 0.5)
mortar.rotation_euler = (math.pi / 2, 0, 0)
mortar.location = (0.0, 0.25, wall_h * 0.5)
mortar.data.materials.append(mortar_mat)
for coll in mortar.users_collection:
    coll.objects.unlink(mortar)
collection.objects.link(mortar)

# ---------- Neon "OPEN" sign ----------
curve = bpy.data.curves.new("OpenText", "FONT")
curve.body = "OPEN"
curve.size = 1.8
curve.extrude = 0.02
curve.bevel_depth = 0.02
curve.bevel_resolution = 3
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.materials.append(pink_mat)
sign = link(bpy.data.objects.new("OpenSign", curve))
sign.location = (0.0, -0.35, 2.6)
sign.rotation_euler = (math.pi / 2, 0.0, 0.0)

# ---------- Lighting ----------
# Pink spill light from the neon
spill_data = bpy.data.lights.new("PinkSpill", "POINT")
spill_data.energy = 250.0
spill_data.color = (1.0, 0.2, 0.6)
spill_data.shadow_soft_size = 0.5
spill = link(bpy.data.objects.new("PinkSpill", spill_data))
spill.location = (0.0, -2.0, 2.6)

# Faint cool fill to keep the brick texture readable
fill_data = bpy.data.lights.new("FillArea", "AREA")
fill_data.energy = 40.0
fill_data.size = 6.0
fill_data.color = (0.8, 0.85, 1.0)
fill = link(bpy.data.objects.new("FillArea", fill_data))
fill.location = (-3.0, -5.0, 5.0)
fill.rotation_euler = (math.radians(60), 0.0, math.radians(-20))

# Near-black world
world = bpy.data.worlds.new("DarkWorld")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.005, 0.005, 0.008, 1.0)
scene.world = world

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("SignCamera")
cam_data.lens = 50.0
cam = link(bpy.data.objects.new("SignCamera", cam_data))
cam.location = (0.0, -8.0, 2.6)
cam.rotation_euler = (math.pi / 2, 0.0, 0.0)
scene.camera = cam

# ---------- Render settings ----------
try:
    scene.render.engine = 'CYCLES'
except Exception:
    pass
if hasattr(scene, "cycles"):
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.frame_start = 1
scene.frame_end = 1

# ---------- Compositor glow via Glare node ----------
tree = None
if hasattr(scene, "compositing_node_group"):
    tree = bpy.data.node_groups.new("OpenSignCompositor", "CompositorNodeTree")
    scene.compositing_node_group = tree
else:
    scene.use_nodes = True
    tree = scene.node_tree

if tree is not None:
    tree.nodes.clear()
    rlayers = tree.nodes.new("CompositorNodeRLayers")
    glare = tree.nodes.new("CompositorNodeGlare")
    glare.glare_type = 'FOG_GLOW'
    glare.quality = 'HIGH'
    glare.threshold = 0.6
    glare.size = 8
    glare.mix = 0.0
    comp = tree.nodes.new("CompositorNodeComposite")
    tree.links.new(rlayers.outputs["Image"], glare.inputs["Image"])
    tree.links.new(glare.outputs["Image"], comp.inputs["Image"])
