import bpy, bmesh, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- Materials ----------
def principled(name, color, metallic=0.0, rough=0.5, aniso=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = aniso
    if coat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
    return m

def brushed_metal():
    m = principled("BrushedSteel", (0.8, 0.8, 0.82), 1.0, 0.28, 0.7)
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 2.0, 300.0)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 8.0
    nz.inputs["Detail"].default_value = 10.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.18
    mr.inputs["To Max"].default_value = 0.38
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    return m

M_METAL = brushed_metal()
M_CHROME = principled("Chrome", (0.9, 0.9, 0.9), 1.0, 0.08)
M_BLACK = principled("MatteBlack", (0.02, 0.02, 0.022), 0.0, 0.85)
M_PLASTIC = principled("BlackPlastic", (0.015, 0.015, 0.015), 0.0, 0.35)
M_CERAMIC = principled("Ceramic", (0.92, 0.91, 0.88), 0.0, 0.12, coat=0.5)
M_COFFEE = principled("Espresso", (0.08, 0.035, 0.015), 0.0, 0.15)
M_CREMA = principled("Crema", (0.45, 0.25, 0.1), 0.0, 0.4)
M_GAUGE = principled("GaugeFace", (0.95, 0.95, 0.93), 0.0, 0.3)
M_RED = principled("Needle", (0.8, 0.05, 0.03), 0.0, 0.4)
M_COUNTER = principled("Counter", (0.35, 0.33, 0.3), 0.0, 0.45)
M_WALL = principled("Wall", (0.75, 0.72, 0.68), 0.0, 0.9)

# ---------- Helpers ----------
def finish(o, mat, bevel=0.0, smooth=True):
    o.data.materials.append(mat)
    if bevel > 0:
        md = o.modifiers.new("Bevel", 'BEVEL')
        md.width = bevel
        md.segments = 4
        md.limit_method = 'ANGLE'
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    return o

def box(name, size, loc, mat, bevel=0.004):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return finish(o, mat, bevel)

def cyl(name, r, d, loc, mat, rot=(0, 0, 0), bevel=0.0, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return finish(o, mat, bevel)

# ---------- Machine ----------
box("Base", (0.44, 0.40, 0.06), (0, 0, 0.03), M_BLACK, 0.008)
box("BodyTower", (0.38, 0.19, 0.34), (0, 0.075, 0.23), M_METAL, 0.01)
box("Overhang", (0.38, 0.16, 0.10), (0, -0.095, 0.35), M_METAL, 0.01)
box("TopRail", (0.36, 0.33, 0.012), (0, 0.0, 0.406), M_CHROME, 0.003)
box("DripTray", (0.34, 0.16, 0.03), (0, -0.095, 0.075), M_BLACK, 0.004)
# grate bars
for i in range(11):
    x = -0.15 + i * 0.03
    box(f"Grate{i}", (0.008, 0.15, 0.004), (x, -0.095, 0.092), M_CHROME, 0.001)

# group head + portafilter
cyl("GroupHead", 0.045, 0.05, (0, -0.10, 0.275), M_CHROME, bevel=0.003)
cyl("Portafilter", 0.043, 0.035, (0, -0.10, 0.235), M_CHROME, bevel=0.003)
cyl("PFStem", 0.009, 0.06, (0, -0.165, 0.235), M_CHROME, rot=(math.radians(90), 0, 0))
cyl("PFHandle", 0.014, 0.12, (0, -0.25, 0.228), M_PLASTIC,
    rot=(math.radians(84), 0, 0), bevel=0.004)
for sx in (-0.012, 0.012):
    cyl("Spout", 0.005, 0.02, (sx, -0.10, 0.208), M_CHROME)

# pressure gauge
gx, gz = 0.12, 0.35
cyl("GaugeRim", 0.03, 0.012, (gx, -0.177, gz), M_CHROME, rot=(math.radians(90), 0, 0), bevel=0.002)
cyl("GaugeFace", 0.025, 0.002, (gx, -0.184, gz), M_GAUGE, rot=(math.radians(90), 0, 0))
needle = box("Needle", (0.002, 0.001, 0.02), (gx + 0.004, -0.1855, gz + 0.006), M_RED, 0)
needle.rotation_euler = (0, math.radians(-35), 0)

# buttons
for i, x in enumerate((-0.16, -0.13, -0.10)):
    cyl(f"Button{i}", 0.01, 0.01, (x, -0.177, 0.35), M_PLASTIC,
        rot=(math.radians(90), 0, 0), bevel=0.002)

# steam wand + knob
cyl("SteamKnob", 0.018, 0.03, (0.215, -0.08, 0.35), M_PLASTIC, rot=(0, math.radians(90), 0), bevel=0.004)
cyl("WandJoint", 0.01, 0.03, (0.16, -0.14, 0.29), M_CHROME)
wand = cyl("SteamWand", 0.006, 0.17, (0.17, -0.15, 0.2), M_CHROME,
           rot=(math.radians(-6), math.radians(8), 0))
cyl("WandTip", 0.008, 0.015, (0.181, -0.159, 0.115), M_CHROME)

# ---------- Cup ----------
cup_z = 0.094
cyl("Saucer", 0.06, 0.008, (0, -0.10, cup_z + 0.004), M_CERAMIC, bevel=0.003, verts=64)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.033, depth=0.055,
                                    location=(0, -0.10, cup_z + 0.008 + 0.0275))
cup = bpy.context.active_object
cup.name = "Cup"
bm = bmesh.new(); bm.from_mesh(cup.data)
top = [f for f in bm.faces if f.normal.z > 0.9]
bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
for v in bm.verts:
    if v.co.z < 0:
        v.co.x *= 0.82; v.co.y *= 0.82
bm.to_mesh(cup.data); bm.free()
sol = cup.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.004
finish(cup, M_CERAMIC, 0.0015)
bpy.ops.mesh.primitive_torus_add(major_radius=0.014, minor_radius=0.004,
                                 location=(0.038, -0.10, cup_z + 0.04),
                                 rotation=(math.radians(90), 0, 0))
h = bpy.context.active_object; h.name = "CupHandle"; finish(h, M_CERAMIC)
cyl("Coffee", 0.03, 0.002, (0, -0.10, cup_z + 0.052), M_CREMA, verts=64)

# ---------- Environment ----------
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
floor = bpy.context.active_object; floor.name = "Counter"; finish(floor, M_COUNTER, smooth=False)
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0.45, 1), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object; wall.name = "Wall"; finish(wall, M_WALL, smooth=False)

world = bpy.data.worlds.new("World"); scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.5, 0.55, 0.6, 1)
bg.inputs["Strength"].default_value = 0.3

def area(name, loc, target, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy; ld.size = size; ld.color = color
    o = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o

area("Key", (-0.8, -0.9, 1.0), (0, 0, 0.2), 120, 0.8, (1, 0.95, 0.88))
area("Fill", (1.0, -0.6, 0.5), (0, 0, 0.2), 40, 1.2, (0.85, 0.9, 1))
area("Rim", (0.4, 0.35, 0.9), (0, -0.05, 0.25), 60, 0.5)
area("Strip", (0.0, -0.8, 0.25), (0, 0, 0.25), 25, 0.15)

# ---------- Camera ----------
cd = bpy.data.cameras.new("Camera"); cd.lens = 55
cam = bpy.data.objects.new("Camera", cd)
scene.collection.objects.link(cam)
cam.location = (0.55, -0.85, 0.45)
target = Vector((0.0, -0.02, 0.2))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cd.dof.use_dof = True
cd.dof.focus_distance = (target - cam.location).length
cd.dof.aperture_fstop = 4.0
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
