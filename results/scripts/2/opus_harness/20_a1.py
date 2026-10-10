import bpy, math

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.frame_start = 1
scene.frame_end = 120
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

def mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

wood = mat("Wood", (0.25, 0.12, 0.05), 0.45)
plastic = mat("Plastic", (0.02, 0.02, 0.02), 0.3)
metal = mat("Chrome", (0.8, 0.8, 0.8), 0.2, 1.0)
floor_m = mat("Table", (0.35, 0.3, 0.25), 0.7)
wall_m = mat("Wall", (0.15, 0.18, 0.22), 0.9)

# Screen material: animated static
scr = bpy.data.materials.new("Static")
nt = scr.node_tree
nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord")
mul = nt.nodes.new("ShaderNodeVectorMath"); mul.operation = 'MULTIPLY'
mul.inputs[1].default_value = (220, 180, 1)
flo = nt.nodes.new("ShaderNodeVectorMath"); flo.operation = 'FLOOR'
wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '4D'
wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = 'BANDS'; wave.bands_direction = 'Y'
wave.inputs["Scale"].default_value = 60
mixm = nt.nodes.new("ShaderNodeMath"); mixm.operation = 'MULTIPLY'
mapr = nt.nodes.new("ShaderNodeMapRange")
mapr.inputs["To Min"].default_value = 0.6
emi = nt.nodes.new("ShaderNodeEmission")
emi.inputs["Strength"].default_value = 4.0
tint = nt.nodes.new("ShaderNodeMix"); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'
tint.inputs[0].default_value = 1.0
tint.inputs[7].default_value = (0.75, 0.9, 1.0, 1)
out = nt.nodes.new("ShaderNodeOutputMaterial")
L = nt.links
L.new(tc.outputs["UV"], mul.inputs[0])
L.new(mul.outputs[0], flo.inputs[0])
L.new(flo.outputs[0], wn.inputs["Vector"])
L.new(tc.outputs["UV"], wave.inputs["Vector"])
L.new(wave.outputs["Fac"], mapr.inputs["Value"])
L.new(wn.outputs["Value"], mixm.inputs[0])
L.new(mapr.outputs["Result"], mixm.inputs[1])
L.new(mixm.outputs[0], tint.inputs[6])
L.new(tint.outputs[2], emi.inputs["Color"])
L.new(emi.outputs[0], out.inputs["Surface"])
w = wn.inputs["W"]
w.default_value = 0.0
w.keyframe_insert("default_value", frame=1)
w.default_value = 600.0
w.keyframe_insert("default_value", frame=120)

def cube(name, loc, scale, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("Bevel", 'BEVEL'); bv.width = bevel; bv.segments = 4
    o.data.materials.append(m)
    return o

def cyl(name, loc, r, d, rot, m):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=32)
    o = bpy.context.object; o.name = name
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o

# Scene base
cube("Table", (0, 0, -0.05), (3, 2, 0.05), floor_m)
cube("Wall", (0, 1.5, 1.5), (4, 0.05, 1.6), wall_m)

# TV body
bz = 0.25 + 0.45
cube("Body", (0, 0, bz), (0.6, 0.45, 0.45), wood, 0.06)
cube("Bezel", (-0.15, -0.44, bz), (0.42, 0.03, 0.34), plastic, 0.04)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.15, -0.475, bz), rotation=(math.radians(90), 0, 0))
s = bpy.context.object; s.name = "Screen"
s.scale = (0.72, 0.58, 1)
s.data.materials.append(scr)
# panel & knobs
cube("Panel", (0.43, -0.44, bz), (0.12, 0.03, 0.34), plastic, 0.02)
for i, z in enumerate((0.18, 0.0)):
    cyl(f"Knob{i}", (0.43, -0.49, bz + z), 0.055, 0.06, (math.radians(90), 0, 0), metal)
for i in range(5):
    cube(f"Grille{i}", (0.43, -0.475, bz - 0.15 - i * 0.035), (0.08, 0.005, 0.008), metal)
# legs
for x in (-0.5, 0.5):
    for y in (-0.35, 0.35):
        cyl("Leg", (x, y, 0.125), 0.025, 0.25, (0, 0, 0), metal)
# antennas
cyl("AntBase", (0, 0.05, bz + 0.47), 0.08, 0.05, (0, 0, 0), plastic)
for a in (-30, 30):
    r = math.radians(a)
    cyl("Antenna", (math.sin(r) * 0.35, 0.05, bz + 0.47 + math.cos(r) * 0.35), 0.008, 0.7, (0, r, 0), metal)

# Screen glow light
bpy.ops.object.light_add(type='AREA', location=(-0.15, -0.6, bz), rotation=(math.radians(-90), 0, 0))
gl = bpy.context.object.data; gl.energy = 30; gl.color = (0.75, 0.88, 1.0); gl.size = 0.8
bpy.ops.object.light_add(type='AREA', location=(2, -2, 3))
k = bpy.context.object; k.data.energy = 120; k.data.size = 2; k.data.color = (1, 0.8, 0.6)
k.rotation_euler = (math.radians(50), 0, math.radians(45))

world = bpy.data.worlds.new("World"); scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1)

# Camera
bpy.ops.object.empty_add(location=(0, -0.2, bz))
tgt = bpy.context.object
bpy.ops.object.camera_add(location=(1.3, -3.2, 1.4))
cam = bpy.context.object
cam.data.lens = 45
c = cam.constraints.new('TRACK_TO'); c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
scene.camera = cam

# Compositor: film grain
tree = bpy.data.node_groups.new("Grain", "CompositorNodeTree")
scene.compositing_node_group = tree
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = tree.nodes.new("CompositorNodeRLayers")
go = tree.nodes.new("NodeGroupOutput")
try:
    coords = tree.nodes.new("CompositorNodeImageCoordinates")
    noise = tree.nodes.new("ShaderNodeTexWhiteNoise")
    noise.noise_dimensions = '4D'
    tree.links.new(coords.outputs["Pixel"], noise.inputs["Vector"])
    nw = noise.inputs["W"]
    nw.default_value = 0.0
    nw.keyframe_insert("default_value", frame=1)
    nw.default_value = 300.0
    nw.keyframe_insert("default_value", frame=120)
    mix = tree.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'; mix.blend_type = 'OVERLAY'
    mix.inputs[0].default_value = 0.18
    tree.links.new(rl.outputs["Image"], mix.inputs[6])
    tree.links.new(noise.outputs["Value"], mix.inputs[7])
    tree.links.new(mix.outputs[2], go.inputs[0])
except Exception:
    tree.links.new(rl.outputs["Image"], go.inputs[0])
