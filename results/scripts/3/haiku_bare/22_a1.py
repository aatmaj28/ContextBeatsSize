import bpy
import math
from mathutils import Vector

# ---------- Clean the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def shade_smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


# ---------- Materials ----------
mat_ground = make_material("Ground", (0.35, 0.55, 0.25), roughness=0.9)
mat_tower = make_material("Tower", (0.85, 0.85, 0.88), roughness=0.4, metallic=0.2)
mat_nacelle = make_material("Nacelle", (0.9, 0.9, 0.92), roughness=0.35, metallic=0.3)
mat_blade = make_material("Blade", (0.95, 0.95, 0.97), roughness=0.5)
mat_hub = make_material("Hub", (0.8, 0.15, 0.1), roughness=0.4, metallic=0.1)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.scale = (30, 30, 1)
assign(ground, mat_ground)

# ---------- Tower ----------
TOWER_HEIGHT = 10.0
bpy.ops.mesh.primitive_cone_add(
    vertices=32, radius1=0.5, radius2=0.22, depth=TOWER_HEIGHT,
    location=(0, 0, TOWER_HEIGHT / 2.0)
)
tower = bpy.context.active_object
tower.name = "Tower"
assign(tower, mat_tower)
shade_smooth(tower)

# Base collar
bpy.ops.mesh.primitive_cylinder_add(
    vertices=32, radius=0.6, depth=0.4, location=(0, 0, 0.2)
)
base = bpy.context.active_object
base.name = "TowerBase"
assign(base, mat_tower)
shade_smooth(base)

# ---------- Nacelle ----------
NACELLE_POS = Vector((0.0, 0.0, TOWER_HEIGHT + 0.3))
bpy.ops.mesh.primitive_cube_add(size=2, location=NACELLE_POS)
nacelle = bpy.context.active_object
nacelle.name = "Nacelle"
nacelle.scale = (0.55, 1.5, 0.55)
assign(nacelle, mat_nacelle)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# ---------- Rotor (pivot empty) ----------
HUB_OFFSET = Vector((0.0, -1.6, 0.0))  # hub sits in front of nacelle along -Y
rotor_pos = NACELLE_POS + HUB_OFFSET

bpy.ops.object.empty_add(type='PLAIN_AXES', location=rotor_pos)
rotor = bpy.context.active_object
rotor.name = "Rotor"
rotor.empty_display_size = 0.5

# Hub sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.38, location=rotor_pos, segments=32, ring_count=16)
hub = bpy.context.active_object
hub.name = "Hub"
assign(hub, mat_hub)
shade_smooth(hub)
hub.parent = rotor

# Nose cone
bpy.ops.mesh.primitive_cone_add(
    vertices=32, radius1=0.38, radius2=0.02, depth=0.6,
    location=rotor_pos + Vector((0, -0.3, 0))
)
nose = bpy.context.active_object
nose.name = "NoseCone"
nose.rotation_euler = (math.radians(90), 0, 0)
assign(nose, mat_hub)
shade_smooth(nose)
nose.parent = rotor

# ---------- Blades ----------
BLADE_LENGTH = 4.0
BLADE_WIDTH = 0.35
BLADE_THICK = 0.06
NUM_BLADES = 3

for i in range(NUM_BLADES):
    a = i * 2.0 * math.pi / NUM_BLADES
    direction = Vector((math.sin(a), 0.0, math.cos(a)))
    # Blade center sits halfway along its length from the hub
    center = direction * (BLADE_LENGTH / 2.0 + 0.2)

    bpy.ops.mesh.primitive_cube_add(size=2, location=rotor_pos + center)
    blade = bpy.context.active_object
    blade.name = f"Blade_{i}"
    # Cube size 2 => half extents equal scale
    blade.scale = (BLADE_WIDTH / 2.0, BLADE_THICK / 2.0, BLADE_LENGTH / 2.0)
    blade.rotation_euler = (0.0, a, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(blade, mat_blade)
    blade.parent = rotor
    blade.matrix_parent_inverse = rotor.matrix_world.inverted()

# ---------- Constant-speed rotation animation ----------
FRAME_END = 120
REVOLUTIONS = 2.0  # total turns over the animation

# Make newly inserted keys use linear interpolation (constant angular speed)
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass

rotor.rotation_mode = 'XYZ'
rotor.rotation_euler = (0.0, 0.0, 0.0)
rotor.keyframe_insert(data_path="rotation_euler", index=1, frame=1)

rotor.rotation_euler = (0.0, REVOLUTIONS * 2.0 * math.pi, 0.0)
rotor.keyframe_insert(data_path="rotation_euler", index=1, frame=FRAME_END)

# Force linear interpolation on the keys explicitly where the API allows it
try:
    action = rotor.animation_data.action
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.extrapolation = 'LINEAR'
except Exception:
    pass

# ---------- Scene timing ----------
scene.frame_start = 1
scene.frame_end = FRAME_END
scene.frame_set(1)

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(10, -10, 15))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

bpy.ops.object.light_add(type='AREA', location=(-8, -6, 8))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 300.0
fill.data.size = 6.0

# ---------- World background ----------
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.55, 0.72, 0.9, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
target = Vector((0.0, -0.6, TOWER_HEIGHT * 0.75))
cam_loc = Vector((13.0, -17.0, 9.0))

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = cam_loc

direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
