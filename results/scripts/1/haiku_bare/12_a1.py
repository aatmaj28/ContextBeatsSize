import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix

random.seed(7)

# ---------- Clear scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
              bpy.data.lights, bpy.data.cameras, bpy.data.node_groups):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene

# Render engine (Cycles is available in background mode)
try:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
except Exception:
    pass

# ---------- Brick wall ----------
WALL_W = 9.0
WALL_H = 4.0
BRICK_L = 0.5
BRICK_H = 0.2
BRICK_D = 0.22
MORTAR = 0.02

bm = bmesh.new()
rows = int(WALL_H / BRICK_H)
for r in range(rows):
    z = r * BRICK_H + BRICK_H * 0.5
    offset = (BRICK_L * 0.5) if (r % 2) else 0.0
    x = -WALL_W * 0.5 - BRICK_L
    while x < WALL_W * 0.5 + BRICK_L:
        cx = x + BRICK_L * 0.5 + offset * 0  # offset applied via x start
        cx = x + BRICK_L * 0.5
        # keep bricks inside the wall slab bounds
        if cx + BRICK_L * 0.5 > -WALL_W * 0.5 and cx - BRICK_L * 0.5 < WALL_W * 0.5:
            sx = BRICK_L - MORTAR
            sz = BRICK_H - MORTAR
            sy = BRICK_D
            # brick depth from y=0 to y=BRICK_D (wall faces -Y)
            M = Matrix.Translation(Vector((cx, BRICK_D * 0.5, z))) @ \
                Matrix.Diagonal(Vector((sx, sy, sz, 1.0)))
            res = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.transform(bm, matrix=M, verts=res['verts'])
        x += BRICK_L

wall_mesh = bpy.data.meshes.new("BrickWallMesh")
bm.to_mesh(wall_mesh)
bm.free()
wall_mesh.update()
wall_obj = bpy.data.objects.new("BrickWall", wall_mesh)
scene.collection.objects.link(wall_obj)
wall_obj.location = (0.0, 0.0, 0.0)

# Dark brick material
brick_mat = bpy.data.materials.new("DarkBrick")
brick_mat.use_nodes = True
nt = brick_mat.node_tree
nodes = nt.nodes
links = nt.links
nodes.clear()

out = nodes.new("ShaderNodeOutputMaterial")
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
texcoord = nodes.new("ShaderNodeTexCoord")
brick_tex = nodes.new("ShaderNodeTexBrick")
noise = nodes.new("ShaderNodeTexNoise")
bump = nodes.new("ShaderNodeBump")

brick_tex.inputs["Color1"].default_value = (0.09, 0.035, 0.03, 1.0)
brick_tex.inputs["Color2"].default_value = (0.065, 0.025, 0.022, 1.0)
brick_tex.inputs["Mortar"].default_value = (0.03, 0.03, 0.03, 1.0)
brick_tex.inputs["Scale"].default_value = 1.0
brick_tex.inputs["Mortar Size"].default_value = 0.02
brick_tex.inputs["Mortar Smooth"].default_value = 0.1
brick_tex.inputs["Brick Width"].default_value = 0.5
brick_tex.inputs["Row Height"].default_value = 0.25
noise.inputs["Scale"].default_value = 60.0
noise.inputs["Detail"].default_value = 8.0
bump.inputs["Strength"].default_value = 0.15
bsdf.inputs["Roughness"].default_value = 0.85

