import bpy
import math
from bpy_extras import anim_utils

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Materials ----------
def make_mat(name, color, rough, metallic=0.0):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m

marble = make_mat("Marble", (0.92, 0.9, 0.86), 0.25)
stone = make_mat("DarkStone", (0.12, 0.12, 0.13), 0.6)
floor_mat = make_mat("Floor", (0.35, 0.33, 0.3), 0.8)
bronze = make_mat("Bronze", (0.7, 0.45, 0.2), 0.3, 1.0)

def assign(obj, mat):
    obj.data.materials.append(mat)

def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

# ---------- Geometry ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
assign(floor, floor_mat)

# Pedestal: base, column, cap
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.15))
base = bpy.context.active_object
base.scale = (1.6, 1.6, 0.3)
assign(base, stone)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.9))
col = bpy.context.active_object
col.scale = (1.1, 1.1, 1.2)
assign(col, stone)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.6))
cap = bpy.context.active_object
cap.scale = (1.4, 1.4, 0.2)
assign(cap, stone)

# Statue figure
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.35, depth=0.15, location=(0, 0, 1.775))
plinth = bpy.context.active_object
assign(plinth, marble); smooth(plinth)

bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.38, radius2=0.22, depth=1.0, location=(0, 0, 2.35))
torso = bpy.context.active_object
torso.scale = (1.0, 0.7, 1.0)
assign(torso, marble); smooth(torso)

bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.32, location=(0, 0, 2.95))
shoulders = bpy.context.active_object
shoulders.scale = (1.5, 0.8, 0.5)
assign(shoulders, marble); smooth(shoulders)

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.09, depth=0.2, location=(0, 0, 3.15))
neck = bpy.context.active_object
assign(neck, marble); smooth(neck)

bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.22, location=(0, 0.02, 3.42))
head = bpy.context.active_object
head.scale = (0.9, 1.0, 1.15)
assign(head, marble); smooth(head)
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.03, location=(0, 0.02, 3.6))
halo = bpy.context.active_object
halo.rotation_euler = (math.radians(15), 0, 0)
assign(halo, bronze); smooth(halo)

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-4, 3, 5))
fill = bpy.context.active_object
fill.data.energy = 400
fill.data.size = 4
fill.rotation_euler = (math.radians(-50), math.radians(-40), 0)

world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Camera orbit ----------
target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
target.location = (0, 0, 2.4)

pivot = bpy.data.objects.new("OrbitPivot", None)
scene.collection.objects.link(pivot)
pivot.location = (0, 0, 0)

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 45
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.parent = pivot
cam.location = (0, -8.5, 3.6)

con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'

scene.camera = cam
scene.frame_start = 1
scene.frame_end = 100

pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, math.radians(360))
pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=101)

ad = pivot.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
if cb:
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

scene.frame_set(1)
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
