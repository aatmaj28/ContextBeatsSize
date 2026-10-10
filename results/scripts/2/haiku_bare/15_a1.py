import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)

# ---------- Clean scene ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.context.scene
try:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64
except Exception:
    pass

# ---------- Helpers ----------
def make_material(name, color, roughness=0.6, metallic=0.0, emit_color=None, emit_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emit_color is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat

def make_quad(name, corners, mat):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = [bm.verts.new(Vector(c)) for c in corners]
    bm.faces.new(verts)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def make_box(name, center, size, mat):
    """Simple solid box built from six quads (for ribs / panels)."""
    cx, cy, cz = center
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    corners = [
        [(cx-sx, cy-sy, cz-sz), (cx+sx, cy-sy, cz-sz), (cx+sx, cy+sy, cz-sz), (cx-sx, cy+sy, cz-sz)],
        [(cx-sx, cy-sy, cz+sz), (cx+sx, cy-sy, cz+sz), (cx+sx, cy+sy, cz+sz), (cx-sx, cy+sy, cz+sz)],
        [(cx-sx, cy-sy, cz-sz), (cx+sx, cy-sy, cz-sz), (cx+sx, cy-sy, cz+sz), (cx-sx, cy-sy, cz+sz)],
        [(cx-sx, cy+sy, cz-sz), (cx+sx, cy+sy, cz-sz), (cx+sx, cy+sy, cz+sz), (cx-sx, cy+sy, cz+sz)],
        [(cx-sx, cy-sy, cz-sz), (cx-sx, cy+sy, cz-sz), (cx-sx, cy+sy, cz+sz), (cx-sx, cy-sy, cz+sz)],
        [(cx+sx, cy-sy, cz-sz), (cx+sx, cy+sy, cz-sz), (cx+sx, cy+sy, cz+sz), (cx+sx, cy-sy, cz+sz)],
    ]
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for face in corners:
        bm.faces.new([bm.verts.new(Vector(c)) for c in face])
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj

# ---------- Corridor dimensions ----------
W = 4.0     # width  (x from -2 to 2)
H = 3.2     # height (z 0..H)
L = 30.0    # length (y from -15 to 15)
hw, hl = W / 2, L / 2

# ---------- Materials ----------
mat_floor = make_material("FloorMetal", (0.08, 0.09, 0.10), roughness=0.35, metallic=0.8)
mat_wall = make_material("WallPanel", (0.20, 0.22, 0.25), roughness=0.55, metallic=0.4)
mat_ceiling = make_material("CeilingDark", (0.06, 0.06, 0.07), roughness=0.7)
mat_rib = make_material("RibMetal", (0.16, 0.17, 0.19), roughness=0.4, metallic=0.9)
mat_glow_cyan = make_material("GlowCyan", (0.0, 0.8, 1.0), roughness=0.2,
                              emit_color=(0.0, 0.9, 1.0), emit_strength=25.0)
mat_glow_magenta = make_material("GlowMagenta", (1.0, 0.1, 0.6), roughness=0.2,
                                 emit_color=(1.0, 0.1, 0.6), emit_strength=20.0)
mat_glow_floor = make_material("GlowFloor", (0.2, 0.9, 1.0), roughness=0.2,
                               emit_color=(0.2, 0.9, 1.0), emit_strength=12.0)

# ---------- Structure ----------
make_quad("Floor", [(-hw, -hl, 0), (hw, -hl, 0), (hw, hl, 0), (-hw, hl, 0)], mat_floor)
make_quad("Ceiling", [(-hw, -hl, H), (hw, -hl, H), (hw, hl, H), (-hw, hl, H)], mat_ceiling)
make_quad("WallLeft", [(-hw, -hl, 0), (-hw, hl, 0), (-hw, hl, H), (-hw, -hl, H)], mat_wall)
make_quad("WallRight", [(hw, -hl, 0), (hw, hl, 0), (hw, hl, H), (hw, -hl, H)], mat_wall)
make_quad("EndFar", [(-hw, hl, 0), (hw, hl, 0), (hw, hl, H), (-hw, hl, H)], mat_wall)
make_quad("EndNear", [(-hw, -hl, 0), (hw, -hl, 0), (hw, -hl, H), (-hw, -hl, H)], mat_wall)

# Ribs across the ceiling every 5 m
y = -hl + 2.5
while y < hl:
    make_box(f"RibTop_{y:.1f}", (0, y, H - 0.12), (W, 0.25, 0.24), mat_rib)
    # Wall pilasters
    make_box(f"PilL_{y:.1f}", (-hw + 0.1, y, H / 2), (0.2, 0.3, H), mat_rib)
    make_box(f"PilR_{y:.1f}", (hw - 0.1, y, H / 2), (0.2, 0.3, H), mat_rib)
    y += 5.0

# Floor center walkway panel
make_box("Walkway", (0, 0, 0.02), (1.6, L, 0.04), mat_rib)

# ---------- Glowing light strips ----------
inset = 0.01
strip_h = 0.08
for side, x in (("L", -hw + inset), ("R", hw - inset)):
    # Ceiling-wall corner strips
    z0 = H - 0.25
    z1 = H - 0.17
    make_quad(f"StripWall_{side}",
              [(x, -hl + 0.2, z0), (x, hl - 0.2, z0), (x, hl - 0.2, z1), (x, -hl + 0.2, z1)],
              mat_glow_cyan)
    # Floor edge strips
    fx = -hw * 0.6 if side == "L" else hw * 0.6
    fx0, fx1 = (fx - 0.06, fx + 0.06)
    make_quad(f"StripFloor_{side}",
              [(fx0, -hl + 0.2, 0.005), (fx1, -hl + 0.2, 0.005),
               (fx1, hl - 0.2, 0.005), (fx0, hl - 0.2, 0.005)],
              mat_glow_floor)

# Magenta accent strip across far end ceiling
make_quad("AccentFar",
          [(-hw + 0.2, hl - 0.02, H - 0.5), (hw - 0.2, hl - 0.02, H - 0.5),
           (hw - 0.2, hl - 0.02, H - 0.42), (-hw + 0.2, hl - 0.02, H - 0.42)],
          mat_glow_magenta)

# Ceiling light bars (emissive) down the center
for yy in range(-12, 13, 6):
    make_quad(f"CeilBar_{yy}",
              [(-0.4, yy - 0.8, H - 0.005), (0.4, yy - 0.8, H - 0.005),
               (0.4, yy + 0.8, H - 0.005), (-0.4, yy + 0.8, H - 0.005)],
              mat_glow_cyan)

# ---------- Real lights (to light the surfaces) ----------
def add_area_light(name, loc, rot, energy, color, size):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.color = color
    ld.size = size
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.collection.objects.link(ob)
    return ob

def add_point_light(name, loc, energy, color, radius=0.2):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    bpy.context.collection.objects.link(ob)
    return ob

for yy in (-10.0, -3.0, 4.0, 11.0):
    add_point_light(f"CyanPt_{yy}", (0, yy, H - 0.4), 180.0, (0.4, 0.9, 1.0), 0.3)

add_point_light("MagentaFar", (0, 13.5, 1.6), 250.0, (1.0, 0.25, 0.7), 0.3)
add_point_light("FillNear", (0, -12.0, 1.4), 60.0, (0.5, 0.6, 0.8), 0.3)

# ---------- Props: a few crates and a hovering orb ----------
crate_mat = make_material("Crate", (0.25, 0.22, 0.18), roughness=0.7, metallic=0.1)
make_box("Crate1", (-1.1, 8.0, 0.4), (0.8, 0.8, 0.8), crate_mat)
make_box("Crate2", (-1.1, 8.0, 1.2), (0.6, 0.6, 0.6), crate_mat)
make_box("Crate3", (1.0, -6.0, 0.35), (0.7, 0.7, 0.7), crate_mat)

orb_mat = make_material("Orb", (0.9, 0.95, 1.0), roughness=0.05, metallic=0.0,
                        emit_color=(0.5, 0.9, 1.0), emit_strength=6.0)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(0.0, 2.0, 1.6))
