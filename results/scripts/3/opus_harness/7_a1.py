import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.5):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

wood = mat("Wood", (0.35, 0.18, 0.08), 0.45)
wood2 = mat("ChairWood", (0.25, 0.12, 0.05), 0.5)
floor_m = mat("Floor", (0.55, 0.45, 0.35), 0.6)
wall_m = mat("Wall", (0.85, 0.82, 0.75), 0.9)
cush = mat("Cushion", (0.5, 0.1, 0.1), 0.8)

def box(name, loc, size, m, rot=0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0]/2, size[1]/2, size[2]/2)
    o.rotation_euler.z = rot
    o.data.materials.append(m)
    return o

# Room
W, D, H = 6, 6, 3
box("Floor", (0, 0, -0.05), (W, D, 0.1), floor_m)
box("WallBack", (0, D/2, H/2), (W, 0.1, H), wall_m)
box("WallLeft", (-W/2, 0, H/2), (0.1, D, H), wall_m)
box("WallRight", (W/2, 0, H/2), (0.1, D, H), wall_m)
box("Ceiling", (0, 0, H+0.05), (W, D, 0.1), wall_m)

# Table
th = 0.75
box("TableTop", (0, 0, th), (1.6, 1.0, 0.06), wood)
for sx in (-1, 1):
    for sy in (-1, 1):
        box("TableLeg", (sx*0.72, sy*0.42, th/2), (0.07, 0.07, th-0.03), wood)

# Chairs
def chair(x, y, rot):
    import mathutils
    R = mathutils.Matrix.Rotation(rot, 4, 'Z')
    def p(lx, ly, lz):
        v = R @ mathutils.Vector((lx, ly, lz))
        return (x+v.x, y+v.y, v.z)
    sh = 0.45
    box("Seat", p(0, 0, sh), (0.45, 0.45, 0.05), wood2, rot)
    box("Cushion", p(0, 0, sh+0.04), (0.4, 0.4, 0.04), cush, rot)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("ChairLeg", p(sx*0.19, sy*0.19, sh/2), (0.04, 0.04, sh), wood2, rot)
        box("BackPost", p(sx*0.19, 0.2, sh+0.25), (0.04, 0.04, 0.5), wood2, rot)
    box("BackRest", p(0, 0.2, sh+0.42), (0.42, 0.03, 0.15), wood2, rot)
    box("BackSlat", p(0, 0.2, sh+0.22), (0.38, 0.02, 0.06), wood2, rot)

# backs face away from table: local +y is back
chair(0, -0.85, 0)              # front side, back toward -y... adjust
chair(0, 0.85, math.pi)
chair(-1.15, 0, -math.pi/2)
chair(1.15, 0, math.pi/2)
# fix front chair: back should point away (-y)
for o in bpy.data.objects:
    pass

# Lights
bpy.ops.object.light_add(type='AREA', location=(0, 0, H-0.1))
l = bpy.context.active_object
l.data.energy = 400
l.data.size = 1.5
bpy.ops.object.light_add(type='POINT', location=(2, -2, 2.2))
bpy.context.active_object.data.energy = 150
bpy.ops.object.light_add(type='SUN', location=(0, -5, 4))
s = bpy.context.active_object
s.data.energy = 1.5
s.rotation_euler = (math.radians(55), 0, math.radians(20))

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.6, 0.65, 0.7, 1)
bg.inputs["Strength"].default_value = 0.3

# Camera
bpy.ops.object.camera_add(location=(2.4, -2.7, 1.9))
cam = bpy.context.active_object
cam.data.lens = 28
import mathutils
d = mathutils.Vector((0, 0, 0.5)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'
