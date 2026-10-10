import bpy
import bmesh
import math
from mathutils import Vector

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
              bpy.data.lights, bpy.data.cameras, bpy.data.node_groups):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.view_settings.view_transform = 'Standard'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# ---------- World (near-black) ----------
world = bpy.data.worlds.new("DarkWorld")
scene.world = world
wbg = world.node_tree.nodes.get("Background")
if wbg:
    wbg.inputs["Color"].default_value = (0.005, 0.005, 0.008, 1.0)
    wbg.inputs["Strength"].default_value = 1.0

# ---------- Brick wall ----------
def make_plane(name, size_x, size_z):
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm = bmesh.new()
    hx, hz = size_x / 2, size_z / 2
    v = [bm.verts.new((-hx, 0, -hz)), bm.verts.new((hx, 0, -hz)),
         bm.verts.new((hx, 0, hz)), bm.verts.new((-hx, 0, hz))]
    bm.faces.new(v)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    return obj

wall = make_plane("BrickWall", 10.0, 6.0)
wall.location = (0, 0, 2.5)
wall.rotation_euler = (math.radians(90), 0, 0)

brick_mat = bpy.data.materials.new("DarkBrick")
brick_mat.use_nodes = True
bnt = brick_mat.node_tree
bnt.nodes.clear()
b_out = bnt.nodes.new("ShaderNodeOutputMaterial")
b_bsdf = bnt.nodes.new("ShaderNodeBsdfPrincipled")
b_tex = bnt.nodes.new("ShaderNodeTexBrick")
b_coord = bnt.nodes.new("ShaderNodeTexCoord")
b_out.location = (400, 0)
b_bsdf.location = (100, 0)
b_tex.location = (-250, 0)
b_coord.location = (-500, 0)

b_tex.inputs["Color1"].default_value = (0.09, 0.025, 0.02, 1.0)
b_tex.inputs["Color2"].default_value = (0.07, 0.02, 0.015, 1.0)
b_tex.inputs["Mortar"].default_value = (0.03, 0.03, 0.03, 1.0)
b_tex.inputs["Scale"].default_value = 4.0
b_tex.inputs["Mortar Size"].default_value = 0.015

bnt.links.new(b_coord.outputs["Generated"], b_tex.inputs["Vector"])
bnt.links.new(b_tex.outputs["Color"], b_bsdf.inputs["Base Color"])
bnt.links.new(b_bsdf.outputs["BSDF"], b_out.inputs["Surface"])
b_bsdf.inputs["Roughness"].default_value = 0.85
wall.data.materials.append(brick_mat)

# ---------- Neon "OPEN" text ----------
neon_mat = bpy.data.materials.new("PinkNeon")
neon_mat.use_nodes = True
nnt = neon_mat.node_tree
nnt.nodes.clear()
n_out = nnt.nodes.new("ShaderNodeOutputMaterial")
n_em = nnt.nodes.new("ShaderNodeEmission")
n_out.location = (300, 0)
n_em.location = (0, 0)
n_em.inputs["Color"].default_value = (1.0, 0.12, 0.65, 1.0)
n_em.inputs["Strength"].default_value = 40.0
nnt.links.new(n_em.outputs["Emission"], n_out.inputs["Surface"])

text_curve = bpy.data.curves.new("NeonOpenText", 'FONT')
text_curve.body = "OPEN"
text_curve.align_x = 'CENTER'
text_curve.align_y = 'CENTER'
text_curve.size = 1.0
text_curve.space_character = 1.05
text_curve.extrude = 0.0
text_curve.bevel_depth = 0.035      # tube thickness
text_curve.bevel_resolution = 6
text_curve.resolution_u = 4

neon_obj = bpy.data.objects.new("NeonOpen", text_curve)
scene.collection.objects.link(neon_obj)
neon_obj.rotation_euler = (math.radians(90), 0, 0)
neon_obj.location = (0, -0.12, 2.6)
neon_obj.data.materials.append(neon_mat)

# Small mounting bracket behind the sign for depth
bracket_mat = bpy.data.materials.new("Metal")
bracket_mat.use_nodes = True
mb = bracket_mat.node_tree.nodes.get("Principled BSDF")
if mb:
    mb.inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1.0)
    mb.inputs["Metallic"].default_value = 1.0
    mb.inputs["Roughness"].default_value = 0.35

for i, x in enumerate((-1.9, 1.9)):
    m = bpy.data.meshes.new(f"Standoff{i}")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                          segments=12, radius1=0.04, radius2=0.04, depth=0.2)
    bm.to_mesh(m)
    bm.free()
    so = bpy.data.objects.new(f"Standoff{i}", m)
    scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(90), 0, 0)
    so.location = (x, -0.06, 2.6)
    so.data.materials.append(bracket_mat)

# ---------- Lighting ----------
# Faint cool fill so the brick reads, neon remains the dominant light
fill_data = bpy.data.lights.new("FillArea", 'AREA')
fill_data.energy = 60
fill_data.size = 4.0
fill_data.color = (0.8, 0.85, 1.0)
fill = bpy.data.objects.new("FillArea", fill_data)
scene.collection.objects.link(fill)
fill.location = (0, -4.0, 5.0)
fill.rotation_euler = (math.radians(20), 0, 0)

# Pink spill light from the sign onto the wall and surroundings
spill_data = bpy.data.lights.new("PinkSpill", 'POINT')
spill_data.energy = 300
spill_data.color = (1.0, 0.2, 0.7)
spill_data.shadow_soft_size = 0.5
spill = bpy.data.objects.new("PinkSpill", spill_data)
scene.collection.objects.link(spill)
spill.location = (0, -1.0, 2.6)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -7.0, 2.4)
target = Vector((0, 0, 2.5))
direction = target - Vector(cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Compositor: Glare glow ----------
comp_tree = bpy.data.node_groups.new("NeonGlowCompositor", "CompositorNodeTree")
scene.compositing_node_group = comp_tree

rlayers = comp_tree.nodes.new(type="CompositorNodeRLayers")
rlayers.location = (-400, 0)

glare = comp_tree.nodes.new(type="CompositorNodeGlare")
glare.location = (-100, 0)
# Glare options are input sockets in Blender 5.x
def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value

set_input(glare, "Type", "Bloom")
set_input(glare, "Quality", "High")
set_input(glare, "Threshold", 0.6)
set_input(glare, "Size", 8)
set_input(glare, "Mix", 0.0)

comp_out = comp_tree.nodes.new(type="NodeGroupOutput")
comp_out.location = (250, 0)
comp_tree.interface.new_socket(name="Image", in_out="OUTPUT",
                               socket_type="NodeSocketColor")

comp_tree.links.new(rlayers.outputs["Image"], glare.inputs["Image"])
comp_tree.links.new(glare.outputs["Image"], comp_out.inputs["Image"])
