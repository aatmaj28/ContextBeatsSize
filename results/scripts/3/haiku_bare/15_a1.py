import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene

# ---------- Clear scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0,
                  emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

def box(name, center, size, mat):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = Vector(center)
    return obj

# ---------- Corridor dimensions ----------
L = 30.0      # length along Y
W = 6.0       # width along X
H = 4.0       # height along Z
T = 0.1       # wall thickness

# ---------- Materials ----------
mat_floor = make_material("FloorMetal", (0.08, 0.09, 0.10), roughness=0.25, metallic=0.8)
mat_wall = make_material("WallPanel", (0.12, 0.13, 0.15), roughness=0.55, metallic=0.3)
mat_ceiling = make_material("CeilingDark", (0.05, 0.05, 0.06), roughness=0.7)
mat_panel = make_material("Panel", (0.18, 0.19, 0.21), roughness=0.4, metallic=0.5)
mat_cyan = make_material("GlowCyan", (0.0, 0.8, 1.0), roughness=0.3,
                         emission=(0.0, 0.8, 1.0), emission_strength=25.0)
mat_magenta = make_material("GlowMagenta", (1.0, 0.1, 0.6), roughness=0.3,
                            emission=(1.0, 0.1, 0.6), emission_strength=25.0)
mat_amber = make_material("GlowAmber", (1.0, 0.5, 0.1), roughness=0.3,
                          emission=(1.0, 0.5, 0.1), emission_strength=18.0)

# ---------- Structure ----------
box("Floor", (0, 0, -0.05), (W, L, T), mat_floor)
box("Ceiling", (0, 0, H + 0.05), (W, L, T), mat_ceiling)
box("WallLeft", (-W / 2 - T / 2, 0, H / 2), (T, L, H), mat_wall)
box("WallRight", (W / 2 + T / 2, 0, H / 2), (T, L, H), mat_wall)

# Wall panel seams / sci-fi panels
for side in (-1, 1):
    for i in range(int(L // 3)):
        y = -L / 2 + 1.5 + i * 3.0
        if random.random() < 0.5:
            continue
        z = random.uniform(1.0, 2.8)
        box(f"Panel_{side}_{i}",
            (side * (W / 2 - 0.03), y, z),
            (0.04, random.uniform(1.0, 2.0), random.uniform(0.6, 1.0)),
            mat_panel)

# Door frames at intervals
for i, y in enumerate([-9.0, 0.0, 9.0]):
    for side in (-1, 1):
        box(f"DoorFrame_{i}_{side}", (side * (W / 2 - 0.1), y, H / 2),
            (0.12, 0.25, H), mat_panel)
    box(f"DoorLintel_{i}", (0, y, H - 0.2), (W, 0.25, 0.4), mat_panel)

# ---------- Glowing light strips ----------
strip_y_size = L - 1.0
# Wall strips, high and low, alternating colors
for side in (-1, 1):
    x = side * (W / 2 - 0.06)
    box(f"StripWallHigh_{side}", (x, 0, H - 0.35), (0.04, strip_y_size, 0.07),
        mat_cyan if side < 0 else mat_magenta)
    box(f"StripWallLow_{side}", (x, 0, 0.35), (0.04, strip_y_size, 0.07),
        mat_magenta if side < 0 else mat_cyan)

# Ceiling center strip
box("StripCeiling", (0, 0, H - 0.02), (0.8, strip_y_size, 0.04), mat_amber)

# Floor edge strips
for side in (-1, 1):
    box(f"StripFloor_{side}", (side * (W / 2 - 0.35), 0, 0.01),
        (0.12, strip_y_size, 0.02), mat_cyan)

# ---------- Lighting ----------
# Point lights spaced along the corridor, tinted to match strips
light_spacing = 6.0
count = int(L // light_spacing) + 1
for i in range(count):
    y = -L / 2 + 3.0 + i * light_spacing
    tint = (0.2, 0.8, 1.0) if i % 2 == 0 else (1.0, 0.25, 0.7)
    ld = bpy.data.lights.new(name=f"CorridorLight_{i}", type='POINT')
    ld.energy = 350.0
    ld.color = tint
    ld.shadow_soft_size = 0.5
    lo = bpy.data.objects.new(f"CorridorLight_{i}", ld)
    bpy.context.collection.objects.link(lo)
    lo.location = (0, y, H - 0.6)

# Soft fill from the far end
fill = bpy.data.lights.new(name="FarFill", type='AREA')
fill.energy = 120.0
fill.color = (0.5, 0.6, 1.0)
fill.size = 4.0
fill_obj = bpy.data.objects.new("FarFill", fill)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = (0, L / 2 + 2.0, H * 0.6)
fill_obj.rotation_euler = (math.radians(70), 0, math.radians(180))

# ---------- World ----------
if scene.world is None:
    scene.world = bpy.data.worlds.new("CorridorWorld")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("CorridorCam")
cam_data.lens = 26.0
cam_data.clip_end = 200.0
cam_obj = bpy.data.objects.new("CorridorCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = Vector((0.3, -L / 2 + 2.0, 1.6))
target = Vector((0.0, L / 2, 1.8))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- Render settings (no rendering performed) ----------
scene.frame_start = 1
scene.frame_end = 1

# ---------- Compositor: vignette + glow ----------
if hasattr(scene, "compositing_node_group"):
    tree = scene.compositing_node_group
    if tree is None:
        tree = bpy.data.node_groups.new("CorridorComposite", "CompositorNodeTree")
        scene.compositing_node_group = tree
else:
    scene.use_nodes = True
    tree = scene.node_tree

nodes = tree.nodes
links = tree.links
nodes.clear()

rl = nodes.new("CompositorNodeRLayers")
if hasattr(rl, "scene"):
    rl.scene = scene

glare = nodes.new("CompositorNodeGlare")
try:
    glare.glare_type = 'FOG_GLOW'
    glare.threshold = 0.8
    glare.size = 7
except Exception:
    pass

ellipse = nodes.new("CompositorNodeEllipseMask")
try:
    ellipse.mask_type = 'MULTIPLY'
except Exception:
    pass
for sock_name, val in (("Width", 0.95), ("Height", 0.95), ("X", 0.5), ("Y", 0.5)):
    for s in ellipse.inputs:
        if s.name.lower() == sock_name.lower() and hasattr(s, "default_value"):
            try:
                s.default_value = val
            except Exception:
                pass

blur = nodes.new("CompositorNodeBlur")
try:
    blur.size_x = 200
    blur.size_y = 200
except Exception:
    pass

vignette_mix = nodes.new("CompositorNodeMixRGB")
vignette_mix.blend_type = 'MULTIPLY'
vignette_mix.inputs[0].default_value = 0.7

comp = nodes.new("CompositorNodeComposite")

# Wire: RenderLayers -> Glare -> Vignette(multiply by blurred mask) -> Composite
def out_sock(node, preferred):
    for s in node.outputs:
        if s.name == preferred:
            return s
    return node.outputs[0]

def in_sock(node, idx):
    return node.inputs[idx]

links.new(out_sock(rl, "Image"), glare.inputs["Image"])
links.new(glare.outputs[0], in_sock(vignette_mix, 1))
links.new(out_sock(ellipse, "Mask"), blur.inputs[0])
links.new(blur.outputs[0], in_sock(vignette_mix, 2))
links.new(vignette_mix.outputs[0], comp.inputs["Image"])
