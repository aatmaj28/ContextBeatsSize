import bpy
import bmesh
import math
from mathutils import Vector

scene = bpy.context.scene

# Clear default scene objects
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def make_box(name, min_v, max_v, mat):
    """Create a box mesh from min/max corners in world space."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    bm = bmesh.new()
    x0, y0, z0 = min_v
    x1, y1, z1 = max_v
    verts = [
        bm.verts.new((x0, y0, z0)), bm.verts.new((x1, y0, z0)),
        bm.verts.new((x1, y1, z0)), bm.verts.new((x0, y1, z0)),
        bm.verts.new((x0, y0, z1)), bm.verts.new((x1, y0, z1)),
        bm.verts.new((x1, y1, z1)), bm.verts.new((x0, y1, z1)),
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
        (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    for f in faces:
        bm.faces.new([verts[i] for i in f])
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    return obj


# Materials
wall_mat = make_material("WallMat", (0.85, 0.82, 0.76), roughness=0.9)
floor_mat = make_material("FloorMat", (0.35, 0.25, 0.18), roughness=0.6)
door_mat = make_material("DoorMat", (0.45, 0.22, 0.10), roughness=0.4)
trim_mat = make_material("TrimMat", (0.95, 0.95, 0.93), roughness=0.5)
brass_mat = make_material("BrassMat", (0.85, 0.65, 0.25), roughness=0.25, metallic=1.0)

# Wall with an opening (opening: x in [-0.5, 0.5], z in [0, 2.1])
wall_thick = 0.2
make_box("WallLeft", (-3.0, -wall_thick / 2, 0.0), (-0.5, wall_thick / 2, 3.0), wall_mat)
make_box("WallRight", (0.5, -wall_thick / 2, 0.0), (3.0, wall_thick / 2, 3.0), wall_mat)
make_box("WallTop", (-0.5, -wall_thick / 2, 2.1), (0.5, wall_thick / 2, 3.0), wall_mat)

# Floor
make_box("Floor", (-3.0, -1.5, -0.1), (3.0, 1.5, 0.0), floor_mat)

# Door frame trim
trim_t = 0.04
make_box("TrimLeft", (-0.55, -0.12, 0.0), (-0.5, 0.12, 2.12), trim_mat)
make_box("TrimRight", (0.5, -0.12, 0.0), (0.55, 0.12, 2.12), trim_mat)
make_box("TrimTop", (-0.55, -0.12, 2.1), (0.55, 0.12, 2.15), trim_mat)

# Door panel: hinge at object origin, panel extends along +X, thickness along Y
door_w, door_h, door_t = 1.0, 2.1, 0.06
hinge = Vector((-0.5, 0.0, 0.0))

door = make_box(
    "Door",
    (0.0, -door_t / 2, 0.0),
    (door_w, door_t / 2, door_h),
    door_mat,
)
door.location = hinge
door.rotation_mode = 'XYZ'

# Door knob near free edge (child of door so it follows rotation)
knob_mesh = bpy.data.meshes.new("Knob")
knob = bpy.data.objects.new("Knob", knob_mesh)
scene.collection.objects.link(knob)
bpy.ops.mesh.primitive_uv_sphere_add  # ensure ops available; we build via bmesh instead
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.04)
bm.to_mesh(knob_mesh)
bm.free()
knob_mesh.materials.append(brass_mat)
knob.location = (door_w - 0.1, door_t / 2 + 0.03, door_h * 0.45)
knob.parent = door

# Animation: ease-in/ease-out swing from closed to ~90 degrees open
FRAME_START = 1
FRAME_END = 40
OPEN_ANGLE = math.radians(-90.0)  # swing toward the camera side (-Y)

scene.frame_start = FRAME_START
scene.frame_end = FRAME_END


def ease_in_out(t):
    # smoothstep ease-in / ease-out
    return t * t * (3.0 - 2.0 * t)


n = FRAME_END - FRAME_START
for i in range(n + 1):
    frame = FRAME_START + i
    t = i / n
    door.rotation_euler = (0.0, 0.0, OPEN_ANGLE * ease_in_out(t))
    door.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)

# Lighting
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.location = (4.0, -4.0, 6.0)
sun.rotation_euler = (math.radians(50), 0.0, math.radians(35))

area_data = bpy.data.lights.new(name="Fill", type='AREA')
area_data.energy = 400.0
area_data.size = 3.0
area = bpy.data.objects.new("Fill", area_data)
scene.collection.objects.link(area)
area.location = (-2.5, -3.0, 2.8)
area.rotation_euler = (math.radians(70), 0.0, math.radians(-30))

# Camera framing the doorway and the swing arc
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((2.6, -4.2, 1.6))
target = Vector((0.0, 0.0, 1.05))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# World background
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.6, 0.65, 0.72, 1.0)
    bg.inputs["Strength"].default_value = 0.8