links.new(texcoord.outputs["Generated"], brick_tex.inputs["Vector"])
links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
links.new(noise.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
links.new(brick_tex.outputs["Color"], bsdf.inputs["Base Color"])
links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

wall_obj.data.materials.append(brick_mat)

# ---------- Neon "OPEN" sign ----------
NEON_PINK = (1.0, 0.12, 0.55, 1.0)

neon_mat = bpy.data.materials.new("NeonPink")
neon_mat.use_nodes = True
nt2 = neon_mat.node_tree
nt2.nodes.clear()
n_out = nt2.nodes.new("ShaderNodeOutputMaterial")
n_em = nt2.nodes.new("ShaderNodeEmission")
n_em.inputs["Color"].default_value = NEON_PINK
n_em.inputs["Strength"].default_value = 25.0
nt2.links.new(n_em.outputs["Emission"], n_out.inputs["Surface"])

tcurve = bpy.data.curves.new("OPENText", type='FONT')
tcurve.body = "OPEN"
tcurve.align_x = 'CENTER'
tcurve.align_y = 'CENTER'
tcurve.size = 1.0
tcurve.extrude = 0.03
tcurve.bevel_depth = 0.01
tcurve.bevel_resolution = 3
tcurve.space_character = 1.05

sign_obj = bpy.data.objects.new("NeonOpenSign", tcurve)
scene.collection.objects.link(sign_obj)
sign_obj.data.materials.append(neon_mat)

# Scale so the word is a comfortable width
bpy.context.view_layer.update()
dims = sign_obj.dimensions
if dims.x > 0:
    k = 3.4 / dims.x
    sign_obj.scale = (k, k, k)

SIGN_CENTER = Vector((0.0, -0.32, 1.9))
sign_obj.location = SIGN_CENTER
sign_obj.rotation_euler = (math.radians(90), 0.0, 0.0)
# Text lies in XY by default; rotate so it faces -Y (toward the camera)
sign_obj.rotation_euler = (math.radians(90), 0.0, math.radians(180))

# Thin mounting backplate (dark metal) behind the letters
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(SIGN_CENTER.x, -0.2, SIGN_CENTER.z))
back = bpy.context.active_object
back.name = "SignBackplate"
back.scale = (2.2, 0.03, 1.1)
bp_mat = bpy.data.materials.new("Backplate")
bp_mat.use_nodes = True
bp_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1.0)
bp_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.4
back.data.materials.append(bp_mat)
back.hide_render = True  # keep it only as a light blocker/visual guide
back.hide_render = False

# ---------- Lighting ----------
world = bpy.data.worlds.new("DarkWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.005, 0.008, 1.0)
    bg.inputs["Strength"].default_value = 0.2
scene.world = world

# Pink point light casting colored spill onto the brick
pl_data = bpy.data.lights.new("PinkSpill", type='POINT')
pl_data.energy = 250.0
pl_data.color = (1.0, 0.25, 0.6)
pl_data.shadow_soft_size = 0.5
pl_obj = bpy.data.objects.new("PinkSpill", pl_data)
scene.collection.objects.link(pl_obj)
pl_obj.location = (SIGN_CENTER.x, -1.2, SIGN_CENTER.z)

# Soft fill to reveal brick texture subtly
area_data = bpy.data.lights.new("KeyFill", type='AREA')
area_data.energy = 40.0
area_data.color = (1.0, 0.9, 0.9)
area_data.size = 4.0
area_obj = bpy.data.objects.new("KeyFill", area_data)
scene.collection.objects.link(area_obj)
area_obj.location = (-3.0, -4.0, 3.5)
area_obj.rotation_euler = (math.radians(55), 0.0, math.radians(-30))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("SignCamera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("SignCamera", cam_data)
scene.collection.objects.link(cam_obj)
cam_pos = Vector((0.0, -7.2, SIGN_CENTER.z + 0.1))
cam_obj.location = cam_pos
direction = (SIGN_CENTER - cam_pos).normalized()
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- Compositor: Glare glow ----------
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

try:
    scene.use_nodes = True
except Exception:
    pass

ctree = None
if hasattr(scene, "compositing_node_group"):
    if scene.compositing_node_group is None:
        scene.compositing_node_group = bpy.data.node_groups.new(
            "NeonCompositor", "CompositorNodeTree")
    ctree = scene.compositing_node_group
else:
    ctree = scene.node_tree

if ctree is not None:
    ctree.nodes.clear()
    rl = ctree.nodes.new("CompositorNodeRLayers")
    try:
        rl.scene = scene
    except Exception:
        pass

    glare = ctree.nodes.new("CompositorNodeGlare")
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
        glare.mix = 0.25
        glare.size = 8
    except Exception:
        pass

    comp = ctree.nodes.new("CompositorNodeComposite")

    img_out = rl.outputs.get("Image")
    if img_out is not None:
        ctree.links.new(img_out, glare.inputs["Image"])
        ctree.links.new(glare.outputs["Image"], comp.inputs["Image"])
