import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Render engine
try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# World - very dark
world = bpy.data.worlds.new("NightWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.005, 0.01, 1)
    bg.inputs["Strength"].default_value = 0.3

# ---------------- Brick wall ----------------
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.15, 0), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.name = "BrickWall"
wall.scale = (12, 8, 1)

wmat = bpy.data.materials.new("DarkBrick")
nt = wmat.node_tree
nodes = nt.nodes
links = nt.links
bsdf = nodes.get("Principled BSDF")
texco = nodes.new("ShaderNodeTexCoord")
brick = nodes.new("ShaderNodeTexBrick")
brick.inputs["Scale"].default_value = 1.6
brick.inputs["Color1"].default_value = (0.09, 0.03, 0.025, 1)
brick.inputs["Color2"].default_value = (0.05, 0.02, 0.018, 1)
brick.inputs["Mortar"].default_value = (0.02, 0.02, 0.02, 1)
brick.inputs["Mortar Size"].default_value = 0.015
brick.inputs["Brick Width"].default_value = 0.5
brick.inputs["Row Height"].default_value = 0.25
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 30
mix = nodes.new("ShaderNodeMix")
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.inputs["Factor"].default_value = 0.5
bump = nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.5
links.new(texco.outputs["Object"], brick.inputs["Vector"])
links.new(texco.outputs["Object"], noise.inputs["Vector"])
links.new(brick.outputs["Color"], mix.inputs["A"])
links.new(noise.outputs["Color"], mix.inputs["B"])
links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
links.new(brick.outputs["Fac"], bump.inputs["Height"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Roughness"].default_value = 0.9
wall.data.materials.append(wmat)

# Floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, -4, -3))
floor = bpy.context.active_object
fmat = bpy.data.materials.new("Floor")
fb = fmat.node_tree.nodes.get("Principled BSDF")
fb.inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1)
fb.inputs["Roughness"].default_value = 0.3
floor.data.materials.append(fmat)

# ---------------- Neon text ----------------
curve = bpy.data.curves.new("OpenText", type='FONT')
curve.body = "OPEN"
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.size = 1.6
curve.bevel_depth = 0.025
curve.bevel_resolution = 4
curve.fill_mode = 'NONE'
curve.offset = -0.03
text = bpy.data.objects.new("NeonOPEN", curve)
scene.collection.objects.link(text)
text.rotation_euler = (math.radians(90), 0, 0)
text.location = (0, 0, 0)

nmat = bpy.data.materials.new("PinkNeon")
nn = nmat.node_tree.nodes
nl = nmat.node_tree.links
for n in list(nn):
    nn.remove(n)
out = nn.new("ShaderNodeOutputMaterial")
em = nn.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.1, 0.55, 1)
em.inputs["Strength"].default_value = 25.0
nl.new(em.outputs["Emission"], out.inputs["Surface"])
text.data.materials.append(nmat)

# Neon border tube (rounded rectangle)
bcurve = bpy.data.curves.new("Border", type='CURVE')
bcurve.dimensions = '3D'
bcurve.bevel_depth = 0.02
bcurve.bevel_resolution = 4
sp = bcurve.splines.new('POLY')
w, h, r = 2.6, 1.15, 0.25
pts = []
corners = [(w - r, h - r, 0), (-w + r, h - r, 90), (-w + r, -h + r, 180), (w - r, -h + r, 270)]
for cx, cy, a0 in corners:
    for i in range(7):
        a = math.radians(a0 + i * 15)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
sp.points.add(len(pts) - 1)
for i, (x, y) in enumerate(pts):
    sp.points[i].co = (x, y, 0, 1)
sp.use_cyclic_u = True
border = bpy.data.objects.new("NeonBorder", bcurve)
scene.collection.objects.link(border)
border.rotation_euler = (math.radians(90), 0, 0)
bmat = bpy.data.materials.new("BlueNeon")
bnn = bmat.node_tree.nodes
for n in list(bnn):
    bnn.remove(n)
bo = bnn.new("ShaderNodeOutputMaterial")
be = bnn.new("ShaderNodeEmission")
be.inputs["Color"].default_value = (1.0, 0.25, 0.7, 1)
be.inputs["Strength"].default_value = 15.0
bmat.node_tree.links.new(be.outputs["Emission"], bo.inputs["Surface"])
border.data.materials.append(bmat)

# Mounting rods
rmat = bpy.data.materials.new("Metal")
rb = rmat.node_tree.nodes.get("Principled BSDF")
rb.inputs["Base Color"].default_value = (0.3, 0.3, 0.3, 1)
rb.inputs["Metallic"].default_value = 1.0
rb.inputs["Roughness"].default_value = 0.4
for x in (-2.0, 2.0):
    for z in (-1.0, 1.0):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.15, location=(x, 0.075, z),
                                            rotation=(math.radians(90), 0, 0))
        bpy.context.active_object.data.materials.append(rmat)

# ---------------- Lights ----------------
pink = bpy.data.lights.new("NeonSpill", type='AREA')
pink.color = (1.0, 0.2, 0.6)
pink.energy = 300
pink.size = 5
pink.shape = 'RECTANGLE'
pink.size_y = 2.3
pl = bpy.data.objects.new("NeonSpill", pink)
scene.collection.objects.link(pl)
pl.location = (0, -0.4, 0)
pl.rotation_euler = (math.radians(-90), 0, 0)

fill = bpy.data.lights.new("Fill", type='AREA')
fill.color = (0.5, 0.6, 1.0)
fill.energy = 40
fill.size = 6
fl = bpy.data.objects.new("Fill", fill)
scene.collection.objects.link(fl)
fl.location = (-4, -5, 4)
fl.rotation_euler = (math.radians(55), 0, math.radians(-35))

# ---------------- Camera ----------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.8, -8.5, 0.3)
cam.rotation_euler = (math.radians(88), 0, math.radians(5))
scene.camera = cam

# ---------------- Compositor glare ----------------
tree = bpy.data.node_groups.new("NeonGlow", "CompositorNodeTree")
scene.compositing_node_group = tree
rl = tree.nodes.new("CompositorNodeRLayers")
glare = tree.nodes.new("CompositorNodeGlare")
outn = tree.nodes.new("NodeGroupOutput")
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
for name, val in (("Type", "Fog Glow"), ("Quality", "High"), ("Threshold", 0.6),
                  ("Size", 0.7), ("Strength", 1.0), ("Smoothness", 0.2)):
    try:
        glare.inputs[name].default_value = val
    except Exception:
        pass
rl.location = (-300, 0)
outn.location = (300, 0)
tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
tree.links.new(glare.outputs["Image"], outn.inputs[0])

scene.frame_start = 1
scene.frame_end = 1
