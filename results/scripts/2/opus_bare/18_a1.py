import bpy, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, metal=0.0, rough=0.5, aniso=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if aniso and "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = aniso
    return m

steel = mat("BrushedSteel", (0.8, 0.8, 0.82), 1.0, 0.28, 0.7)
black = mat("MatteBlack", (0.02, 0.02, 0.02), 0.0, 0.85)
ceramic = mat("Ceramic", (0.95, 0.94, 0.9), 0.0, 0.15)
coffee = mat("Coffee", (0.08, 0.03, 0.01), 0.0, 0.1)
counter = mat("Counter", (0.35, 0.28, 0.22), 0.0, 0.6)
chrome = mat("Chrome", (0.9, 0.9, 0.9), 1.0, 0.05)

def add(obj, m, bevel=0.0, smooth=False):
    obj.data.materials.append(m)
    if bevel:
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 4
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj

def cube(loc, size, m, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.scale = (size[0]/2, size[1]/2, size[2]/2)
    bpy.ops.object.transform_apply(scale=True)
    return add(o, m, bevel)

def cyl(loc, r, d, m, rot=(0,0,0), verts=48, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=verts)
    return add(bpy.context.object, m, bevel, True)

# Counter
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
add(bpy.context.object, counter)

# Base
cube((0, 0, 0.06), (1.0, 0.8, 0.12), black, 0.03)
# Drip tray
cube((0, -0.12, 0.135), (0.6, 0.45, 0.03), steel, 0.01)
for i in range(7):
    cube((0, -0.3 + i*0.06, 0.152), (0.55, 0.015, 0.006), black, 0.002)
# Main body
cube((0, 0.22, 0.6), (0.9, 0.36, 0.9), steel, 0.04)
# Top
cube((0, 0.12, 1.08), (0.95, 0.6, 0.06), black, 0.02)
# Front head overhang
cube((0, -0.02, 0.9), (0.9, 0.2, 0.3), steel, 0.04)
# Group head
cyl((0, -0.12, 0.72), 0.1, 0.07, chrome)
cyl((0, -0.12, 0.66), 0.085, 0.05, steel)
# Portafilter handle
h = cyl((0, -0.38, 0.66), 0.025, 0.4, black, rot=(math.radians(90), 0, 0), bevel=0.0)
cyl((0, -0.12, 0.62), 0.03, 0.04, chrome)
# Steam wand
cyl((0.38, -0.08, 0.6), 0.012, 0.45, chrome, rot=(math.radians(-10), 0, 0))
cyl((0.38, -0.09, 0.85), 0.03, 0.08, black)
# Dials
for x in (-0.25, 0.25):
    cyl((x, -0.13, 0.95), 0.05, 0.03, black, rot=(math.radians(90), 0, 0))
    cyl((x, -0.15, 0.95), 0.035, 0.02, chrome, rot=(math.radians(90), 0, 0))
# Gauge
cyl((0, -0.125, 0.95), 0.06, 0.02, chrome, rot=(math.radians(90), 0, 0))
cyl((0, -0.137, 0.95), 0.05, 0.005, ceramic, rot=(math.radians(90), 0, 0))
# Feet
for x in (-0.42, 0.42):
    for y in (-0.32, 0.32):
        cyl((x, y, 0.005), 0.03, 0.01, black)

# Cup
cupz = 0.155
bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.1, location=(0, -0.12, cupz + 0.05), vertices=48)
cup = bpy.context.object
add(cup, ceramic, smooth=True)
sol = cup.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.008
# remove top face via bmesh
import bmesh
bm = bmesh.new(); bm.from_mesh(cup.data)
top = [f for f in bm.faces if f.calc_center_median().z > 0.049]
bmesh.ops.delete(bm, geom=top, context='FACES')
bm.to_mesh(cup.data); bm.free()
sub = cup.modifiers.new("Sub", 'SUBSURF'); sub.levels = 1
cyl((0, -0.12, cupz + 0.08), 0.064, 0.005, coffee)
bpy.ops.mesh.primitive_torus_add(major_radius=0.025, minor_radius=0.007, location=(0.085, -0.12, cupz + 0.055), rotation=(math.radians(90), 0, 0))
add(bpy.context.object, ceramic, smooth=True)
# Saucer
cyl((0, -0.12, cupz + 0.005), 0.11, 0.01, ceramic, bevel=0.004)

# Lighting
bpy.ops.object.light_add(type='AREA', location=(-1.5, -1.5, 2.0))
k = bpy.context.object; k.data.energy = 400; k.data.size = 1.5
k.rotation_euler = (math.radians(50), 0, math.radians(-45))
bpy.ops.object.light_add(type='AREA', location=(1.8, -1.0, 1.2))
f = bpy.context.object; f.data.energy = 150; f.data.size = 2
f.rotation_euler = (math.radians(65), 0, math.radians(60))
bpy.ops.object.light_add(type='AREA', location=(0, 1.5, 2.0))
r = bpy.context.object; r.data.energy = 200; r.data.size = 1
r.rotation_euler = (math.radians(-40), 0, 0)

world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5

# Camera
bpy.ops.object.camera_add(location=(1.4, -2.2, 1.3))
cam = bpy.context.object
cam.data.lens = 50
d = Vector((0, 0, 0.55)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
