import bpy
import math
from mathutils import Matrix, Vector

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

def make_mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return m

wall_mat = make_mat("Wall", (0.85, 0.82, 0.75), 0.8)
wood_mat = make_mat("Wood", (0.35, 0.18, 0.08), 0.45)
frame_mat = make_mat("Frame", (0.95, 0.95, 0.92), 0.4)
floor_mat = make_mat("Floor", (0.45, 0.32, 0.22), 0.6)
brass_mat = make_mat("Brass", (0.9, 0.7, 0.3), 0.25, 1.0)

def box(name, size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.active_object
    o.name = name
    o.data.transform(Matrix.Diagonal((*size, 1.0)))
    o.location = loc
    o.data.materials.append(mat)
    return o

# Floor
box("Floor", (10, 10, 0.1), (0, 0, -0.05), floor_mat)

# Wall with opening (opening x: -0.5..0.5, z: 0..2.1)
t = 0.15
box("WallLeft", (2.5, t, 3), (-1.75, 0, 1.5), wall_mat)
box("WallRight", (2.5, t, 3), (1.75, 0, 1.5), wall_mat)
box("WallTop", (1.0, t, 0.9), (0, 0, 2.55), wall_mat)

# Door frame trim
fw = 0.08
box("FrameL", (fw, t + 0.04, 2.1 + fw), (-0.5 - fw / 2, 0, (2.1 + fw) / 2), frame_mat)
box("FrameR", (fw, t + 0.04, 2.1 + fw), (0.5 + fw / 2, 0, (2.1 + fw) / 2), frame_mat)
box("FrameT", (1.0 + 2 * fw, t + 0.04, fw), (0, 0, 2.1 + fw / 2), frame_mat)

# Hinge pivot
hinge = bpy.data.objects.new("Hinge", None)
scene.collection.objects.link(hinge)
hinge.location = (-0.5, 0, 0)
hinge.empty_display_size = 0.2

# Door (geometry offset so hinge edge is at pivot)
bpy.ops.mesh.primitive_cube_add(size=1)
door = bpy.context.active_object
door.name = "Door"
door.data.transform(Matrix.Translation((0.49, 0, 1.045)) @ Matrix.Diagonal((0.98, 0.05, 2.08, 1.0)))
door.data.materials.append(wood_mat)
bev = door.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.01
bev.segments = 2
door.parent = hinge

# Door panels (decorative insets)
for i, (zc, h) in enumerate([(0.55, 0.7), (1.5, 0.8)]):
    p = box(f"Panel{i}", (0.7, 0.07, h), (0.49, 0, zc), wood_mat)
    p.scale = (1, 1, 1)
    p.parent = hinge

# Knobs
for y in (-0.06, 0.06):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0.88, y, 1.0))
    k = bpy.context.active_object
    k.data.materials.append(brass_mat)
    bpy.ops.object.shade_smooth()
    k.parent = hinge
    k.location = (0.88, y, 1.0)

# Animation: swing open with ease in/out
scene.frame_start = 1
scene.frame_end = 60
hinge.rotation_euler = (0, 0, 0)
hinge.keyframe_insert("rotation_euler", index=2, frame=1)
hinge.rotation_euler = (0, 0, math.radians(100))
hinge.keyframe_insert("rotation_euler", index=2, frame=41)

ad = hinge.animation_data
if ad and ad.action:
    try:
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
        for fc in cb.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.easing = 'EASE_IN_OUT'
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'
            fc.update()
    except Exception:
        pass

# Lighting
sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 3.0
so = bpy.data.objects.new("Sun", sun)
so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
scene.collection.objects.link(so)

inside = bpy.data.lights.new("Inside", 'POINT')
inside.energy = 400
inside.color = (1.0, 0.8, 0.55)
io = bpy.data.objects.new("Inside", inside)
io.location = (0.3, 2.5, 2.2)
scene.collection.objects.link(io)

fill = bpy.data.lights.new("Fill", 'AREA')
fill.energy = 200
fill.size = 3
fo = bpy.data.objects.new("Fill", fill)
fo.location = (3, -4, 3)
fo.rotation_euler = (math.radians(55), 0, math.radians(35))
scene.collection.objects.link(fo)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1)
    bg.inputs["Strength"].default_value = 0.5

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (2.6, -5.5, 1.8)
direction = Vector((0, 0.3, 1.1)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
scene.frame_set(1)
