import bpy
import math

scene = bpy.context.scene

# Clear the scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

def make_mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return m

stone = make_mat("Stone", (0.75, 0.73, 0.68), 0.7)
bronze = make_mat("Bronze", (0.55, 0.35, 0.18), 0.35, 1.0)
ground_mat = make_mat("Ground", (0.25, 0.28, 0.25), 0.9)

def add(obj, mat):
    obj.data.materials.append(mat)
    return obj

# Ground
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
add(bpy.context.object, ground_mat)

# Pedestal
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.6))
p = bpy.context.object
p.scale = (1.4, 1.4, 1.2)
add(p, stone)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.3))
p = bpy.context.object
p.scale = (1.6, 1.6, 0.2)
add(p, stone)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.1))
p = bpy.context.object
p.scale = (1.7, 1.7, 0.2)
add(p, stone)

# Statue figure
base_z = 1.4
# legs
for x in (-0.18, 0.18):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=1.0, location=(x, 0, base_z + 0.5))
    add(bpy.context.object, bronze)
# torso
bpy.ops.mesh.primitive_cylinder_add(radius=0.32, depth=0.9, location=(0, 0, base_z + 1.4))
t = bpy.context.object
t.scale = (1, 0.65, 1)
add(t, bronze)
# arms
bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.85, location=(-0.45, 0, base_z + 1.35), rotation=(0, math.radians(-15), 0))
add(bpy.context.object, bronze)
bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.85, location=(0.55, 0, base_z + 1.95), rotation=(0, math.radians(30), 0))
add(bpy.context.object, bronze)
# raised torch / orb
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0.78, 0, 2.35 + base_z * 0 + 1.0))
add(bpy.context.object, bronze)
# head
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, base_z + 2.1))
bpy.ops.object.shade_smooth()
add(bpy.context.object, bronze)

# Target for the camera
bpy.ops.object.empty_add(location=(0, 0, 2.6))
target = bpy.context.object
target.name = "StatueTarget"

# Orbit pivot with camera parented
bpy.ops.object.empty_add(location=(0, 0, 0))
pivot = bpy.context.object
pivot.name = "OrbitPivot"

bpy.ops.object.camera_add(location=(8, 0, 4))
cam = bpy.context.object
cam.data.lens = 40
cam.parent = pivot
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

# Animate the orbit
scene.frame_start = 1
scene.frame_end = 100
pivot.rotation_euler = (0, 0, 0)
pivot.keyframe_insert("rotation_euler", index=2, frame=1)
pivot.rotation_euler = (0, 0, math.radians(360 * 100 / 101))
pivot.keyframe_insert("rotation_euler", index=2, frame=101)
try:
    for fc in pivot.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
except Exception:
    pass

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.object
sun.data.energy = 3
sun.rotation_euler = (math.radians(45), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-4, 4, 6))
a = bpy.context.object
a.data.energy = 500
a.data.size = 4
a.rotation_euler = (math.radians(-45), 0, math.radians(-135))

# World
world = bpy.data.worlds.new("World") if not scene.world else scene.world
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.5, 0.6, 0.75, 1)
    bg.inputs["Strength"].default_value = 0.6

scene.frame_set(1)
