import bpy, bmesh, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- Materials ----------
def principled(name, color, metallic=0.0, rough=0.5, aniso=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = aniso
    return m

def brushed_metal():
    m = principled("BrushedSteel", (0.8, 0.8, 0.82), 1.0, 0.25, 0.6)
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 400.0, 400.0)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 8.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.18
    mr.inputs["To Max"].default_value = 0.38
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    return m

M_STEEL = brushed_metal()
M_BLACK = principled("MatteBlack", (0.02, 0.02, 0.022), 0.0, 0.85)
M_CHROME = principled("Chrome", (0.9, 0.9, 0.9), 1.0, 0.08)
M_CUP = principled("Ceramic", (0.92, 0.9, 0.86), 0.0, 0.15)
M_COFFEE = principled("Coffee", (0.12, 0.05, 0.02), 0.0, 0.3)
M_CREMA = principled("Crema", (0.45, 0.25, 0.1), 0.0, 0.4)
M_COUNTER = principled("Counter", (0.35, 0.3, 0.26), 0.0, 0.45)
M_GAUGE = principled("GaugeFace", (0.95, 0.95, 0.92), 0.0, 0.3)

def assign(o, m):
    o.data.materials.append(m)

def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True

def box(name, loc, size, mat, bevel=0.01):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        md = o.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = 4
    smooth(o)
    assign(o, mat)
    return o

def cyl(name, loc, r, d, mat, rot=(0, 0, 0), bevel=0.003, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    if bevel > 0:
        md = o.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = 3
        md.limit_method = 'ANGLE'
    smooth(o)
    assign(o, mat)
    return o

# ---------- Counter ----------
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
counter = bpy.context.active_object
assign(counter, M_COUNTER)

# ---------- Machine ----------
box("Base", (0, 0, 0.04), (0.52, 0.46, 0.08), M_BLACK, 0.015)
box("Body", (0, 0.07, 0.29), (0.44, 0.24, 0.42), M_STEEL, 0.02)
box("Overhang", (0, -0.12, 0.44), (0.44, 0.16, 0.12), M_STEEL, 0.02)
box("TopTray", (0, 0.03, 0.505), (0.40, 0.32, 0.012), M_BLACK, 0.004)

# Group head + portafilter
cyl("GroupHead", (0, -0.13, 0.355), 0.045, 0.05, M_CHROME)
cyl("Portafilter", (0, -0.13, 0.31), 0.05, 0.04, M_CHROME)
cyl("PFNeck", (0, -0.2, 0.31), 0.012, 0.06, M_CHROME, rot=(math.radians(90), 0, 0))
cyl("PFHandle", (0, -0.31, 0.305), 0.017, 0.16, M_BLACK,
    rot=(math.radians(85), 0, 0), bevel=0.006)
cyl("Spout", (0, -0.13, 0.28), 0.012, 0.025, M_CHROME)

# Drip tray with grate
box("DripTray", (0, -0.12, 0.095), (0.32, 0.19, 0.03), M_STEEL, 0.006)
for i in range(9):
    x = -0.14 + i * 0.035
    box(f"Slat{i}", (x, -0.12, 0.112), (0.012, 0.17, 0.006), M_CHROME, 0.002)

# Steam wand
cyl("WandBase", (0.19, -0.13, 0.37), 0.014, 0.04, M_CHROME)
wand = cyl("SteamWand", (0.205, -0.15, 0.28), 0.006, 0.17, M_CHROME,
           rot=(math.radians(12), math.radians(8), 0), bevel=0)
cyl("WandTip", (0.217, -0.168, 0.195), 0.008, 0.015, M_CHROME, bevel=0.002)

# Knobs on the side and front
for z in (0.2, 0.3):
    cyl("Knob", (0.225, 0.07, z), 0.025, 0.025, M_BLACK, rot=(0, math.radians(90), 0))
cyl("PowerKnob", (-0.15, -0.205, 0.44), 0.018, 0.02, M_BLACK, rot=(math.radians(90), 0, 0))
cyl("LED", (0.15, -0.203, 0.44), 0.006, 0.006, principled("LED", (1, 0.3, 0.05)),
    rot=(math.radians(90), 0, 0), bevel=0)
led = bpy.data.materials["LED"].node_tree.nodes["Principled BSDF"]
led.inputs["Emission Color"].default_value = (1, 0.3, 0.05, 1)
led.inputs["Emission Strength"].default_value = 15

# Pressure gauge
cyl("GaugeRim", (-0.13, -0.06, 0.25), 0.045, 0.02, M_CHROME, rot=(math.radians(90), 0, 0))
cyl("GaugeFace", (-0.13, -0.071, 0.25), 0.038, 0.002, M_GAUGE, rot=(math.radians(90), 0, 0), bevel=0)
needle = box("Needle", (-0.13, -0.074, 0.26), (0.003, 0.002, 0.03), M_BLACK, 0)
needle.rotation_euler = (0, math.radians(35), 0)

# Feet
for x in (-0.22, 0.22):
    for y in (-0.19, 0.19):
        cyl("Foot", (x, y, -0.002), 0.02, 0.01, M_BLACK, bevel=0)

# ---------- Cup ----------
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=0.028, radius2=0.036, depth=0.055)
top = max(bm.faces, key=lambda f: f.calc_center_median().z)
bmesh.ops.delete(bm, geom=[top], context='FACES_ONLY')
me = bpy.data.meshes.new("Cup")
bm.to_mesh(me)
bm.free()
cup = bpy.data.objects.new("Cup", me)
scene.collection.objects.link(cup)
cup.location = (0, -0.13, 0.115 + 0.0275)
sol = cup.modifiers.new("Solid", "SOLIDIFY")
sol.thickness = 0.004
sub = cup.modifiers.new("Sub", "SUBSURF")
sub.levels = 2
sub.render_levels = 2
smooth(cup)
assign(cup, M_CUP)

bpy.ops.mesh.primitive_torus_add(major_radius=0.015, minor_radius=0.004,
                                 location=(0.043, -0.13, 0.145), rotation=(math.radians(90), 0, 0))
h = bpy.context.active_object
h.name = "CupHandle"
smooth(h)
assign(h, M_CUP)

cyl("Saucer", (0, -0.13, 0.117), 0.055, 0.005, M_CUP, bevel=0.002)
c = cyl("Coffee", (0, -0.13, 0.158), 0.032, 0.002, M_CREMA, bevel=0)

# ---------- Lighting ----------
def area(name, loc, energy, size, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy = energy
    d.size = size
    d.color = color
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.location = loc
    direction = Vector((0, 0, 0.25)) - Vector(loc)
    o.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return o

area("Key", (1.0, -0.8, 1.2), 120, 0.8, (1, 0.95, 0.9))
area("Fill", (-1.2, -0.6, 0.6), 40, 1.2, (0.85, 0.9, 1))
area("Rim", (-0.3, 1.0, 1.0), 80, 0.6)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)
bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.85, -1.25, 0.6)
target = Vector((0, -0.03, 0.25))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.frame_start = 1
scene.frame_end = 1
