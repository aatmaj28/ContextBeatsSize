import bpy, bmesh, math, random
from mathutils import Vector, Euler

random.seed(42)
scene = bpy.context.scene

# Clear scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def make_mat(name, color, rough=0.5, metallic=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
    return m

dough_mat = make_mat("Dough", (0.75, 0.42, 0.15), 0.6)
frost_mat = make_mat("Frosting", (1.0, 0.35, 0.6), 0.15, coat=0.6)
plate_mat = make_mat("Plate", (0.95, 0.95, 0.95), 0.1, coat=0.8)
table_mat = make_mat("Table", (0.35, 0.22, 0.14), 0.5)

# Table
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
bpy.context.object.data.materials.append(table_mat)

# Plate (lathe profile via screw)
bm = bmesh.new()
prof = [(0, 0.0), (1.2, 0.0), (1.35, 0.02), (1.6, 0.1), (1.75, 0.16), (1.78, 0.14), (1.6, 0.06), (1.3, 0.04), (0, 0.04)]
verts = [bm.verts.new((x, 0, z + 0.01)) for x, z in prof]
for i in range(len(verts) - 1):
    bm.edges.new((verts[i], verts[i + 1]))
me = bpy.data.meshes.new("Plate")
bm.to_mesh(me)
plate = bpy.data.objects.new("Plate", me)
scene.collection.objects.link(plate)
scr = plate.modifiers.new("Screw", "SCREW")
scr.steps = 96
scr.render_steps = 96
plate.modifiers.new("Sub", "SUBSURF").levels = 2
plate.data.materials.append(plate_mat)
for p in plate.data.polygons:
    p.use_smooth = True

# Donut
R, r = 0.8, 0.35
base_z = 0.05 + r * 0.85
bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=64, minor_segments=32, location=(0, 0, base_z))
donut = bpy.context.object
donut.scale.z = 0.85
donut.data.materials.append(dough_mat)
bpy.ops.object.shade_smooth()
donut.modifiers.new("Sub", "SUBSURF").levels = 1

# Frosting: torus slightly larger, delete lower part with wavy edge
bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r * 1.06, major_segments=96, minor_segments=48, location=(0, 0, base_z))
frost = bpy.context.object
frost.scale.z = 0.85
bm = bmesh.new()
bm.from_mesh(frost.data)
kill = []
for v in bm.verts:
    ang = math.atan2(v.co.y, v.co.x)
    thresh = -0.05 + 0.06 * math.sin(ang * 7) + 0.03 * math.sin(ang * 13 + 1)
    if v.co.z < thresh:
        kill.append(v)
bmesh.ops.delete(bm, geom=kill, context='VERTS')
bm.to_mesh(frost.data)
bm.free()
frost.data.materials.append(frost_mat)
bpy.ops.object.shade_smooth()
sol = frost.modifiers.new("Solid", "SOLIDIFY")
sol.thickness = 0.02
frost.modifiers.new("Sub", "SUBSURF").levels = 2

# Sprinkles
colors = [(1, 0.1, 0.1), (1, 0.85, 0.1), (0.1, 0.5, 1), (0.1, 0.85, 0.3), (1, 1, 1), (0.6, 0.2, 0.9), (1, 0.5, 0.05)]
smats = [make_mat(f"Spr{i}", c, 0.3, coat=0.3) for i, c in enumerate(colors)]
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.018, depth=0.09)
proto = bpy.context.object
proto_mesh = proto.data
bpy.ops.object.shade_smooth()
bpy.data.objects.remove(proto, do_unlink=True)

rr = r * 1.06 + 0.02
for i in range(220):
    u = random.uniform(0, 2 * math.pi)
    v = random.uniform(math.radians(-10), math.radians(185))
    # tube angle v: 0 = outer, 90 = top
    n = Vector((math.cos(v) * math.cos(u), math.cos(v) * math.sin(u), math.sin(v) * 0.85)).normalized()
    pos = Vector(((R + rr * math.cos(v)) * math.cos(u), (R + rr * math.cos(v)) * math.sin(u), base_z + rr * math.sin(v) * 0.85))
    if pos.z < base_z + 0.05:
        continue
    ob = bpy.data.objects.new(f"Sprinkle{i}", proto_mesh.copy())
    ob.data.materials.append(random.choice(smats))
    ob.location = pos
    # align cylinder axis tangent to surface
    rot = n.to_track_quat('Z', 'Y')
    ob.rotation_mode = 'QUATERNION'
    tilt = Euler((math.pi / 2, 0, random.uniform(0, 2 * math.pi))).to_quaternion()
    ob.rotation_quaternion = rot @ tilt
    scene.collection.objects.link(ob)

# Lighting
bpy.ops.object.light_add(type='AREA', location=(3, -3, 5))
key = bpy.context.object
key.data.energy = 800
key.data.size = 3
key.rotation_euler = (math.radians(40), 0, math.radians(45))
bpy.ops.object.light_add(type='AREA', location=(-4, 2, 3))
fill = bpy.context.object
fill.data.energy = 250
fill.data.size = 4
fill.rotation_euler = (math.radians(60), 0, math.radians(-120))
bpy.ops.object.light_add(type='SPOT', location=(0, 5, 3))
rim = bpy.context.object
rim.data.energy = 400
rim.rotation_euler = (math.radians(-60), 0, math.radians(180))
rim.rotation_euler = (Vector((0, 0, 0.3)) - rim.location).to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.8, 0.85, 0.95, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.4

# Camera
bpy.ops.object.camera_add(location=(0, -3.6, 2.6))
cam = bpy.context.object
cam.data.lens = 50
target = Vector((0, 0, 0.3))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
