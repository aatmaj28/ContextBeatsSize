import bpy, math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

m_tower = mat("Tower", (0.85, 0.8, 0.7))
m_roof = mat("Roof", (0.35, 0.12, 0.08))
m_wood = mat("Wood", (0.35, 0.22, 0.12))
m_sail = mat("Sail", (0.9, 0.88, 0.82), 0.9)
m_ground = mat("Ground", (0.15, 0.35, 0.1), 0.95)
m_metal = mat("Metal", (0.2, 0.2, 0.22), 0.4, 1.0)

def assign(o, m):
    o.data.materials.append(m)
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=80)
assign(bpy.context.object, m_ground)

# Tower
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=2.0, radius2=1.3, depth=8, location=(0, 0, 4))
t = assign(bpy.context.object, m_tower)
bpy.ops.object.shade_flat()

# Roof cap
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.6, radius2=0.2, depth=1.8, location=(0, 0, 8.9))
assign(bpy.context.object, m_roof)

# Door
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.9, 0.9))
d = bpy.context.object
d.scale = (0.9, 0.2, 1.8)
assign(d, m_wood)

# Windows
for z in (3.5, 6.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.95 + (z - 0.0) * 0.09, z))
    w = bpy.context.object
    w.scale = (0.5, 0.2, 0.7)
    assign(w, m_wood)

# Axle
hub_loc = Vector((0, -1.9, 8.2))
bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=1.6, location=(0, -1.3, 8.2), rotation=(math.pi/2, 0, 0))
assign(bpy.context.object, m_metal)

# Pivot empty
pivot = bpy.data.objects.new("BladePivot", None)
scene.collection.objects.link(pivot)
pivot.location = hub_loc

bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=0.4, location=(0, 0, 0), rotation=(math.pi/2, 0, 0))
hub = assign(bpy.context.object, m_wood)
hub.parent = pivot

for i in range(4):
    a = i * math.pi / 2
    # spar
    bpy.ops.mesh.primitive_cube_add(size=1)
    s = bpy.context.object
    s.scale = (0.18, 0.15, 5.0)
    s.rotation_euler = (0, a, 0)
    s.location = (math.sin(a) * 2.6, -0.1, math.cos(a) * 2.6)
    assign(s, m_wood)
    s.parent = pivot
    # sail
    bpy.ops.mesh.primitive_cube_add(size=1)
    sl = bpy.context.object
    sl.scale = (0.9, 0.04, 3.8)
    off = 0.55
    r = 3.0
    sl.rotation_euler = (0, a, 0)
    sl.location = (math.sin(a) * r + math.cos(a) * off, -0.05, math.cos(a) * r - math.sin(a) * off)
    assign(sl, m_sail)
    sl.parent = pivot

# Animation: constant spin
scene.frame_start = 1
scene.frame_end = 120
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", index=1, frame=1)
pivot.rotation_euler = (0, -2 * math.pi, 0)
pivot.keyframe_insert("rotation_euler", index=1, frame=121)
ad = pivot.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
for fc in cb.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10), rotation=(math.radians(50), math.radians(10), math.radians(-30)))
bpy.context.object.data.energy = 4
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (10, -20, 5)
target = Vector((0, 0, 5.5))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam_data.lens = 35
scene.camera = cam
