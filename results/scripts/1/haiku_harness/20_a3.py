import bpy
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene

# ---------------------------------------------------------------
# Clear default scene contents
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def link_object(obj):
    scene.collection.objects.link(obj)
    return obj


def make_principled(name, base, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (base[0], base[1], base[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_box(name, loc, scale, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler = rot
    obj.data.materials.append(mat)
    return obj


def add_cylinder(name, loc, radius, depth, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = rot
    obj.data.materials.append(mat)
    return obj


def add_sphere(name, loc, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def add_light(name, light_type, loc, energy, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, light_type)
    ld.energy = energy
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    link_object(ob)
    ob.location = loc
    return ob


def aim(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def socket_by_identifier(sockets, identifier):
    # Mix node sockets share names ("A", "B", "Result") across data types,
    # so select them by identifier (e.g. "A_Color", "Result_Color").
    for s in sockets:
        if s.identifier == identifier:
            return s
    raise KeyError(f"No socket with identifier '{identifier}'")


# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
wood_mat = make_principled("WoodCabinet", (0.28, 0.13, 0.06), roughness=0.45)
metal_mat = make_principled("ChromeTrim", (0.7, 0.7, 0.72), roughness=0.25, metallic=1.0)
knob_mat = make_principled("BlackPlastic", (0.02, 0.02, 0.02), roughness=0.35)
floor_mat = make_principled("Floor", (0.18, 0.17, 0.16), roughness=0.8)
wall_mat = make_principled("Wall", (0.04, 0.045, 0.06), roughness=0.9)


def make_static_material():
    mat = bpy.data.materials.new("TVStatic")
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 3.0

    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 60.0
    noise.inputs["Detail"].default_value = 14.0
    noise.inputs["Roughness"].default_value = 0.7

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.02, 0.03, 0.05, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.9, 0.95, 1.0, 1.0)

    links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], out.inputs["Surface"])

    # Animate the static by jumping the noise location every frame
    for f in range(1, 121):
        mapping.inputs["Location"].default_value = (
            random.uniform(0.0, 1000.0),
            random.uniform(0.0, 1000.0),
            random.uniform(0.0, 1000.0),
        )
        mapping.inputs["Location"].keyframe_insert("default_value", frame=f)

    return mat


static_mat = make_static_material()

# ---------------------------------------------------------------
# TV geometry
# ---------------------------------------------------------------
cabinet = add_box("TV_Cabinet", (0, 0, 1.2), (1.0, 0.8, 0.8), wood_mat)
bevel = cabinet.modifiers.new("Bevel", "BEVEL")
bevel.width = 0.06
bevel.segments = 4

# Screen (slightly proud of the front face at y = -0.8)
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(-0.2, -0.81, 1.25))
screen = bpy.context.active_object
screen.name = "TV_Screen"
screen.rotation_euler = (math.radians(90), 0, 0)
screen.scale = (0.65, 0.5, 1.0)
screen.data.materials.append(static_mat)

# Inner bezel ring to frame the screen
add_box("TV_Bezel", (-0.2, -0.79, 1.25), (0.72, 0.02, 0.56), knob_mat)

# Control knobs on the right side
for i, z in enumerate([1.6, 1.25, 0.9]):
    add_cylinder(f"TV_Knob_{i}", (0.72, -0.86, z), 0.07, 0.08, metal_mat,
                 rot=(math.radians(90), 0, 0))

# Speaker grille slots at the bottom right
for i in range(4):
    add_box(f"TV_Grille_{i}", (0.72, -0.81, 0.62 + i * 0.08), (0.18, 0.01, 0.015), knob_mat)

# Legs
for i, (x, y) in enumerate([(-0.6, -0.5), (0.6, -0.5), (-0.6, 0.5), (0.6, 0.5)]):
    add_cylinder(f"TV_Leg_{i}", (x, y, 0.2), 0.05, 0.4, knob_mat)

# Rabbit-ear antennae
for side, sign in [("L", -1), ("R", 1)]:
    angle = math.radians(25) * sign
    add_cylinder(f"Antenna_{side}", (sign * 0.254, 0, 2.544), 0.02, 1.2, metal_mat,
                 rot=(0, angle, 0))
    add_sphere(f"AntennaTip_{side}", (sign * 0.507, 0, 3.088), 0.04, metal_mat)

# ---------------------------------------------------------------
# Environment
# ---------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.scale = (10, 10, 1)
floor.data.materials.append(floor_mat)

bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 2.5, 3.0))
wall = bpy.context.active_object
wall.name = "Wall"
wall.rotation_euler = (math.radians(90), 0, 0)
wall.scale = (10, 6, 1)
wall.data.materials.append(wall_mat)

# World: very dark ambient
world = bpy.data.worlds.new("RoomWorld")
scene.world = world
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1.0)
bg.inputs["Strength"].default_value = 0.5

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
key = add_light("KeyArea", 'AREA', (0.0, -3.5, 4.0), 250.0)
key.data.size = 3.0
aim(key, (0, 0, 1.0))

rim = add_light("RimArea", 'AREA', (2.5, 2.0, 3.0), 120.0, color=(0.8, 0.9, 1.0))
rim.data.size = 2.0
aim(rim, (0, 0, 1.2))

# Cool glow spilling from the screen onto the room
spill = add_light("ScreenSpill", 'POINT', (-0.2, -2.0, 1.25), 60.0, color=(0.7, 0.85, 1.0))
spill.data.shadow_soft_size = 0.5

# ---------------------------------------------------------------
# Camera
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("TV_Camera")
cam_data.lens = 65
cam = bpy.data.objects.new("TV_Camera", cam_data)
link_object(cam)
cam.location = (0.0, -6.8, 1.8)
aim(cam, (0.0, 0.0, 1.45))
scene.camera = cam

# ---------------------------------------------------------------
# Render settings
# ---------------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 120

# ---------------------------------------------------------------
# Compositor: film grain
# ---------------------------------------------------------------
comp_tree = bpy.data.node_groups.new("FilmGrainComp", "CompositorNodeTree")
scene.compositing_node_group = comp_tree

# Output interface first so the Group Output node has its socket
comp_tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")

cnodes = comp_tree.nodes
clinks = comp_tree.links

render_layers = cnodes.new("CompositorNodeRLayers")
img_coords = cnodes.new("CompositorNodeImageCoordinates")

grain_noise = cnodes.new("ShaderNodeTexNoise")
grain_noise.inputs["Scale"].default_value = 500.0
grain_noise.inputs["Detail"].default_value = 2.0
grain_noise.inputs["Roughness"].default_value = 0.6

grain_mix = cnodes.new("ShaderNodeMix")
grain_mix.data_type = 'RGBA'
grain_mix.blend_type = 'OVERLAY'
grain_mix.inputs["Factor"].default_value = 0.12

group_out = cnodes.new("NodeGroupOutput")

# Mix node in RGBA mode: select the color sockets by identifier
mix_a = socket_by_identifier(grain_mix.inputs, "A_Color")
mix_b = socket_by_identifier(grain_mix.inputs, "B_Color")
mix_result = socket_by_identifier(grain_mix.outputs, "Result_Color")

clinks.new(img_coords.outputs["Normalized"], grain_noise.inputs["Vector"])
clinks.new(render_layers.outputs["Image"], mix_a)
clinks.new(grain_noise.outputs["Color"], mix_b)
clinks.new(mix_result, group_out.inputs[0])

print("TV scene built: frames", scene.frame_start, "-", scene.frame_end)
