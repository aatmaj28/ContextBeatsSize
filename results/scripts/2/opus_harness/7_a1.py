import bpy, math

scene = bpy.context.scene

def mat(name, color, rough=0.5):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

wood = mat("Wood", (0.35, 0.18, 0.08), 0.45)
chair_wood = mat("ChairWood", (0.25, 0.12, 0.05), 0.5)
wall_m = mat("Wall", (0.85, 0.8, 0.7), 0.9)
floor_m = mat("Floor", (0.5, 0.35, 0.22), 0.6)
seat_m = mat("Cushion", (0.5, 0.08, 0.08), 0.8)

def box(name, loc, size, m, rot=0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=(0, 0, rot))
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0]/2, size[1]/2, size[2]/2)
    o.data.materials.append(m)
    return o

# Room
box("Floor", (0, 0, -0.05), (6, 6, 0.1), floor_m)
box("WallBack", (0, 3, 1.5), (6, 0.1, 3), wall_m)
box("WallLeft", (-3, 0, 1.5), (0.1, 6, 3), wall_m)
box("WallRight", (3, 0, 1.5), (0.1, 6, 3), wall_m)
box("Ceiling", (0, 0, 3.05), (6, 6, 0.1), wall_m)

# Table
box("TableTop", (0, 0, 0.75), (1.6, 1.0, 0.06), wood)
for x in (-0.72, 0.72):
    for y in (-0.42, 0.42):
        box("TableLeg", (x, y, 0.36), (0.07, 0.07, 0.72), wood)

# Chairs
def chair(px, py, rot):
    c, s = math.cos(rot), math.sin(rot)
    def p(lx, ly, z):
        return (px + lx*c - ly*s, py + lx*s + ly*c, z)
    box("Seat", p(0, 0, 0.45), (0.45, 0.45, 0.05), chair_wood, rot)
    box("Cushion", p(0, 0, 0.485), (0.4, 0.4, 0.03), seat_m, rot)
    for lx in (-0.19, 0.19):
        for ly in (-0.19, 0.19):
            box("ChairLeg", p(lx, ly, 0.22), (0.04, 0.04, 0.44), chair_wood, rot)
    # backrest on +ly side (away from table)
    for lx in (-0.19, 0.19):
        box("BackPost", p(lx, 0.2, 0.72), (0.04, 0.04, 0.5), chair_wood, rot)
    box("BackRest", p(0, 0.2, 0.88), (0.42, 0.03, 0.18), chair_wood, rot)

# Positions: chair's local +y points away from table
chair(0, -0.85, 0)            # front: back at -y... adjust rot
for o in []: pass
# Recreate chairs properly by orientation: local +y must point outward
for obj in [o for o in bpy.data.objects if o.name.startswith(("Seat","Cushion","ChairLeg","BackPost","BackRest"))]:
    bpy.data.objects.remove(obj, do_unlink=True)
chair(0, -0.85, math.pi)       # outward = -y
chair(0, 0.85, 0)              # outward = +y
chair(1.15, 0, -math.pi/2)     # outward = +x
chair(-1.15, 0, math.pi/2)     # outward = -x

# Lights
bpy.ops.object.light_add(type='AREA', location=(0, 0, 2.9))
l = bpy.context.active_object
l.data.energy = 300
l.data.size = 2
bpy.ops.object.light_add(type='POINT', location=(-2, -2, 2.2))
bpy.context.active_object.data.energy = 150

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)

# Camera
bpy.ops.object.camera_add(location=(2.4, -2.6, 2.0))
cam = bpy.context.active_object
cam.data.lens = 24
from mathutils import Vector
d = Vector((0, 0, 0.5)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
