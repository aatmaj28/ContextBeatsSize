import bpy
import math

scene = bpy.context.scene

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 96

# Floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
fmat = bpy.data.materials.new("FloorMat")
fmat.use_nodes = True
bsdf = fmat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.35, 0.35, 0.38, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
floor.data.materials.append(fmat)

# Subject objects
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(-1.5, 0, 0.8))
s = bpy.context.active_object
bpy.ops.object.shade_smooth()
smat = bpy.data.materials.new("SphereMat")
smat.use_nodes = True
b = smat.node_tree.nodes.get("Principled BSDF")
if b:
    b.inputs["Base Color"].default_value = (0.8, 0.2, 0.15, 1)
    b.inputs["Roughness"].default_value = 0.3
s.data.materials.append(smat)

bpy.ops.mesh.primitive_cube_add(size=1.2, location=(1.5, 0.3, 0.6))
c = bpy.context.active_object
c.rotation_euler = (0, 0, math.radians(30))
cmat = bpy.data.materials.new("CubeMat")
cmat.use_nodes = True
b = cmat.node_tree.nodes.get("Principled BSDF")
if b:
    b.inputs["Base Color"].default_value = (0.15, 0.4, 0.8, 1)
c.data.materials.append(cmat)

# Small emissive bulb marking light position
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, -0.5, 2.5))
bulb = bpy.context.active_object
bmat = bpy.data.materials.new("BulbMat")
bmat.use_nodes = True
nt = bmat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1.0, 0.85, 0.6, 1)
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
bulb.data.materials.append(bmat)
bulb.visible_shadow = False

# Pulsing point light
ldata = bpy.data.lights.new("PulseLight", type='POINT')
ldata.color = (1.0, 0.85, 0.6)
ldata.shadow_soft_size = 0.15
light = bpy.data.objects.new("PulseLight", ldata)
light.location = (0, -0.5, 2.5)
scene.collection.objects.link(light)

dim, bright = 50.0, 1500.0
em_dim, em_bright = 1.0, 30.0
for f in range(1, 98, 24):
    # frames 1,49,97 dim; 25,73 bright
    is_bright = ((f - 1) // 24) % 2 == 1
    ldata.energy = bright if is_bright else dim
    ldata.keyframe_insert("energy", frame=f)
    em.inputs["Strength"].default_value = em_bright if is_bright else em_dim
    em.inputs["Strength"].keyframe_insert("default_value", frame=f)

for idblock in (ldata, nt):
    ad = idblock.animation_data
    if ad and ad.action:
        try:
            curves = ad.action.fcurves
        except AttributeError:
            curves = []
            for layer in ad.action.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        curves.extend(cb.fcurves)
        for fc in curves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'SINE'
                kp.easing = 'EASE_IN_OUT'

# Weak fill so scene is never fully black
wdata = bpy.data.worlds.new("World") if not scene.world else scene.world
scene.world = wdata
wdata.use_nodes = True
bg = wdata.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.03, 1)
    bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -8, 4)
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 0.9)
scene.collection.objects.link(target)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam
