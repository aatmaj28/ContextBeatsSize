import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene

# ---------- Clean up default scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ---------- World: near-black ----------
world = bpy.data.worlds.new("DarkWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.005, 0.008, 1.0)
    bg.inputs["Strength"].default_value = 0.2
scene.world = world

# ---------- Brick wall materials ----------
brick_mat = bpy.data.materials.new("DarkBrick")
brick_mat.use_nodes = True
bsdf = brick_mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.12, 0.045, 0.035, 1.0)
bsdf.inputs["Roughness"].default_value = 0.92

mortar_mat = bpy.data.materials.new("Mortar")
mortar_mat.use_nodes = True
msdf = mortar_mat.node_tree.nodes.get("Principled BSDF")
msdf.inputs["Base Color"].default_value = (0.06, 0.06, 0.06, 1.0)
msdf.inputs["Roughness"].default_value = 1.0

# ---------- Build brick wall as one mesh ----------
bw, bh, bd = 0.62, 0.26, 0.22   # brick width, height, depth
gap = 0.03                       # mortar gap
x_min, x_max = -6.0, 6.0
z_min, z_max = -3.0, 3.5

wall_mesh = bpy.data.meshes.new("BrickWallMesh")
wall_obj = bpy.data.objects.new("BrickWall", wall_mesh)
scene.collection.objects.link(wall_obj)
bm = bmesh.new()

row = 0
z = z_min
while z < z_max:
    offset = (bw / 2) if row % 2 else 0.0
    x = x_min - bw + offset
    while x < x_max:
        jitter = random.uniform(-0.012, 0.012)
        sx = bw - gap
        sz = bh - gap
        # Brick center in world space; front face at y = 0, extends to +y (back)
        cx = x + bw / 2
        cz = z + bh / 2
        cy = bd / 2
        res = bmesh.ops.create_cube(bm, size=1.0)
        verts = res["verts"]
        for v in verts:
            v.co.x = v.co.x * sx + cx + jitter
            v.co.y = v.co.y * bd + cy
            v.co.z = v.co.z * sz + cz
        # Assign per-face material index (brick)
        for f in res["faces"]:
            f.material_index = 0
        x += bw
    z += bh
    row += 1

bm.normal_update()
bm.to_mesh(wall_mesh)
bm.free()
wall_mesh.materials.append(brick_mat)
for p in wall_mesh.polygons:
    p.use_smooth = False

# ---------- Neon sign: OPEN ----------
neon_mat = bpy.data.materials.new("PinkNeon")
neon_mat.use_nodes = True
nt = neon_mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
emit = nt.nodes.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (1.0, 0.12, 0.55, 1.0)
emit.inputs["Strength"].default_value = 25.0
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])

tube_mat = bpy.data.materials.new("SignTube")
tube_mat.use_nodes = True
tb = tube_mat.node_tree.nodes.get("Principled BSDF")
tb.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1.0)
tb.inputs["Roughness"].default_value = 0.4

font_curve = bpy.data.curves.new("OpenText", type='FONT')
font_curve.body = "OPEN"
font_curve.align_x = 'CENTER'
font_curve.align_y = 'CENTER'
font_curve.size = 1.0
font_curve.space_character = 1.15
font_curve.extrude = 0.02
font_curve.bevel_depth = 0.035
font_curve.bevel_resolution = 4
font_curve.resolution_u = 6

sign_obj = bpy.data.objects.new("NeonOpen", font_curve)
scene.collection.objects.link(sign_obj)
font_curve.materials.append(neon_mat)
font_curve.materials.append(tube_mat)
# Lie the text in the XZ plane, facing -Y (toward camera)
sign_obj.rotation_euler = (math.radians(90), 0.0, 0.0)
sign_obj.location = (0.0, -0.22, 0.6)
sign_obj.scale = (1.6, 1.6, 1.6)

# Backing frame / mounting plate behind the neon for contrast
plate_mesh = bpy.data.meshes.new("SignPlateMesh")
plate_obj = bpy.data.objects.new("SignPlate", plate_mesh)
scene.collection.objects.link(plate_obj)
pbm = bmesh.new()
bmesh.ops.create_cube(pbm, size=1.0)
for v in pbm.verts:
    v.co.x *= 3.4
    v.co.y *= 0.05
    v.co.z *= 1.5
pbm.to_mesh(plate_mesh)
pbm.free()
plate_mesh.materials.append(mortar_mat)
plate_obj.location = (0.0, -0.1, 0.6)

# ---------- Lighting ----------
# Pink spill light in front of the wall
pink_light_data = bpy.data.lights.new("PinkSpill", type='POINT')
pink_light_data.energy = 60.0
pink_light_data.color = (1.0, 0.2, 0.6)
pink_light_data.shadow_soft_size = 0.5
pink_light = bpy.data.objects.new("PinkSpill", pink_light_data)
scene.collection.objects.link(pink_light)
pink_light.location = (0.0, -1.6, 0.6)

# Faint cool fill from above-left to keep bricks readable
fill_data = bpy.data.lights.new("Fill", type='AREA')
fill_data.energy = 8.0
fill_data.size = 4.0
fill = bpy.data.objects.new("Fill", fill_data)
scene.collection.objects.link(fill)
fill.location = (-3.0, -4.0, 3.0)
fill.rotation_euler = (math.radians(60), 0.0, math.radians(-30))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.0, -6.0, 0.6)
target = Vector((0.0, 0.0, 0.6))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Compositor: Glare glow ----------
if hasattr(scene, "compositing_node_group"):
    comp_tree = bpy.data.node_groups.new("NeonCompositor", "CompositorNodeTree")
    scene.compositing_node_group = comp_tree
else:
    scene.use_nodes = True
    comp_tree = scene.node_tree

for n in list(comp_tree.nodes):
    comp_tree.nodes.remove(n)

rlayers = comp_tree.nodes.new("CompositorNodeRLayers")
glare = comp_tree.nodes.new("CompositorNodeGlare")
composite = comp_tree.nodes.new("CompositorNodeComposite")

try:
    glare.glare_type = 'BLOOM'
except Exception:
    pass
try:
    glare.quality = 'HIGH'
except Exception:
    pass
try:
    glare.threshold = 0.6
    glare.size = 8
    glare.mix = 0.0
except Exception:
    pass

rlayers.location = (-400, 0)
glare.location = (-100, 0)
composite.location = (200, 0)

img_out = rlayers.outputs.get("Image")
if img_out is not None:
    comp_tree.links.new(img_out, glare.inputs["Image"])
comp_tree.links.new(glare.outputs["Image"], composite.inputs["Image"])

# ---------- Frame range (single still) ----------
scene.frame_start = 1
scene.frame_end = 1
