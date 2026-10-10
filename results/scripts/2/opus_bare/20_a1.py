import bpy, bmesh, math, random
from mathutils import Vector

scene = bpy.context.scene
# clear
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 120
scene.render.resolution_x = 960
scene.render.resolution_y = 540
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = eng
        break
    except Exception:
        pass

def mat_principled(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

wood = mat_principled("Wood", (0.25, 0.12, 0.05), 0.45)
plastic = mat_principled("DarkPlastic", (0.03, 0.03, 0.03), 0.35)
metal = mat_principled("Chrome", (0.8, 0.8, 0.8), 0.2, 1.0)
table_m = mat_principled("Table", (0.12, 0.09, 0.07), 0.6)

# static screen material
scr = bpy.data.materials.new("Static")
scr.use_nodes = True
nt = scr.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
emi = nt.nodes.new("ShaderNodeEmission")
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (320, 240, 1)
snap = nt.nodes.new("ShaderNodeVectorMath")
snap.operation = 'FLOOR'
wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
wn.noise_dimensions = '4D'
val = nt.nodes.new("ShaderNodeValue")
fc = val.outputs[0].driver_add("default_value")
fc.driver.expression = "frame"
wave = nt.nodes.new("ShaderNodeTexWave")
wave.wave_type = 'BANDS'
wave.bands_direction = 'Y'
wave.inputs["Scale"].default_value = 60
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
ramp = nt.nodes.new("ShaderNodeMapRange")
ramp.inputs["To Min"].default_value = 0.6
ramp.inputs["To Max"].default_value = 1.0
tint = nt.nodes.new("ShaderNodeMix"); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'
tint.inputs[0].default_value = 1.0
nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
nt.links.new(mp.outputs[0], snap.inputs[0])
nt.links.new(snap.outputs[0], wn.inputs["Vector"])
nt.links.new(val.outputs[0], wn.inputs["W"])
nt.links.new(tc.outputs["UV"], wave.inputs["Vector"])
nt.links.new(wave.outputs["Fac"], ramp.inputs["Value"])
nt.links.new(wn.outputs["Value"], mul.inputs[0])
nt.links.new(ramp.outputs[0], mul.inputs[1])
cols = [s for s in tint.inputs if s.type == 'RGBA']
nt.links.new(mul.outputs[0], cols[0])
cols[1].default_value = (0.85, 0.95, 1.0, 1)
nt.links.new([s for s in tint.outputs if s.type == 'RGBA'][0], emi.inputs["Color"])
emi.inputs["Strength"].default_value = 4.0
nt.links.new(emi.outputs[0], out.inputs["Surface"])

def add(obj, mat):
    obj.data.materials.append(mat)
    return obj

# TV body
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1.25))
body = bpy.context.object
body.scale = (0.9, 0.65, 0.65)
bpy.ops.object.transform_apply(scale=True)
bv = body.modifiers.new("Bevel", 'BEVEL'); bv.width = 0.08; bv.segments = 5
add(body, wood)
bpy.ops.object.shade_smooth()

# bezel
bpy.ops.mesh.primitive_cube_add(location=(-0.18, -0.64, 1.25))
bez = bpy.context.object
bez.scale = (0.6, 0.03, 0.5)
b2 = bez.modifiers.new("Bevel", 'BEVEL'); b2.width = 0.05; b2.segments = 4
add(bez, plastic)

# screen
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.18, -0.68, 1.25), rotation=(math.radians(90), 0, 0))
screen = bpy.context.object
screen.scale = (1.04, 0.82, 1)
add(screen, scr)

# knobs
for i, z in enumerate((1.45, 1.15)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.08, location=(0.68, -0.68, z), rotation=(math.radians(90), 0, 0))
    add(bpy.context.object, metal)
# speaker grille slats
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(location=(0.68, -0.66, 0.95 - i * 0.05))
    s = bpy.context.object; s.scale = (0.1, 0.01, 0.01)
    add(s, plastic)

# legs
for x in (-0.7, 0.7):
    for y in (-0.45, 0.45):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.6, location=(x, y, 0.33),
                                            rotation=(math.radians(8 * (1 if y > 0 else -1)), math.radians(-8 * (1 if x < 0 else -1)), 0))
        add(bpy.context.object, metal)

# antennas
for ang in (-25, 30):
    a = math.radians(ang)
    L = 0.9
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=L,
        location=(0.1 + math.sin(a) * L / 2, 0.1, 1.9 + math.cos(a) * L / 2), rotation=(0, a, 0))
    add(bpy.context.object, metal)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0.1, 0.1, 1.9))
add(bpy.context.object, plastic)

# floor & wall
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
add(bpy.context.object, table_m)
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 3, 5), rotation=(math.radians(90), 0, 0))
add(bpy.context.object, mat_principled("Wall", (0.15, 0.17, 0.2), 0.9))

# lights
bpy.ops.object.light_add(type='AREA', location=(-3, -3, 4))
l = bpy.context.object; l.data.energy = 150; l.data.size = 3
l.data.color = (1.0, 0.8, 0.6)
l.rotation_euler = (math.radians(50), 0, math.radians(-45))
bpy.ops.object.light_add(type='AREA', location=(-0.18, -1.2, 1.25), rotation=(math.radians(-90), 0, 0))
g = bpy.context.object; g.data.energy = 40; g.data.size = 1.0; g.data.color = (0.8, 0.9, 1.0)

world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.02, 1)

# camera
bpy.ops.object.camera_add(location=(1.6, -4.2, 1.7))
cam = bpy.context.object
cam.data.lens = 45
d = Vector((0, 0, 1.25)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# grain image
W, H = scene.render.resolution_x, scene.render.resolution_y
img = bpy.data.images.new("Grain", W, H, float_buffer=True)
rnd = random.Random(7)
px = []
for _ in range(W * H):
    v = 0.5 + rnd.gauss(0, 0.18)
    px.extend((v, v, v, 1.0))
img.pixels.foreach_set(px)

# compositor
tree = None
new_api = hasattr(scene, "compositing_node_group")
if new_api:
    tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    scene.compositing_node_group = tree
else:
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()
N, Lk = tree.nodes, tree.links
rl = N.new("CompositorNodeRLayers")
glare = N.new("CompositorNodeGlare")
for attr, v in (("glare_type", 'BLOOM'), ("glare_type", 'FOG_GLOW')):
    try:
        setattr(glare, attr, v); break
    except Exception:
        pass
for name, v in (("Threshold", 0.8), ("Strength", 0.6)):
    if name in glare.inputs:
        try: glare.inputs[name].default_value = v
        except Exception: pass
gimg = N.new("CompositorNodeImage"); gimg.image = img
try:
    mix = N.new("CompositorNodeMixRGB")
except Exception:
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'
mix.blend_type = 'OVERLAY'
mix.inputs[0].default_value = 0.35
mcols = [s for s in mix.inputs if s.type == 'RGBA' and s.enabled]
Lk.new(rl.outputs["Image"], glare.inputs[0])
Lk.new(glare.outputs[0], mcols[0])
Lk.new(gimg.outputs[0], mcols[1])
mout = [s for s in mix.outputs if s.type == 'RGBA' and s.enabled][0]
if new_api:
    tree.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    go = N.new("NodeGroupOutput")
    Lk.new(mout, go.inputs[0])
else:
    comp = N.new("CompositorNodeComposite")
    Lk.new(mout, comp.inputs[0])
