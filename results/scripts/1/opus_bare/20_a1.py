import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
    try:
        scene.render.engine = eng
        break
    except Exception:
        pass
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.frame_start = 1
scene.frame_end = 72

def mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

wood = mat("Wood", (0.25, 0.12, 0.05), 0.4)
dark = mat("DarkPlastic", (0.02, 0.02, 0.02), 0.35)
chrome = mat("Chrome", (0.8, 0.8, 0.8), 0.15, 1.0)
floor_m = mat("Floor", (0.15, 0.13, 0.12), 0.8)

# Static screen material
scr = bpy.data.materials.new("Static")
scr.use_nodes = True
nt = scr.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
em = nt.nodes.new("ShaderNodeEmission")
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.noise_dimensions = '4D'
noise.inputs["Scale"].default_value = 400.0
noise.inputs["Detail"].default_value = 0.0
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.4
ramp.color_ramp.elements[1].position = 0.6
ramp.color_ramp.elements[1].color = (0.85, 0.95, 1.0, 1)
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
em.inputs["Strength"].default_value = 4.0
nt.links.new(em.outputs[0], out.inputs["Surface"])
try:
    d = noise.inputs["W"].driver_add("default_value").driver
    d.expression = "frame*3.7"
except Exception:
    noise.inputs["W"].keyframe_insert("default_value", frame=1)
    noise.inputs["W"].default_value = 250
    noise.inputs["W"].keyframe_insert("default_value", frame=72)

def add(obj, m):
    obj.data.materials.append(m)
    return obj

# TV body
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1.0))
body = bpy.context.object
body.scale = (1.0, 0.8, 0.75)
bv = body.modifiers.new("Bevel", "BEVEL"); bv.width = 0.12; bv.segments = 5
add(body, wood)
bpy.ops.object.shade_smooth()

# Bezel
bpy.ops.mesh.primitive_cube_add(location=(-0.2, -0.79, 1.0))
bez = bpy.context.object
bez.scale = (0.68, 0.03, 0.6)
bv = bez.modifiers.new("Bevel", "BEVEL"); bv.width = 0.08; bv.segments = 4
add(bez, dark)

# Screen (slightly bulged)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(-0.2, -0.78, 1.0), segments=48, ring_count=24)
s = bpy.context.object
s.scale = (0.58, 0.06, 0.48)
add(s, scr)
bpy.ops.object.shade_smooth()

# Knobs & speaker panel
for i, z in enumerate((1.3, 1.0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.08, location=(0.72, -0.82, z), rotation=(math.pi/2, 0, 0))
    add(bpy.context.object, chrome)
for k in range(5):
    bpy.ops.mesh.primitive_cube_add(location=(0.72, -0.805, 0.5 + k*0.07))
    g = bpy.context.object
    g.scale = (0.14, 0.01, 0.012)
    add(g, dark)

# Legs
for x in (-0.8, 0.8):
    for y in (-0.6, 0.6):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.35, location=(x, y, 0.1))
        add(bpy.context.object, dark)

# Antenna
for ang in (-0.5, 0.5):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=1.1, location=(math.sin(ang)*0.5, 0, 1.75 + 0.5*math.cos(ang)), rotation=(0, ang, 0))
    add(bpy.context.object, chrome)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 1.78))
add(bpy.context.object, dark)

# Floor & wall
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.07))
add(bpy.context.object, floor_m)
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 3, 5), rotation=(math.pi/2, 0, 0))
add(bpy.context.object, mat("Wall", (0.08, 0.09, 0.1), 0.9))

# Lights
bpy.ops.object.light_add(type='AREA', location=(-3, -3, 4))
l = bpy.context.object; l.data.energy = 150; l.data.size = 3
l.rotation_euler = (math.radians(50), 0, math.radians(-45))
l.data.color = (1.0, 0.8, 0.6)
bpy.ops.object.light_add(type='POINT', location=(-0.2, -2.0, 1.0))
l2 = bpy.context.object; l2.data.energy = 40; l2.data.color = (0.7, 0.85, 1.0)

# World
w = scene.world or bpy.data.worlds.new("World")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.005, 0.005, 0.008, 1)

# Camera
bpy.ops.object.camera_add(location=(1.4, -4.6, 1.6))
cam = bpy.context.object
cam.data.lens = 45
tgt = bpy.data.objects.new("Target", None)
scene.collection.objects.link(tgt)
tgt.location = (0, 0, 1.0)
c = cam.constraints.new("TRACK_TO"); c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
scene.camera = cam

# Compositor: glow + film grain
try:
    tree = None
    new_api = hasattr(scene, "compositing_node_group")
    if new_api:
        tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
        scene.compositing_node_group = tree
        tree.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        outn = tree.nodes.new("NodeGroupOutput")
    else:
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        outn = tree.nodes.new("CompositorNodeComposite")
    rl = tree.nodes.new("CompositorNodeRLayers")
    cur = rl.outputs["Image"]
    try:
        gl = tree.nodes.new("CompositorNodeGlare")
        try:
            gl.glare_type = 'FOG_GLOW'
        except Exception:
            try:
                gl.inputs["Type"].default_value = 'Fog Glow'
            except Exception:
                pass
        tree.links.new(cur, gl.inputs["Image"])
        cur = gl.outputs["Image"]
    except Exception:
        pass
    grain = None
    try:
        tex = bpy.data.textures.new("Grain", 'NOISE')
        tn = tree.nodes.new("CompositorNodeTexture")
        tn.texture = tex
        grain = tn.outputs[-1]
    except Exception:
        try:
            nz = tree.nodes.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = 2000.0
            nz.inputs["Detail"].default_value = 0.0
            grain = nz.outputs["Color"]
        except Exception:
            grain = None
    if grain is not None:
        try:
            mx = tree.nodes.new("ShaderNodeMix")
            mx.data_type = 'RGBA'
            mx.blend_type = 'OVERLAY'
            cols = [s for s in mx.inputs if s.type == 'RGBA']
            mx.inputs[0].default_value = 0.18
            tree.links.new(cur, cols[0])
            tree.links.new(grain, cols[1])
            cur = [s for s in mx.outputs if s.type == 'RGBA'][0]
        except Exception:
            mx = tree.nodes.new("CompositorNodeMixRGB")
            mx.blend_type = 'OVERLAY'
            mx.inputs[0].default_value = 0.18
            tree.links.new(cur, mx.inputs[1])
            tree.links.new(grain, mx.inputs[2])
            cur = mx.outputs[0]
    tree.links.new(cur, outn.inputs[0])
except Exception as e:
    print("Compositor setup failed:", e)
