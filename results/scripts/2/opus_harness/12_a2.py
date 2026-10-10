import bpy, math
import mathutils

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# World
world = bpy.data.worlds.new("DarkWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.005, 0.008, 1)
    bg.inputs["Strength"].default_value = 0.5

# ---------- Brick wall ----------
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.15, 0), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.name = "BrickWall"
wall.scale = (12, 7, 1)

wm = bpy.data.materials.new("BrickMat")
nt = wm.node_tree
nodes, links = nt.nodes, nt.links
bsdf = nodes.get("Principled BSDF")
tc = nodes.new("ShaderNodeTexCoord")
mapn = nodes.new("ShaderNodeMapping")
mapn.inputs["Scale"].default_value = (1, 1, 1)
brick = nodes.new("ShaderNodeTexBrick")
brick.inputs["Color1"].default_value = (0.18, 0.05, 0.035, 1)
brick.inputs["Color2"].default_value = (0.12, 0.035, 0.025, 1)
brick.inputs["Mortar"].default_value = (0.05, 0.045, 0.04, 1)
brick.inputs["Scale"].default_value = 4.0
brick.inputs["Mortar Size"].default_value = 0.015
brick.inputs["Brick Width"].default_value = 0.5
brick.inputs["Row Height"].default_value = 0.2
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 40
mix = nodes.new("ShaderNodeMix")
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.inputs["Factor"].default_value = 0.4
bump = nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.6
links.new(tc.outputs["Object"], mapn.inputs["Vector"])
links.new(mapn.outputs["Vector"], brick.inputs["Vector"])
links.new(mapn.outputs["Vector"], noise.inputs["Vector"])
links.new(brick.outputs["Color"], mix.inputs["A"])
links.new(noise.outputs["Color"], mix.inputs["B"])
links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
links.new(brick.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Roughness"].default_value = 0.9
wall.data.materials.append(wm)

# ---------- Neon material ----------
neon = bpy.data.materials.new("NeonPink")
nn = neon.node_tree
for n in list(nn.nodes):
    if n.type != 'OUTPUT_MATERIAL':
        nn.nodes.remove(n)
out = [n for n in nn.nodes if n.type == 'OUTPUT_MATERIAL'][0]
em = nn.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.08, 0.55, 1)
em.inputs["Strength"].default_value = 12.0
nn.links.new(em.outputs["Emission"], out.inputs["Surface"])

# ---------- Text ----------
tcurve = bpy.data.curves.new("OpenText", type='FONT')
tcurve.body = "OPEN"
tcurve.align_x = 'CENTER'
tcurve.align_y = 'CENTER'
tcurve.size = 1.6
tcurve.fill_mode = 'NONE'
tcurve.bevel_depth = 0.03
tcurve.bevel_resolution = 4
txt = bpy.data.objects.new("OpenSign", tcurve)
scene.collection.objects.link(txt)
txt.location = (0, -0.05, 0)
txt.rotation_euler = (math.radians(90), 0, 0)
tcurve.materials.append(neon)

# ---------- Neon border ----------
bc = bpy.data.curves.new("Border", type='CURVE')
bc.dimensions = '3D'
bc.bevel_depth = 0.025
bc.bevel_resolution = 4
sp = bc.splines.new('POLY')
pts = [(-2.6, 0, -1.2), (2.6, 0, -1.2), (2.6, 0, 1.2), (-2.6, 0, 1.2)]
sp.points.add(len(pts) - 1)
for p, c in zip(sp.points, pts):
    p.co = (c[0], c[1], c[2], 1)
sp.use_cyclic_u = True
border = bpy.data.objects.new("Border", bc)
scene.collection.objects.link(border)
border.location = (0, -0.05, 0)
bc.materials.append(neon)

# ---------- Lights ----------
ld = bpy.data.lights.new("PinkSpill", type='AREA')
ld.energy = 150
ld.color = (1.0, 0.2, 0.6)
ld.size = 5
la = bpy.data.objects.new("PinkSpill", ld)
scene.collection.objects.link(la)
la.location = (0, -0.6, 0)
la.rotation_euler = (math.radians(-90), 0, 0)

fd = bpy.data.lights.new("Fill", type='AREA')
fd.energy = 30
fd.color = (0.4, 0.5, 1.0)
fd.size = 6
fo = bpy.data.objects.new("Fill", fd)
scene.collection.objects.link(fo)
fo.location = (3, -6, 3)
fo.rotation_euler = (math.radians(60), 0, math.radians(25))

# ---------- Camera ----------
cd = bpy.data.cameras.new("Cam")
cd.lens = 40
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
cam.location = (0.6, -8, 0.3)
direction = mathutils.Vector((0, 0, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Compositor glare ----------
tree = bpy.data.node_groups.new("NeonComp", "CompositorNodeTree")
scene.compositing_node_group = tree
rl = tree.nodes.new("CompositorNodeRLayers")
glare = tree.nodes.new("CompositorNodeGlare")

def set_in(node, name, val):
    try:
        if name in node.inputs:
            node.inputs[name].default_value = val
    except Exception:
        pass

set_in(glare, "Type", "Bloom")
set_in(glare, "Quality", "High")
set_in(glare, "Threshold", 0.8)
set_in(glare, "Strength", 1.0)
set_in(glare, "Size", 0.7)

tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
outn = tree.nodes.new("NodeGroupOutput")
tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
gout = glare.outputs["Image"] if "Image" in glare.outputs else glare.outputs[0]
tree.links.new(gout, outn.inputs[0])
rl.location = (-400, 0)
glare.location = (0, 0)
outn.location = (300, 0)

scene.view_settings.view_transform = 'AgX'
