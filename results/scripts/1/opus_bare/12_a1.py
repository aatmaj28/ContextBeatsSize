import bpy
import math

scene = bpy.context.scene

# Clean scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

# Render engine
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = eng
        break
    except Exception:
        pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
try:
    scene.view_settings.view_transform = 'AgX'
except Exception:
    pass

# World
world = bpy.data.worlds.new("World") if scene.world is None else scene.world
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.005, 0.005, 0.008, 1)
    bg.inputs["Strength"].default_value = 0.3

# ---------- Brick wall ----------
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.15, 0), rotation=(math.pi / 2, 0, 0))
wall = bpy.context.active_object
wall.name = "BrickWall"
wall.scale = (14, 9, 1)

wm = bpy.data.materials.new("DarkBrick")
wm.use_nodes = True
nt = wm.node_tree
nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
tc = nt.nodes.new('ShaderNodeTexCoord')
brick = nt.nodes.new('ShaderNodeTexBrick')
noise = nt.nodes.new('ShaderNodeTexNoise')
mix = nt.nodes.new('ShaderNodeMixRGB')
bump = nt.nodes.new('ShaderNodeBump')
nt.links.new(tc.outputs['Object'], brick.inputs['Vector'])
nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
brick.inputs['Color1'].default_value = (0.09, 0.03, 0.025, 1)
brick.inputs['Color2'].default_value = (0.05, 0.02, 0.018, 1)
brick.inputs['Mortar'].default_value = (0.03, 0.03, 0.03, 1)
brick.inputs['Scale'].default_value = 1.0
brick.inputs['Mortar Size'].default_value = 0.012
brick.inputs['Brick Width'].default_value = 0.08
brick.inputs['Row Height'].default_value = 0.035
noise.inputs['Scale'].default_value = 40.0
mix.blend_type = 'MULTIPLY'
mix.inputs['Fac'].default_value = 0.5
nt.links.new(brick.outputs['Color'], mix.inputs['Color1'])
nt.links.new(noise.outputs['Color'], mix.inputs['Color2'])
nt.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.9
bump.inputs['Strength'].default_value = 0.6
nt.links.new(brick.outputs['Fac'], bump.inputs['Height'])
nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
wall.data.materials.append(wm)

# ---------- Neon material ----------
def neon_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree
    n.nodes.clear()
    o = n.nodes.new('ShaderNodeOutputMaterial')
    e = n.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = color
    e.inputs['Strength'].default_value = strength
    n.links.new(e.outputs['Emission'], o.inputs['Surface'])
    return m

pink = neon_mat("NeonPink", (1.0, 0.08, 0.45, 1), 25.0)
pink_frame = neon_mat("NeonPinkFrame", (1.0, 0.15, 0.6, 1), 12.0)

# ---------- Neon text ----------
curve = bpy.data.curves.new("OPEN_curve", 'FONT')
curve.body = "OPEN"
curve.size = 1.4
curve.align_x = 'CENTER'
curve.align_y = 'CENTER'
curve.fill_mode = 'NONE'
curve.extrude = 0.0
curve.bevel_depth = 0.035
curve.bevel_resolution = 4
curve.resolution_u = 16
txt = bpy.data.objects.new("OPEN", curve)
scene.collection.objects.link(txt)
txt.rotation_euler = (math.pi / 2, 0, 0)
txt.location = (0, 0, 0)
curve.materials.append(pink)

# ---------- Neon frame (rounded-ish rectangle tube) ----------
fc = bpy.data.curves.new("Frame", 'CURVE')
fc.dimensions = '3D'
fc.bevel_depth = 0.025
fc.bevel_resolution = 4
sp = fc.splines.new('POLY')
w, h, c = 2.4, 1.05, 0.2
pts = [(-w + c, -h), (w - c, -h), (w, -h + c), (w, h - c), (w - c, h),
       (-w + c, h), (-w, h - c), (-w, -h + c)]
sp.points.add(len(pts) - 1)
for p, (x, z) in zip(sp.points, pts):
    p.co = (x, -0.02, z, 1)
sp.use_cyclic_u = True
frame = bpy.data.objects.new("NeonFrame", fc)
scene.collection.objects.link(frame)
fc.materials.append(pink_frame)

# Small mounting standoffs
mount = bpy.data.materials.new("Metal")
mount.use_nodes = True
mb = mount.node_tree.nodes.get("Principled BSDF")
mb.inputs['Base Color'].default_value = (0.3, 0.3, 0.32, 1)
mb.inputs['Metallic'].default_value = 1.0
mb.inputs['Roughness'].default_value = 0.35
for x in (-1.8, -0.6, 0.6, 1.8):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.17, location=(x, 0.07, -0.55),
                                        rotation=(math.pi / 2, 0, 0))
    bpy.context.active_object.data.materials.append(mount)

# ---------- Lights ----------
ld = bpy.data.lights.new("NeonSpill", 'POINT')
ld.color = (1.0, 0.2, 0.55)
ld.energy = 120
ld.shadow_soft_size = 1.5
lo = bpy.data.objects.new("NeonSpill", ld)
lo.location = (0, -0.6, 0)
scene.collection.objects.link(lo)

ad = bpy.data.lights.new("Fill", 'AREA')
ad.energy = 40
ad.size = 6
ad.color = (0.6, 0.7, 1.0)
ao = bpy.data.objects.new("Fill", ad)
ao.location = (3, -5, 4)
ao.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(ao)

# ---------- Camera ----------
cd = bpy.data.cameras.new("Camera")
cd.lens = 40
cam = bpy.data.objects.new("Camera", cd)
cam.location = (0.6, -8.0, 0.4)
scene.collection.objects.link(cam)
con = cam.constraints.new('TRACK_TO')
con.target = txt
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

# ---------- Compositor glare ----------
def set_input(node, name, value):
    s = node.inputs.get(name)
    if s is not None:
        try:
            s.default_value = value
            return True
        except Exception:
            pass
    return False

tree = None
new_api = hasattr(scene, "compositing_node_group")
if new_api:
    tree = bpy.data.node_groups.new("Compositing", 'CompositorNodeTree')
    scene.compositing_node_group = tree
    tree.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    out_node = tree.nodes.new('NodeGroupOutput')
else:
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()
    out_node = tree.nodes.new('CompositorNodeComposite')

rl = tree.nodes.new('CompositorNodeRLayers')
rl.location = (-400, 0)
glare = tree.nodes.new('CompositorNodeGlare')
glare.location = (-100, 0)
out_node.location = (200, 0)

# Glare settings (old properties or new socket inputs)
try:
    glare.glare_type = 'FOG_GLOW'
except Exception:
    for v in ('Fog Glow', 'FOG_GLOW', 'Bloom'):
        if set_input(glare, 'Type', v):
            break
try:
    glare.quality = 'HIGH'
except Exception:
    set_input(glare, 'Quality', 'High')
try:
    glare.threshold = 0.8
except Exception:
    set_input(glare, 'Threshold', 0.8)
try:
    glare.size = 9
except Exception:
    set_input(glare, 'Size', 0.8)
set_input(glare, 'Strength', 1.0)
try:
    glare.mix = 0.0
except Exception:
    pass

tree.links.new(rl.outputs['Image'], glare.inputs['Image'])
tree.links.new(glare.outputs['Image'], out_node.inputs[0])

scene.frame_start = 1
scene.frame_end = 1
