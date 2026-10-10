import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clean scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 1

# ---------- Helpers ----------
def make_material(name, base_color, roughness=0.5, metallic=0.0,
                  emit_color=None, emit_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emit_color is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat

def add_box(bm, center, size):
    """Adds an axis-aligned box to the bmesh."""
    res = bmesh.ops.create_cube(bm, size=1.0)
    for v in res["verts"]:
        v.co = Vector((
            v.co.x * size[0] + center[0],
            v.co.y * size[1] + center[1],
            v.co.z * size[2] + center[2],
        ))

def bmesh_to_object(bm, name, material):
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj

# ---------- Materials ----------
hull_mat = make_material("HullMetal", (0.12, 0.13, 0.15), roughness=0.45, metallic=0.8)
floor_mat = make_material("FloorGrating", (0.05, 0.05, 0.06), roughness=0.7, metallic=0.6)
panel_mat = make_material("Panel", (0.25, 0.27, 0.30), roughness=0.35, metallic=0.5)
strip_cyan = make_material("StripCyan", (0.0, 0.8, 1.0), roughness=0.2,
                           emit_color=(0.0, 0.8, 1.0), emit_strength=25.0)
strip_orange = make_material("StripOrange", (1.0, 0.4, 0.05), roughness=0.2,
                             emit_color=(1.0, 0.4, 0.05), emit_strength=18.0)

# ---------- Corridor shell (inward-facing box) ----------
CORR_W = 4.0    # width  (X)
CORR_H = 3.0    # height (Z)
CORR_L = 32.0   # length (Y)
Y_START = -CORR_L / 2
Y_END = CORR_L / 2

bm = bmesh.new()
add_box(bm, (0, 0, CORR_H / 2), (CORR_W, CORR_L, CORR_H))
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
corridor = bmesh_to_object(bm, "CorridorShell", hull_mat)

# ---------- Floor grating and wall panels ----------
bm = bmesh.new()
# Raised floor walkway
add_box(bm, (0, 0, 0.05), (CORR_W * 0.6, CORR_L, 0.1))
# Floor side rails
for sx in (-1, 1):
    add_box(bm, (sx * CORR_W * 0.5 * 0.8, 0, 0.12), (0.15, CORR_L, 0.25))
floor_obj = bmesh_to_object(bm, "FloorDetail", floor_mat)

bm = bmesh.new()
# Vertical ribs on walls every 4 m
y = Y_START + 2.0
while y < Y_END - 1.0:
    for sx in (-1, 1):
        add_box(bm, (sx * (CORR_W / 2 - 0.08), y, CORR_H / 2), (0.16, 0.25, CORR_H * 0.95))
    # Ceiling cross beam
    add_box(bm, (0, y, CORR_H - 0.12), (CORR_W, 0.3, 0.2))
    y += 4.0
panel_obj = bmesh_to_object(bm, "WallRibs", panel_mat)

# ---------- Glowing light strips ----------
bm = bmesh.new()
# Ceiling strips (cyan), two lines
for sx in (-0.9, 0.9):
    add_box(bm, (sx, 0, CORR_H - 0.06), (0.12, CORR_L - 1.0, 0.04))
# Wall strips at mid-height (orange) on both walls
for sx in (-1, 1):
    add_box(bm, (sx * (CORR_W / 2 - 0.02), 0, 1.2), (0.04, CORR_L - 1.0, 0.08))
cyan_strips = bmesh_to_object(bm, "CyanStrips", strip_cyan)

# Low floor strips (orange) for accent
bm = bmesh.new()
for sx in (-1, 1):
    add_box(bm, (sx * CORR_W * 0.3, 0, 0.13), (0.06, CORR_L - 2.0, 0.02))
orange_strips = bmesh_to_object(bm, "FloorStrips", strip_orange)

# ---------- Lights ----------
# Point lights along the ceiling for actual illumination
for i in range(7):
    y = Y_START + 3.0 + i * (CORR_L - 6.0) / 6
    ld = bpy.data.lights.new(f"CeilingLight{i}", type='POINT')
    ld.energy = 250.0
    ld.color = (0.4, 0.85, 1.0)
    ld.shadow_soft_size = 0.3
    lo = bpy.data.objects.new(f"CeilingLight{i}", ld)
    lo.location = (0, y, CORR_H - 0.3)
    bpy.context.collection.objects.link(lo)

# Warm accent lights near the floor
for i, y in enumerate((-8.0, 0.0, 8.0)):
    ld = bpy.data.lights.new(f"AccentLight{i}", type='POINT')
    ld.energy = 60.0
    ld.color = (1.0, 0.5, 0.2)
    ld.shadow_soft_size = 0.2
    lo = bpy.data.objects.new(f"AccentLight{i}", ld)
    lo.location = (-CORR_W * 0.3, y, 0.4)
    bpy.context.collection.objects.link(lo)

# Faint overall fill so geometry reads clearly
sun_data = bpy.data.lights.new("FillArea", type='AREA')
sun_data.energy = 40.0
sun_data.size = 6.0
sun_data.color = (0.6, 0.7, 1.0)
sun_obj = bpy.data.objects.new("FillArea", sun_data)
sun_obj.location = (0, -6.0, CORR_H + 1.0)
sun_obj.rotation_euler = (0.0, 0.0, 0.0)
bpy.context.collection.objects.link(sun_obj)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("CorridorCam")
cam_data.lens = 28.0
cam_data.clip_end = 100.0
cam_obj = bpy.data.objects.new("CorridorCam", cam_data)
bpy.context.collection.objects.link(cam_obj)

cam_pos = Vector((0.0, Y_START + 2.5, 1.5))
look_at = Vector((0.0, Y_END - 4.0, 1.4))
cam_obj.location = cam_pos
direction = (look_at - cam_pos).normalized()
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- World ----------
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.015, 0.02, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Render resolution ----------
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100

# ---------- Compositor: vignette ----------
scene.use_nodes = True
tree = getattr(scene, "node_tree", None)
if tree is None and hasattr(scene, "compositing_node_group"):
    tree = bpy.data.node_groups.new("CompositorVignette", "CompositorNodeTree")
    scene.compositing_node_group = tree

if tree is not None:
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    rl = nodes.new("CompositorNodeRLayers")
    rl.location = (-600, 0)

    ellipse = nodes.new("CompositorNodeEllipseMask")
    ellipse.location = (-600, -300)
    try:
        ellipse.mask_type = 'ELLIPSE'
        ellipse.x = 0.5
        ellipse.y = 0.5
        ellipse.width = 0.75
        ellipse.height = 0.75
    except Exception:
        pass

    blur = nodes.new("CompositorNodeBlur")
    blur.location = (-350, -300)
    try:
        blur.filter_type = 'GAUSS'
        blur.size_x = 300
        blur.size_y = 300
    except Exception:
        pass

    mix = nodes.new("CompositorNodeMixRGB")
    mix.location = (-100, 0)
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1.0

    comp = nodes.new("CompositorNodeComposite")
    comp.location = (150, 0)

    links.new(ellipse.outputs[0], blur.inputs[0])
    links.new(rl.outputs["Image"], mix.inputs[1])
    links.new(blur.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], comp.inputs["Image"])
