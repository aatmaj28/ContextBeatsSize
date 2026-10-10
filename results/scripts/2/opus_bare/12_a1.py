import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- Render engine ----------
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = eng
        break
    except Exception:
        pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# ---------- World ----------
world = bpy.data.worlds.new("DarkWorld")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.005, 0.004, 0.006, 1)
    bg.inputs[1].default_value = 1.0

# ---------- Brick wall ----------
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.5), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.name = "BrickWall"
wall.scale = (14, 8, 1)

wm = bpy.data.materials.new("DarkBrick")
wm.use_nodes = True
nt = wm.node_tree
bsdf = nt.nodes.get("Principled BSDF")
tc = nt.nodes.new("ShaderNodeTexCoord")
brick = nt.nodes.new("ShaderNodeTexBrick")
brick.inputs["Color1"].default_value = (0.09, 0.035, 0.025, 1)
brick.inputs["Color2"].default_value = (0.06, 0.025, 0.02, 1)
brick.inputs["Mortar"].default_value = (0.03, 0.03, 0.03, 1)
brick.inputs["Scale"].default_value = 1.0
brick.inputs["Mortar Size"].default_value = 0.015
brick.inputs["Brick Width"].default_value = 0.5
brick.inputs["Row Height"].default_value = 0.2
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 40
mix = nt.nodes.new("ShaderNodeMixRGB")
mix.blend_type = 'MULTIPLY'
mix.inputs[0].default_value = 0.5
nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
nt.links.new(brick.outputs["Color"], mix.inputs[1])
nt.links.new(noise.outputs["Color"], mix.inputs[2])
nt.links.new(mix.outputs[0], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.9
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.6
nt.links.new(brick.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
wall.data.materials.append(wm)

# ---------- Neon letters ----------
def arc(cx, cy, rx, ry, a0, a1, n=32):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

strokes = []  # (points, cyclic)
# O
strokes.append((arc(0.4, 0.5, 0.38, 0.5, 0, 360, 64)[:-1], True))
# P
ox = 1.15
strokes.append(([(ox, 0), (ox, 1)] + [(ox + x, y) for x, y in arc(0.38, 0.725, 0.27, 0.275, 90, -90, 24)] + [(ox, 0.45)], False))
# E
ox = 2.15
strokes.append(([(ox + 0.7, 1), (ox, 1), (ox, 0), (ox + 0.7, 0)], False))
strokes.append(([(ox, 0.5), (ox + 0.55, 0.5)], False))
# N
ox = 3.15
strokes.append(([(ox, 0), (ox, 1), (ox + 0.75, 0), (ox + 0.75, 1)], False))

total_w = 3.9
scale = 1.2
cu = bpy.data.curves.new("NeonCurve", 'CURVE')
cu.dimensions = '3D'
cu.bevel_depth = 0.035
cu.bevel_resolution = 6
for pts, cyc in strokes:
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        sp.points[i].co = ((x - total_w / 2) * scale, 0, y * scale, 1)
    sp.use_cyclic_u = cyc
neon = bpy.data.objects.new("NeonOPEN", cu)
scene.collection.objects.link(neon)
neon.location = (0, -0.15, 1.0)

nm = bpy.data.materials.new("PinkNeon")
nm.use_nodes = True
nn = nm.node_tree
for n in list(nn.nodes):
    nn.nodes.remove(n)
em = nn.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.08, 0.55, 1)
em.inputs["Strength"].default_value = 18
mo = nn.nodes.new("ShaderNodeOutputMaterial")
nn.links.new(em.outputs[0], mo.inputs["Surface"])
cu.materials.append(nm)

# Clear acrylic backing plate
bpy.ops.mesh.primitive_cube_add(location=(0, -0.08, 1.6))
plate = bpy.context.active_object
plate.scale = (2.6, 0.015, 0.85)
pm = bpy.data.materials.new("Backplate")
pm.use_nodes = True
pb = pm.node_tree.nodes.get("Principled BSDF")
pb.inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1)
pb.inputs["Roughness"].default_value = 0.2
plate.data.materials.append(pm)

# ---------- Lights ----------
ld = bpy.data.lights.new("NeonSpill", 'AREA')
ld.energy = 120
ld.color = (1.0, 0.2, 0.6)
ld.shape = 'RECTANGLE'
ld.size = 4.5
ld.size_y = 1.2
lo = bpy.data.objects.new("NeonSpill", ld)
lo.location = (0, -0.5, 1.6)
lo.rotation_euler = (math.radians(-90), 0, 0)
lo.rotation_euler = (math.radians(90), 0, 0)
scene.collection.objects.link(lo)

fd = bpy.data.lights.new("Fill", 'AREA')
fd.energy = 30
fd.color = (0.4, 0.5, 1.0)
fd.size = 6
fo = bpy.data.objects.new("Fill", fd)
fo.location = (3, -6, 4)
fo.rotation_euler = (math.radians(60), 0, math.radians(25))
scene.collection.objects.link(fo)

# ---------- Camera ----------
cd = bpy.data.cameras.new("Cam")
cd.lens = 40
cam = bpy.data.objects.new("Cam", cd)
cam.location = (0.6, -7.5, 1.9)
scene.collection.objects.link(cam)
tgt = bpy.data.objects.new("CamTarget", None)
tgt.location = (0, 0, 1.6)
scene.collection.objects.link(tgt)
c = cam.constraints.new('TRACK_TO')
c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam

# ---------- Compositor glare ----------
tree = None
out_node = None
if hasattr(scene, "compositing_node_group"):
    tree = bpy.data.node_groups.new("NeonGlow", "CompositorNodeTree")
    try:
        tree.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    except Exception:
        pass
    scene.compositing_node_group = tree
    out_node = tree.nodes.new("NodeGroupOutput")
else:
    scene.use_nodes = True
    tree = scene.node_tree
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    out_node = tree.nodes.new("CompositorNodeComposite")

rl = tree.nodes.new("CompositorNodeRLayers")
rl.location = (-400, 0)
glare = tree.nodes.new("CompositorNodeGlare")
glare.location = (0, 0)
out_node.location = (400, 0)

def set_glare(prop, sock, val, sval=None):
    try:
        setattr(glare, prop, val)
        return
    except Exception:
        pass
    try:
        glare.inputs[sock].default_value = sval if sval is not None else val
    except Exception:
        pass

set_glare("glare_type", "Type", 'FOG_GLOW', 'Fog Glow')
set_glare("quality", "Quality", 'HIGH', 'High')
set_glare("threshold", "Threshold", 0.6)
set_glare("size", "Size", 8, 0.8)
try:
    glare.inputs["Strength"].default_value = 1.0
except Exception:
    pass
try:
    glare.inputs["Saturation"].default_value = 1.2
except Exception:
    pass

tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
tree.links.new(glare.outputs[0], out_node.inputs[0])

scene.frame_start = 1
scene.frame_end = 1
