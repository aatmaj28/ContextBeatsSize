import bpy, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

wood = mat("Wood", (0.25, 0.12, 0.05), 0.4)
plastic = mat("Plastic", (0.03, 0.03, 0.03), 0.3)
metal = mat("Metal", (0.7, 0.7, 0.7), 0.25, 1.0)
floor_m = mat("Floor", (0.35, 0.3, 0.25), 0.7)

# Static screen material
scr = bpy.data.materials.new("Static")
nt = scr.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
em = nt.nodes.new("ShaderNodeEmission")
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.noise_dimensions = '4D'
noise.inputs["Scale"].default_value = 350.0
noise.inputs["Detail"].default_value = 0.0
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[1].position = 0.65
wave = nt.nodes.new("ShaderNodeTexWave")
wave.wave_type = 'BANDS'
wave.bands_direction = 'Z'
wave.inputs["Scale"].default_value = 60.0
mul = nt.nodes.new("ShaderNodeMix")
mul.data_type = 'RGBA'
mul.blend_type = 'MULTIPLY'
mul.inputs[0].default_value = 0.35
tint = nt.nodes.new("ShaderNodeMix")
tint.data_type = 'RGBA'
tint.blend_type = 'MULTIPLY'
tint.inputs[0].default_value = 1.0
tint.inputs[7].default_value = (0.75, 0.9, 1.0, 1)
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], mul.inputs[6])
nt.links.new(wave.outputs["Color"], mul.inputs[7])
nt.links.new(mul.outputs[2], tint.inputs[6])
nt.links.new(tint.outputs[2], em.inputs["Color"])
em.inputs["Strength"].default_value = 4.0
nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
scene.frame_start, scene.frame_end = 1, 48
w = noise.inputs["W"]
w.default_value = 0.0
w.keyframe_insert("default_value", frame=1)
w.default_value = 60.0
w.keyframe_insert("default_value", frame=48)

def cube(name, loc, size, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0]/2, size[1]/2, size[2]/2)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("Bevel", 'BEVEL')
        bv.width = bevel
        bv.segments = 4
    return o

def cyl(name, loc, r, d, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=32)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o

base_z = 0.35
cube("Cabinet", (0, 0, base_z + 0.55), (1.6, 1.0, 1.1), wood, 0.06)
cube("Bezel", (-0.2, -0.49, base_z + 0.55), (1.12, 0.06, 0.88), plastic, 0.04)
# slightly bulged screen
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(-0.2, -0.47, base_z + 0.55), segments=48, ring_count=24)
s = bpy.context.active_object
s.name = "Screen"
s.scale = (0.48, 0.06, 0.37)
s.data.materials.append(scr)
bpy.ops.object.shade_smooth()
# control panel
cube("Panel", (0.6, -0.49, base_z + 0.55), (0.28, 0.05, 0.85), plastic, 0.02)
for i, z in enumerate((0.85, 0.6)):
    cyl(f"Knob{i}", (0.6, -0.54, base_z + z), 0.07, 0.06, metal, (math.pi/2, 0, 0))
for i in range(6):
    cube(f"Grille{i}", (0.6, -0.52, base_z + 0.2 + i*0.04), (0.2, 0.01, 0.015), metal)
# legs
for x in (-0.65, 0.65):
    for y in (-0.35, 0.35):
        cyl("Leg", (x, y, base_z/2), 0.03, base_z, metal)
# antenna
top = base_z + 1.1
cyl("AntBase", (0, 0, top + 0.04), 0.1, 0.08, plastic)
for a in (-0.45, 0.45):
    L = 0.9
    cyl("Antenna", (math.sin(a)*L/2, 0, top + 0.05 + math.cos(a)*L/2), 0.008, L, metal, (0, a, 0))

bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(floor_m)

# lighting
bpy.ops.object.light_add(type='AREA', location=(2.5, -2.5, 3.0))
key = bpy.context.active_object
key.data.energy = 150
key.data.size = 2
key.rotation_euler = (Vector((0, 0, 0.9)) - key.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.light_add(type='POINT', location=(-0.2, -1.2, 0.9))
glow = bpy.context.active_object
glow.data.energy = 40
glow.data.color = (0.75, 0.88, 1.0)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.01, 0.015, 1)

# camera
bpy.ops.object.camera_add(location=(1.4, -3.6, 1.6))
cam = bpy.context.active_object
cam.rotation_euler = (Vector((-0.05, 0, 0.95)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 40
scene.camera = cam

# compositor with glow and film grain
tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
scene.compositing_node_group = tree
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = tree.nodes.new("CompositorNodeRLayers")
outn = tree.nodes.new("NodeGroupOutput")
current = rl.outputs["Image"]
try:
    gl = tree.nodes.new("CompositorNodeGlare")
    try:
        gl.inputs["Type"].default_value = "Fog Glow"
    except Exception:
        pass
    try:
        gl.inputs["Threshold"].default_value = 0.8
    except Exception:
        pass
    tree.links.new(current, gl.inputs["Image"])
    current = gl.outputs["Image"]
except Exception:
    pass
try:
    gn = tree.nodes.new("ShaderNodeTexNoise")
    gn.inputs["Scale"].default_value = 800.0
    gn.inputs["Detail"].default_value = 0.0
    mix = tree.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.blend_type = 'OVERLAY'
    mix.inputs[0].default_value = 0.25
    tree.links.new(current, mix.inputs[6])
    tree.links.new(gn.outputs["Color"], mix.inputs[7])
    current = mix.outputs[2]
except Exception:
    pass
tree.links.new(current, outn.inputs[0])
