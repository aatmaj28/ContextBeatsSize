import bpy
import math
import random
from mathutils import Vector

random.seed(7)

# ---------------------------------------------------------------
# Clear the scene
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

scene = bpy.context.scene
FRAME_START, FRAME_END = 1, 96
scene.frame_start = FRAME_START
scene.frame_end = FRAME_END
scene.frame_set(FRAME_START)

# Render engine (configured only, not rendered here)
try:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64
except Exception:
    pass


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def make_principled(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_driver(socket, index, expression):
    """Drive one component of a socket's vector default_value with a frame expression."""
    fc = socket.driver_add("default_value", index)
    if isinstance(fc, (list, tuple)):
        fc = fc[0]
    drv = fc.driver
    drv.type = 'SCRIPTED'
    drv.expression = expression
    return fc


def link_obj(obj, collection):
    collection.objects.link(obj)
    return obj


col = bpy.context.collection

# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
wood_mat = make_principled("TV_Casing", (0.10, 0.06, 0.035), roughness=0.45)
metal_mat = make_principled("TV_Metal", (0.5, 0.5, 0.52), roughness=0.25, metallic=1.0)
dark_mat = make_principled("TV_Dark", (0.02, 0.02, 0.02), roughness=0.6)
floor_mat = make_principled("Floor", (0.25, 0.23, 0.22), roughness=0.8)

# Glowing static screen material
screen_mat = bpy.data.materials.new("Static_Screen")
sn = screen_mat.node_tree
sn.nodes.clear()
s_out = sn.nodes.new("ShaderNodeOutputMaterial")
s_emit = sn.nodes.new("ShaderNodeEmission")
s_ramp = sn.nodes.new("ShaderNodeValToRGB")
s_noise = sn.nodes.new("ShaderNodeTexNoise")
s_noise.inputs["Scale"].default_value = 260.0
s_noise.inputs["Detail"].default_value = 2.0
s_noise.inputs["Roughness"].default_value = 0.7
s_noise.inputs["Distortion"].default_value = 0.0
s_noise.location = (-600, 0)
s_ramp.location = (-300, 0)
s_emit.location = (0, 0)
s_out.location = (250, 0)

# Ramp: dark blue-ish to bright cyan-white
s_ramp.color_ramp.elements[0].position = 0.25
s_ramp.color_ramp.elements[0].color = (0.01, 0.02, 0.05, 1.0)
s_ramp.color_ramp.elements[1].position = 0.85
s_ramp.color_ramp.elements[1].color = (0.75, 0.9, 1.0, 1.0)

sn.links.new(s_noise.outputs["Fac"], s_ramp.inputs["Fac"])
sn.links.new(s_ramp.outputs["Color"], s_emit.inputs["Color"])
sn.links.new(s_emit.outputs["Emission"], s_out.inputs["Surface"])
s_emit.inputs["Strength"].default_value = 6.0

# Animate static by driving the noise's Vector input (always present,
# independent of the noise dimensionality setting).
add_driver(s_noise.inputs["Vector"], 0, "frame * 13.7")
add_driver(s_noise.inputs["Vector"], 1, "frame * 3.1")

# ---------------------------------------------------------------
# TV Geometry
# ---------------------------------------------------------------
# Main casing
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 1.0))
casing = bpy.context.active_object
casing.name = "TV_Casing"
casing.scale = (1.0, 0.8, 0.8)
casing.data.materials.append(wood_mat)
bevel = casing.modifiers.new("Bevel", 'BEVEL')
bevel.width = 0.07
bevel.segments = 4
bpy.ops.object.shade_smooth()

# Screen bezel (dark inset ring as a thin box in front)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.79, 1.05))
bezel = bpy.context.active_object
bezel.name = "TV_Bezel"
bezel.scale = (0.9, 0.03, 0.72)
bezel.data.materials.append(dark_mat)

# Screen (glowing static)
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, -0.80, 1.05))
screen = bpy.context.active_object
screen.name = "TV_Screen"
screen.rotation_euler = (math.radians(90), 0, 0)
screen.scale = (0.72, 0.55, 1.0)
screen.data.materials.append(screen_mat)

# Stand / base
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0.1))
stand = bpy.context.active_object
stand.name = "TV_Stand"
stand.scale = (0.9, 0.6, 0.1)
stand.data.materials.append(dark_mat)

