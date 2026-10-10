import bpy, bmesh, math, random
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.frame_start = 1
scene.frame_end = 48

def mat_principled(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

wood = mat_principled("Wood", (0.25, 0.12, 0.05), 0.45)
dark = mat_principled("DarkPlastic", (0.02, 0.02, 0.02), 0.35)
metal = mat_principled("Chrome", (0.8, 0.8, 0.8), 0.2, 1.0)
tablem = mat_principled("Table", (0.35, 0.3, 0.25), 0.7)
fabric = mat_principled("Speaker", (0.12, 0.09, 0.06), 0.9)

# Wood body
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0.9))
body = bpy.context.object
body.scale = (1.2, 0.8, 0.9)
bev = body.modifiers.new("Bevel", 'BEVEL'); bev.width = 0.08; bev.segments = 4
body.data.materials.append(wood)
bpy.ops.object.shade_smooth()

# Bezel
bpy.ops.mesh.primitive_cube_add(location=(-0.25, -0.79, 0.95))
bez = bpy.context.object
bez.scale = (0.85, 0.03, 0.65)
b2 = bez.modifiers.new("Bevel", 'BEVEL'); b2.width = 0.05; b2.segments = 3
bez.data.materials.append(dark)

# Curved screen
bpy.ops.mesh.primitive_grid_add(x_subdivisions=32, y_subdivisions=24, size=1, location=(-0.25, -0.83, 0.95))
scr = bpy.context.object
scr.scale = (1.5, 1.1, 1)
bm = bmesh.new(); bm.from_mesh(scr.data)
for v in bm.verts:
    v.co.z = 0.06 * (1 - (2*v.co.x)**2) * (1 - (2*v.co.y)**2)
bm.to_mesh(scr.data); bm.free()
scr.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.object.shade_smooth()

sm = bpy.data.materials.new("Static")
nt = sm.node_tree; nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord")
snap = nt.nodes.new("ShaderNodeVectorMath"); snap.operation = 'SNAP'
snap.inputs[1].default_value = (0.006, 0.006, 0.006)
wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '4D'
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.15
ramp.color_ramp.elements[1].position = 0.9
wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = 'BANDS'; wave.bands_direction = 'Y'
wave.inputs["Scale"].default_value = 60
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY_ADD'
mul.inputs[2].default_value = 0.75
mul.inputs[1].default_value = 0.25
tint = nt.nodes.new("ShaderNodeMix"); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'
tint.inputs[0].default_value = 1.0
tint.inputs[7].default_value = (0.75, 0.9, 1.0, 1)
emis = nt.nodes.new("ShaderNodeEmission"); emis.inputs["Strength"].default_value = 4.0
fac = nt.nodes.new("ShaderNodeMath"); fac.operation = 'MULTIPLY'
out = nt.nodes.new("ShaderNodeOutputMaterial")
L = nt.links.new
L(tc.outputs["UV"], snap.inputs[0])
L(snap.outputs[0], wn.inputs["Vector"])
L(wn.outputs["Value"], ramp.inputs["Fac"])
L(tc.outputs["UV"], wave.inputs["Vector"])
L(wave.outputs["Fac"], mul.inputs[0])
L(ramp.outputs["Color"], tint.inputs[6])
L(tint.outputs[2], emis.inputs["Color"])
L(mul.outputs[0], fac.inputs[0])
fac.inputs[1].default_value = 4.0
L(fac.outputs[0], emis.inputs["Strength"])
L(emis.outputs[0], out.inputs["Surface"])
try:
    d = wn.inputs["W"].driver_add("default_value")
    d.driver.expression = "frame * 1.37"
except Exception:
    pass
scr.data.materials.append(sm)

# Screen glow light
bpy.ops.object.light_add(type='AREA', location=(-0.25, -1.1, 0.95), rotation=(math.radians(90), 0, 0))
gl = bpy.context.object.data; gl.energy = 40; gl.color = (0.75, 0.85, 1.0); gl.size = 1.5

# Knobs
for i, z in enumerate((1.35, 0.95)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.1, location=(0.88, -0.83, z), rotation=(math.radians(90), 0, 0))
    k = bpy.context.object; k.data.materials.append(dark)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.12, location=(0.88, -0.85, z), rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(metal)
# Speaker grille
bpy.ops.mesh.primitive_cube_add(location=(0.88, -0.8, 0.45))
g = bpy.context.object; g.scale = (0.22, 0.02, 0.25); g.data.materials.append(fabric)

# Legs
for x in (-0.95, 0.95):
    for y in (-0.55, 0.55):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.4, location=(x, y, -0.2))
        bpy.context.object.data.materials.append(metal)

# Antennas
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, 0, 1.8))
bpy.context.object.data.materials.append(dark)
for a in (-30, 30):
    r = math.radians(a)
    ln = 1.4
    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=ln,
        location=(math.sin(r)*ln/2, 0, 1.8 + math.cos(r)*ln/2), rotation=(0, r, 0))
    bpy.context.object.data.materials.append(metal)

# Floor / table
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.4))
bpy.context.object.data.materials.append(tablem)

# Lights
bpy.ops.object.light_add(type='AREA', location=(4, -3, 5))
k = bpy.context.object; k.data.energy = 250; k.data.size = 3; k.data.color = (1.0, 0.8, 0.6)
k.rotation_euler = (Vector((0, 0, 1)) - k.location).to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("World"); scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.01, 0.01, 0.015, 1)

# Camera
bpy.ops.object.camera_add(location=(2.6, -6.0, 2.0))
cam = bpy.context.object
cam.rotation_euler = (Vector((0, 0, 0.9)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 45
scene.camera = cam

# Film grain via compositor
W, H = scene.render.resolution_x, scene.render.resolution_y
img = bpy.data.images.new("Grain", W, H, float_buffer=True)
rnd = random.random
px = []
for _ in range(W * H):
    v = 0.5 + (rnd() - 0.5) * 0.6
    px.extend((v, v, v, 1.0))
img.pixels.foreach_set(px)

tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
scene.compositing_node_group = tree
rl = tree.nodes.new("CompositorNodeRLayers")
im = tree.nodes.new("CompositorNodeImage"); im.image = img
mix = tree.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'OVERLAY'
mix.inputs[0].default_value = 0.35
outn = tree.nodes.new("NodeGroupOutput")
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
tree.links.new(rl.outputs["Image"], mix.inputs[6])
tree.links.new(im.outputs["Image"], mix.inputs[7])
tree.links.new(mix.outputs[2], outn.inputs[0])
