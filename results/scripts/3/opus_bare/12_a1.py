import bpy
import math

scene = bpy.context.scene

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Render settings ----------
try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# World: very dark
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.005, 0.005, 0.008, 1)
    bg.inputs[1].default_value = 1.0

# ---------- Brick wall material ----------
wall_mat = bpy.data.materials.new("DarkBrick")
wall_mat.use_nodes = True
nt = wall_mat.node_tree
nodes, links = nt.nodes, nt.links
bsdf = nodes.get("Principled BSDF")
texco = nodes.new("ShaderNodeTexCoord")
brick = nodes.new("ShaderNodeTexBrick")
brick.inputs["Color1"].default_value = (0.09, 0.03, 0.025, 1)
brick.inputs["Color2"].default_value = (0.05, 0.02, 0.018, 1)
brick.inputs["Mortar"].default_value = (0.02, 0.02, 0.02, 1)
brick.inputs["Scale"].default_value = 1.0
brick.inputs["Mortar Size"].default_value = 0.015
brick.inputs["Brick Width"].default_value = 0.4
brick.inputs["Row Height"].default_value = 0.15
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 30.0
mix = nodes.new("ShaderNodeMix")
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.inputs[0].default_value = 0.5
links.new(texco.outputs["Object"], brick.inputs["Vector"])
links.new(texco.outputs["Object"], noise.inputs["Vector"])
links.new(brick.outputs["Color"], mix.inputs[6])
links.new(noise.outputs["Color"], mix.inputs[7])
links.new(mix.outputs[2], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.9
bump = nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.6
links.new(brick.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
wall = bpy.context.active_object
wall.name = "BrickWall"
wall.scale = (10, 6, 1)
wall.rotation_euler = (math.radians(90), 0, 0)
wall.data.materials.append(wall_mat)

# Floor
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, -5, -2.5))
floor = bpy.context.active_object
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fb = fm.node_tree.nodes.get("Principled BSDF")
fb.inputs["Base Color"].default_value = (0.02, 0.02, 0.022, 1)
fb.inputs["Roughness"].default_value = 0.35
floor.data.materials.append(fm)

# ---------- Neon material ----------
neon = bpy.data.materials.new("PinkNeon")
neon.use_nodes = True
nn = neon.node_tree
for n in list(nn.nodes):
    nn.nodes.remove(n)
em = nn.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.08, 0.55, 1)
em.inputs["Strength"].default_value = 25.0
out = nn.nodes.new("ShaderNodeOutputMaterial")
nn.links.new(em.outputs[0], out.inputs["Surface"])

# ---------- OPEN text as neon tubes ----------
curve = bpy.data.curves.new("OpenText", type='FONT')
curve.body = "OPEN"
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.size = 1.3
curve.extrude = 0.0
curve.bevel_depth = 0.025
curve.bevel_resolution = 4
try:
    curve.fill_mode = 'NONE'
except Exception:
    pass
txt = bpy.data.objects.new("OPEN", curve)
scene.collection.objects.link(txt)
txt.location = (0, -0.15, 0.3)
txt.rotation_euler = (math.radians(90), 0, 0)
txt.data.materials.append(neon)

# Neon border rectangle
bc = bpy.data.curves.new("Border", type='CURVE')
bc.dimensions = '3D'
bc.bevel_depth = 0.02
bc.bevel_resolution = 4
sp = bc.splines.new('POLY')
w, h = 2.0, 0.85
pts = [(-w, -h), (w, -h), (w, h), (-w, h)]
sp.points.add(len(pts) - 1)
for p, (x, z) in zip(sp.points, pts):
    p.co = (x, -0.15, z + 0.3, 1)
sp.use_cyclic_u = True
border = bpy.data.objects.new("Border", bc)
scene.collection.objects.link(border)
border.data.materials.append(neon)

# Dark acrylic backing plate
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.07, 0.3))
plate = bpy.context.active_object
plate.scale = (4.3, 0.04, 1.9)
pm = bpy.data.materials.new("Backing")
pm.use_nodes = True
pb = pm.node_tree.nodes.get("Principled BSDF")
pb.inputs["Base Color"].default_value = (0.01, 0.01, 0.012, 1)
pb.inputs["Roughness"].default_value = 0.15
plate.data.materials.append(pm)

# ---------- Lighting ----------
def add_point(name, loc, energy, color, radius=0.3):
    ld = bpy.data.lights.new(name, type='POINT')
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    scene.collection.objects.link(lo)

add_point("NeonSpill", (0, -0.6, 0.3), 250, (1.0, 0.15, 0.6), 1.5)
add_point("NeonSpillL", (-1.8, -0.5, 0.3), 80, (1.0, 0.15, 0.6), 0.5)
add_point("NeonSpillR", (1.8, -0.5, 0.3), 80, (1.0, 0.15, 0.6), 0.5)
add_point("Fill", (-3, -5, 2), 20, (0.4, 0.5, 1.0), 2.0)

# ---------- Camera ----------
cd = bpy.data.cameras.new("Camera")
cd.lens = 40
cam = bpy.data.objects.new("Camera", cd)
scene.collection.objects.link(cam)
cam.location = (0.6, -7.0, 0.0)
cam.rotation_euler = (math.radians(92), 0, math.radians(5))
scene.camera = cam

# ---------- Compositor glare ----------
def set_input(node, names, value):
    for n in names:
        if n in node.inputs:
            try:
                node.inputs[n].default_value = value
                return True
            except Exception:
                pass
    return False

try:
    tree = bpy.data.node_groups.new("NeonComp", 'CompositorNodeTree')
    scene.compositing_node_group = tree
    new_api = True
except Exception:
    scene.use_nodes = True
    tree = scene.node_tree
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    new_api = False

rl = tree.nodes.new('CompositorNodeRLayers')
rl.location = (-400, 0)
glare = tree.nodes.new('CompositorNodeGlare')
glare.location = (0, 0)
ok = False
try:
    glare.glare_type = 'FOG_GLOW'
    ok = True
except Exception:
    pass
if not ok:
    for v in ('Fog Glow', 'FOG_GLOW', 'Bloom', 'BLOOM'):
        if set_input(glare, ["Type"], v):
            break
try:
    glare.quality = 'HIGH'
except Exception:
    set_input(glare, ["Quality"], 'High')
try:
    glare.size = 9
except Exception:
    pass
try:
    glare.threshold = 0.8
except Exception:
    pass
set_input(glare, ["Threshold", "Highlights Threshold"], 0.8)
set_input(glare, ["Strength"], 1.0)
set_input(glare, ["Size"], 0.9)
set_input(glare, ["Saturation"], 1.2)

tree.links.new(rl.outputs["Image"], glare.inputs["Image"])

if new_api:
    try:
        tree.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    except Exception:
        pass
    go = tree.nodes.new('NodeGroupOutput')
    go.location = (300, 0)
    tree.links.new(glare.outputs["Image"], go.inputs[0])
else:
    comp = tree.nodes.new('CompositorNodeComposite')
    comp.location = (300, 0)
    tree.links.new(glare.outputs["Image"], comp.inputs["Image"])

scene.frame_start = 1
scene.frame_end = 1
