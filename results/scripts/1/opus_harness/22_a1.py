import bpy, math
from mathutils import Vector
from bpy_extras import anim_utils

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.7):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

m_stone = mat("Stone", (0.75, 0.68, 0.55))
m_roof = mat("Roof", (0.45, 0.12, 0.08))
m_wood = mat("Wood", (0.3, 0.18, 0.08))
m_sail = mat("Sail", (0.92, 0.9, 0.82))
m_grass = mat("Grass", (0.15, 0.4, 0.1), 0.9)
m_dark = mat("Dark", (0.05, 0.04, 0.03))

def assign(o, m):
    o.data.materials.append(m)
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=80)
assign(bpy.context.object, m_grass)

# Tower
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=2.2, radius2=1.3, depth=7, location=(0, 0, 3.5))
t = assign(bpy.context.object, m_stone)
bpy.ops.object.shade_flat()

# Roof cap
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.6, radius2=0.1, depth=2.2, location=(0, 0, 8.1))
assign(bpy.context.object, m_roof)

# Door and windows
bpy.ops.mesh.primitive_cube_add(location=(0, -2.05, 0.9))
d = bpy.context.object; d.scale = (0.45, 0.2, 0.9); assign(d, m_wood)
for z in (3.5, 5.5):
    bpy.ops.mesh.primitive_cube_add(location=(0, -1.95 + (z - 3.5) * 0.12, z))
    w = bpy.context.object; w.scale = (0.3, 0.2, 0.4); assign(w, m_dark)

# Axle
bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1.2, location=(0, -1.5, 7.3), rotation=(math.radians(90), 0, 0))
assign(bpy.context.object, m_wood)

# Rotor empty
rotor = bpy.data.objects.new("Rotor", None)
scene.collection.objects.link(rotor)
rotor.location = (0, -2.1, 7.3)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(0, 0, 0))
hub = assign(bpy.context.object, m_wood)
hub.parent = rotor

for i in range(4):
    a = i * math.pi / 2
    s, c = math.sin(a), math.cos(a)
    bpy.ops.mesh.primitive_cube_add()
    arm = bpy.context.object
    arm.scale = (0.08, 0.08, 2.0)
    arm.location = (s * 2.0, 0, c * 2.0)
    arm.rotation_euler = (0, a, 0)
    assign(arm, m_wood); arm.parent = rotor
    bpy.ops.mesh.primitive_cube_add()
    sail = bpy.context.object
    sail.scale = (0.4, 0.03, 1.5)
    x, z = 0.48, 2.4
    sail.location = (x * c + z * s, -0.05, -x * s + z * c)
    sail.rotation_euler = (0, a, 0)
    assign(sail, m_sail); sail.parent = rotor

# Animation: constant spin
scene.frame_start = 1
scene.frame_end = 120
rotor.rotation_euler = (0, 0, 0)
rotor.keyframe_insert("rotation_euler", index=1, frame=1)
rotor.rotation_euler = (0, 2 * math.pi, 0)
rotor.keyframe_insert("rotation_euler", index=1, frame=121)
ad = rotor.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
for fc in cb.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.object
sun.data.energy = 4
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1)
bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(10, -17, 4.5))
cam = bpy.context.object
direction = Vector((0, 0, 5.2)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 40
scene.camera = cam
