import bpy, math
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
m_roof = mat("Roof", (0.35, 0.12, 0.08))
m_wood = mat("Wood", (0.3, 0.18, 0.08))
m_sail = mat("Sail", (0.9, 0.88, 0.8))
m_grass = mat("Grass", (0.15, 0.4, 0.1), 0.9)
m_door = mat("Door", (0.2, 0.1, 0.05))

def assign(o, m):
    o.data.materials.append(m)
    return o

# Ground
bpy.ops.mesh.primitive_plane_add(size=80)
assign(bpy.context.active_object, m_grass)

# Tower
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.6, radius2=1.0, depth=6, location=(0, 0, 3))
t = assign(bpy.context.active_object, m_stone)
bpy.ops.object.shade_smooth()

# Roof cap
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.25, radius2=0.0, depth=1.6, location=(0, 0, 6.8))
assign(bpy.context.active_object, m_roof)
bpy.ops.object.shade_smooth()

# Door and window
bpy.ops.mesh.primitive_cube_add(location=(0, -1.5, 0.8), scale=(0.4, 0.15, 0.8))
assign(bpy.context.active_object, m_door)
bpy.ops.mesh.primitive_cube_add(location=(0, -1.2, 3.8), scale=(0.25, 0.15, 0.3))
assign(bpy.context.active_object, m_door)

# Axle
bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=1.0, location=(0, -1.2, 6.0), rotation=(math.pi/2, 0, 0))
assign(bpy.context.active_object, m_wood)

# Hub (rotating)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=(0, -1.7, 6.0))
hub = assign(bpy.context.active_object, m_wood)
bpy.ops.object.shade_smooth()

for i in range(4):
    a = i * math.pi / 2
    piv = bpy.data.objects.new(f"BladePivot{i}", None)
    scene.collection.objects.link(piv)
    piv.parent = hub
    piv.rotation_euler = (0, a, 0)
    bpy.ops.mesh.primitive_cube_add(scale=(0.07, 0.07, 1.6))
    arm = assign(bpy.context.active_object, m_wood)
    arm.parent = piv
    arm.location = (0, -0.05, 1.75)
    bpy.ops.mesh.primitive_cube_add(scale=(0.4, 0.02, 1.2))
    sail = assign(bpy.context.active_object, m_sail)
    sail.parent = piv
    sail.location = (0.45, 0.0, 2.1)
    for k in range(5):
        bpy.ops.mesh.primitive_cube_add(scale=(0.42, 0.03, 0.025))
        s = assign(bpy.context.active_object, m_wood)
        s.parent = piv
        s.location = (0.45, -0.03, 1.0 + k * 0.55)

# Animation: one full turn every 120 frames, linear
scene.frame_start = 1
scene.frame_end = 120
hub.rotation_euler = (0, 0, 0)
hub.keyframe_insert("rotation_euler", index=1, frame=1)
hub.rotation_euler = (0, 2 * math.pi, 0)
hub.keyframe_insert("rotation_euler", index=1, frame=121)
ad = hub.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
if cb:
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.extrapolation = 'LINEAR'

# Lighting
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(-30)))
sun = bpy.context.active_object
sun.data.energy = 4
sun.data.color = (1, 0.95, 0.85)

world = bpy.data.worlds.new("Sky")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1)
bg.inputs["Strength"].default_value = 1.0

# Camera
bpy.ops.object.camera_add(location=(9, -15, 4.5))
cam = bpy.context.active_object
tgt = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(tgt)
tgt.location = (0, 0, 4.5)
c = cam.constraints.new('TRACK_TO')
c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
cam.data.lens = 40
scene.camera = cam