# Antennas (V shape)
for side, sign in (("L", -1), ("R", 1)):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.018, depth=1.3,
        location=(sign * 0.25, 0.0, 2.0 + 0.55),
    )
    ant = bpy.context.active_object
    ant.name = f"TV_Antenna_{side}"
    ant.rotation_euler = (0, math.radians(-sign * 25), 0)
    ant.data.materials.append(metal_mat)
    # Tip ball
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=0.035,
        location=(sign * 0.25 + sign * 0.33, 0.0, 2.0 + 0.55 + 0.6),
    )
    tip = bpy.context.active_object
    tip.name = f"TV_AntennaTip_{side}"
    tip.data.materials.append(metal_mat)

# Control knobs on the right side of the front face
for i, z in enumerate((1.45, 0.65)):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.065, depth=0.08,
        location=(0.72, -0.84, z),
    )
    knob = bpy.context.active_object
    knob.name = f"TV_Knob_{i}"
    knob.rotation_euler = (math.radians(90), 0, 0)
    knob.data.materials.append(metal_mat)

# Speaker grille slots on the left side of the face
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.72, -0.81, 0.35 + i * 0.12))
    slot = bpy.context.active_object
    slot.name = f"TV_Grille_{i}"
    slot.scale = (0.22, 0.02, 0.012)
    slot.data.materials.append(dark_mat)

# Floor
bpy.ops.mesh.primitive_plane_add(size=30.0, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
bpy.ops.object.light_add(type='AREA', location=(2.5, -3.5, 4.0))
key = bpy.context.active_object
key.name = "Key_Light"
key.data.energy = 250
key.data.size = 2.5
key.data.color = (1.0, 0.95, 0.9)

bpy.ops.object.light_add(type='AREA', location=(-3.0, -1.5, 2.0))
fill = bpy.context.active_object
fill.name = "Fill_Light"
fill.data.energy = 60
fill.data.size = 3.0
fill.data.color = (0.7, 0.8, 1.0)

# Soft glow light from the screen itself
bpy.ops.object.light_add(type='POINT', location=(0.0, -1.6, 1.05))
glow = bpy.context.active_object
glow.name = "Screen_Glow"
glow.data.energy = 25
glow.data.color = (0.6, 0.8, 1.0)
glow.data.shadow_soft_size = 0.3

# World: dark room
world = bpy.data.worlds.new("RoomWorld")
scene.world = world
wbg = world.node_tree.nodes.get("Background")
wbg.inputs["Color"].default_value = (0.015, 0.015, 0.02, 1.0)
wbg.inputs["Strength"].default_value = 1.0

# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("TV_Camera")
cam_data.lens = 70
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = 5.2
cam_data.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("TV_Camera", cam_data)
col.objects.link(cam)
cam.location = (3.4, -4.6, 2.3)

target = Vector((0.0, 0.0, 1.05))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------------------------------------------------------------
# Compositor: bloom glow + film grain
# ---------------------------------------------------------------
comp = bpy.data.node_groups.new("TV_Compositor", "CompositorNodeTree")
scene.compositing_node_group = comp
comp.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")

rlayers = comp.nodes.new("CompositorNodeRLayers")
rlayers.location = (-800, 0)

glare = comp.nodes.new("CompositorNodeGlare")
glare.location = (-500, 0)
try:
    glare.inputs["Type"].default_value = "Bloom"
except Exception:
    pass
try:
    glare.inputs["Threshold"].default_value = 0.6
    glare.inputs["Mix"].default_value = -0.4
except Exception:
    pass

# Film grain source: animated noise
grain_noise = comp.nodes.new("ShaderNodeTexNoise")
grain_noise.location = (-500, -350)
grain_noise.inputs["Scale"].default_value = 900.0
grain_noise.inputs["Detail"].default_value = 1.0
grain_noise.inputs["Roughness"].default_value = 0.5
add_driver(grain_noise.inputs["Vector"], 0, "frame * 29.3")
add_driver(grain_noise.inputs["Vector"], 1, "frame * 7.9")

grain_mix = comp.nodes.new("ShaderNodeMix")
grain_mix.location = (-200, 0)
grain_mix.data_type = 'RGBA'
grain_mix.blend_type = 'OVERLAY'
grain_mix.inputs["Factor"].default_value = 0.14

out = comp.nodes.new("NodeGroupOutput")
out.location = (100, 0)

comp.links.new(rlayers.outputs["Image"], glare.inputs["Image"])
comp.links.new(glare.outputs["Image"], grain_mix.inputs[6])        # A (color)
comp.links.new(grain_noise.outputs["Color"], grain_mix.inputs[7])  # B (color)
comp.links.new(grain_mix.outputs[2], out.inputs[0])                # Result (color)
