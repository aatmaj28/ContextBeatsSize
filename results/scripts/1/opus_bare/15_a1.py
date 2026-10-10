import bpy
import math

scene = bpy.context.scene

# ---------- cleanup ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- render settings ----------
try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Punchy'
except Exception:
    pass

# world
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.005, 0.007, 0.012, 1)
    bg.inputs[1].default_value = 1.0

# ---------- materials ----------
def make_mat(name, color, metallic=0.0, rough=0.5, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

mat_wall = make_mat("Wall", (0.08, 0.09, 0.11), 0.8, 0.35)
mat_floor = make_mat("Floor", (0.04, 0.045, 0.05), 0.9, 0.2)
mat_rib = make_mat("Rib", (0.15, 0.16, 0.18), 0.9, 0.3)
mat_panel = make_mat("Panel", (0.03, 0.03, 0.035), 0.5, 0.6)
mat_cyan = make_mat("GlowCyan", (0, 0, 0), 0, 0.5, (0.1, 0.8, 1.0), 25.0)
mat_orange = make_mat("GlowOrange", (0, 0, 0), 0, 0.5, (1.0, 0.35, 0.05), 20.0)
mat_ceil_light = make_mat("CeilLight", (0, 0, 0), 0, 0.5, (0.85, 0.92, 1.0), 8.0)

def box(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o

# ---------- corridor ----------
L = 40.0
W = 4.0
H = 3.5
cy = L / 2 - 2

box("Floor", (0, cy, -0.05), (W, L, 0.1), mat_floor)
box("Ceiling", (0, cy, H + 0.05), (W, L, 0.1), mat_wall)
box("WallL", (-W / 2 - 0.05, cy, H / 2), (0.1, L, H), mat_wall)
box("WallR", (W / 2 + 0.05, cy, H / 2), (0.1, L, H), mat_wall)
box("EndWall", (0, cy + L / 2, H / 2), (W, 0.1, H), mat_panel)
box("EndDoorGlow", (0, cy + L / 2 - 0.06, 1.2), (1.4, 0.02, 2.4), mat_orange)

# floor center grating strip
box("FloorTrim", (0, cy, 0.005), (1.2, L, 0.01), mat_panel)

# light strips along walls
for side in (-1, 1):
    x = side * (W / 2 - 0.02)
    box(f"StripLow_{side}", (x, cy, 0.35), (0.04, L, 0.04), mat_cyan)
    box(f"StripHigh_{side}", (x, cy, H - 0.45), (0.04, L, 0.03), mat_cyan)
    # floor-edge accent
    box(f"FloorEdge_{side}", (side * (W / 2 - 0.25), cy, 0.01), (0.03, L, 0.02), mat_orange)

# ribs / frames and wall panels
y = -1.0
i = 0
while y < cy + L / 2 - 1:
    for side in (-1, 1):
        x = side * (W / 2 - 0.1)
        box(f"RibV_{i}_{side}", (x, y, H / 2), (0.2, 0.3, H), mat_rib)
        # angled corner piece
        c = box(f"RibC_{i}_{side}", (side * (W / 2 - 0.35), y, H - 0.3), (0.7, 0.3, 0.2), mat_rib)
        c.rotation_euler = (0, side * math.radians(35), 0)
        # recessed panel between ribs
        box(f"Panel_{i}_{side}", (side * (W / 2 - 0.04), y + 1.0, 1.6), (0.04, 1.5, 1.6), mat_panel)
    box(f"RibTop_{i}", (0, y, H - 0.1), (W, 0.3, 0.2), mat_rib)
    box(f"CeilLight_{i}", (0, y + 1.0, H - 0.02), (1.0, 1.2, 0.03), mat_ceil_light)
    y += 2.0
    i += 1

# ---------- lights ----------
for k in range(6):
    ly = k * 6.0 + 1
    bpy.ops.object.light_add(type='AREA', location=(0, ly, H - 0.15))
    l = bpy.context.active_object
    l.data.energy = 150
    l.data.size = 1.0
    l.data.color = (0.8, 0.9, 1.0)
    for side in (-1, 1):
        bpy.ops.object.light_add(type='POINT', location=(side * (W / 2 - 0.3), ly + 3, 0.4))
        p = bpy.context.active_object
        p.data.energy = 40
        p.data.color = (0.2, 0.8, 1.0)
        p.data.shadow_soft_size = 0.3

# ---------- camera ----------
bpy.ops.object.camera_add(location=(0.4, -1.5, 1.55))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(88), 0, math.radians(-1.5))
cam.data.lens = 24
scene.camera = cam

# ---------- compositor (glow + vignette) ----------
def set_in(node, names, value, attrs=()):
    for a in attrs:
        if hasattr(node, a):
            try:
                setattr(node, a, value if not isinstance(value, (tuple, list)) else value[0])
                return True
            except Exception:
                pass
    for n in names:
        s = node.inputs.get(n)
        if s is not None:
            try:
                s.default_value = value
                return True
            except Exception:
                try:
                    s.default_value = value[0]
                    return True
                except Exception:
                    pass
    return False

try:
    if hasattr(scene, "compositing_node_group"):
        tree = bpy.data.node_groups.new("VignetteComp", "CompositorNodeTree")
        scene.compositing_node_group = tree
        tree.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        out = tree.nodes.new("NodeGroupOutput")
        out_sock = out.inputs[0]
    else:
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        out = tree.nodes.new("CompositorNodeComposite")
        out_sock = out.inputs["Image"]
    nodes, links = tree.nodes, tree.links

    rl = nodes.new("CompositorNodeRLayers")
    rl.location = (-600, 0)
    out.location = (600, 0)

    # bloom glare
    glare = nodes.new("CompositorNodeGlare")
    glare.location = (-350, 100)
    try:
        glare.glare_type = 'BLOOM'
    except Exception:
        set_in(glare, ["Type"], 'Bloom')
    set_in(glare, ["Threshold"], 1.0)
    set_in(glare, ["Strength"], 0.6)
    links.new(rl.outputs["Image"], glare.inputs["Image"])
    img_out = glare.outputs["Image"]

    # ellipse mask
    ell = nodes.new("CompositorNodeEllipseMask")
    ell.location = (-350, -250)
    if not set_in(ell, ["Size"], (1.15, 1.0)):
        ell.width = 1.15
        ell.height = 1.0
    try:
        ell.inputs.get("Value").default_value = 1.0
    except Exception:
        pass

    blur = nodes.new("CompositorNodeBlur")
    blur.location = (-120, -250)
    if not set_in(blur, ["Size"], (350.0, 350.0)):
        blur.size_x = 350
        blur.size_y = 350
    links.new(ell.outputs[0], blur.inputs[0])

    # mix: black -> image by mask
    try:
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = 'RGBA'
        mix.blend_type = 'MIX'
        mix.inputs["A_Color"].default_value = (0, 0, 0, 1)
        links.new(blur.outputs[0], mix.inputs["Factor_Float"])
        links.new(img_out, mix.inputs["B_Color"])
        mix_out = mix.outputs["Result_Color"]
    except Exception:
        mix = nodes.new("CompositorNodeMixRGB")
        mix.blend_type = 'MIX'
        mix.inputs[1].default_value = (0, 0, 0, 1)
        links.new(blur.outputs[0], mix.inputs[0])
        links.new(img_out, mix.inputs[2])
        mix_out = mix.outputs[0]
    mix.location = (250, 0)
    links.new(mix_out, out_sock)
except Exception as e:
    print("Compositor setup issue:", e)

scene.frame_start = 1
scene.frame_end = 1
