import bpy
import math

scene = bpy.context.scene

# ---------- Cleanup ----------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

# ---------- Render engine ----------
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'CYCLES'):
    try:
        scene.render.engine = eng
        break
    except Exception:
        pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
try:
    scene.view_settings.view_transform = 'AgX'
except Exception:
    pass

# ---------- Materials ----------
def make_mat(name, color, metallic=0.0, rough=0.5, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit:
        ec = b.inputs.get("Emission Color") or b.inputs.get("Emission")
        ec.default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

mat_wall = make_mat("Wall", (0.12, 0.13, 0.15), 0.7, 0.35)
mat_panel = make_mat("Panel", (0.05, 0.055, 0.065), 0.8, 0.25)
mat_floor = make_mat("Floor", (0.04, 0.04, 0.045), 0.9, 0.2)
mat_rib = make_mat("Rib", (0.2, 0.21, 0.23), 0.9, 0.3)
mat_cyan = make_mat("GlowCyan", (0.0, 0.0, 0.0), 0, 0.5, (0.1, 0.8, 1.0), 25.0)
mat_orange = make_mat("GlowOrange", (0.0, 0.0, 0.0), 0, 0.5, (1.0, 0.35, 0.05), 15.0)

def box(name, loc, scale, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    return o

# ---------- Corridor ----------
L = 40.0
W = 4.0
H = 3.5
cy = L / 2 - 2

box("Floor", (0, cy, -0.05), (W, L, 0.1), mat_floor)
box("Ceiling", (0, cy, H + 0.05), (W, L, 0.1), mat_wall)
box("WallL", (-W / 2 - 0.05, cy, H / 2), (0.1, L, H), mat_wall)
box("WallR", (W / 2 + 0.05, cy, H / 2), (0.1, L, H), mat_wall)
box("EndWall", (0, cy + L / 2, H / 2), (W, 0.1, H), mat_panel)
box("EndGlow", (0, cy + L / 2 - 0.06, H / 2), (1.2, 0.02, 2.4), mat_orange)

# Floor grating stripe
box("FloorCenter", (0, cy, 0.01), (1.2, L, 0.02), mat_panel)

seg = 2.5
n = int(L / seg)
for i in range(n):
    y = -2 + i * seg + seg / 2
    # Wall panels
    for s in (-1, 1):
        x = s * (W / 2 - 0.03)
        box(f"PanelLow_{i}_{s}", (x, y, 0.8), (0.06, seg - 0.4, 1.0), mat_panel)
        box(f"PanelHigh_{i}_{s}", (x, y, 2.45), (0.06, seg - 0.4, 1.3), mat_panel)
        # Floor-level light strip
        box(f"StripLow_{i}_{s}", (s * (W / 2 - 0.07), y, 0.12), (0.03, seg - 0.3, 0.04), mat_cyan)
        # Mid-wall light strip
        box(f"StripMid_{i}_{s}", (s * (W / 2 - 0.07), y, 1.5), (0.03, seg - 0.3, 0.05), mat_cyan)
    # Ceiling strip
    box(f"CeilStrip_{i}", (0, y, H - 0.02), (0.15, seg - 0.6, 0.03), mat_cyan)
    # Structural rib frame
    yr = -2 + i * seg
    box(f"RibL_{i}", (-W / 2 + 0.1, yr, H / 2), (0.25, 0.3, H), mat_rib)
    box(f"RibR_{i}", (W / 2 - 0.1, yr, H / 2), (0.25, 0.3, H), mat_rib)
    box(f"RibT_{i}", (0, yr, H - 0.12), (W, 0.3, 0.25), mat_rib)
    box(f"RibAccent_{i}", (0, yr - 0.16, H - 0.25), (W - 0.6, 0.02, 0.03), mat_orange)

# ---------- Lights ----------
for i in range(0, n, 2):
    y = -2 + i * seg + seg / 2
    ld = bpy.data.lights.new(f"Fill_{i}", 'POINT')
    ld.energy = 150
    ld.color = (0.5, 0.85, 1.0)
    ld.shadow_soft_size = 0.5
    lo = bpy.data.objects.new(f"Fill_{i}", ld)
    lo.location = (0, y, H - 0.5)
    scene.collection.objects.link(lo)

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.005, 0.007, 0.01, 1)
    bg.inputs[1].default_value = 1.0

# ---------- Camera ----------
cd = bpy.data.cameras.new("Cam")
cd.lens = 24
cam = bpy.data.objects.new("Cam", cd)
cam.location = (0.3, -1.0, 1.6)
cam.rotation_euler = (math.radians(89), 0, math.radians(-1.5))
scene.collection.objects.link(cam)
scene.camera = cam

# ---------- Compositor vignette ----------
def set_in(node, names, value, attr=None):
    for nm in names:
        s = node.inputs.get(nm)
        if s is not None:
            try:
                s.default_value = value
                return True
            except Exception:
                pass
    if attr and hasattr(node, attr):
        try:
            setattr(node, attr, value)
            return True
        except Exception:
            pass
    return False

try:
    tree = None
    legacy = False
    if hasattr(scene, "compositing_node_group"):
        tree = bpy.data.node_groups.new("Vignette Comp", 'CompositorNodeTree')
        scene.compositing_node_group = tree
    else:
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        legacy = True
    nodes, links = tree.nodes, tree.links

    rl = nodes.new('CompositorNodeRLayers')
    rl.location = (-600, 200)

    ell = nodes.new('CompositorNodeEllipseMask')
    ell.location = (-600, -150)
    set_in(ell, ["Width"], 0.85, "width")
    set_in(ell, ["Height"], 0.75, "height")
    if not set_in(ell, ["Size"], (0.85, 0.75)):
        pass

    blur = nodes.new('CompositorNodeBlur')
    blur.location = (-350, -150)
    if not set_in(blur, ["Size"], (250.0, 250.0)):
        try:
            blur.size_x = 250
            blur.size_y = 250
        except Exception:
            pass
    try:
        blur.filter_type = 'GAUSS'
    except Exception:
        pass
    links.new(ell.outputs[0], blur.inputs[0])

    # Remap mask so edges darken but don't go fully black
    mr = nodes.new('CompositorNodeMapRange')
    mr.location = (-150, -150)
    set_in(mr, ["From Min"], 0.0)
    set_in(mr, ["From Max"], 1.0)
    set_in(mr, ["To Min"], 0.15)
    set_in(mr, ["To Max"], 1.0)
    links.new(blur.outputs[0], mr.inputs[0])

    # Multiply
    mix = None
    try:
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1.0
        links.new(rl.outputs["Image"], mix.inputs[6])
        links.new(mr.outputs[0], mix.inputs[7])
        mix_out = mix.outputs[2]
    except Exception:
        if mix:
            nodes.remove(mix)
        mix = nodes.new('CompositorNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1.0
        links.new(rl.outputs["Image"], mix.inputs[1])
        links.new(mr.outputs[0], mix.inputs[2])
        mix_out = mix.outputs[0]
    mix.location = (100, 150)

    if legacy:
        comp = nodes.new('CompositorNodeComposite')
        comp.location = (350, 150)
        links.new(mix_out, comp.inputs[0])
    else:
        try:
            tree.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        except Exception:
            pass
        out = nodes.new('NodeGroupOutput')
        out.location = (350, 150)
        links.new(mix_out, out.inputs[0])
except Exception as e:
    print("Compositor setup failed:", e)

scene.frame_start = 1
scene.frame_end = 1