orb = bpy.context.active_object
orb.name = "FloatingOrb"
orb.data.materials.append(orb_mat)
bpy.ops.object.shade_smooth()

# ---------- World ----------
world = bpy.data.worlds.new("CorridorWorld")
world.use_nodes = True
wbg = world.node_tree.nodes["Background"]
wbg.inputs["Color"].default_value = (0.01, 0.015, 0.03, 1.0)
wbg.inputs["Strength"].default_value = 0.2
scene.world = world

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("CorridorCam")
cam_data.lens = 24.0
cam_data.clip_end = 100.0
cam = bpy.data.objects.new("CorridorCam", cam_data)
cam.location = (0.0, -12.5, 1.5)
cam.rotation_euler = (math.radians(88), 0.0, 0.0)
bpy.context.collection.objects.link(cam)
scene.camera = cam

# ---------- Animation range (static frame) ----------
scene.frame_start = 1
scene.frame_end = 1

# ---------- Compositor vignette ----------
def set_socket_or_prop(node, name, value):
    try:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return
    except Exception:
        pass
    try:
        setattr(node, name.lower().replace(" ", "_"), value)
    except Exception:
        pass

try:
    if hasattr(scene, "compositing_node_group"):
        comp_tree = bpy.data.node_groups.new("CorridorVignette", "CompositorNodeTree")
        scene.compositing_node_group = comp_tree
    else:
        scene.use_nodes = True
        comp_tree = scene.node_tree
    comp_tree.nodes.clear()

    rl = comp_tree.nodes.new("CompositorNodeRLayers")
    ellipse = comp_tree.nodes.new("CompositorNodeEllipseMask")
    set_socket_or_prop(ellipse, "Width", 0.85)
    set_socket_or_prop(ellipse, "Height", 0.85)
    set_socket_or_prop(ellipse, "X", 0.5)
    set_socket_or_prop(ellipse, "Y", 0.5)

    blur = comp_tree.nodes.new("CompositorNodeBlur")
    set_socket_or_prop(blur, "Size X", 250)
    set_socket_or_prop(blur, "Size Y", 250)
    try:
        blur.size_x = 250
        blur.size_y = 250
    except Exception:
        pass

    mix = comp_tree.nodes.new("CompositorNodeMixRGB")
    try:
        mix.blend_type = 'MULTIPLY'
    except Exception:
        pass
    mix.inputs[0].default_value = 1.0

    comp_out = comp_tree.nodes.new("CompositorNodeComposite")

    comp_tree.links.new(rl.outputs["Image"], mix.inputs[1])
    comp_tree.links.new(ellipse.outputs[0], blur.inputs[0])
    comp_tree.links.new(blur.outputs[0], mix.inputs[2])
    comp_tree.links.new(mix.outputs[0], comp_out.inputs["Image"])
except Exception as e:
    print("Compositor setup skipped:", e)
