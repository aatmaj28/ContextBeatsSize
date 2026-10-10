import bpy, math

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

scene.render.engine = 'CYCLES'
try:
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
except Exception:
    pass

# World with Sky Texture
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
nt = world.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
sky = nt.nodes.new("ShaderNodeTexSky")
for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING'):
    try:
        sky.sky_type = t
        break
    except Exception:
        pass
for attr, val in (("sun_elevation", math.radians(25)),
                  ("sun_rotation", math.radians(60)),
                  ("sun_size", math.radians(1.5)),
                  ("air_density", 1.0)):
    try:
        setattr(sky, attr, val)
    except Exception:
        pass
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 0.35
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

def principled(mat):
    return mat.node_tree.nodes.get("Principled BSDF")

# Floor
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
floor = bpy.context.active_object
fm = bpy.data.materials.new("Checker")
p = principled(fm)
chk = fm.node_tree.nodes.new("ShaderNodeTexChecker")
chk.inputs["Scale"].default_value = 40.0
chk.inputs["Color1"].default_value = (0.9, 0.9, 0.9, 1)
chk.inputs["Color2"].default_value = (0.05, 0.05, 0.05, 1)
fm.node_tree.links.new(chk.outputs["Color"], p.inputs["Base Color"])
p.inputs["Roughness"].default_value = 0.35
floor.data.materials.append(fm)

# Glass sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32, location=(-1.2, 0, 1))
glass = bpy.context.active_object
bpy.ops.object.shade_smooth()
gm = bpy.data.materials.new("Glass")
p = principled(gm)
p.inputs["Base Color"].default_value = (1, 1, 1, 1)
p.inputs["Roughness"].default_value = 0.0
p.inputs["IOR"].default_value = 1.45
p.inputs["Transmission Weight"].default_value = 1.0
glass.data.materials.append(gm)

# Gold sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32, location=(1.2, 0.3, 1))
gold = bpy.context.active_object
bpy.ops.object.shade_smooth()
gdm = bpy.data.materials.new("Gold")
p = principled(gdm)
p.inputs["Base Color"].default_value = (1.0, 0.71, 0.29, 1)
p.inputs["Metallic"].default_value = 1.0
p.inputs["Roughness"].default_value = 0.15
gold.data.materials.append(gdm)

# Camera
target = bpy.data.objects.new("Target", None)
target.location = (0, 0.1, 0.8)
scene.collection.objects.link(target)
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0, -8, 3)
scene.collection.objects.link(cam)
c = cam.constraints.new('TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
scene.camera = cam

scene.render.resolution_x = 1600
scene.render.resolution_y = 900
