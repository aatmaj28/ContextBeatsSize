import bpy, math

scene = bpy.context.scene
# Clear scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

scene.render.engine = 'CYCLES'
try:
    scene.cycles.samples = 128
except Exception:
    pass

# Floor
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
floor = bpy.context.active_object
fmat = bpy.data.materials.new("Checker")
nt = fmat.node_tree
bsdf = nt.nodes.get("Principled BSDF")
chk = nt.nodes.new("ShaderNodeTexChecker")
chk.inputs["Scale"].default_value = 40.0
chk.inputs["Color1"].default_value = (0.9, 0.9, 0.9, 1)
chk.inputs["Color2"].default_value = (0.05, 0.05, 0.05, 1)
nt.links.new(chk.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.35
floor.data.materials.append(fmat)

# Glass sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32, location=(-1.2, 0, 1))
glass = bpy.context.active_object
bpy.ops.object.shade_smooth()
gmat = bpy.data.materials.new("Glass")
b = gmat.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (1, 1, 1, 1)
b.inputs["Transmission Weight"].default_value = 1.0
b.inputs["Roughness"].default_value = 0.0
b.inputs["IOR"].default_value = 1.45
glass.data.materials.append(gmat)

# Gold sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32, location=(1.2, 0.3, 1))
gold = bpy.context.active_object
bpy.ops.object.shade_smooth()
aumat = bpy.data.materials.new("Gold")
b = aumat.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (1.0, 0.766, 0.336, 1)
b.inputs["Metallic"].default_value = 1.0
b.inputs["Roughness"].default_value = 0.15
gold.data.materials.append(aumat)

# World with Sky Texture
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
wnt = world.node_tree
bg = wnt.nodes.get("Background")
sky = wnt.nodes.new("ShaderNodeTexSky")
for t in ('MULTIPLE_SCATTERING', 'SINGLE_SCATTERING', 'NISHITA'):
    try:
        sky.sky_type = t
        break
    except Exception:
        pass
for attr, val in (("sun_elevation", math.radians(25)), ("sun_rotation", math.radians(140)),
                  ("altitude", 100.0), ("air_density", 1.0), ("dust_density", 1.0)):
    try:
        setattr(sky, attr, val)
    except Exception:
        pass
wnt.links.new(sky.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.4

# Camera
target = bpy.data.objects.new("Target", None)
target.location = (0, 0, 0.8)
scene.collection.objects.link(target)
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -8.5, 3.2)
scene.collection.objects.link(cam)
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
