import bpy
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene

# ---------- Clear scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Helpers ----------
def make_principled(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj

def add_box(name, size, loc, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = Vector(size)
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 3
    bpy.ops.object.shade_smooth()
    return assign(obj, mat)

def add_cylinder(name, radius, depth, loc, rot, mat, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius,
                                        depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return assign(obj, mat)

# ---------- Materials ----------
wood_mat = make_principled("Wood", (0.32, 0.18, 0.09), roughness=0.45)
dark_mat = make_principled("DarkPlastic", (0.03, 0.03, 0.03), roughness=0.35)
metal_mat = make_principled("Metal", (0.6, 0.6, 0.62), roughness=0.25, metallic=1.0)
knob_mat = make_principled("Knob", (0.05, 0.05, 0.05), roughness=0.3)
bezel_mat = make_principled("Bezel", (0.08, 0.07, 0.06), roughness=0.6)

# ---------- Screen material (animated static) ----------
screen_mat = bpy.data.materials.new("StaticScreen")
screen_mat.use_nodes = True
nt = screen_mat.node_tree
nodes, links = nt.nodes, nt.links
nodes.clear()

out = nodes.new("ShaderNodeOutputMaterial")
out.location = (600, 0)
emit = nodes.new("ShaderNodeEmission")
emit.location = (350, 0)
emit.inputs["Strength"].default_value = 6.0
ramp = nodes.new("ShaderNodeValToRGB")
ramp.location = (100, 0)
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = (0.02, 0.05, 0.03, 1.0)
ramp.color_ramp.elements[1].position = 0.65
ramp.color_ramp.elements[1].color = (0.75, 1.0, 0.85, 1.0)
noise = nodes.new("ShaderNodeTexNoise")
noise.location = (-150, 0)
noise.inputs["Scale"].default_value = 60.0
noise.inputs["Detail"].default_value = 16.0
noise.inputs["Roughness"].default_value = 0.7
coord = nodes.new("ShaderNodeTexCoord")
coord.location = (-400, 0)

links.new(coord.outputs["Generated"], noise.inputs["Vector"])
links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
links.new(ramp.outputs["Color"], emit.inputs["Color"])
links.new(emit.outputs["Emission"], out.inputs["Surface"])

# Animate the noise W coordinate for flicker, looping back to frame 1
scene.frame_start = 1
scene.frame_end = 48
scene.render.fps = 24
w_socket = noise.inputs["W"]
for f in range(1, 49):
    if f == 48:
        w_socket.default_value = first_w
    else:
        w_socket.default_value = random.uniform(0.0, 100.0)
        if f == 1:
            first_w = w_socket.default_value
    w_socket.keyframe_insert(data_path="default_value", frame=f)
try:
    for fc in nt.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT'
except Exception:
    pass

# ---------- TV geometry ----------
TV_Z = 1.0
# Wooden cabinet body
add_box("TV_Body", (2.0, 1.4, 1.6), (0, 0, TV_Z), wood_mat, bevel=0.06)
# Front bezel (dark frame around screen)
add_box("TV_Bezel", (1.62, 0.05, 1.3), (0, -0.72, TV_Z), bezel_mat, bevel=0.03)

# Screen (plane facing -Y)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.12, -0.75, TV_Z + 0.02),
                                 rotation=(math.radians(90), 0, 0))
screen = bpy.context.active_object
screen.name = "TV_Screen"
screen.scale = (0.66, 0.5, 1.0)
bpy.ops.object.transform_apply(scale=True)
assign(screen, screen_mat)

# Control panel on the right: knobs
for i, z in enumerate([1.42, 1.22, 1.02, 0.82]):
    add_cylinder(f"Knob_{i}", 0.06, 0.08, (0.72, -0.78, z),
                 (math.radians(90), 0, 0), knob_mat)
    add_cylinder(f"KnobCap_{i}", 0.04, 0.02, (0.72, -0.83, z),
                 (math.radians(90), 0, 0), metal_mat)

# Speaker grille slots (lower-right)
for i in range(5):
    add_box(f"Slot_{i}", (0.28, 0.02, 0.025), (0.5, -0.78, 0.45 + i * 0.07),
            dark_mat)

# Legs
for x in (-0.8, 0.8):
    for y in (-0.5, 0.5):
        add_cylinder(f"Leg_{x}_{y}", 0.05, 0.25, (x, y, 0.125), (0, 0, 0), metal_mat)

# Antenna (rabbit ears)
for side, ang in ((-1, math.radians(-30)), (1, math.radians(30))):
    add_cylinder(f"Antenna_{side}", 0.012, 1.0,
                 (0.2 * side, 0.0, TV_Z + 0.8 + 0.5 * math.cos(ang)),
                 (ang * 0.0, math.radians(0), math.radians(-side * 30)),
                 metal_mat, verts=8)
# Antenna base
add_cylinder("AntennaBase", 0.08, 0.06, (0, 0, TV_Z + 0.83), (0, 0, 0), dark_mat)

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
assign(floor, make_principled("Floor", (0.08, 0.08, 0.09), roughness=0.8))

# ---------- World ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.01, 0.01, 0.015, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------- Lights ----------
bpy.ops.object.light_add(type='AREA', location=(0, -4.0, 4.0))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 250
key.data.size = 3.0
key.rotation_euler = (math.radians(55), 0, 0)

# Screen spill light: cool glow in front of the TV
bpy.ops.object.light_add(type='POINT', location=(0, -2.0, 1.1))
spill = bpy.context.active_object
spill.name = "ScreenGlow"
spill.data.energy = 120
spill.data.color = (0.75, 0.95, 1.0)
spill.data.shadow_soft_size = 0.8

# Rim light from behind
bpy.ops.object.light_add(type='AREA', location=(2.5, 3.0, 3.0))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 120
rim.data.size = 2.0
rim.data.color = (1.0, 0.8, 0.6)
rim.rotation_euler = (math.radians(-40), 0, math.radians(35))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 70
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((0.4, -6.2, 1.6))
target = Vector((0.0, 0.0, 1.05))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Film grain in compositor ----------
grain_tex = bpy.data.textures.new("FilmGrain", type='NOISE')

def get_compositor_tree():
    if hasattr(scene, "compositing_node_group"):
        tree = bpy.data.node_groups.new("FilmGrainCompositor", "CompositorNodeTree")
        scene.compositing_node_group = tree
        return tree
    scene.use_nodes = True
    return scene.node_tree

try:
    ctree = get_compositor_tree()
    cn = ctree.nodes
    cl = ctree.links
    cn.clear()

    rlayers = cn.new("CompositorNodeRLayers")
    rlayers.location = (-400, 0)
    mix = cn.new("CompositorNodeMixRGB")
    mix.location = (-100, 0)
    mix.blend_type = 'OVERLAY'
    mix.inputs[0].default_value = 0.12  # grain strength
    tex = cn.new("CompositorNodeTexture")
    tex.location = (-400, -250)
    tex.texture = grain_tex
    comp = cn.new("CompositorNodeComposite")
    comp.location = (300, 0)

    # Subtle bloom on the glowing screen
    try:
        glare = cn.new("CompositorNodeGlare")
        glare.location = (100, 150)
        glare.glare_type = 'BLOOM'
        glare.mix = -0.4
        glare.threshold = 0.6
        cl.new(rlayers.outputs["Image"], glare.inputs["Image"])
        cl.new(glare.outputs["Image"], mix.inputs[1])
    except Exception:
        cl.new(rlayers.outputs["Image"], mix.inputs[1])

    cl.new(tex.outputs[0], mix.inputs[2])
    cl.new(mix.outputs[0], comp.inputs["Image"])
except Exception as e:
    print("Compositor setup skipped:", e)

scene.frame_current = 1
