import bpy, math, random

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, metal=0.5, rough=0.4, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

m_wall = mat("Wall", (0.12, 0.13, 0.15), 0.7, 0.35)
m_floor = mat("Floor", (0.05, 0.05, 0.06), 0.8, 0.25)
m_rib = mat("Rib", (0.2, 0.21, 0.24), 0.9, 0.3)
m_cyan = mat("Cyan", (0.0, 0.5, 1.0), 0, 0.5, (0.0, 0.7, 1.0), 25)
m_orange = mat("Orange", (1.0, 0.4, 0.0), 0, 0.5, (1.0, 0.35, 0.05), 15)
m_white = mat("White", (1, 1, 1), 0, 0.5, (0.85, 0.9, 1.0), 12)

def box(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.materials.append(m)
    return o

L = 40.0
W = 4.0
H = 3.5
yc = L / 2 - 5
box("Floor", (0, yc, -0.05), (W, L, 0.1), m_floor)
box("Ceiling", (0, yc, H + 0.05), (W, L, 0.1), m_wall)
box("WallL", (-W / 2 - 0.05, yc, H / 2), (0.1, L, H), m_wall)
box("WallR", (W / 2 + 0.05, yc, H / 2), (0.1, L, H), m_wall)
box("EndWall", (0, L - 5, H / 2), (W, 0.1, H), m_wall)
box("EndLight", (0, L - 5.1, H / 2), (1.2, 0.05, 2.2), m_white)

# Angled lower wall panels
for s in (-1, 1):
    box("LowerPanel", (s * (W / 2 - 0.25), yc, 0.35), (0.12, L, 0.9), m_wall, (0, s * math.radians(-30), 0))
    box("UpperPanel", (s * (W / 2 - 0.25), yc, H - 0.35), (0.12, L, 0.9), m_wall, (0, s * math.radians(30), 0))
    # continuous light strips
    box("StripMid", (s * (W / 2 - 0.02), yc, 1.6), (0.04, L, 0.06), m_cyan)
    box("StripLow", (s * (W / 2 - 0.42), yc, 0.05), (0.06, L, 0.03), m_orange)

# Ceiling light strip
box("CeilStrip", (0, yc, H - 0.01), (0.3, L, 0.03), m_white)

# Ribs / frames
y = -4.0
while y < L - 5:
    for s in (-1, 1):
        box("RibSide", (s * (W / 2 - 0.12), y, H / 2), (0.25, 0.3, H), m_rib)
        box("RibLight", (s * (W / 2 - 0.25), y, H / 2), (0.02, 0.06, H * 0.7), m_cyan)
    box("RibTop", (0, y, H - 0.12), (W, 0.3, 0.25), m_rib)
    box("FloorGrate", (0, y, 0.01), (W * 0.8, 0.05, 0.02), m_orange)
    y += 3.0

# Lights
for i in range(6):
    bpy.ops.object.light_add(type='POINT', location=(0, -2 + i * 6, H - 0.4))
    l = bpy.context.active_object
    l.data.energy = 150
    l.data.color = (0.6, 0.85, 1.0)
    l.data.shadow_soft_size = 0.5

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.002, 0.003, 0.006, 1)

# Camera
bpy.ops.object.camera_add(location=(0.3, -4.5, 1.55), rotation=(math.radians(89), 0, math.radians(-1)))
cam = bpy.context.active_object
cam.data.lens = 22
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
try:
    scene.view_settings.view_transform = 'AgX'
except Exception:
    pass

# Compositor vignette
tree = bpy.data.node_groups.new("Vignette", "CompositorNodeTree")
scene.compositing_node_group = tree
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = tree.nodes.new("CompositorNodeRLayers")
out = tree.nodes.new("NodeGroupOutput")
image_src = rl.outputs["Image"]

# optional glare
try:
    gl = tree.nodes.new("CompositorNodeGlare")
    try:
        gl.inputs["Type"].default_value = "Fog Glow"
    except Exception:
        pass
    try:
        gl.inputs["Threshold"].default_value = 1.0
    except Exception:
        pass
    tree.links.new(gl.inputs["Image"], image_src)
    image_src = gl.outputs["Image"]
except Exception:
    pass

try:
    ell = tree.nodes.new("CompositorNodeEllipseMask")
    try:
        ell.inputs["Size"].default_value = (0.85, 0.75)
    except Exception:
        try:
            ell.width = 0.85
            ell.height = 0.75
        except Exception:
            pass
    blur = tree.nodes.new("CompositorNodeBlur")
    try:
        blur.inputs["Type"].default_value = "Gaussian"
    except Exception:
        pass
    blur.inputs["Size"].default_value = (300, 300)
    mask_out = ell.outputs["Mask"] if "Mask" in ell.outputs else ell.outputs[0]
    tree.links.new(blur.inputs["Image"], mask_out)

    mix = tree.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 0.85
    tree.links.new(mix.inputs[6], image_src)
    tree.links.new(mix.inputs[7], blur.outputs["Image"])
    tree.links.new(out.inputs[0], mix.outputs[2])
except Exception:
    for l in list(tree.links):
        if l.to_node == out:
            tree.links.remove(l)
    tree.links.new(out.inputs[0], image_src)

scene.frame_start = 1
scene.frame_end = 1
