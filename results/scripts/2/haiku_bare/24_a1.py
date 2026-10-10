import bpy
import bmesh
import math
from mathutils import Vector

# ---------- Clear the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for light in list(bpy.data.lights):
    if light.users == 0:
        bpy.data.lights.remove(light)
for cam in list(bpy.data.cameras):
    if cam.users == 0:
        bpy.data.cameras.remove(cam)

scene = bpy.context.scene
collection = scene.collection


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_mesh_object(name, build_fn, material):
    bm = bmesh.new()
    build_fn(bm)
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def mat_translate_scale(loc, scale=(1, 1, 1), rot=(0, 0, 0)):
    import mathutils
    t = mathutils.Matrix.Translation(loc)
    r = mathutils.Euler(rot).to_matrix().to_4x4()
    s = mathutils.Matrix.Diagonal((*scale, 1.0))
    return t @ r @ s


# ---------- Materials ----------
stone_mat = make_material("Stone", (0.72, 0.70, 0.66), roughness=0.6)
marble_mat = make_material("Marble", (0.85, 0.84, 0.82), roughness=0.25)
base_mat = make_material("Pedestal", (0.25, 0.22, 0.20), roughness=0.5)

# ---------- Statue geometry ----------
# Pedestal
def build_pedestal(bm):
    bmesh.ops.create_cube(bm, size=1.0,
                          matrix=mat_translate_scale((0, 0, 0.4), (2.0, 2.0, 0.8)))

pedestal = add_mesh_object("Pedestal", build_pedestal, base_mat)

# Plinth top lip
def build_lip(bm):
    bmesh.ops.create_cube(bm, size=1.0,
                          matrix=mat_translate_scale((0, 0, 0.85), (1.7, 1.7, 0.1)))

lip = add_mesh_object("PedestalLip", build_lip, stone_mat)

# Torso (tapered cylinder)
def build_torso(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=32,
                          radius1=0.45, radius2=0.32, depth=1.6,
                          matrix=mat_translate_scale((0, 0, 2.1)))

torso = add_mesh_object("Torso", build_torso, marble_mat)

# Neck
def build_neck(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=24,
                          radius1=0.16, radius2=0.16, depth=0.3,
                          matrix=mat_translate_scale((0, 0, 3.05)))

neck = add_mesh_object("Neck", build_neck, marble_mat)

# Head
def build_head(bm):
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=20, radius=0.34,
                              matrix=mat_translate_scale((0, 0, 3.5), (1.0, 0.92, 1.1)))

head = add_mesh_object("Head", build_head, marble_mat)

# Arms (raised, slightly angled)
def build_arm_left(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=20,
                          radius1=0.12, radius2=0.09, depth=1.1,
                          matrix=mat_translate_scale((-0.5, 0, 2.6), (1, 1, 1), (0, 0, 0.5)))

def build_arm_right(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=20,
                          radius1=0.12, radius2=0.09, depth=1.1,
                          matrix=mat_translate_scale((0.5, 0, 2.6), (1, 1, 1), (0, 0, -0.5)))

arm_l = add_mesh_object("ArmLeft", build_arm_left, marble_mat)
arm_r = add_mesh_object("ArmRight", build_arm_right, marble_mat)

# Shoulder spheres to blend limbs
def build_shoulder_l(bm):
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.16,
                              matrix=mat_translate_scale((-0.42, 0, 2.7)))

def build_shoulder_r(bm):
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.16,
                              matrix=mat_translate_scale((0.42, 0, 2.7)))

add_mesh_object("ShoulderLeft", build_shoulder_l, marble_mat)
add_mesh_object("ShoulderRight", build_shoulder_r, marble_mat)

# Parent statue parts to a single empty for tidiness
statue_root = bpy.data.objects.new("StatueRoot", None)
statue_root.empty_display_type = 'PLAIN_AXES'
collection.objects.link(statue_root)
for obj in list(collection.objects):
    if obj is not statue_root and obj.type == 'MESH':
        obj.parent = statue_root

# Look-at target at the statue's visual center
focus = bpy.data.objects.new("FocusTarget", None)
focus.empty_display_type = 'PLAIN_AXES'
focus.location = (0, 0, 2.0)
collection.objects.link(focus)

# ---------- Lighting ----------
key_data = bpy.data.lights.new(name="KeyLight", type='AREA')
key_data.energy = 1500
key_data.size = 4.0
key_obj = bpy.data.objects.new("KeyLight", key_data)
key_obj.location = (4, -5, 6)
collection.objects.link(key_obj)
key_obj.constraints.new('TRACK_TO')
key_obj.constraints['Track To'].target = focus
key_obj.constraints['Track To'].track_axis = 'TRACK_NEGATIVE_Z'
key_obj.constraints['Track To'].up_axis = 'UP_Y'

fill_data = bpy.data.lights.new(name="FillLight", type='AREA')
fill_data.energy = 400
fill_data.size = 6.0
fill_obj = bpy.data.objects.new("FillLight", fill_data)
fill_obj.location = (-6, -3, 3)
collection.objects.link(fill_obj)
fill_obj.constraints.new('TRACK_TO')
fill_obj.constraints['Track To'].target = focus
fill_obj.constraints['Track To'].track_axis = 'TRACK_NEGATIVE_Z'
fill_obj.constraints['Track To'].up_axis = 'UP_Y'

sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 2.0
sun_obj = bpy.data.objects.new("Sun", sun_data)
sun_obj.rotation_euler = (math.radians(55), 0, math.radians(30))
collection.objects.link(sun_obj)

# World background
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
    bg.inputs["Strength"].default_value = 0.6
scene.world = world

# ---------- Camera orbit ----------
cam_data = bpy.data.cameras.new("OrbitCamera")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("OrbitCamera", cam_data)
collection.objects.link(cam_obj)
scene.camera = cam_obj

track = cam_obj.constraints.new('TRACK_TO')
track.target = focus
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

FRAME_COUNT = 100
scene.frame_start = 1
scene.frame_end = FRAME_COUNT

radius = 7.0
height = 3.0
center = Vector((0.0, 0.0, 2.0))

# Linear keyframe interpolation for a constant-speed orbit
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

for i in range(FRAME_COUNT):
    frame = scene.frame_start + i
    angle = 2.0 * math.pi * i / FRAME_COUNT
    cam_obj.location = (
        center.x + radius * math.cos(angle),
        center.y + radius * math.sin(angle),
        height,
    )
    cam_obj.keyframe_insert(data_path="location", frame=frame)

# Ensure the camera starts at the first frame position
scene.frame_set(scene.frame_start)
