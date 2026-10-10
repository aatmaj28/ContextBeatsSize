import bpy
import math
import random
import mathutils

random.seed(7)
scene = bpy.context.scene

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------- Helpers ----------
def new_principled(name, color, rough=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


# ---------- Table ----------
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.05))
table = bpy.context.active_object
table.name = "Table"
table.scale = (3.0, 1.6, 0.1)
assign(table, new_principled("Wood", (0.25, 0.14, 0.07), rough=0.45))

# ---------- TV body ----------
BODY_Z = 0.85
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, BODY_Z))
body = bpy.context.active_object
body.name = "TV_Body"
body.scale = (1.2, 0.9, 0.8)
bevel = body.modifiers.new("Bevel", "BEVEL")
bevel.width = 0.08
bevel.segments = 4
assign(body, new_principled("Plastic", (0.08, 0.06, 0.05), rough=0.35))

# Front bezel panel (slightly darker frame around the screen)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.44, BODY_Z))
bezel = bpy.context.active_object
bezel.name = "Bezel"
bezel.scale = (1.0, 0.04, 0.78)
assign(bezel, new_principled("Bezel", (0.02, 0.02, 0.02), rough=0.6))

# ---------- Static screen material ----------
scr_mat = bpy.data.materials.new("Static_Screen")
snt = scr_mat.node_tree
snodes = snt.nodes
snodes.clear()
s_out = snodes.new("ShaderNodeOutputMaterial")
s_em = snodes.new("ShaderNodeEmission")
s_ramp = snodes.new("ShaderNodeValToRGB")
s_noise = snodes.new("ShaderNodeTexNoise")

s_noise.noise_dimensions = "4D"
s_noise.inputs["Scale"].default_value = 180.0
s_noise.inputs["Detail"].default_value = 16.0
s_noise.inputs["Roughness"].default_value = 0.65

s_ramp.color_ramp.elements[0].position = 0.25
s_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
s_ramp.color_ramp.elements[1].position = 0.75
s_ramp.color_ramp.elements[1].color = (0.82, 0.95, 0.88, 1.0)

s_em.inputs["Strength"].default_value = 3.5

snt.links.new(s_noise.outputs["Fac"], s_ramp.inputs["Fac"])
snt.links.new(s_ramp.outputs["Color"], s_em.inputs["Color"])
snt.links.new(s_em.outputs["Emission"], s_out.inputs["Surface"])

# Animate the noise seed per frame for flickering static
FRAMES = 48
for f in range(1, FRAMES + 1):
    s_noise.inputs["W"].default_value = random.uniform(0.0, 100.0)
    s_noise.inputs["W"].keyframe_insert("default_value", frame=f)

# Screen plane facing -Y
SCREEN_W, SCREEN_H = 1.5, 1.1
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.47, BODY_Z + 0.02),
                                 rotation=(math.radians(90), 0, 0))
screen = bpy.context.active_object
screen.name = "Screen"
screen.scale = (SCREEN_W, SCREEN_H, 1.0)
assign(screen, scr_mat)

# ---------- Knobs ----------
for x in (0.78, 0.62):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.055, depth=0.08,
        location=(x, -0.48, BODY_Z + 0.55),
        rotation=(math.radians(90), 0, 0))
    knob = bpy.context.active_object
    knob.name = "Knob"
    assign(knob, new_principled("Knob_Metal", (0.5, 0.5, 0.5), rough=0.3, metallic=1.0))

# ---------- Antennas ----------
body_top = BODY_Z + 0.4
for sign in (-1, 1):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.015, depth=1.1,
        location=(sign * 0.35, 0.0, body_top + 0.5),
        rotation=(0, math.radians(-sign * 28), 0))
    ant = bpy.context.active_object
    ant.name = "Antenna"
    assign(ant, new_principled("Antenna_Metal", (0.6, 0.6, 0.6), rough=0.25, metallic=1.0))

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.025, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Lights ----------
bpy.ops.object.light_add(type="AREA", location=(2.8, -3.5, 3.2))
key = bpy.context.active_object
key.name = "Key_Light"
key.data.energy = 250
key.data.size = 3.0

bpy.ops.object.light_add(type="POINT", location=(-2.5, -2.0, 1.5))
fill = bpy.context.active_object
fill.name = "Fill_Light"
fill.data.energy = 60
fill.data.color = (0.6, 0.75, 1.0)

# Soft glow light from the screen onto the table/body
bpy.ops.object.light_add(type="POINT", location=(0.0, -1.2, BODY_Z))
glow = bpy.context.active_object
glow.name = "Screen_Glow_Light"
glow.data.energy = 40
glow.data.color = (0.8, 0.95, 0.9)
glow.data.shadow_soft_size = 0.5

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 60
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
cam_loc = mathutils.Vector((2.4, -6.0, 2.1))
target = mathutils.Vector((0.0, 0.0, BODY_Z + 0.1))
cam_obj.location = cam_loc
cam_obj.rotation_euler = (target - cam_loc).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam_obj

# ---------- Render settings / timeline ----------
scene.frame_start = 1
scene.frame_end = FRAMES
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# ---------- Compositor: glow + film grain ----------
def find_input(node, name, sock_type):
    for s in node.inputs:
        if s.name == name and s.type == sock_type and s.enabled:
            return s
    return None


try:
    ctree = bpy.data.node_groups.new("FilmGrainComp", "CompositorNodeTree")
    scene.compositing_node_group = ctree
    ctree.interface.new_socket(name="Image", in_out="OUTPUT",
                               socket_type="NodeSocketColor")

    c_rlayers = ctree.nodes.new("CompositorNodeRLayers")

    # Bloom-style glow on the bright static
    c_glare = ctree.nodes.new("CompositorNodeGlare")
    try:
        c_glare.inputs["Type"].default_value = "Bloom"
    except Exception:
        pass
    try:
        c_glare.inputs["Threshold"].default_value = 0.6
    except Exception:
        pass

    # Film grain: animated noise overlaid on the image
    c_coords = ctree.nodes.new("CompositorNodeImageCoordinates")
    c_grain = ctree.nodes.new("ShaderNodeTexNoise")
    c_grain.noise_dimensions = "4D"
    c_grain.inputs["Scale"].default_value = 900.0
    c_grain.inputs["Detail"].default_value = 2.0
    for f in range(1, FRAMES + 1):
        c_grain.inputs["W"].default_value = random.uniform(0.0, 100.0)
        c_grain.inputs["W"].keyframe_insert("default_value", frame=f)

    c_mix = ctree.nodes.new("ShaderNodeMix")
    c_mix.data_type = "RGBA"
    c_mix.blend_type = "OVERLAY"
    factor = find_input(c_mix, "Factor", "VALUE")
    if factor:
        factor.default_value = 0.12

    try:
        ctree.links.new(c_coords.outputs["Normalized"],
                        c_grain.inputs["Vector"])
    except Exception:
        pass

    ctree.links.new(c_rlayers.outputs["Image"], c_glare.inputs["Image"])

    mix_a = find_input(c_mix, "A", "RGBA")
    mix_b = find_input(c_mix, "B", "RGBA")
    mix_out = None
    for o in c_mix.outputs:
        if o.name == "Result" and o.type == "RGBA":
            mix_out = o
            break

    ctree.links.new(c_glare.outputs["Image"], mix_a)
    ctree.links.new(c_grain.outputs["Color"], mix_b)

    c_out = ctree.nodes.new("NodeGroupOutput")
    ctree.links.new(mix_out, c_out.inputs["Image"])
except Exception as e:
    print("Compositor setup skipped:", e)
