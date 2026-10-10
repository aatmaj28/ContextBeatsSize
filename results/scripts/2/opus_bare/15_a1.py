import bpy
import math

scene = bpy.context.scene

# ---------- clean ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- materials ----------
def make_mat(name, color, metal=0.8, rough=0.35, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

m_wall = make_mat("Wall", (0.12, 0.13, 0.15), 0.7, 0.4)
m_floor = make_mat("Floor", (0.05, 0.055, 0.06), 0.9, 0.25)
m_rib = make_mat("Rib", (0.25, 0.26, 0.28), 0.9, 0.3)
m_strip = make_mat("Strip", (0.0, 0.0, 0.0), 0.0, 0.5, (0.1, 0.8, 1.0), 25.0)
m_strip2 = make_mat("StripOrange", (0.0, 0.0, 0.0), 0.0, 0.5, (1.0, 0.35, 0.05), 20.0)
m_ceil_light = make_mat("CeilLight", (0, 0, 0), 0.0, 0.5, (0.9, 0.95, 1.0), 12.0)

def box(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.materials.append(mat)
    return o

W, H, L = 4.0, 3.5, 44.0
yc = L / 2 - 4

# shell
box("Floor", (0, yc, -0.05), (W + 1, L, 0.1), m_floor)
box("Ceiling", (0, yc, H + 0.05), (W + 1, L, 0.1), m_wall)
box("WallL", (-W / 2 - 0.05, yc, H / 2), (0.1, L, H), m_wall)
box("WallR", (W / 2 + 0.05, yc, H / 2), (0.1, L, H), m_wall)
box("EndWall", (0, L - 4, H / 2), (W, 0.1, H), m_wall)

# ribs, panels, strips
y = 0.0
i = 0
while y < L - 5:
    # ribs (frames)
    box(f"RibL{i}", (-W / 2 + 0.1, y, H / 2), (0.2, 0.3, H), m_rib)
    box(f"RibR{i}", (W / 2 - 0.1, y, H / 2), (0.2, 0.3, H), m_rib)
    box(f"RibT{i}", (0, y, H - 0.1), (W, 0.3, 0.2), m_rib)
    # angled corner braces
    for sx in (-1, 1):
        b = box(f"Brace{i}_{sx}", (sx * (W / 2 - 0.35), y, H - 0.35), (0.12, 0.28, 0.9), m_rib)
        b.rotation_euler = (0, sx * math.radians(45), 0)
        b = box(f"BraceB{i}_{sx}", (sx * (W / 2 - 0.3), y, 0.3), (0.12, 0.28, 0.8), m_rib)
        b.rotation_euler = (0, -sx * math.radians(45), 0)
    # wall panels between ribs
    seg = 2.5
    for sx in (-1, 1):
        box(f"Panel{i}_{sx}", (sx * (W / 2 - 0.03), y + seg / 2, 1.8), (0.06, seg - 0.4, 1.6), m_wall)
        # glowing strips
        box(f"StripHi{i}_{sx}", (sx * (W / 2 - 0.06), y + seg / 2, 2.75), (0.05, seg - 0.4, 0.06), m_strip)
        box(f"StripLo{i}_{sx}", (sx * (W / 2 - 0.06), y + seg / 2, 0.75), (0.05, seg - 0.4, 0.04), m_strip)
        # floor edge strip
        box(f"StripFl{i}_{sx}", (sx * (W / 2 - 0.45), y + seg / 2, 0.01), (0.04, seg - 0.4, 0.02), m_strip2)
    # ceiling light
    box(f"CeilLight{i}", (0, y + seg / 2, H - 0.01), (0.6, 1.4, 0.02), m_ceil_light)
    # floor grate segments
    box(f"Grate{i}", (0, y + seg / 2, 0.01), (1.6, seg - 0.2, 0.02), m_rib)
    y += seg
    i += 1

# door glow at end
box("Door", (0, L - 4.1, 1.3), (1.6, 0.05, 2.6), m_strip2)

# ---------- lights ----------
for k in range(0, int(L - 6), 5):
    bpy.ops.object.light_add(type='AREA', location=(0, k + 1.25, H - 0.15))
    l = bpy.context.active_object
    l.data.energy = 120
    l.data.size = 1.0
    l.data.color = (0.85, 0.92, 1.0)
    for sx in (-1, 1):
        bpy.ops.object.light_add(type='POINT', location=(sx * (W / 2 - 0.3), k + 1.25, 2.6))
        p = bpy.context.active_object
        p.data.energy = 40
        p.data.color = (0.2, 0.8, 1.0)
        p.data.shadow_soft_size = 0.3

# world
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.007, 0.01, 1)

# ---------- camera ----------
bpy.ops.object.camera_add(location=(0.4, -2.0, 1.55), rotation=(math.radians(88), 0, math.radians(-3)))
cam = bpy.context.active_object
cam.data.lens = 24
scene.camera = cam

# ---------- render ----------
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = eng
        break
    except Exception:
        pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Punchy'
except Exception:
    pass

# ---------- compositor vignette ----------
def si(node, name, val):
    if name in node.inputs:
        try:
            node.inputs[name].default_value = val
            return True
        except Exception:
            pass
    return False

def sa(node, attr, val):
    try:
        setattr(node, attr, val)
    except Exception:
        pass

tree = None
out_socket = None
try:
    tree = bpy.data.node_groups.new("Vignette Comp", 'CompositorNodeTree')
    scene.compositing_node_group = tree
    tree.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    out = tree.nodes.new('NodeGroupOutput')
    out_socket = out.inputs[0]
except Exception:
    scene.use_nodes = True
    tree = scene.node_tree
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    out = tree.nodes.new('CompositorNodeComposite')
    out_socket = out.inputs[0]
out.location = (900, 0)

rl = tree.nodes.new('CompositorNodeRLayers')
rl.location = (-400, 200)

# soft glow
img_socket = rl.outputs["Image"]
try:
    glare = tree.nodes.new('CompositorNodeGlare')
    glare.location = (-150, 250)
    sa(glare, "glare_type", 'BLOOM')
    if not si(glare, "Type", 'Bloom'):
        pass
    tree.links.new(img_socket, glare.inputs[0])
    img_socket = glare.outputs[0]
except Exception:
    pass

ell = tree.nodes.new('CompositorNodeEllipseMask')
ell.location = (-400, -200)
sa(ell, "width", 0.85)
sa(ell, "height", 0.75)
si(ell, "Size", (0.85, 0.75))
si(ell, "Value", 1.0)
si(ell, "Mask", 0.0)

blur = tree.nodes.new('CompositorNodeBlur')
blur.location = (-150, -200)
sa(blur, "size_x", 250)
sa(blur, "size_y", 250)
sa(blur, "filter_type", 'GAUSS')
si(blur, "Size", (250, 250))
tree.links.new(ell.outputs[0], blur.inputs[0])

try:
    mix = tree.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 0.85
    tree.links.new(img_socket, mix.inputs[6])
    tree.links.new(blur.outputs[0], mix.inputs[7])
    mix_out = mix.outputs[2]
except Exception:
    mix = tree.nodes.new('CompositorNodeMixRGB')
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 0.85
    tree.links.new(img_socket, mix.inputs[1])
    tree.links.new(blur.outputs[0], mix.inputs[2])
    mix_out = mix.outputs[0]
mix.location = (300, 0)
tree.links.new(mix_out, out_socket)

scene.frame_start = 1
scene.frame_end = 1
