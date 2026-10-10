import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

def make_mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return m

mat_wall = make_mat("Wall", (0.85, 0.82, 0.75), 0.8)
mat_floor = make_mat("Floor", (0.35, 0.22, 0.12), 0.4)
mat_door = make_mat("Door", (0.45, 0.12, 0.08), 0.35)
mat_frame = make_mat("Frame", (0.95, 0.95, 0.93), 0.4)
mat_brass = make_mat("Brass", (0.85, 0.65, 0.25), 0.25, 1.0)

def box(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o

# Floor
bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(mat_floor)

# Wall with opening (opening: x -0.5..0.5, z 0..2.15)
wall_h = 3.0
box("WallLeft", (-1.75, 0, wall_h / 2), (2.5, 0.2, wall_h), mat_wall)
box("WallRight", (1.75, 0, wall_h / 2), (2.5, 0.2, wall_h), mat_wall)
box("WallTop", (0, 0, (2.15 + wall_h) / 2), (1.0, 0.2, wall_h - 2.15), mat_wall)

# Door frame trim
box("FrameL", (-0.5, -0.02, 1.1), (0.08, 0.26, 2.2), mat_frame)
box("FrameR", (0.5, -0.02, 1.1), (0.08, 0.26, 2.2), mat_frame)
box("FrameT", (0, -0.02, 2.19), (1.08, 0.26, 0.08), mat_frame)

# Hinge pivot
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(-0.46, 0, 0))
hinge = bpy.context.active_object
hinge.name = "Hinge"

# Door panel (built at origin then parented with local offset)
door = box("Door", (0, 0, 0), (0.92, 0.05, 2.12), mat_door)
door.parent = hinge
door.location = (0.46, 0, 1.07)

# Panel details
for i, (zc, h) in enumerate([(0.55, 0.75), (1.5, 0.9)]):
    for side in (-1, 1):
        p = box(f"Panel{i}_{side}", (0, 0, 0), (0.62, 0.015, h), mat_door)
        p.parent = hinge
        p.location = (0.46, side * 0.03, zc)

# Knobs
for side in (-1, 1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0, 0, 0))
    k = bpy.context.active_object
    k.name = "Knob"
    k.data.materials.append(mat_brass)
    bpy.ops.object.shade_smooth()
    k.parent = hinge
    k.location = (0.8, side * 0.07, 1.0)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.05, location=(0, 0, 0),
                                        rotation=(math.radians(90), 0, 0))
    s = bpy.context.active_object
    s.data.materials.append(mat_brass)
    s.parent = hinge
    s.location = (0.8, side * 0.045, 1.0)

# Animation: swing open over 40 frames with ease in/out
scene.frame_start = 1
scene.frame_end = 40
hinge.rotation_euler = (0, 0, 0)
hinge.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
hinge.rotation_euler = (0, 0, math.radians(100))
hinge.keyframe_insert(data_path="rotation_euler", index=2, frame=40)

def iter_fcurves(action):
    try:
        for fc in action.fcurves:
            yield fc
        return
    except Exception:
        pass
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        yield fc
    except Exception:
        pass

if hinge.animation_data and hinge.animation_data.action:
    for fc in iter_fcurves(hinge.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = 'SINE'
            kp.easing = 'EASE_IN_OUT'

# Lighting
bpy.ops.object.light_add(type='SUN', location=(4, -5, 6))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(0, 2.5, 2.5))
inside = bpy.context.active_object
inside.data.energy = 300
inside.data.size = 2.0
inside.data.color = (1.0, 0.85, 0.6)
inside.rotation_euler = (math.radians(-40), 0, 0)

bpy.ops.object.light_add(type='AREA', location=(-2, -3, 3))
fill = bpy.context.active_object
fill.data.energy = 200
fill.data.size = 3.0
fill.rotation_euler = (math.radians(50), 0, math.radians(-35))

# Camera
bpy.ops.object.camera_add(location=(2.6, -4.6, 1.9))
cam = bpy.context.active_object
cam.data.lens = 35
bpy.ops.object.empty_add(location=(0, 0.2, 1.05))
target = bpy.context.active_object
target.name = "CamTarget"
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam

# World
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 0.5

scene.frame_set(1)
