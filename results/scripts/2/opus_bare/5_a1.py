import bpy, math, random

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def emissive_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

def planet_mat(name, color, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

# Sun
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, segments=64, ring_count=32, location=(0, 0, 0))
sun = bpy.context.active_object
sun.name = "Sun"
bpy.ops.object.shade_smooth()
sun.data.materials.append(emissive_mat("SunMat", (1.0, 0.6, 0.15), 8.0))

sun_light = bpy.data.lights.new("SunLight", 'POINT')
sun_light.energy = 8000
sun_light.color = (1.0, 0.85, 0.6)
sun_light.shadow_soft_size = 1.5
lo = bpy.data.objects.new("SunLight", sun_light)
scene.collection.objects.link(lo)

planets = [
    ("Mercury", 0.3, 3.0, (0.6, 0.55, 0.5), 20),
    ("Earth", 0.5, 4.6, (0.1, 0.35, 0.8), 110),
    ("Mars", 0.4, 6.2, (0.8, 0.3, 0.12), 215),
    ("Saturn", 0.8, 8.5, (0.85, 0.75, 0.5), 320),
]

orbit_mat = emissive_mat("OrbitMat", (0.4, 0.5, 0.8), 0.5)

for name, r, dist, col, ang in planets:
    a = math.radians(ang)
    loc = (dist * math.cos(a), dist * math.sin(a), 0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=24, location=loc)
    p = bpy.context.active_object
    p.name = name
    bpy.ops.object.shade_smooth()
    p.data.materials.append(planet_mat(name + "Mat", col))
    # orbit line
    bpy.ops.mesh.primitive_torus_add(major_radius=dist, minor_radius=0.012,
                                     major_segments=128, minor_segments=6, location=(0, 0, 0))
    orb = bpy.context.active_object
    orb.name = name + "Orbit"
    orb.data.materials.append(orbit_mat)
    if name == "Saturn":
        bpy.ops.mesh.primitive_torus_add(major_radius=1.35, minor_radius=0.3,
                                         major_segments=96, minor_segments=24, location=loc)
        ring = bpy.context.active_object
        ring.name = "SaturnRing"
        ring.scale = (1, 1, 0.05)
        ring.rotation_euler = (math.radians(25), math.radians(10), 0)
        bpy.ops.object.shade_smooth()
        ring.data.materials.append(planet_mat("RingMat", (0.75, 0.65, 0.45), 0.4))

# Stars
random.seed(3)
star_mat = emissive_mat("StarMat", (1, 1, 1), 5)
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.05, subdivisions=1, location=(0, 0, 0))
base = bpy.context.active_object
base.data.materials.append(star_mat)
for i in range(200):
    th = random.uniform(0, 2 * math.pi)
    ph = math.acos(random.uniform(-1, 1))
    R = random.uniform(40, 60)
    s = base.copy()
    s.location = (R * math.sin(ph) * math.cos(th), R * math.sin(ph) * math.sin(th), R * math.cos(ph))
    s.scale = [random.uniform(1, 3)] * 3
    scene.collection.objects.link(s)
bpy.data.objects.remove(base, do_unlink=True)

# World
world = bpy.data.worlds.new("Space")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.005, 0.015, 1)
bg.inputs["Strength"].default_value = 1.0

# Fill light
fill = bpy.data.lights.new("Fill", 'SUN')
fill.energy = 0.3
fill.color = (0.6, 0.7, 1.0)
fo = bpy.data.objects.new("Fill", fill)
fo.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(fo)

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -17, 10)
c = cam.constraints.new('TRACK_TO')
c.target = sun
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam

try:
    scene.eevee.use_bloom = True
except Exception:
    pass
scene.frame_start = 1
scene.frame_end = 1
