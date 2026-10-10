import bpy, math
from mathutils import Vector

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, metallic=0.0, rough=0.5, aniso=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if aniso and "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = aniso
    return m

brushed = mat("Brushed", (0.8, 0.8, 0.82), 1.0, 0.3, 0.7)
black = mat("MatteBlack", (0.02, 0.02, 0.02), 0.0, 0.85)
ceramic = mat("Ceramic", (0.95, 0.94, 0.9), 0.0, 0.15)
coffee = mat("Coffee", (0.08, 0.035, 0.01), 0.0, 0.1)
chrome = mat("Chrome", (0.9, 0.9, 0.9), 1.0, 0.08)
counter = mat("Counter", (0.35, 0.25, 0.18), 0.0, 0.6)

def add(obj, m, bevel=0.0):
    obj.data.materials.append(m)
    if bevel:
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 3
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj

def box(loc, scale, m, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return add(o, m, bevel)

def cyl(loc, r, d, m, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=verts)
    return add(bpy.context.object, m)

# Counter
box((0, 0, -0.05), (3, 2, 0.05), counter, 0)

# Base (matte black)
box((0, 0, 0.06), (0.55, 0.45, 0.06), black, 0.03)
# Drip tray grill
box((0, -0.18, 0.13), (0.3, 0.18, 0.01), chrome, 0.005)
# Main body
box((0, 0.12, 0.75), (0.5, 0.3, 0.63), brushed, 0.04)
# Top black cap
box((0, 0.12, 1.41), (0.52, 0.32, 0.03), black, 0.02)
# Upper front overhang
box((0, -0.12, 1.15), (0.5, 0.1, 0.22), brushed, 0.03)

# Group head
cyl((0, -0.22, 0.88), 0.12, 0.1, chrome)
# Portafilter
cyl((0, -0.22, 0.79), 0.11, 0.08, chrome)
cyl((0, -0.55, 0.79), 0.03, 0.5, black, rot=(math.radians(90), 0, 0))
cyl((0, -0.22, 0.73), 0.02, 0.05, chrome)

# Gauge
cyl((0.25, -0.225, 1.2), 0.08, 0.02, chrome, rot=(math.radians(90), 0, 0))
cyl((0.25, -0.235, 1.2), 0.065, 0.01, ceramic, rot=(math.radians(90), 0, 0))
# Knobs
for x in (-0.3, -0.15):
    cyl((x, -0.24, 1.2), 0.04, 0.05, black, rot=(math.radians(90), 0, 0))

# Steam wand
cyl((0.42, -0.2, 0.75), 0.015, 0.5, chrome)

# Cup
bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.12, location=(0, -0.22, 0.2), vertices=48)
cup = bpy.context.object
sol = cup.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.008
add(cup, ceramic)
bpy.ops.object.mode_set(mode='EDIT')
import bmesh
bm = bmesh.from_edit_mesh(cup.data)
for f in bm.faces:
    if f.normal.z > 0.9:
        bm.faces.remove(f)
        break
bmesh.update_edit_mesh(cup.data)
bpy.ops.object.mode_set(mode='OBJECT')
cyl((0, -0.22, 0.24), 0.083, 0.005, coffee)
# Saucer
cyl((0, -0.22, 0.145), 0.14, 0.012, ceramic)
# Handle
bpy.ops.mesh.primitive_torus_add(location=(0.11, -0.22, 0.2), rotation=(math.radians(90), 0, 0),
                                 major_radius=0.035, minor_radius=0.01)
add(bpy.context.object, ceramic)

# Lights
bpy.ops.object.light_add(type='AREA', location=(-1.5, -1.5, 2.2))
l = bpy.context.object; l.data.energy = 400; l.data.size = 2
l.rotation_euler = (math.radians(50), 0, math.radians(-45))
bpy.ops.object.light_add(type='AREA', location=(1.8, -1, 1.5))
l = bpy.context.object; l.data.energy = 200; l.data.size = 1.5
l.rotation_euler = (math.radians(60), 0, math.radians(60))
bpy.ops.object.light_add(type='AREA', location=(0, 1.5, 2.5))
l = bpy.context.object; l.data.energy = 150; l.data.size = 2
l.rotation_euler = (math.radians(-40), 0, 0)

# World
w = bpy.data.worlds.new("World"); scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)

# Camera
bpy.ops.object.camera_add(location=(1.6, -2.6, 1.3))
cam = bpy.context.object
direction = Vector((0, 0, 0.7)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 45
scene.camera = cam
