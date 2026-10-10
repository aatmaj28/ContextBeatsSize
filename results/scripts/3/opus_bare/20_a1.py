import bpy, math, bmesh
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

wood = mat("Wood", (0.25, 0.12, 0.05), 0.4)
plastic = mat("Plastic", (0.08, 0.07, 0.06), 0.35)
chrome = mat("Chrome", (0.8, 0.8, 0.8), 0.15, 1.0)
floor_m = mat("Floor", (0.15, 0.13, 0.12), 0.8)
wall_m = mat("Wall", (0.3, 0.32, 0.35), 0.9)

def box(name, loc, size, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0]/2, size[1]/2, size[2]/2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        md = o.modifiers.new("Bevel", 'BEVEL')
        md.width = bevel
        md.segments = 4
        bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    return o

# Room
box("Floor", (0, 0, -0.01), (10, 10, 0.02), floor_m)
box("Wall", (0, 2.5, 2.5), (10, 0.1, 5), wall_m)
# Table
box("TableTop", (0, 0, 0.7), (2.2, 1.2, 0.08), wood, 0.01)
for x in (-1.0, 1.0):
    for y in (-0.5, 0.5):
        box("Leg", (x, y, 0.33), (0.07, 0.07, 0.66), wood)

# TV body
tz = 0.74 + 0.45
box("TVBody", (0, 0, tz), (1.3, 0.9, 0.9), wood, 0.06)
box("TVBezel", (-0.15, -0.44, tz), (0.92, 0.04, 0.76), plastic, 0.03)
box("Panel", (0.47, -0.44, tz), (0.26, 0.04, 0.76), plastic, 0.02)
for i, z in enumerate((0.2, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.05, location=(0.47, -0.48, tz + z),
                                        rotation=(math.radians(90), 0, 0))
    k = bpy.context.object; k.data.materials.append(chrome); bpy.ops.object.shade_smooth()
for i in range(5):
    box("Grille", (0.47, -0.465, tz - 0.2 - i*0.04), (0.18, 0.01, 0.015), chrome)

# Screen (slightly bulged)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=24, size=1)
scr = bpy.context.object
scr.name = "Screen"
for v in scr.data.vertices:
    x, y = v.co.x, v.co.y
    v.co.x *= 0.8; v.co.y *= 0.62
    v.co.z = 0.04 * (1 - (2*x)**2) * (1 - (2*y)**2)
scr.rotation_euler = (math.radians(90), 0, 0)
scr.location = (-0.15, -0.465, tz)
bpy.ops.object.shade_smooth()

sm = bpy.data.materials.new("Static")
sm.use_nodes = True
nt = sm.node_tree
nt.nodes.clear()
outn = nt.nodes.new("ShaderNodeOutputMaterial")
emi = nt.nodes.new("ShaderNodeEmission")
emi.inputs["Strength"].default_value = 3.0
tc = nt.nodes.new("ShaderNodeTexCoord")
scale = nt.nodes.new("ShaderNodeVectorMath"); scale.operation = 'MULTIPLY'
scale.inputs[1].default_value = (220, 170, 1)
snap = nt.nodes.new("ShaderNodeVectorMath"); snap.operation = 'FLOOR'
wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '4D'
nt.links.new(tc.outputs["UV"], scale.inputs[0])
nt.links.new(scale.outputs[0], snap.inputs[0])
nt.links.new(snap.outputs[0], wn.inputs["Vector"])
wav = nt.nodes.new("ShaderNodeTexWave")
wav.wave_type = 'BANDS'; wav.bands_direction = 'Y'
wav.inputs["Scale"].default_value = 60
nt.links.new(tc.outputs["UV"], wav.inputs["Vector"])
sl = nt.nodes.new("ShaderNodeMapRange")
sl.inputs["To Min"].default_value = 0.65
nt.links.new(wav.outputs["Fac"], sl.inputs["Value"])
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
nt.links.new(wn.outputs["Value"], mul.inputs[0])
nt.links.new(sl.outputs["Result"], mul.inputs[1])
tint = nt.nodes.new("ShaderNodeMix"); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'
tint.inputs[0].default_value = 1.0
nt.links.new(mul.outputs[0], tint.inputs[6])
tint.inputs[7].default_value = (0.8, 0.9, 1.0, 1)
nt.links.new(tint.outputs[2], emi.inputs["Color"])
nt.links.new(emi.outputs[0], outn.inputs["Surface"])
scr.data.materials.append(sm)

scene.frame_start = 1
scene.frame_end = 96
w = wn.inputs["W"]
w.default_value = 0; w.keyframe_insert("default_value", frame=1)
w.default_value = 950; w.keyframe_insert("default_value", frame=96)
try:
    for fc in sm.node_tree.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
except Exception:
    pass

# Antennas
for ang in (-30, 35):
    a = math.radians(ang)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.9)
    r = bpy.context.object
    r.rotation_euler = (0, a, 0)
    r.location = (0.1 + 0.45*math.sin(a), 0.1, tz + 0.48 + 0.45*math.cos(a))
    r.data.materials.append(chrome)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(0.1, 0.1, tz + 0.47))
