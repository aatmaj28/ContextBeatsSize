import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, emit=0.0, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit > 0:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m

# World
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.005, 0.015, 1)
bg.inputs["Strength"].default_value = 1.0

# Sun
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, segments=64, ring_count=32, location=(0, 0, 0))
sun = bpy.context.active_object
sun.name = "Sun"
bpy.ops.object.shade_smooth()
sun.data.materials.append(mat("SunMat", (1.0, 0.6, 0.15), emit=8.0))

light = bpy.data.lights.new("SunLight", 'POINT')
light.energy = 3000
light.shadow_soft_size = 1.5
light.color = (1.0, 0.85, 0.6)
lo = bpy.data.objects.new("SunLight", light)
scene.collection.objects.link(lo)

# Planets: (name, radius, orbit, color, angle, speed)
planets = [
    ("Mercury", 0.25, 3.0, (0.6, 0.55, 0.5), 0.5, 4.0),
    ("Earth", 0.45, 4.6, (0.15, 0.35, 0.9), 2.2, 2.5),
    ("Mars", 0.35, 6.3, (0.8, 0.25, 0.1), 4.0, 1.6),
    ("Saturn", 0.8, 8.8, (0.85, 0.75, 0.45), 5.4, 1.0),
]

scene.frame_start = 1
scene.frame_end = 240

for name, r, orbit, col, ang, speed in planets:
    pivot = bpy.data.objects.new(name + "_Pivot", None)
    scene.collection.objects.link(pivot)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=24, location=(orbit, 0, 0))
    p = bpy.context.active_object
    p.name = name
    bpy.ops.object.shade_smooth()
    p.data.materials.append(mat(name + "Mat", col, rough=0.6))
    p.parent = pivot
    if name == "Saturn":
        bpy.ops.mesh.primitive_torus_add(major_radius=1.35, minor_radius=0.3, major_segments=64, minor_segments=16, location=(orbit, 0, 0))
        ring = bpy.context.active_object
        ring.name = "SaturnRing"
        ring.scale = (1, 1, 0.05)
        ring.rotation_euler = (math.radians(20), math.radians(10), 0)
        ring.data.materials.append(mat("RingMat", (0.75, 0.65, 0.5), rough=0.7))
        bpy.ops.object.shade_smooth()
        ring.parent = pivot
    # orbit path (thin torus)
    bpy.ops.mesh.primitive_torus_add(major_radius=orbit, minor_radius=0.015, major_segments=128, minor_segments=6)
    path = bpy.context.active_object
    path.name = name + "_Orbit"
    path.data.materials.append(mat(name + "OrbitMat", (0.3, 0.3, 0.4), emit=0.3))
    # animate
    pivot.rotation_euler = (0, 0, ang)
    pivot.keyframe_insert("rotation_euler", frame=1)
    pivot.rotation_euler = (0, 0, ang + speed * math.pi * 2 * 0.5)
    pivot.keyframe_insert("rotation_euler", frame=240)
    for fc in pivot.animation_data.action.fcurves if hasattr(pivot.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -17, 9)
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam

try:
    scene.eevee.use_bloom = True
except Exception:
    pass
