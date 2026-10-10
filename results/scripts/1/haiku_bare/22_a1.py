import bpy
import math
from mathutils import Vector

# ---------- Clean up any existing objects ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Animation settings ----------
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120
scene.frame_set(1)

# Linear keyframe interpolation so the spin speed is constant
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

# ---------- Helper functions ----------
def make_material(name, color, roughness=0.6, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj

# ---------- Materials ----------
mat_ground = make_material("Grass", (0.18, 0.42, 0.16), roughness=0.9)
mat_tower = make_material("TowerWhite", (0.85, 0.84, 0.80), roughness=0.5)
mat_nacelle = make_material("NacelleGrey", (0.45, 0.47, 0.50), roughness=0.4, metallic=0.3)
mat_blade = make_material("BladeWhite", (0.92, 0.92, 0.95), roughness=0.35)
mat_hub = make_material("HubRed", (0.75, 0.12, 0.10), roughness=0.4)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
ground = bpy.context.active_object
ground.scale = (40, 40, 1)
assign(ground, mat_ground)

# ---------- Tower ----------
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.9, radius2=0.45,
                                depth=12, location=(0, 0, 6))
tower = bpy.context.active_object
tower.name = "Tower"
assign(tower, mat_tower)

# ---------- Nacelle (housing at top of tower) ----------
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.0, 12.0))
nacelle = bpy.context.active_object
nacelle.name = "Nacelle"
nacelle.scale = (0.8, 1.2, 0.8)
assign(nacelle, mat_nacelle)

# ---------- Rotor pivot (spins around its local Y axis) ----------
HUB_POS = Vector((0.0, -1.4, 12.0))

bpy.ops.object.empty_add(type='PLAIN_AXES', location=HUB_POS)
rotor = bpy.context.active_object
rotor.name = "RotorPivot"
rotor.empty_display_size = 0.5

# ---------- Hub ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=24, ring_count=16,
                                     location=HUB_POS)
hub = bpy.context.active_object
hub.name = "Hub"
assign(hub, mat_hub)
hub.parent = rotor

# ---------- Blades (3, evenly spaced at 120 degrees) ----------
BLADE_RADIAL_CENTER = 3.1   # distance of blade center from hub
BLADE_HALF_LENGTH = 2.5

for i in range(3):
    a = 2.0 * math.pi * i / 3.0
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    blade = bpy.context.active_object
    blade.name = f"Blade_{i}"
    blade.scale = (0.30, 0.04, BLADE_HALF_LENGTH)
    # Position outward from hub in the XZ plane, oriented radially
    blade.location = (BLADE_RADIAL_CENTER * math.sin(a),
                      0.0,
                      BLADE_RADIAL_CENTER * math.cos(a))
    blade.rotation_euler = (0.0, a, 0.0)
    assign(blade, mat_blade)
    blade.parent = rotor

# ---------- Constant-speed spin animation ----------
# Two full revolutions over 120 frames, linear interpolation.
rotor.rotation_mode = 'XYZ'
rotor.rotation_euler = (0.0, 0.0, 0.0)
rotor.keyframe_insert(data_path="rotation_euler", index=1, frame=1)

rotor.rotation_euler = (0.0, 4.0 * math.pi, 0.0)
rotor.keyframe_insert(data_path="rotation_euler", index=1, frame=120)

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0.0, math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(-12, -10, 10))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 600
fill.data.size = 10
fill.rotation_euler = (math.radians(60), 0.0, math.radians(-60))

# ---------- World background ----------
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.55, 0.72, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (16.0, -26.0, 9.0)

target = Vector((0.0, 0.0, 8.5))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
