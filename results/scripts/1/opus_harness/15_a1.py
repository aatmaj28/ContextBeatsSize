import bpy
import math

scene = bpy.context.scene

# Clean scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

# ---------- Materials ----------
def make_mat(name, color, metallic=0.0, rough=0.5, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    return m

mat_wall = make_mat("Wall", (0.12, 0.13, 0.15), 0.8, 0.35)
mat_floor = make_mat("Floor", (0.05, 0.05, 0.06), 0.9, 0.25)
mat_rib = make_mat("Rib", (0.2, 0.21, 0.24), 0.9, 0.3)
mat_cyan = make_mat("CyanGlow", (0.0, 0.6, 1.0), emit=(0.1, 0.7, 1.0), strength=25.0)
mat_orange = make_mat("OrangeGlow", (1.0, 0.4, 0.05), emit=(1.0, 0.35, 0.05), strength=15.0)

def box(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.materials.append(mat)
    return o

L = 40.0
W = 4.0
H = 3.0
cy = L / 2

# Shell
box("Floor", (0, cy, -0.05), (W, L, 0.1), mat_floor)
box("Ceiling", (0, cy, H + 0.05), (W, L, 0.1), mat_wall)
box("WallL", (-W / 2 - 0.05, cy, H / 2), (0.1, L, H), mat_wall)
box("WallR", (W / 2 + 0.05, cy, H / 2), (0.1, L, H), mat_wall)
box("EndWall", (0, L + 0.05, H / 2), (W, 0.1, H), mat_wall)

# Ribs / frames
y = 1.0
i = 0
while y < L:
    box(f"RibL{i}", (-W / 2 + 0.1, y, H / 2), (0.2, 0.3, H), mat_rib)
    box(f"RibR{i}", (W / 2 - 0.1, y, H / 2), (0.2, 0.3, H), mat_rib)
    box(f"RibT{i}", (0, y, H - 0.1), (W, 0.3, 0.2), mat_rib)
    # angled corner braces
    for s in (-1, 1):
        b = box(f"Brace{i}_{s}", (s * (W / 2 - 0.3), y, H - 0.3), (0.5, 0.25, 0.15), mat_rib)
        b.rotation_euler = (0, s * math.radians(45), 0)
    # wall panels between ribs
    for s in (-1, 1):
        box(f"Panel{i}_{s}", (s * (W / 2 - 0.04), y + 1.25, 1.3), (0.08, 2.0, 1.4), mat_rib)
    y += 2.5
    i += 1

# Light strips
for s in (-1, 1):
    box(f"StripLow{s}", (s * (W / 2 - 0.06), cy, 0.35), (0.04, L, 0.05), mat_cyan)
    box(f"StripHigh{s}", (s * (W / 2 - 0.06), cy, 2.35), (0.04, L, 0.05), mat_cyan)
    box(f"FloorStrip{s}", (s * 1.4, cy, 0.005), (0.05, L, 0.02), mat_orange)
box("CeilStrip", (0, cy, H - 0.01), (0.15, L, 0.03), mat_cyan)
box("EndLight", (0, L - 0.01, 1.5), (1.2, 0.04, 2.2), mat_orange)

# Extra point lights for fill
for k in range(6):
    bpy.ops.object.light_add(type='POINT', location=(0, 3 + k * 6.5, 2.4))
    l = bpy.context.active_object
    l.data.energy = 150
    l.data.color = (0.5, 0.8, 1.0)

# World
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.006, 0.01, 1)

# Camera
bpy.ops.object.camera_add(location=(0.4, 0.3, 1.5), rotation=(math.radians(88), 0, math.radians(-3)))
cam = bpy.context.active_object
cam.data.lens = 24
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# ---------- Compositor vignette ----------
def set_in(node, name, val):
    try:
        if name in node.inputs:
            node.inputs[name].default_value = val
            return True
    except Exception:
        pass
    return False

tree = bpy.data.node_groups.new("VignetteComp", "CompositorNodeTree")
scene.compositing_node_group = tree
nodes, links = tree.nodes, tree.links

rl = nodes.new("CompositorNodeRLayers")
rl.location = (-600, 0)

ell = nodes.new("CompositorNodeEllipseMask")
ell.location = (-600, -300)
if not set_in(ell, "Size", (0.85, 0.75)):
    try:
        ell.width = 0.85
        ell.height = 0.75
    except Exception:
        pass
set_in(ell, "Value", 1.0)
set_in(ell, "Mask", 0.0)

blur = nodes.new("CompositorNodeBlur")
blur.location = (-350, -300)
set_in(blur, "Type", "Gaussian")
if not set_in(blur, "Size", (300, 300)):
    set_in(blur, "Size", 300)

mix = nodes.new("ShaderNodeMix")
mix.location = (-100, 0)
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.inputs[0].default_value = 1.0

out = nodes.new("NodeGroupOutput")
out.location = (150, 0)
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")

links.new(blur.inputs["Image"], ell.outputs[0])
links.new(mix.inputs[6], rl.outputs["Image"])
links.new(mix.inputs[7], blur.outputs[0])
links.new(out.inputs[0], mix.outputs[2])
