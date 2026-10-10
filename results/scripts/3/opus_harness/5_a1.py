import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def emissive_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

def pbr_mat(name, color, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

# Sun
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, segments=64, ring_count=32, location=(0, 0, 0))
sun = bpy.context.active_object
sun.name = "Sun"
bpy.ops.object.shade_smooth()
sun.data.materials.append(emissive_mat("SunMat", (1.0, 0.6, 0.15, 1), 12.0))

# Sun light
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
pl = bpy.context.active_object
pl.data.energy = 6000
pl.data.color = (1.0, 0.85, 0.6)
pl.data.shadow_soft_size = 1.5

planets = [
    ("Mercury", 0.3, 3.0, 20, (0.6, 0.55, 0.5, 1), False),
    ("Earth", 0.55, 4.6, 110, (0.1, 0.35, 0.8, 1), False),
    ("Ringed", 0.85, 6.8, 210, (0.85, 0.7, 0.45, 1), True),
    ("Mars", 0.45, 9.0, 300, (0.8, 0.25, 0.1, 1), False),
]

for name, r, dist, ang, col, ring in planets:
    a = math.radians(ang)
    loc = (dist * math.cos(a), dist * math.sin(a), 0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=24, location=loc)
    p = bpy.context.active_object
    p.name = name
    bpy.ops.object.shade_smooth()
    p.data.materials.append(pbr_mat(name + "Mat", col))
    if ring:
        bpy.ops.mesh.primitive_torus_add(location=loc, major_radius=r * 1.8,
                                         minor_radius=r * 0.4, major_segments=96, minor_segments=16)
        rg = bpy.context.active_object
        rg.name = name + "Ring"
        rg.scale = (1, 1, 0.08)
        rg.rotation_euler = (math.radians(25), math.radians(10), 0)
        bpy.ops.object.shade_smooth()
        rg.data.materials.append(pbr_mat("RingMat", (0.75, 0.65, 0.5, 1), 0.8))
    # orbit path
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0), major_radius=dist,
                                     minor_radius=0.012, major_segments=128, minor_segments=6)
    orb = bpy.context.active_object
    orb.name = name + "Orbit"
    orb.data.materials.append(emissive_mat(name + "OrbitMat", (0.4, 0.5, 0.8, 1), 0.6))

# World: dark space
world = bpy.data.worlds.new("Space")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.006, 0.015, 1)
bg.inputs["Strength"].default_value = 1.0

# Fill light
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
fl = bpy.context.active_object
fl.data.energy = 0.3
fl.rotation_euler = (math.radians(40), 0, math.radians(30))

# Camera
bpy.ops.object.camera_add(location=(0, -17, 9))
cam = bpy.context.active_object
cam.data.lens = 35
tgt = bpy.data.objects.new("Target", None)
scene.collection.objects.link(tgt)
c = cam.constraints.new('TRACK_TO')
c.target = tgt
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.frame_start = 1
scene.frame_end = 1
