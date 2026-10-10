import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

def mat_pbr(name, color, metal=0.8, rough=0.35):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    return m

def mat_emit(name, color, strength):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], out.inputs[0])
    return m

def box(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.materials.append(mat)
    return o

wall = mat_pbr("Wall", (0.08, 0.09, 0.1), 0.7, 0.4)
floor_m = mat_pbr("Floor", (0.04, 0.045, 0.05), 0.9, 0.25)
rib_m = mat_pbr("Rib", (0.15, 0.16, 0.18), 0.9, 0.3)
cyan = mat_emit("Cyan", (0.1, 0.7, 1.0), 25)
orange = mat_emit("Orange", (1.0, 0.35, 0.05), 15)
white = mat_emit("White", (0.85, 0.9, 1.0), 8)

W, H, L = 4.0, 3.5, 40.0
cy = L / 2 - 4
box("Floor", (0, cy, -0.05), (W + 1, L, 0.1), floor_m)
box("Ceiling", (0, cy, H + 0.05), (W + 1, L, 0.1), wall)
box("WallL", (-W / 2 - 0.05, cy, H / 2), (0.1, L, H), wall)
box("WallR", (W / 2 + 0.05, cy, H / 2), (0.1, L, H), wall)
box("EndWall", (0, cy + L / 2, H / 2), (W, 0.1, H), wall)

# Long glowing strips along walls
for side in (-1, 1):
    x = side * (W / 2 - 0.02)
    box("StripLow", (x, cy, 0.4), (0.04, L, 0.05), cyan)
    box("StripHigh", (x, cy, H - 0.5), (0.04, L, 0.03), cyan)
    box("FloorEdge", (side * (W / 2 - 0.35), cy, 0.005), (0.03, L, 0.02), orange)

# Ribs / frames
y = -2.0
while y < cy + L / 2 - 1:
    for side in (-1, 1):
        box("Rib", (side * (W / 2 - 0.15), y, H / 2), (0.3, 0.35, H), rib_m)
        box("RibLight", (side * (W / 2 - 0.31), y, H / 2), (0.02, 0.08, H * 0.6), orange)
    box("RibTop", (0, y, H - 0.15), (W, 0.35, 0.3), rib_m)
    box("CeilPanel", (0, y + 1.5, H - 0.01), (1.2, 1.6, 0.02), white)
    y += 3.0

# Grates on floor
for i in range(int(L / 1.5)):
    box("Grate", (0, -2 + i * 1.5, 0.01), (1.6, 0.08, 0.02), rib_m)

# Lights
for i in range(6):
    bpy.ops.object.light_add(type='POINT', location=(0, i * 6.0, H - 0.6))
    l = bpy.context.active_object
    l.data.energy = 300
    l.data.color = (0.7, 0.85, 1.0)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.005, 0.007, 0.01, 1)

# Camera
bpy.ops.object.camera_add(location=(0.4, -3.0, 1.5))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(90), 0, math.radians(3))
cam.data.lens = 22
scene.camera = cam

# Compositor: glare + vignette
try:
    tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    scene.compositing_node_group = tree
    tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers")
    img = rl.outputs["Image"]
    try:
        gl = tree.nodes.new("CompositorNodeGlare")
        try:
            gl.inputs["Type"].default_value = "Bloom"
        except Exception:
            pass
        tree.links.new(gl.inputs["Image"], img)
        img = gl.outputs["Image"]
    except Exception:
        pass
    el = tree.nodes.new("CompositorNodeEllipseMask")
    for k, v in (("Size", (0.85, 0.75)), ("Position", (0.5, 0.5)), ("Value", 1.0)):
        try:
            el.inputs[k].default_value = v
        except Exception:
            pass
    bl = tree.nodes.new("CompositorNodeBlur")
    try:
        bl.inputs["Type"].default_value = "Gaussian"
    except Exception:
        pass
    bl.inputs["Size"].default_value = (250, 250)
    tree.links.new(bl.inputs["Image"], el.outputs[0])
    mr = tree.nodes.new("ShaderNodeMapRange")
    mr.inputs[3].default_value = 0.2
    mr.inputs[4].default_value = 1.0
    tree.links.new(mr.inputs[0], bl.outputs[0])
    mix = tree.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1.0
    tree.links.new(mix.inputs[6], img)
    tree.links.new(mix.inputs[7], mr.outputs[0])
    out = tree.nodes.new("NodeGroupOutput")
    tree.links.new(out.inputs[0], mix.outputs[2])
except Exception as e:
    print("Compositor setup failed:", e)

scene.frame_start = 1
scene.frame_end = 1
