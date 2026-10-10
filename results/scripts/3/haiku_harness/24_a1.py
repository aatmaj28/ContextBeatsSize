import bpy
import bmesh
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------------------------------------------------------------
# Clear the default scene contents
# ---------------------------------------------------------------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_part(name, kind, loc, scale=(1, 1, 1), rot=(0, 0, 0), mat=None):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    if kind == 'cube':
        bmesh.ops.create_cube(bm, size=1.0)
    elif kind == 'sphere':
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    elif kind == 'cylinder':
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=32,
                              radius1=1.0, radius2=1.0, depth=1.0)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = (kind != 'cube')
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.location = Vector(loc)
    obj.scale = Vector(scale)
    obj.rotation_euler = rot
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


# ---------------------------------------------------------------
# Materials
# ---------------------------------------------------------------
marble = make_material("Marble", (0.85, 0.83, 0.78), roughness=0.4)
plinth_mat = make_material("PlinthStone", (0.25, 0.26, 0.28), roughness=0.7)
ground_mat = make_material("Ground", (0.12, 0.12, 0.13), roughness=0.9)

# ---------------------------------------------------------------
# Ground
# ---------------------------------------------------------------
add_part("Ground", 'cube', loc=(0, 0, -0.025),
         scale=(12, 12, 0.05), mat=ground_mat)

# ---------------------------------------------------------------
# Statue (built from primitives)
# ---------------------------------------------------------------
# Plinth
add_part("Plinth", 'cube', loc=(0, 0, 0.2),
         scale=(0.9, 0.9, 0.4), mat=plinth_mat)

# Torso
add_part("Torso", 'sphere', loc=(0, 0, 1.25),
         scale=(0.45, 0.3, 0.7), mat=marble)

# Shoulders
add_part("Shoulders", 'sphere', loc=(0, 0, 1.75),
         scale=(0.55, 0.28, 0.18), mat=marble)

# Neck
add_part("Neck", 'cylinder', loc=(0, 0, 1.95),
         scale=(0.14, 0.14, 0.3), mat=marble)

# Head
add_part("Head", 'sphere', loc=(0, 0, 2.2),
         scale=(0.28, 0.3, 0.33), mat=marble)

# Arms (hanging, slightly angled)
add_part("ArmL", 'sphere', loc=(-0.5, 0, 1.45),
         scale=(0.13, 0.13, 0.42), rot=(0, math.radians(10), 0), mat=marble)
add_part("ArmR", 'sphere', loc=(0.5, 0, 1.45),
         scale=(0.13, 0.13, 0.42), rot=(0, math.radians(-10), 0), mat=marble)

# ---------------------------------------------------------------
# Orbit pivot (empty at statue center, rotates over time)
# ---------------------------------------------------------------
pivot = bpy.data.objects.new("OrbitPivot", None)
pivot.empty_display_type = 'PLAIN_AXES'
pivot.empty_display_size = 0.3
scene.collection.objects.link(pivot)
pivot.location = (0, 0, 1.1)

FRAME_START = 1
FRAME_END = 100
scene.frame_start = FRAME_START
scene.frame_end = FRAME_END

for f in range(FRAME_START, FRAME_END + 1):
    t = (f - FRAME_START) / (FRAME_END - FRAME_START + 1)  # 0..<1, seamless loop
    pivot.rotation_euler = (0.0, 0.0, 2.0 * math.pi * t)
    pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=f)

# ---------------------------------------------------------------
# Camera (child of pivot, always tracking the pivot/statue center)
# ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("OrbitCameraData")
cam_data.lens = 50.0
cam = bpy.data.objects.new("OrbitCamera", cam_data)
scene.collection.objects.link(cam)
cam.parent = pivot
cam.location = (0.0, -7.5, 0.5)  # local offset from pivot

track = cam.constraints.new(type='TRACK_TO')
track.target = pivot
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

scene.camera = cam

# ---------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------
sun_data = bpy.data.lights.new("KeySun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("KeySun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

area_data = bpy.data.lights.new("FillArea", 'AREA')
area_data.energy = 400.0
area_data.size = 4.0
area = bpy.data.objects.new("FillArea", area_data)
scene.collection.objects.link(area)
area.location = (3.5, -4.0, 4.0)
area_track = area.constraints.new(type='TRACK_TO')
area_track.target = pivot
area_track.track_axis = 'TRACK_NEGATIVE_Z'
area_track.up_axis = 'UP_Y'

rim_data = bpy.data.lights.new("RimPoint", 'POINT')
rim_data.energy = 300.0
rim = bpy.data.objects.new("RimPoint", rim_data)
scene.collection.objects.link(rim)
rim.location = (-3.0, 3.5, 3.0)

# ---------------------------------------------------------------
# World background
# ---------------------------------------------------------------
world = bpy.data.worlds.new("StudioWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 1.0