bpy.context.object.data.materials.append(plastic)
bpy.ops.object.shade_smooth()

# Lights
bpy.ops.object.light_add(type='POINT', location=(-0.15, -0.9, tz))
gl = bpy.context.object; gl.data.energy = 40; gl.data.color = (0.75, 0.85, 1.0)
bpy.ops.object.light_add(type='AREA', location=(-2.5, -2, 3.5))
k = bpy.context.object; k.data.energy = 120; k.data.size = 2; k.data.color = (1.0, 0.8, 0.6)
k.rotation_euler = (math.radians(50), 0, math.radians(-50))
scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.01, 0.012, 0.02, 1)

# Camera
bpy.ops.object.camera_add(location=(-1.1, -3.4, 1.65))
cam = bpy.context.object
d = Vector((-0.05, 0, tz)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 45
scene.camera = cam

for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = eng; break
    except Exception:
        pass

# Compositor: glare + film grain
def setup_comp():
    tree = None; out_sock = None
    if hasattr(scene, "compositing_node_group"):
        tree = bpy.data.node_groups.new("Comp", 'CompositorNodeTree')
        scene.compositing_node_group = tree
        tree.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        go = tree.nodes.new("NodeGroupOutput")
        out_sock = go.inputs[0]
    else:
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        out_sock = tree.nodes.new("CompositorNodeComposite").inputs[0]
    rl = tree.nodes.new("CompositorNodeRLayers")
    cur = rl.outputs["Image"]
    try:
        g = tree.nodes.new("CompositorNodeGlare")
        try: g.glare_type = 'FOG_GLOW'
        except Exception: pass
        tree.links.new(cur, g.inputs[0]); cur = g.outputs[0]
    except Exception:
        pass
    grain = None
    try:
        n = tree.nodes.new("ShaderNodeTexWhiteNoise")
        n.noise_dimensions = '3D'
        grain = n.outputs["Value"]
    except Exception:
        try:
            tex = bpy.data.textures.new("Grain", 'NOISE')
            n = tree.nodes.new("CompositorNodeTexture"); n.texture = tex
            grain = n.outputs[0]
        except Exception:
            grain = None
    if grain is not None:
        try:
            mx = tree.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'OVERLAY'
            mx.inputs[0].default_value = 0.12
            tree.links.new(cur, mx.inputs[6]); tree.links.new(grain, mx.inputs[7])
            cur = mx.outputs[2]
        except Exception:
            try:
                mx = tree.nodes.new("CompositorNodeMixRGB"); mx.blend_type = 'OVERLAY'
                mx.inputs[0].default_value = 0.12
                tree.links.new(cur, mx.inputs[1]); tree.links.new(grain, mx.inputs[2])
                cur = mx.outputs[0]
            except Exception:
                pass
    tree.links.new(cur, out_sock)

try:
    setup_comp()
except Exception as e:
    print("Compositor setup failed:", e)
