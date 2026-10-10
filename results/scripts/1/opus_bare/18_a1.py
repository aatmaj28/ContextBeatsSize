import bpy
import bmesh
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- helpers ----------
def set_input(node, name, value):
    if name in node.inputs:
        try:
            node.inputs[name].default_value = value
        except Exception:
            pass

def make_principled(name, color, metallic=0.0, rough=0.5, aniso=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", (*color, 1.0))
    set_input(bsdf, "Metallic", metallic)
    set_input(bsdf, "Roughness", rough)
    set_input(bsdf, "Anisotropic", aniso)
    return mat, bsdf, nt

def brushed_metal(name, color=(0.75, 0.75, 0.77)):
    mat, bsdf, nt = make_principled(name, color, 1.0, 0.25, 0.7)
    texco = nt.nodes.new("ShaderNodeTexCoord")
    mapn = nt.nodes.new("ShaderNodeMapping")
    mapn.inputs["Scale"].default_value = (400.0, 2.0, 400.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 8.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.18
    mr.inputs["To Max"].default_value = 0.35
    nt.links.new(texco.outputs["Object"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    return mat

def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

def bevel(obj, width=0.008, seg=4):
    m = obj.modifiers.new("Bevel", 'BEVEL')
    m.width = width
    m.segments = seg
    m.limit_method = 'ANGLE'

def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

def box(name, size, loc, mat, bev=0.008):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, mat)
    if bev > 0:
        bevel(o, bev)
    smooth(o)
    return o

def cyl(name, r, depth, loc, mat, rot=(0, 0, 0), verts=48, bev=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                        location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    assign(o, mat)
    if bev > 0:
        bevel(o, bev, 3)
    smooth(o)
    return o

# ---------- materials ----------
metal = brushed_metal("BrushedSteel")
chrome, _, _ = make_principled("Chrome", (0.9, 0.9, 0.92), 1.0, 0.08)
black, _, _ = make_principled("MatteBlack", (0.02, 0.02, 0.022), 0.0, 0.85)
plastic, _, _ = make_principled("BlackPlastic", (0.015, 0.015, 0.015), 0.0, 0.4)
ceramic, _, _ = make_principled("Ceramic", (0.92, 0.9, 0.86), 0.0, 0.15)
coffee, _, _ = make_principled("Coffee", (0.08, 0.035, 0.015), 0.0, 0.1)
crema, _, _ = make_principled("Crema", (0.45, 0.25, 0.1), 0.0, 0.5)
counter, _, _ = make_principled("Counter", (0.35, 0.3, 0.25), 0.0, 0.45)
wall, _, _ = make_principled("Wall", (0.6, 0.6, 0.58), 0.0, 0.9)
glass, gbsdf, _ = make_principled("GaugeFace", (0.95, 0.95, 0.95), 0.0, 0.3)

# ---------- environment ----------
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
assign(bpy.context.active_object, counter)
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0.6, 1.0), rotation=(math.radians(90), 0, 0))
assign(bpy.context.active_object, wall)

# ---------- machine ----------
# matte black base
box("Base", (0.40, 0.42, 0.06), (0, 0, 0.03), black, 0.01)
# back column body
box("Body", (0.36, 0.22, 0.32), (0, 0.09, 0.22), metal, 0.012)
# top overhang
box("TopHousing", (0.36, 0.40, 0.08), (0, 0.0, 0.40), metal, 0.012)
# black trim strip
box("TopTrim", (0.362, 0.402, 0.008), (0, 0.0, 0.36), black, 0.002)
# cup warmer rail
for x in (-0.16, 0.16):
    cyl("RailPost", 0.004, 0.03, (x, -0.17, 0.455), chrome)
    cyl("RailPostB", 0.004, 0.03, (x, 0.17, 0.455), chrome)
cyl("RailFront", 0.004, 0.32, (0, -0.17, 0.47), chrome, rot=(0, math.radians(90), 0))
cyl("RailBack", 0.004, 0.32, (0, 0.17, 0.47), chrome, rot=(0, math.radians(90), 0))
cyl("RailL", 0.004, 0.34, (-0.16, 0, 0.47), chrome, rot=(math.radians(90), 0, 0))
cyl("RailR", 0.004, 0.34, (0.16, 0, 0.47), chrome, rot=(math.radians(90), 0, 0))

# drip tray + grille
box("DripTray", (0.30, 0.18, 0.02), (0, -0.10, 0.07), black, 0.004)
for i in range(9):
    box("Grille", (0.28, 0.006, 0.004), (0, -0.175 + i * 0.019, 0.082), chrome, 0.0)

# group head
cyl("GroupHead", 0.045, 0.04, (0, -0.09, 0.34), chrome, bev=0.004)
cyl("GroupRing", 0.04, 0.02, (0, -0.09, 0.31), metal)

# portafilter
cyl("Portafilter", 0.038, 0.03, (0, -0.09, 0.287), chrome, bev=0.004)
box("PFArm", (0.02, 0.06, 0.015), (0, -0.15, 0.287), chrome, 0.004)
h = cyl("PFHandle", 0.012, 0.12, (0, -0.23, 0.28), plastic,
        rot=(math.radians(80), 0, 0), bev=0.004)
for dx in (-0.01, 0.01):
    cyl("Spout", 0.005, 0.02, (dx, -0.09, 0.265), chrome)

# steam wand
cyl("WandValve", 0.012, 0.03, (0.14, -0.15, 0.355), chrome)
bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
wand = bpy.context.active_object
wand.name = "SteamWand"
sp = wand.data.splines[0]
pts = sp.bezier_points
pts[0].co = Vector((0.14, -0.15, 0.34))
pts[0].handle_left = Vector((0.14, -0.15, 0.36))
pts[0].handle_right = Vector((0.14, -0.15, 0.30))
pts[1].co = Vector((0.155, -0.19, 0.17))
pts[1].handle_left = Vector((0.15, -0.17, 0.24))
pts[1].handle_right = Vector((0.16, -0.21, 0.10))
wand.data.bevel_depth = 0.005
wand.data.bevel_resolution = 4
wand.data.materials.append(chrome)
cyl("SteamKnob", 0.018, 0.025, (0.14, -0.21, 0.40), plastic,
    rot=(math.radians(90), 0, 0), bev=0.003)

# pressure gauge
cyl("GaugeBezel", 0.03, 0.012, (-0.08, -0.201, 0.40), chrome,
    rot=(math.radians(90), 0, 0), bev=0.002)
cyl("GaugeFace", 0.025, 0.004, (-0.08, -0.207, 0.40), glass,
    rot=(math.radians(90), 0, 0))
box("GaugeNeedle", (0.002, 0.001, 0.02), (-0.084, -0.21, 0.405), black, 0.0).rotation_euler[1] = math.radians(30)

# buttons
for i, x in enumerate((-0.02, 0.02, 0.06)):
    cyl("Button", 0.01, 0.01, (x, -0.204, 0.40), plastic,
        rot=(math.radians(90), 0, 0), bev=0.002)

# feet
for x in (-0.17, 0.17):
    for y in (-0.18, 0.18):
        cyl("Foot", 0.012, 0.006, (x, y, 0.003), plastic, verts=24)

# ---------- cup ----------
cyl("Saucer", 0.055, 0.008, (0, -0.09, 0.088), ceramic, verts=64, bev=0.003)

bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.03, depth=0.055,
                                    location=(0, -0.09, 0.12))
cup = bpy.context.active_object
cup.name = "Cup"
bm = bmesh.new()
bm.from_mesh(cup.data)
top = [f for f in bm.faces if f.normal.z > 0.9]
bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
bm.to_mesh(cup.data)
bm.free()
sol = cup.modifiers.new("Solid", 'SOLIDIFY')
sol.thickness = 0.004
sol.offset = -1
bevel(cup, 0.0015, 2)
sub = cup.modifiers.new("Sub", 'SUBSURF')
sub.levels = 1
sub.render_levels = 2
assign(cup, ceramic)
smooth(cup)

bpy.ops.mesh.primitive_torus_add(major_radius=0.014, minor_radius=0.004,
                                 location=(0.036, -0.09, 0.122),
                                 rotation=(math.radians(90), 0, 0))
handle = bpy.context.active_object
handle.scale = (0.8, 1.0, 1.0)
assign(handle, ceramic)
smooth(handle)

cyl("CoffeeSurface", 0.0255, 0.002, (0, -0.09, 0.138), crema, verts=64)
cyl("CoffeeBody", 0.0255, 0.04, (0, -0.09, 0.117), coffee, verts=64)

# ---------- lighting ----------
def area(name, loc, energy, size, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy = energy
    d.size = size
    d.color = color
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.location = loc
    direction = Vector((0, 0, 0.22)) - Vector(loc)
    o.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return o

area("Key", (-0.9, -0.9, 1.1), 120, 0.8, (1.0, 0.95, 0.88))
area("Fill", (1.0, -0.7, 0.6), 40, 1.0, (0.85, 0.9, 1.0))
area("Rim", (0.4, 0.5, 1.2), 70, 0.5)
area("Top", (0, 0, 1.4), 30, 1.5)

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.055, 1)
    bg.inputs["Strength"].default_value = 1.0

# ---------- camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.75, -1.05, 0.55)
target = Vector((0, -0.02, 0.22))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
