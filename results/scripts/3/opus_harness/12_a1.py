import bpy
import math

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# World: very dark
world = bpy.data.worlds.new("DarkWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.005, 0.008, 1)
    bg.inputs["Strength"].default_value = 1.0

PINK = (1.0, 0.08, 0.5, 1.0)

# ---------- Brick wall ----------
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0.15, 0), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.name = "BrickWall"
wmat = bpy.data.materials.new("DarkBrick")
nt = wmat.node_tree
nodes, links = nt.nodes, nt.links
bsdf = nodes.get("Principled BSDF")
brick = nodes.new("ShaderNodeTexBrick")
brick.location = (-500, 200)
brick.inputs["Color1"].default_value = (0.07, 0.025, 0.02, 1)
brick.inputs["Color2"].default_value = (0.045, 0.018, 0.015, 1)
brick.inputs["Mortar"].default_value = (0.015, 0.015, 0.015, 1)
brick.inputs["Scale"].default_value = 9.0
brick.inputs["Mortar Size"].default_value = 0.015
noise = nodes.new("ShaderNodeTexNoise")
noise.location = (-700, -100)
noise.inputs["Scale"].default_value = 40.0
mix = nodes.new("ShaderNodeMix")
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.location = (-250, 200)
mix.inputs["Factor"].default_value = 0.4
links.new(brick.outputs["Color"], mix.inputs["A"])
links.new(noise.outputs["Color"], mix.inputs["B"])
links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
bump = nodes.new("ShaderNodeBump")
bump.location = (-250, -200)
bump.inputs["Strength"].default_value = 0.6
links.new(brick.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Roughness"].default_value = 0.9
wall.data.materials.append(wmat)

# ---------- Neon material ----------
neon = bpy.data.materials.new("PinkNeon")
nb = neon.node_tree.nodes.get("Principled BSDF")
nb.inputs["Base Color"].default_value = PINK
nb.inputs["Emission Color"].default_value = PINK
nb.inputs["Emission Strength"].default_value = 25.0
nb.inputs["Roughness"].default_value = 0.2

# ---------- OPEN text ----------
tcurve = bpy.data.curves.new("OpenText", 'FONT')
tcurve.body = "OPEN"
tcurve.align_x = 'CENTER'
tcurve.align_y = 'CENTER'
tcurve.size = 1.0
tcurve.extrude = 0.02
tcurve.bevel_depth = 0.012
tcurve.bevel_resolution = 3
txt = bpy.data.objects.new("OpenSign", tcurve)
scene.collection.objects.link(txt)
txt.location = (0, 0, 0)
txt.rotation_euler = (math.radians(90), 0, 0)
txt.data.materials.append(neon)

# ---------- Neon border tube ----------
bc = bpy.data.curves.new("Border", 'CURVE')
bc.dimensions = '3D'
bc.bevel_depth = 0.025
bc.bevel_resolution = 4
sp = bc.splines.new('POLY')
w, h = 1.85, 0.8
pts = [(-w, 0, -h), (w, 0, -h), (w, 0, h), (-w, 0, h)]
sp.points.add(len(pts) - 1)
for p, c in zip(sp.points, pts):
    p.co = (c[0], c[1], c[2], 1)
sp.use_cyclic_u = True
border = bpy.data.objects.new("NeonBorder", bc)
scene.collection.objects.link(border)
border.location = (0, 0.02, 0)
border.data.materials.append(neon)

# ---------- Lights ----------
pl = bpy.data.lights.new("NeonSpill", 'POINT')
pl.color = (1.0, 0.2, 0.6)
pl.energy = 150
pl.shadow_soft_size = 1.0
plo = bpy.data.objects.new("NeonSpill", pl)
plo.location = (0, -0.6, 0)
scene.collection.objects.link(plo)

fill = bpy.data.lights.new("Fill", 'AREA')
fill.energy = 20
fill.size = 4
fill.color = (0.5, 0.6, 1.0)
fo = bpy.data.objects.new("Fill", fill)
fo.location = (3, -4, 3)
fo.rotation_euler = (math.radians(60), 0, math.radians(35))
scene.collection.objects.link(fo)

# ---------- Camera ----------
cam = bpy.data.cameras.new("Cam")
cam.lens = 45
camo = bpy.data.objects.new("Cam", cam)
camo.location = (0.6, -6.5, 0.3)
camo.rotation_euler = (math.radians(88), 0, math.radians(5))
scene.collection.objects.link(camo)
scene.camera = camo

# ---------- Compositor with Glare ----------
tree = bpy.data.node_groups.new("NeonComp", "CompositorNodeTree")
scene.compositing_node_group = tree
rl = tree.nodes.new("CompositorNodeRLayers")
rl.location = (-400, 0)
glare = tree.nodes.new("CompositorNodeGlare")
glare.location = (0, 0)
for name, val in (("Type", "Fog Glow"), ("Quality", "High"), ("Threshold", 0.8),
                  ("Size", 0.7), ("Strength", 1.0), ("Mix", 0.0)):
    try:
        glare.inputs[name].default_value = val
    except Exception:
        pass
out = tree.nodes.new("NodeGroupOutput")
out.location = (300, 0)
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
tree.links.new(glare.inputs["Image"], rl.outputs["Image"])
tree.links.new(out.inputs["Image"], glare.outputs["Image"])
