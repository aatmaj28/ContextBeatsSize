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

def add_box(name, loc, size, mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if mat:
        assign(obj, mat)
    return obj

def add_cyl(name, loc, radius, depth, rot=(0, 0, 0), mat=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius,
                                        depth=depth, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = rot
    if mat:
        assign(obj, mat)
    return obj

# ---------- Materials ----------
wood_mat = make_principled("WoodCase", (0.22, 0.11, 0.05), roughness=0.45)
dark_mat = make_principled("DarkPlastic", (0.03, 0.03, 0.03), roughness=0.35)
metal_mat = make_principled("ChromeTrim", (0.8, 0.8, 0.8), roughness=0.2, metallic=1.0)
floor_mat = make_principled("Floor", (0.25, 0.24, 0.23), roughness=0.9)

# Screen emission material with animated static noise
screen_mat = bpy.data.materials.new("StaticScreen")
screen_mat.use_nodes = True
sn = screen_mat.node_tree.nodes
sl = screen_mat.node_tree.links
sn.clear()

out = sn.new("ShaderNodeOutputMaterial")
out.location = (900, 0)
emit = sn.new("ShaderNodeEmission")
emit.location = (600, 0)
emit.inputs["Strength"].default_value = 3.0
ramp = sn.new("ShaderNodeValToRGB")
ramp.location = (300, 0)
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
ramp.color_ramp.elements[1].position = 0.65
ramp.color_ramp.elements[1].color = (0.75, 0.9, 1.0, 1.0)
noise = sn.new("ShaderNodeTexNoise")
noise.location = (0, 0)
noise.inputs["Scale"].default_value = 180.0
noise.inputs["Detail"].default_value = 2.0
noise.inputs["Roughness"].default_value = 0.7
noise.inputs["W"].default_value = 0.0
sl.new(noise.outputs["Fac"], ramp.inputs["Fac"])
sl.new(ramp.outputs["Color"], emit.inputs["Color"])
sl.new(emit.outputs["Emission"], out.inputs["Surface"])

# Animate the noise W coordinate so the static crawls
noise.inputs["W"].default_value = 0.0
noise.inputs["W"].keyframe_insert("default_value", frame=1)
noise.inputs["W"].default_value = 60.0
noise.inputs["W"].keyframe_insert("default_value", frame=60)
if screen_mat.node_tree.animation_data and screen_mat.node_tree.animation_data.action:
    for fc in screen_mat.node_tree.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

scene.frame_start = 1
scene.frame_end = 60

# ---------- TV geometry ----------
body = add_box("TV_Body", (0, 0, 1.0), (1.2, 0.8, 0.95), wood_mat)
bev = body.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.06
bev.segments = 4
bpy.context.view_layer.objects.active = body
bpy.ops.object.shade_smooth()

# Front bezel (dark) and screen
bezel = add_box("Bezel", (-0.12, -0.80, 1.0), (0.92, 0.02, 0.76), dark_mat)

bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-0.12, -0.815, 1.0))
screen = bpy.context.active_object
screen.name = "Screen"
screen.rotation_euler = (math.radians(90), 0, 0)
screen.scale = (0.80, 0.62, 1.0)
bpy.ops.object.transform_apply(rotation=True, scale=True)
assign(screen, screen_mat)

# Control panel on right side
panel = add_box("ControlPanel", (0.82, -0.80, 1.0), (0.28, 0.02, 0.76), wood_mat)

# Knobs
for i, z in enumerate([1.45, 1.22, 0.98]):
    add_cyl(f"Knob{i}", (0.82, -0.84, z), 0.07, 0.10,
            rot=(math.radians(90), 0, 0), mat=metal_mat)
    add_cyl(f"KnobTick{i}", (0.82, -0.895, z + 0.04), 0.008, 0.02,
            rot=(math.radians(90), 0, 0), mat=dark_mat)

# Speaker slats
for i in range(5):
    add_box(f"Slat{i}", (0.82, -0.80, 0.62 + i * 0.07), (0.20, 0.02, 0.012), dark_mat)

# Feet
for i, x in enumerate([-0.8, 0.8]):
    add_box(f"Foot{i}", (x, -0.2, 0.05), (0.2, 0.4, 0.1), dark_mat)

