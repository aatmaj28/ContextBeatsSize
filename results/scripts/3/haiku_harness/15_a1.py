import bpy
import bmesh
import math
from mathutils import Vector

# ---------------------------------------------------------------
# Clean up
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.resolution_percentage = 100
scene.frame_start = 1
scene.frame_end = 1

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def link(obj):
    bpy.context.collection.objects.link(obj)
    return obj

def make_box(name, loc, size, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me))
    obj.location = Vector(loc)
    obj.data.materials.append(mat)
    return obj

def emission_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m

def surface_mat(name, color, roughness, metallic):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return m

# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
hull_mat = surface_mat("HullMetal", (0.12, 0.14, 0.17), 0.45, 0.8)
rib_mat = surface_mat("Rib", (0.25, 0.27, 0.30), 0.35, 0.9)
cyan_mat = emission_mat("GlowCyan", (0.0, 0.85, 1.0), 25.0)
magenta_mat = emission_mat("GlowMagenta", (1.0, 0.15, 0.7), 22.0)
white_mat = emission_mat("GlowFloor", (0.8, 0.9, 1.0), 15.0)

# ---------------------------------------------------------------
# Corridor shell (inward-facing box)
# ---------------------------------------------------------------
W, L, H = 4.0, 30.0, 3.5
shell_me = bpy.data.meshes.new("CorridorShell")
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co.x *= W
    v.co.y *= L
    v.co.z *= H
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
bm.to_mesh(shell_me)
bm.free()
shell = link(bpy.data.objects.new("CorridorShell", shell_me))
shell.location = (0.0, 0.0, H / 2)
shell.data.materials.append(hull_mat)

# ---------------------------------------------------------------
# Structural ribs along the walls
# ---------------------------------------------------------------
for i, y in enumerate([-12, -6, 0, 6, 12]):
    make_box(f"RibL{i}", (-W / 2 + 0.1, y, H / 2), (0.2, 0.35, H), rib_mat)
    make_box(f"RibR{i}", (W / 2 - 0.1, y, H / 2), (0.2, 0.35, H), rib_mat)

# ---------------------------------------------------------------
# Glowing light strips
# ---------------------------------------------------------------
make_box("StripWallL", (-W / 2 + 0.04, 0, 0.3), (0.06, L - 2, 0.08), cyan_mat)
make_box("StripWallR", (W / 2 - 0.04, 0, 0.3), (0.06, L - 2, 0.08), magenta_mat)
make_box("StripCeilL", (-0.8, 0, H - 0.06), (0.25, L - 2, 0.05), white_mat)
make_box("StripCeilR", (0.8, 0, H - 0.06), (0.25, L - 2, 0.05), white_mat)
make_box("StripFloor", (0.0, 0, 0.012), (0.5, L - 2, 0.02), white_mat)

# ---------------------------------------------------------------
# Lights that spill colour onto the walls
# ---------------------------------------------------------------
for i, y in enumerate([-10, 0, 10]):
    for side, color in ((-1, (0.0, 0.8, 1.0)), (1, (1.0, 0.2, 0.7))):
        ld = bpy.data.lights.new(f"Glow{i}{side}", 'POINT')
        ld.energy = 60.0
        ld.color = color
        ld.shadow_soft_size = 0.25
        lo = link(bpy.data.objects.new(ld.name, ld))
        lo.location = (side * (W / 2 - 0.5), y, 2.4)

# Soft overhead fill
fill = bpy.data.lights.new("Fill", 'AREA')
fill.energy = 40.0
fill.size = 3.0
fill.color = (0.6, 0.7, 1.0)
fo = link(bpy.data.objects.new("Fill", fill))
fo.location = (0, 0, H - 0.3)
fo.rotation_euler = (0, 0, 0)

# ---------------------------------------------------------------
# World: dark blue-black ambience
# ---------------------------------------------------------------
world = bpy.data.worlds.new("SpaceDark")
scene.world = world
wnt = world.node_tree
for n in wnt.nodes:
    if n.type == 'BACKGROUND':
        n.inputs["Color"].default_value = (0.01, 0.015, 0.03, 1.0)
        n.inputs["Strength"].default_value = 1.0

# ---------------------------------------------------------------
# Camera at the corridor entrance looking down its length
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("CorridorCam")
cam_data.lens = 28.0
cam = link(bpy.data.objects.new("CorridorCam", cam_data))
cam.location = (0.0, -12.5, 1.5)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam

# ---------------------------------------------------------------
# Compositor: vignette multiplied over the render
# ---------------------------------------------------------------
w, h = scene.render.resolution_x, scene.render.resolution_y

vig_img = bpy.data.images.new("VignetteMask", width=w, height=h,
                              alpha=True, float_buffer=True)
pixels = []
half_w = w * 0.5
half_h = h * 0.5
for py in range(h):
    ny = (py - half_h) / half_h
    for px in range(w):
        nx = (px - half_w) / half_w
        d = math.sqrt(nx * nx + ny * ny) / math.sqrt(2.0)
        t = min(1.0, max(0.0, (d - 0.45) / (1.0 - 0.45)))
        v = 1.0 - 0.7 * t * t * (3.0 - 2.0 * t)
        pixels.extend((v, v, v, 1.0))
vig_img.pixels.foreach_set(pixels)
vig_img.update()

ctree = bpy.data.node_groups.new("CorridorComp", "CompositorNodeTree")
scene.compositing_node_group = ctree

rlayers = ctree.nodes.new("CompositorNodeRLayers")
img_node = ctree.nodes.new("CompositorNodeImage")
img_node.image = vig_img

mix = ctree.nodes.new("ShaderNodeMix")
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.inputs["Factor"].default_value = 1.0

color_inputs = [s for s in mix.inputs if s.type == 'RGBA' and s.enabled]
color_out = [s for s in mix.outputs if s.type == 'RGBA'][0]

ctree.links.new(color_inputs[0], rlayers.outputs["Image"])
ctree.links.new(color_inputs[1], img_node.outputs["Image"])

group_out = ctree.nodes.new("NodeGroupOutput")
ctree.interface.new_socket(name="Image", in_out="OUTPUT",
                           socket_type="NodeSocketColor")
ctree.links.new(group_out.inputs[0], color_out)
