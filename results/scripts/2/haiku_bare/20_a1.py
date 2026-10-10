import bpy
import bmesh
import mathutils
import math
import random
import colorsys

random.seed(7)

# ---------- Clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- Helpers ----------
def make_material(name, base_color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def assign(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def add_bevel(obj, width=0.06, segments=4):
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'

def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

# ---------- Materials ----------
mat_wood = make_material("CaseWood", (0.28, 0.14, 0.06), roughness=0.45)
mat_dark = make_material("Dark", (0.02, 0.02, 0.02), roughness=0.6)
mat_metal = make_material("Chrome", (0.8, 0.8, 0.82), roughness=0.2, metallic=1.0)
mat_floor = make_material("Floor", (0.08, 0.08, 0.09), roughness=0.8)
mat_knob = make_material("Knob", (0.6, 0.55, 0.45), roughness=0.35)

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
assign(floor, mat_floor)

# ---------- TV cabinet ----------
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1.0))
body = bpy.context.active_object
body.name = "TV_Body"
body.scale = (1.0, 0.7, 0.8)
bpy.ops.object.transform_apply(scale=True)
add_bevel(body, width=0.12, segments=5)
assign(body, mat_wood)
smooth(body)

# Front bezel (dark frame around the screen)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, -0.70, 1.0))
bezel = bpy.context.active_object
bezel.name = "Bezel"
bezel.scale = (0.9, 0.03, 0.74)
bpy.ops.object.transform_apply(scale=True)
add_bevel(bezel, width=0.04, segments=3)
assign(bezel, mat_dark)

# ---------- Screen (glowing static) ----------
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, -0.73, 1.0),
                                 rotation=(math.radians(90), 0, 0))
screen = bpy.context.active_object
screen.name = "Screen"
screen.scale = (0.75, 0.6, 1.0)
bpy.ops.object.transform_apply(scale=True)

scr_mat = bpy.data.materials.new("StaticScreen")
scr_mat.use_nodes = True
nt = scr_mat.node_tree
nt.nodes.clear()

tex_coord = nt.nodes.new("ShaderNodeTexCoord")
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 90.0
noise.inputs["Detail"].default_value = 3.0
noise.inputs["Roughness"].default_value = 0.8

ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
ramp.color_ramp.elements[1].position = 0.65
ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

emit = nt.nodes.new("ShaderNodeEmission")
emit.inputs["Strength"].default_value = 2.5
emit.inputs["Color"].default_value = (0.75, 0.9, 1.0, 1.0)  # cool phosphor tint

out = nt.nodes.new("ShaderNodeOutputMaterial")

nt.links.new(tex_coord.outputs["Generated"], noise.inputs["Vector"])
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], emit.inputs["Color"])
nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])

# Animate static: new random W each frame, constant interpolation (TV-style jumps)
FRAMES = 48
scene.frame_start = 1
scene.frame_end = FRAMES
for f in range(1, FRAMES + 1):
    noise.inputs["W"].default_value = random.uniform(0.0, 300.0)
    noise.inputs["W"].keyframe_insert("default_value", frame=f)

if nt.animation_data and nt.animation_data.action:
    for fc in nt.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT'

assign(screen, scr_mat)

# ---------- Back cabinet detail ----------
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0.55, 0.7))
vent = bpy.context.active_object
vent.name = "Vents"
vent.scale = (0.8, 0.1, 0.5)
bpy.ops.object.transform_apply(scale=True)
assign(vent, mat_dark)

# ---------- Feet ----------
for x in (-0.8, 0.8):
    for y in (-0.4, 0.4):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.2,
                                            location=(x, y, 0.1))
        foot = bpy.context.active_object
        foot.name = "Foot"
        assign(foot, mat_dark)

# ---------- Knobs on right side ----------
for i, z in enumerate((1.45, 0.9)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.12,
                                        location=(0.98, -0.72, z),
                                        rotation=(math.radians(90), 0, 0))
    knob = bpy.context.active_object
    knob.name = f"Knob_{i}"
    assign(knob, mat_knob)

# ---------- Rabbit-ear antenna ----------
for side in (-1, 1):
    length = 0.9
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=length,
                                        location=(0, 0, 0))
    rod = bpy.context.active_object
    rod.name = "Antenna"
    rod.location = (side * 0.25, 0.0, 2.0 + length / 2 * 0.8)
    rod.rotation_euler = (0, math.radians(-side * 30), 0)
    assign(rod, mat_metal)

# ---------- Lighting ----------
bpy.ops.object.light_add(type='AREA', location=(2.5, -3.5, 3.0))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 400
key.data.size = 3.0
key.rotation_euler = (math.radians(55), 0, math.radians(35))

bpy.ops.object.light_add(type='POINT', location=(-2.0, -2.5, 1.0))
fill = bpy.context.active_object
fill.name = "ScreenGlowLight"
fill.data.energy = 60
fill.data.color = (0.6, 0.8, 1.0)

bpy.ops.object.light_add(type='POINT', location=(0, 2.5, 2.5))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 120

# World: dark ambient
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.01, 0.01, 0.015, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 65
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (0.0, -5.4, 1.5)

target = mathutils.Vector((0.0, 0.0, 1.0))
direction = target - mathutils.Vector(cam_obj.location)
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj

# ---------- Render settings ----------
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.resolution_percentage = 100
try:
    scene.render.engine = 'BLENDER_EEVEE'
except TypeError:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'

# ---------- Film grain image (generated procedurally) ----------
W, H = 960, 540
grain_img = bpy.data.images.new("FilmGrain", width=W, height=H)
vals = []
for _ in range(W * H):
    v = min(1.0, max(0.0, random.gauss(0.5, 0.18)))
    vals.extend((v, v, v, 1.0))
grain_img.pixels.foreach_set(vals)
grain_img.pack()
grain_img.use_fake_user = True

# ---------- Compositor ----------
scene.use_nodes = True
ctree = None
if hasattr(scene, "compositing_node_group"):
    if scene.compositing_node_group is None:
        scene.compositing_node_group = bpy.data.node_groups.new(
            "Compositor", 'CompositorNodeTree')
    ctree = scene.compositing_node_group
else:
    ctree = scene.node_tree
ctree.nodes.clear()

rlayers = ctree.nodes.new("CompositorNodeRLayers")
glare = ctree.nodes.new("CompositorNodeGlare")
glare.glare_type = 'FOG_GLOW'
glare.threshold = 0.6
glare.mix = 0.0 if False else glare.mix  # keep default mix
glare.size = 8

grain_node = ctree.nodes.new("CompositorNodeImage")
grain_node.image = grain_img

mix = ctree.nodes.new("CompositorNodeMixRGB")
mix.blend_type = 'OVERLAY'
mix.inputs[0].default_value = 0.12  # grain strength

comp = ctree.nodes.new("CompositorNodeComposite")

# Links: render -> glow -> mix(base) ; grain -> mix(overlay) -> output
rl_image = rlayers.outputs.get("Image")
ctree.links.new(rl_image, glare.inputs["Image"])
ctree.links.new(glare.outputs["Image"], mix.inputs[1])
ctree.links.new(grain_node.outputs["Image"], mix.inputs[2])
ctree.links.new(mix.outputs["Image"], comp.inputs["Image"])

# ---------- Frame the scene ----------
scene.frame_current = 1
