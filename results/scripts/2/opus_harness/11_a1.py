import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Render settings
scene.render.engine = 'CYCLES'
try:
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
except Exception:
    pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"

floor_mat = bpy.data.materials.new("CheckerFloor")
nt = floor_mat.node_tree
nodes = nt.nodes
bsdf = nodes.get("Principled BSDF")
texcoord = nodes.new("ShaderNodeTexCoord")
texcoord.location = (-800, 0)
checker = nodes.new("ShaderNodeTexChecker")
checker.location = (-500, 0)
checker.inputs["Scale"].default_value = 20.0
checker.inputs["Color1"].default_value = (0.9, 0.9, 0.9, 1.0)
checker.inputs["Color2"].default_value = (0.05, 0.05, 0.05, 1.0)
nt.links.new(texcoord.outputs["UV"], checker.inputs["Vector"])
nt.links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.35
floor.data.materials.append(floor_mat)

# ---------- Glass sphere ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(-1.25, 0, 1.0), segments=64, ring_count=32)
glass = bpy.context.active_object
glass.name = "GlassSphere"
bpy.ops.object.shade_smooth()

glass_mat = bpy.data.materials.new("Glass")
gb = glass_mat.node_tree.nodes.get("Principled BSDF")
gb.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
gb.inputs["Roughness"].default_value = 0.0
gb.inputs["IOR"].default_value = 1.45
for name in ("Transmission Weight", "Transmission"):
    if name in gb.inputs:
        gb.inputs[name].default_value = 1.0
        break
glass.data.materials.append(glass_mat)

# ---------- Gold sphere ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(1.25, 0.3, 1.0), segments=64, ring_count=32)
gold = bpy.context.active_object
gold.name = "GoldSphere"
bpy.ops.object.shade_smooth()

gold_mat = bpy.data.materials.new("Gold")
au = gold_mat.node_tree.nodes.get("Principled BSDF")
au.inputs["Base Color"].default_value = (1.0, 0.766, 0.336, 1.0)
au.inputs["Metallic"].default_value = 1.0
au.inputs["Roughness"].default_value = 0.15
gold.data.materials.append(gold_mat)

# ---------- World with Sky Texture ----------
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
wnt = world.node_tree
bg = wnt.nodes.get("Background")
if bg is None:
    bg = wnt.nodes.new("ShaderNodeBackground")
out = wnt.nodes.get("World Output")
if out is None:
    out = wnt.nodes.new("ShaderNodeOutputWorld")
sky = wnt.nodes.new("ShaderNodeTexSky")
sky.location = (-300, 0)
for st in ('MULTIPLE_SCATTERING', 'SINGLE_SCATTERING', 'NISHITA', 'HOSEK_WILKIE'):
    try:
        sky.sky_type = st
        break
    except Exception:
        continue
for attr, val in (("sun_elevation", math.radians(25)),
                  ("sun_rotation", math.radians(135)),
                  ("sun_size", math.radians(1.5)),
                  ("altitude", 100.0)):
    try:
        setattr(sky, attr, val)
    except Exception:
        pass
wnt.links.new(sky.outputs["Color"], bg.inputs["Color"])
wnt.links.new(bg.outputs["Background"], out.inputs["Surface"])
bg.inputs["Strength"].default_value = 0.3

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.5, -8.5, 3.2)

target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
target.location = (0, 0.15, 0.9)
track = cam.constraints.new('TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

scene.camera = cam
scene.frame_start = 1
scene.frame_end = 1
