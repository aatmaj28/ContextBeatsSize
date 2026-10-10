import bpy, math

scene = bpy.context.scene

# Clear any existing objects
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat_basic(name, color, rough=0.5, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

def sphere(name, r, loc, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=64, ring_count=32)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o

# World: dark space
world = bpy.data.worlds.new("Space")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.006, 0.015, 1)
bg.inputs["Strength"].default_value = 1.0

# Sun
sun_mat = mat_basic("SunMat", (1.0, 0.6, 0.1), emit=(1.0, 0.55, 0.1), strength=12.0)
sun = sphere("Sun", 1.5, (0, 0, 0), sun_mat)

# Light inside the sun so it illuminates the planets
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
pl = bpy.context.active_object
pl.data.energy = 8000
pl.data.color = (1.0, 0.85, 0.6)
pl.data.shadow_soft_size = 1.5
sun.visible_shadow = False

# Planets: (name, radius, orbit distance, color, speed)
planets = [
    ("Mercury", 0.25, 3.0, (0.6, 0.55, 0.5), 4.0),
    ("Earth", 0.45, 4.6, (0.1, 0.35, 0.9), 2.5),
    ("Mars", 0.35, 6.2, (0.85, 0.25, 0.08), 1.8),
    ("Saturn", 0.8, 8.5, (0.9, 0.78, 0.5), 1.0),
]

scene.frame_start = 1
scene.frame_end = 240

orbit_mat = mat_basic("OrbitMat", (0.3, 0.3, 0.4), emit=(0.3, 0.35, 0.5), strength=0.3)

for i, (name, r, d, col, speed) in enumerate(planets):
    # Pivot empty that rotates around the sun
    bpy.ops.object.empty_add(location=(0, 0, 0))
    pivot = bpy.context.active_object
    pivot.name = name + "_Pivot"
    start = i * 1.3
    pivot.rotation_euler = (0, 0, start)
    pivot.keyframe_insert("rotation_euler", frame=1)
    pivot.rotation_euler = (0, 0, start + speed * math.pi * 0.5)
    pivot.keyframe_insert("rotation_euler", frame=240)
    for fc in pivot.animation_data.action.fcurves if hasattr(pivot.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

    p = sphere(name, r, (d, 0, 0), mat_basic(name + "Mat", col, rough=0.6))
    p.parent = pivot

    # Orbit line
    bpy.ops.mesh.primitive_torus_add(major_radius=d, minor_radius=0.012,
                                     major_segments=128, minor_segments=6)
    orb = bpy.context.active_object
    orb.name = name + "_Orbit"
    orb.data.materials.append(orbit_mat)

    if name == "Saturn":
        bpy.ops.mesh.primitive_torus_add(major_radius=1.35, minor_radius=0.3,
                                         major_segments=96, minor_segments=24,
                                         location=(d, 0, 0))
        ring = bpy.context.active_object
        ring.name = "SaturnRing"
        ring.scale = (1, 1, 0.05)
        ring.rotation_euler = (math.radians(25), math.radians(10), 0)
        ring.data.materials.append(mat_basic("RingMat", (0.8, 0.7, 0.55), rough=0.7))
        bpy.ops.object.shade_smooth()
        ring.parent = pivot

# Camera
bpy.ops.object.camera_add(location=(0, -16, 9))
cam = bpy.context.active_object
cam.data.lens = 35
bpy.ops.object.empty_add(location=(0, 0, 0))
tgt = bpy.context.active_object
tgt.name = "CamTarget"
c = cam.constraints.new('TRACK_TO')
c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam

# Soft fill so dark sides aren't fully black
bpy.ops.object.light_add(type='SUN', location=(0, -10, 10))
fill = bpy.context.active_object
fill.data.energy = 0.3
fill.rotation_euler = (math.radians(40), 0, 0)

try:
    scene.eevee.use_bloom = True
except Exception:
    pass
