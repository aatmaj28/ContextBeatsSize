import bpy
import math

scene = bpy.context.scene

# Clear existing objects
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 96

# Floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor_mat = bpy.data.materials.new("FloorMat")
floor_mat.use_nodes = True
bsdf = floor_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.4, 0.4, 0.42, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(floor_mat)

# Some subject objects
def make_mat(name, color, rough=0.4, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = color
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
    return m

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(-1.6, 0.5, 0.8), segments=48, ring_count=24)
s = bpy.context.active_object
bpy.ops.object.shade_smooth()
s.data.materials.append(make_mat("Red", (0.8, 0.1, 0.08, 1), 0.3))

bpy.ops.mesh.primitive_cube_add(size=1.2, location=(1.6, 0.6, 0.6), rotation=(0, 0, math.radians(30)))
c = bpy.context.active_object
c.data.materials.append(make_mat("Blue", (0.1, 0.25, 0.8, 1), 0.5))

bpy.ops.mesh.primitive_torus_add(location=(0, -1.6, 0.25), major_radius=0.7, minor_radius=0.25)
t = bpy.context.active_object
bpy.ops.object.shade_smooth()
t.data.materials.append(make_mat("Gold", (1.0, 0.75, 0.3, 1), 0.25, 1.0))

# Small emissive bulb mesh at the light position
light_loc = (0, 0, 2.5)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=light_loc)
bulb = bpy.context.active_object
bulb_mat = bpy.data.materials.new("BulbMat")
bulb_mat.use_nodes = True
bb = bulb_mat.node_tree.nodes.get("Principled BSDF")
if bb:
    bb.inputs["Base Color"].default_value = (1, 0.85, 0.6, 1)
    bb.inputs["Emission Color"].default_value = (1, 0.85, 0.6, 1)
    bb.inputs["Emission Strength"].default_value = 1.0
bulb.data.materials.append(bulb_mat)
bulb.visible_shadow = False

# Point light
light_data = bpy.data.lights.new("PulseLight", type='POINT')
light_data.color = (1.0, 0.85, 0.6)
light_data.shadow_soft_size = 0.15
light_obj = bpy.data.objects.new("PulseLight", light_data)
light_obj.location = light_loc
scene.collection.objects.link(light_obj)

dim, bright = 50.0, 1500.0
period = 48
for f in range(1, 97, period // 2):
    phase = ((f - 1) % period) / period
    val = dim if phase < 0.5 else bright
    light_data.energy = val
    light_data.keyframe_insert("energy", frame=f)
    if bb:
        bb.inputs["Emission Strength"].default_value = val / 100.0
        bb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
# final frame closes loop
light_data.energy = dim
light_data.keyframe_insert("energy", frame=97)
if bb:
    bb.inputs["Emission Strength"].default_value = dim / 100.0
    bb.inputs["Emission Strength"].keyframe_insert("default_value", frame=97)

# Weak fill light so dim phase isn't pitch black
fill = bpy.data.lights.new("Fill", type='SUN')
fill.energy = 0.3
fill_obj = bpy.data.objects.new("Fill", fill)
fill_obj.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(fill_obj)

# World
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.01, 0.015, 1)
    bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (6.5, -7.5, 4.5)
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 0.8)
scene.collection.objects.link(target)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam
