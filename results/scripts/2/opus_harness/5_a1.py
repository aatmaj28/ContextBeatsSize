import bpy, math, random

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def emissive_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

def planet_mat(name, color, rough=0.6):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

# Sun
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, segments=64, ring_count=32, location=(0, 0, 0))
sun = bpy.context.active_object
sun.name = "Sun"
bpy.ops.object.shade_smooth()
sun.data.materials.append(emissive_mat("SunMat", (1.0, 0.55, 0.1), 12))

sl = bpy.data.lights.new("SunLight", 'POINT')
sl.energy = 3000
sl.color = (1.0, 0.85, 0.6)
sl.shadow_soft_size = 1.5
slo = bpy.data.objects.new("SunLight", sl)
scene.collection.objects.link(slo)

planets = [
    ("Mercury", 0.3, 3.0, (0.6, 0.55, 0.5), 20, False),
    ("Earth", 0.5, 4.6, (0.1, 0.35, 0.9), 75, False),
    ("Mars", 0.4, 6.2, (0.85, 0.3, 0.1), 140, False),
    ("Saturn", 0.8, 8.5, (0.85, 0.75, 0.5), 230, True),
]
scene.frame_start = 1
scene.frame_end = 240

for name, r, dist, col, ang, ring in planets:
    pivot = bpy.data.objects.new(name + "_Pivot", None)
    scene.collection.objects.link(pivot)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=24, location=(dist, 0, 0))
    p = bpy.context.active_object
    p.name = name
    bpy.ops.object.shade_smooth()
    p.data.materials.append(planet_mat(name + "Mat", col))
    p.parent = pivot
    if ring:
        bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.02, vertices=96, location=(dist, 0, 0))
        rg = bpy.context.active_object
        rg.name = "SaturnRing"
        mod = rg.modifiers.new("hole", 'SOLIDIFY')
        bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.2, vertices=96, location=(dist, 0, 0))
        cutter = bpy.context.active_object
        rg.modifiers.remove(mod)
        b = rg.modifiers.new("cut", 'BOOLEAN')
        b.object = cutter
        b.operation = 'DIFFERENCE'
        cutter.hide_viewport = True
        cutter.hide_render = True
        rg.data.materials.append(planet_mat("RingMat", (0.75, 0.65, 0.45), 0.8))
        rg.rotation_euler = (math.radians(25), math.radians(10), 0)
        rg.parent = pivot
        cutter.rotation_euler = rg.rotation_euler
        cutter.parent = pivot
    # orbit lines
    bpy.ops.mesh.primitive_torus_add(major_radius=dist, minor_radius=0.01, major_segments=128, minor_segments=6)
    t = bpy.context.active_object
    t.name = name + "_Orbit"
    t.data.materials.append(emissive_mat(name + "OrbitMat", (0.3, 0.35, 0.5), 0.5))
    # animate orbit
    speed = 360 * 1.5 / (dist ** 1.5) * 3
    pivot.rotation_euler = (0, 0, math.radians(ang))
    pivot.keyframe_insert("rotation_euler", index=2, frame=1)
    pivot.rotation_euler = (0, 0, math.radians(ang + speed))
    pivot.keyframe_insert("rotation_euler", index=2, frame=240)
    for fc in pivot.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# Stars
random.seed(3)
star_mat = emissive_mat("StarMat", (1, 1, 1), 8)
for i in range(150):
    th = random.uniform(0, 2 * math.pi)
    ph = random.uniform(-0.5, 1.2)
    d = random.uniform(40, 60)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=random.uniform(0.05, 0.15), subdivisions=1,
        location=(d * math.cos(th) * math.cos(ph), d * math.sin(th) * math.cos(ph), d * math.sin(ph)))
    bpy.context.active_object.data.materials.append(star_mat)

# World
w = bpy.data.worlds.new("Space")
scene.world = w
bg = w.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.005, 0.015, 1)
bg.inputs["Strength"].default_value = 1.0

# Fill light
fl = bpy.data.lights.new("Fill", 'SUN')
fl.energy = 0.3
flo = bpy.data.objects.new("Fill", fl)
flo.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(flo)

# Camera
cam = bpy.data.cameras.new("Cam")
cam.lens = 35
camo = bpy.data.objects.new("Cam", cam)
scene.collection.objects.link(camo)
camo.location = (0, -17, 9)
tgt = bpy.data.objects.new("Target", None)
scene.collection.objects.link(tgt)
c = camo.constraints.new('TRACK_TO')
c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = camo

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
