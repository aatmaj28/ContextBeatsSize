import bpy
import math

scene = bpy.context.scene

# Clear the scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 96

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("GroundMat")
gmat.use_nodes = True
bsdf = gmat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.35, 0.35, 0.38, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
ground.data.materials.append(gmat)

# Subject: a few objects for the light to illuminate
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

bpy.ops.mesh.primitive_cube_add(size=1.2, location=(1.6, 0.6, 0.6))
c = bpy.context.active_object
c.rotation_euler = (0, 0, math.radians(30))
c.data.materials.append(make_mat("Blue", (0.1, 0.25, 0.8, 1), 0.5))

bpy.ops.mesh.primitive_torus_add(location=(0, -1.4, 0.35), major_radius=0.7, minor_radius=0.25)
t = bpy.context.active_object
bpy.ops.object.shade_smooth()
t.data.materials.append(make_mat("Gold", (1.0, 0.75, 0.3, 1), 0.25, 1.0))

# Visible bulb at the light position
light_loc = (0, 0.3, 2.6)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=light_loc)
bulb = bpy.context.active_object
bmat = bpy.data.materials.new("BulbMat")
bmat.use_nodes = True
nt = bmat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
emit = nt.nodes.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (1.0, 0.85, 0.6, 1)
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
bulb.data.materials.append(bmat)

# Point light
ldata = bpy.data.lights.new("PulseLight", type='POINT')
ldata.color = (1.0, 0.85, 0.6)
ldata.shadow_soft_size = 0.15
light = bpy.data.objects.new("PulseLight", ldata)
light.location = light_loc
scene.collection.objects.link(light)

dim, bright = 50.0, 1500.0
emit_dim, emit_bright = 1.0, 30.0
for f in (1, 25, 49, 73, 97):
    is_bright = f in (25, 73)
    ldata.energy = bright if is_bright else dim
    ldata.keyframe_insert(data_path="energy", frame=f)
    emit.inputs["Strength"].default_value = emit_bright if is_bright else emit_dim
    emit.inputs["Strength"].keyframe_insert(data_path="default_value", frame=f)

# Smooth easing on keyframes
def smooth(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action:
        return
    try:
        curves = ad.action.fcurves
    except AttributeError:
        curves = []
        for layer in ad.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves.extend(bag.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'

try:
    smooth(ldata)
    smooth(bmat.node_tree)
except Exception:
    pass

# Faint world light
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
cam.location = (0, -8.5, 4.5)
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 0.9)
scene.collection.objects.link(target)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam
scene.frame_set(1)
