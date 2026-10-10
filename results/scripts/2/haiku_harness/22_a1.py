import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Clean slate ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------- Helpers ----------
def make_material(name, rgba, roughness=0.5, metallic=0.0):
    m = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return m

def assign(obj, mat):
    obj.data.materials.append(mat)

def link(obj):
    scene.collection.objects.link(obj)
    return obj

# ---------- Materials ----------
mat_ground = make_material("Grass", (0.22, 0.42, 0.18, 1.0), roughness=0.9)
mat_tower = make_material("Tower", (0.86, 0.86, 0.84, 1.0), roughness=0.45)
mat_nacelle = make_material("Nacelle", (0.55, 0.57, 0.60, 1.0), roughness=0.35, metallic=0.6)
mat_hub = make_material("Hub", (0.75, 0.12, 0.10, 1.0), roughness=0.3, metallic=0.2)
mat_blade = make_material("Blade", (0.94, 0.94, 0.96, 1.0), roughness=0.4)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
ground = bpy.context.active_object
assign(ground, mat_ground)

# ---------- Tower ----------
bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=1.1, radius2=0.5,
                                depth=20.0, location=(0, 0, 10.0))
tower = bpy.context.active_object
assign(tower, mat_tower)

# ---------- Nacelle ----------
TOP_Z = 20.6
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -1.2, TOP_Z))
nacelle = bpy.context.active_object
nacelle.scale = (1.1, 3.2, 1.1)
assign(nacelle, mat_nacelle)

# ---------- Rotor pivot (hub position, spins about Y) ----------
HUB_POS = Vector((0.0, -2.9, TOP_Z))
bpy.ops.object.empty_add(type='PLAIN_AXES', location=HUB_POS)
rotor = bpy.context.active_object
rotor.name = "Rotor"
rotor.empty_display_size = 0.5

# Hub sphere (child of rotor, local origin)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, segments=24, ring_count=12, location=(0, 0, 0))
hub = bpy.context.active_object
hub.name = "Hub"
assign(hub, mat_hub)
hub.parent = rotor
hub.location = (0, 0, 0)

# Hub nose cone pointing toward -Y
bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.6, radius2=0.12,
                                depth=0.9, location=(0, 0, 0))
nose = bpy.context.active_object
nose.name = "HubNose"
nose.rotation_euler = (math.radians(90), 0, 0)
assign(nose, mat_hub)
nose.parent = rotor
nose.location = (0, -0.55, 0)

# ---------- Blades (children of rotor) ----------
BLADE_LEN = 6.5
BLADE_ROOT = 0.5
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    blade = bpy.context.active_object
    blade.name = f"Blade_{i}"
    blade.scale = (0.35, 0.06, BLADE_LEN / 2.0)
    assign(blade, mat_blade)
    blade.parent = rotor
    blade.location = (0, 0, BLADE_ROOT + BLADE_LEN / 2.0)
    blade.rotation_euler = (0, i * 2.0 * math.pi / 3.0, 0)

# ---------- Constant-speed animation ----------
# Linear interpolation gives a constant angular velocity.
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

scene.frame_start = 1
scene.frame_end = 120
scene.frame_current = 1

rotor.rotation_mode = 'XYZ'
rotor.rotation_euler = (0.0, 0.0, 0.0)
rotor.keyframe_insert(data_path="rotation_euler", index=1, frame=1)

# Two full revolutions across 120 frames (constant speed)
rotor.rotation_euler = (0.0, 4.0 * math.pi, 0.0)
rotor.keyframe_insert(data_path="rotation_euler", index=1, frame=120)

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.5
sun_data.angle = math.radians(3.0)
sun = link(bpy.data.objects.new("Sun", sun_data))
sun.location = (10, -15, 30)
sun.rotation_euler = (math.radians(50), 0, math.radians(35))

fill_data = bpy.data.lights.new(name="Fill", type='AREA')
fill_data.energy = 1500.0
fill_data.size = 12.0
fill = link(bpy.data.objects.new("Fill", fill_data))
fill.location = (-14, -20, 22)
fill.rotation_euler = (math.radians(60), 0, math.radians(-40))

# ---------- World ----------
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.70, 0.92, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = link(bpy.data.objects.new("Camera", cam_data))
cam_loc = Vector((24.0, -40.0, 15.0))
target = Vector((0.0, -1.0, 13.5))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
