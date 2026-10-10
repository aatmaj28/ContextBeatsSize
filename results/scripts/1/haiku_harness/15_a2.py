import bpy
import math
import random

random.seed(7)

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100

# ---------- Helpers ----------
def make_material(name, color, roughness=0.4, metallic=0.0,
                  emit_color=None, emit_strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emit_color is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat

def add_box(name, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    return obj

# ---------- Materials ----------
floor_mat = make_material("FloorMetal", (0.08, 0.09, 0.1), roughness=0.25, metallic=0.9)
wall_mat = make_material("WallPanel", (0.15, 0.17, 0.2), roughness=0.5, metallic=0.4)
ceiling_mat = make_material("CeilingDark", (0.05, 0.05, 0.06), roughness=0.7)
cyan_glow = make_material("CyanGlow", (0.0, 0.8, 1.0), emit_color=(0.0, 0.85, 1.0), emit_strength=25.0)
magenta_glow = make_material("MagentaGlow", (1.0, 0.1, 0.6), emit_color=(1.0, 0.1, 0.6), emit_strength=20.0)
amber_glow = make_material("AmberGlow", (1.0, 0.5, 0.1), emit_color=(1.0, 0.5, 0.1), emit_strength=18.0)

# ---------- Corridor geometry ----------
CORRIDOR_HALF_W = 3.0
CORRIDOR_H = 4.0
CORRIDOR_HALF_L = 15.0

add_box("Floor", (0, 0, -0.1), (CORRIDOR_HALF_W + 0.2, CORRIDOR_HALF_L + 0.2, 0.2), floor_mat)
add_box("Ceiling", (0, 0, CORRIDOR_H + 0.1), (CORRIDOR_HALF_W + 0.2, CORRIDOR_HALF_L + 0.2, 0.2), ceiling_mat)
add_box("WallLeft", (-CORRIDOR_HALF_W - 0.1, 0, CORRIDOR_H / 2), (0.2, CORRIDOR_HALF_L + 0.2, CORRIDOR_H / 2), wall_mat)
add_box("WallRight", (CORRIDOR_HALF_W + 0.1, 0, CORRIDOR_H / 2), (0.2, CORRIDOR_HALF_L + 0.2, CORRIDOR_H / 2), wall_mat)

# Wall panel seams / ribs for detail
for i in range(-14, 15, 4):
    y = i + 0.5
    add_box(f"RibL_{i}", (-CORRIDOR_HALF_W + 0.05, y, CORRIDOR_H / 2),
            (0.06, 0.08, CORRIDOR_H / 2 - 0.05), wall_mat)
    add_box(f"RibR_{i}", (CORRIDOR_HALF_W - 0.05, y, CORRIDOR_H / 2),
            (0.06, 0.08, CORRIDOR_H / 2 - 0.05), wall_mat)

# ---------- Glowing light strips ----------
strip_len = CORRIDOR_HALF_L * 2 - 1.0
inset = 0.02

# Ceiling strips (two parallel)
for x in (-1.4, 1.4):
    add_box(f"CeilStrip_{x}", (x, 0, CORRIDOR_H - 0.02),
            (0.12, strip_len / 2, 0.02), cyan_glow)

# Wall strips at mid-height on both walls
for side, mat in ((-1, cyan_glow), (1, magenta_glow)):
    add_box(f"WallStrip_hi_{side}", (side * (CORRIDOR_HALF_W - inset), 0, 3.1),
            (0.03, strip_len / 2, 0.05), mat)
    add_box(f"WallStrip_lo_{side}", (side * (CORRIDOR_HALF_W - inset), 0, 0.6),
            (0.03, strip_len / 2, 0.05), amber_glow if side > 0 else cyan_glow)

# Floor edge strips
for side in (-1, 1):
    add_box(f"FloorStrip_{side}", (side * (CORRIDOR_HALF_W - 0.25), 0, 0.02),
            (0.05, strip_len / 2, 0.02), magenta_glow if side < 0 else cyan_glow)

# Pulsing wall light pads at intervals (adds visual accents)
for y in range(-12, 13, 6):
    for side in (-1, 1):
        mat = random.choice([cyan_glow, magenta_glow, amber_glow])
        add_box(f"Pad_{y}_{side}", (side * (CORRIDOR_HALF_W - inset), y, 2.0),
                (0.02, 0.4, 0.6), mat)

# ---------- Lights (so surfaces receive illumination) ----------
def add_point_light(name, location, color, energy):
    light_data = bpy.data.lights.new(name, type='POINT')
    light_data.color = color
    light_data.energy = energy
    light_data.shadow_soft_size = 0.3
    obj = bpy.data.objects.new(name, light_data)
    obj.location = location
    scene.collection.objects.link(obj)
    return obj

for i, y in enumerate(range(-12, 13, 6)):
    col = (0.2, 0.9, 1.0) if i % 2 == 0 else (1.0, 0.3, 0.7)
    add_point_light(f"CeilLight_{i}", (0, y, CORRIDOR_H - 0.5), col, 300.0)

# Dim fill light from the far end
add_point_light("FarGlow", (0, 14, 1.5), (0.3, 0.6, 1.0), 400.0)

# ---------- World ----------
world = bpy.data.worlds.new("CorridorWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.015, 0.025, 1.0)
    bg.inputs["Strength"].default_value = 0.3

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("CorridorCam")
cam_data.lens = 26
cam_obj = bpy.data.objects.new("CorridorCam", cam_data)
cam_obj.location = (0.4, -13.0, 1.7)
cam_obj.rotation_euler = (math.radians(88), 0.0, 0.0)  # looks down the corridor (+Y)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# ---------- Compositor: vignette ----------
comp_tree = bpy.data.node_groups.new("VignetteComp", "CompositorNodeTree")
scene.compositing_node_group = comp_tree

def find_sock(sockets, name, typ=None):
    for s in sockets:
        if s.name == name and s.enabled and (typ is None or s.type == typ):
            return s
    raise KeyError(f"Socket {name} not found")

def pick_output(node, preferred, fallback_type='VECTOR'):
    # Try known names first
    for n in preferred:
        for s in node.outputs:
            if s.name == n and s.enabled:
                return s
    # Fall back to a non-integer vector-like output
    for s in node.outputs:
        if s.enabled and s.type == fallback_type and "Pixel" not in s.name:
            return s
    # Last resort: first enabled output
    for s in node.outputs:
        if s.enabled:
            return s
    raise KeyError("No usable output found on node")

# Output interface first so the group output node picks up its socket
comp_tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")

rlayers = comp_tree.nodes.new("CompositorNodeRLayers")
rlayers.location = (-900, 0)

coords = comp_tree.nodes.new("CompositorNodeImageCoordinates")
coords.location = (-900, -300)

sub = comp_tree.nodes.new("ShaderNodeVectorMath")
sub.operation = 'SUBTRACT'
sub.location = (-650, -300)
sub.inputs[1].default_value = (0.5, 0.5, 0.0)

length_node = comp_tree.nodes.new("ShaderNodeVectorMath")
length_node.operation = 'LENGTH'
length_node.location = (-450, -300)

map_range = comp_tree.nodes.new("ShaderNodeMapRange")
map_range.location = (-250, -300)
map_range.clamp = True
map_range.inputs["From Min"].default_value = 0.3
map_range.inputs["From Max"].default_value = 0.8
map_range.inputs["To Min"].default_value = 1.0
map_range.inputs["To Max"].default_value = 0.25

mix = comp_tree.nodes.new("ShaderNodeMix")
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.location = (0, 0)
find_sock(mix.inputs, "Factor").default_value = 1.0

out_node = comp_tree.nodes.new("NodeGroupOutput")
out_node.location = (250, 0)

# Links
coord_out = pick_output(coords, ["UV", "Normalized", "Coordinates"])
comp_tree.links.new(coord_out, sub.inputs[0])
comp_tree.links.new(sub.outputs[0], length_node.inputs[0])
comp_tree.links.new(length_node.outputs["Value"], map_range.inputs["Value"])

mix_a = find_sock(mix.inputs, "A", 'RGBA')
mix_b = find_sock(mix.inputs, "B", 'RGBA')
mix_out = find_sock(mix.outputs, "Result", 'RGBA')
image_out = pick_output(rlayers, ["Image", "Combined"], fallback_type='RGBA')

comp_tree.links.new(image_out, mix_a)
comp_tree.links.new(map_range.outputs["Result"], mix_b)
comp_tree.links.new(mix_out, out_node.inputs[0])
