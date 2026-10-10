import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

scene.render.engine = 'BLENDER_EEVEE'

# World
world = bpy.data.worlds.new("Space")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.005, 0.006, 0.015, 1)
bg.inputs["Strength"].default_value = 1.0

def mat_principled(name, color, rough=0.6, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m

def sphere(name, r, loc, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=64, ring_count=32)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o

# Sun
sun_mat = mat_principled("Sun", (1, 0.6, 0.1), emit=(1, 0.55, 0.1), strength=15)
sphere("Sun", 1.5, (0, 0, 0), sun_mat)
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
pl = bpy.context.active_object
pl.data.energy = 6000
pl.data.color = (1, 0.85, 0.6)
pl.data.shadow_soft_size = 1.5

planets = [
    ("Mercury", 0.25, 2.6, 20, (0.6, 0.55, 0.5)),
    ("Earth", 0.45, 4.0, 110, (0.1, 0.35, 0.9)),
    ("Mars", 0.35, 5.5, 200, (0.85, 0.3, 0.1)),
    ("Saturn", 0.8, 7.8, 300, (0.9, 0.75, 0.45)),
]
orbit_mat = mat_principled("Orbit", (0.3, 0.3, 0.4), emit=(0.3, 0.35, 0.5), strength=0.5)
for name, r, d, ang, col in planets:
    a = math.radians(ang)
    loc = (d * math.cos(a), d * math.sin(a), 0)
    p = sphere(name, r, loc, mat_principled(name, col, 0.7))
    # orbit line
    bpy.ops.mesh.primitive_torus_add(major_radius=d, minor_radius=0.008,
                                     major_segments=128, minor_segments=6)
    bpy.context.active_object.data.materials.append(orbit_mat)
    if name == "Saturn":
        bpy.ops.mesh.primitive_torus_add(major_radius=1.35, minor_radius=0.35,
                                         major_segments=96, minor_segments=24,
                                         location=loc, rotation=(math.radians(70), math.radians(15), 0))
        ring = bpy.context.active_object
        ring.name = "Ring"
        ring.scale = (1, 1, 0.04)
        bpy.ops.object.shade_smooth()
        ring.data.materials.append(mat_principled("RingMat", (0.8, 0.7, 0.55), 0.5))

# Fill light
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
bpy.context.active_object.data.energy = 0.3

# Camera
bpy.ops.object.camera_add(location=(4, -14, 7.5))
cam = bpy.context.active_object
target = (1.0, 2.0, 0)
import mathutils
direction = mathutils.Vector(target) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 32
scene.camera = cam