# Antennas (rabbit ears)
add_cyl("AntennaL", (-0.25, -0.1, 2.25), 0.012, 1.1,
        rot=(0, math.radians(-30), math.radians(-18)), mat=metal_mat, verts=12)
add_cyl("AntennaR", (0.25, -0.1, 2.25), 0.012, 1.1,
        rot=(0, math.radians(30), math.radians(18)), mat=metal_mat, verts=12)
add_cyl("AntennaBaseL", (-0.15, -0.1, 1.97), 0.03, 0.06, mat=metal_mat, verts=12)
add_cyl("AntennaBaseR", (0.15, -0.1, 1.97), 0.03, 0.06, mat=metal_mat, verts=12)

# Table / stand under TV
add_box("Table", (0, -0.1, -0.12), (2.2, 1.2, 0.12), wood_mat)

# Floor
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.5))
floor = bpy.context.active_object
floor.name = "Floor"
assign(floor, floor_mat)

# ---------- Lighting ----------
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.015, 0.016, 0.02, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

bpy.ops.object.light_add(type='AREA', location=(0.5, -4.0, 4.0))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 250
key.data.size = 3.0
key.rotation_euler = (math.radians(55), 0, math.radians(10))

bpy.ops.object.light_add(type='AREA', location=(-3.5, -1.5, 2.5))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 120
rim.data.size = 2.0
rim.data.color = (0.6, 0.75, 1.0)
rim.rotation_euler = (math.radians(70), 0, math.radians(-60))

# Screen glow spilling onto surroundings
bpy.ops.object.light_add(type='POINT', location=(0, -1.6, 1.0))
glow = bpy.context.active_object
glow.name = "ScreenGlow"
glow.data.energy = 60
glow.data.color = (0.7, 0.85, 1.0)
glow.data.shadow_soft_size = 0.5

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(0.9, -5.6, 1.9))
cam = bpy.context.active_object
cam.name = "Camera"
cam.data.lens = 70
target = Vector((0.0, 0.0, 1.05))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Compositor: glow + film grain ----------
# Grain texture (random grayscale, centered on 0.5 so Overlay is near-neutral)
GRAIN_SIZE = 256
grain_img = bpy.data.images.new("FilmGrain", width=GRAIN_SIZE, height=GRAIN_SIZE)
pixels = []
for _ in range(GRAIN_SIZE * GRAIN_SIZE):
    v = min(1.0, max(0.0, random.gauss(0.5, 0.12)))
    pixels.extend((v, v, v, 1.0))
grain_img.pixels.foreach_set(pixels)
grain_img.pack()

# Create compositor tree (Blender 5.x uses a compositing node group)
comp_tree = None
try:
    comp_tree = bpy.data.node_groups.new("Compositor", 'CompositorNodeTree')
    scene.compositing_node_group = comp_tree
except Exception:
    scene.use_nodes = True
    comp_tree = scene.node_tree

cn = comp_tree.nodes
cl = comp_tree.links
cn.clear()

rlayers = cn.new("CompositorNodeRLayers")
rlayers.location = (-600, 0)
try:
    rlayers.scene = scene
except Exception:
    pass

glare = cn.new("CompositorNodeGlare")
glare.location = (-300, 0)
try:
    glare.glare_type = 'FOG_GLOW'
except Exception:
    pass
try:
    glare.mix = 0.0
    glare.threshold = 0.6
except Exception:
    pass

grain_node = cn.new("CompositorNodeImage")
grain_node.location = (-300, -250)
grain_node.image = grain_img

grain_mix = cn.new("CompositorNodeMixRGB")
grain_mix.location = (0, 0)
grain_mix.blend_type = 'OVERLAY'
grain_mix.inputs[0].default_value = 0.06

composite = cn.new("CompositorNodeComposite")
composite.location = (300, 0)

cl.new(rlayers.outputs["Image"], glare.inputs["Image"])
cl.new(glare.outputs["Image"], grain_mix.inputs[1])
cl.new(grain_node.outputs["Image"], grain_mix.inputs[2])
cl.new(grain_mix.outputs["Image"], composite.inputs["Image"])
