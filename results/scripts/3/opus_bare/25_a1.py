import bpy
import math

scene = bpy.context.scene

# Make new keyframes linear by default
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass

# Clean scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 24

# World
world = bpy.data.worlds.new("Space")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.002, 0.002, 0.006, 1)
    bg.inputs[1].default_value = 1.0

def make_mat(name, color, emission=None, strength=0.0, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    if emission:
        p.inputs["Emission Color"].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m

# Star
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, segments=64, ring_count=32, location=(0, 0, 0))
star = bpy.context.active_object
star.name = "Star"
bpy.ops.object.shade_smooth()
star.data.materials.append(make_mat("StarMat", (1.0, 0.7, 0.2), (1.0, 0.6, 0.15), 15.0))

bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
light = bpy.context.active_object
light.data.energy = 8000
light.data.shadow_soft_size = 1.5
light.data.color = (1.0, 0.85, 0.6)

# Fill light so the night side isn't pitch black
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
fill = bpy.context.active_object
fill.data.energy = 0.3

# Orbit pivot
orbit_radius = 6.0
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
pivot = bpy.context.active_object
pivot.name = "OrbitPivot"

# Planet
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=48, ring_count=24, location=(orbit_radius, 0, 0))
planet = bpy.context.active_object
planet.name = "Planet"
bpy.ops.object.shade_smooth()
planet.data.materials.append(make_mat("PlanetMat", (0.1, 0.35, 0.8), rough=0.6))
planet.parent = pivot

# Orbit path ring
bpy.ops.mesh.primitive_torus_add(major_radius=orbit_radius, minor_radius=0.015,
                                 major_segments=128, minor_segments=8, location=(0, 0, 0))
ring = bpy.context.active_object
ring.name = "OrbitRing"
ring.data.materials.append(make_mat("RingMat", (0.5, 0.5, 0.6), (0.4, 0.45, 0.6), 0.5))

# Animate: full circle over 120 frames (frame 121 == frame 1 for a seamless loop)
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, 2 * math.pi)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=121)

# Planet self-spin
planet.rotation_euler = (0, 0, 0)
planet.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
planet.rotation_euler = (0, 0, 4 * math.pi)
planet.keyframe_insert(data_path="rotation_euler", index=2, frame=121)

def get_fcurves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    fcs = []
    try:
        fcs = list(act.fcurves)
    except Exception:
        pass
    if not fcs:
        try:
            for layer in act.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        fcs.extend(cb.fcurves)
        except Exception:
            pass
    return fcs

for ob in (pivot, planet):
    for fc in get_fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        try:
            fc.extrapolation = 'LINEAR'
        except Exception:
            pass

# Camera
bpy.ops.object.camera_add(location=(0, -14, 9))
cam = bpy.context.active_object
cam.data.lens = 35
track = cam.constraints.new('TRACK_TO')
track.target = star
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_set(1)
