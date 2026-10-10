import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 100

# ---------- Materials ----------
def make_mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return m

marble = make_mat("Marble", (0.85, 0.83, 0.78), 0.3)
stone = make_mat("Stone", (0.35, 0.33, 0.31), 0.8)
ground_mat = make_mat("Ground", (0.15, 0.2, 0.12), 0.9)

def add(obj, mat):
    obj.data.materials.append(mat)
    return obj

# ---------- Geometry ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
add(bpy.context.active_object, ground_mat)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
p = bpy.context.active_object
p.scale = (1.6, 1.6, 1.0)
add(p, stone)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.1))
p2 = bpy.context.active_object
p2.scale = (1.3, 1.3, 0.2)
add(p2, stone)

# legs
for x in (-0.18, 0.18):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=1.0, location=(x, 0, 1.7))
    o = bpy.context.active_object
    add(o, marble)
    bpy.ops.object.shade_smooth()

# torso (tapered cone)
bpy.ops.mesh.primitive_cone_add(radius1=0.32, radius2=0.42, depth=0.9, location=(0, 0, 2.6), vertices=32)
add(bpy.context.active_object, marble)
bpy.ops.object.shade_smooth()

# shoulders / arms
for side in (-1, 1):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(side * 0.45, 0, 3.0))
    add(bpy.context.active_object, marble)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.8,
                                        location=(side * 0.58, 0, 2.65),
                                        rotation=(0, side * math.radians(15), 0))
    add(bpy.context.active_object, marble)
    bpy.ops.object.shade_smooth()

# raised arm holding a torch-like sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0.62, 0, 2.2))
add(bpy.context.active_object, marble)
bpy.ops.object.shade_smooth()

# neck and head
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.2, location=(0, 0, 3.15))
add(bpy.context.active_object, marble)
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(0, 0, 3.45), segments=48, ring_count=24)
h = bpy.context.active_object
h.scale = (0.9, 0.95, 1.1)
add(h, marble)
bpy.ops.object.shade_smooth()

# ---------- Orbit rig ----------
target = bpy.data.objects.new("Target", None)
target.location = (0, 0, 2.2)
scene.collection.objects.link(target)

pivot = bpy.data.objects.new("OrbitPivot", None)
pivot.location = (0, 0, 0)
scene.collection.objects.link(pivot)

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.parent = pivot
cam.location = (8.0, 0.0, 3.5)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, math.radians(360) * 100 / 99)
pivot.keyframe_insert("rotation_euler", index=2, frame=100)
# make it so frame 100 is just before a full loop; linear interpolation
try:
    ad = pivot.animation_data
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
except Exception:
    pass
pivot.rotation_euler = (0, 0, 0)

# ---------- Lighting ----------
sun = bpy.data.lights.new("Sun", 'SUN')
sun.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun)
sun_obj.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))
scene.collection.objects.link(sun_obj)

area = bpy.data.lights.new("Fill", 'AREA')
area.energy = 400
area.size = 4
area_obj = bpy.data.objects.new("Fill", area)
area_obj.location = (-4, -4, 5)
scene.collection.objects.link(area_obj)
c = area_obj.constraints.new('TRACK_TO')
c.target = target

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.5, 0.6, 0.75, 1.0)
    bg.inputs["Strength"].default_value = 0.6

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_set(1)
