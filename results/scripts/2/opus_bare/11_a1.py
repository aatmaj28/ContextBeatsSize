import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Render engine
try:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
except Exception:
    pass

# ---------- Materials ----------
def make_principled(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    return mat, bsdf

def set_input(bsdf, names, value):
    for n in names:
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = value
            return

# Glass
glass_mat, gb = make_principled("Glass")
set_input(gb, ["Base Color"], (1.0, 1.0, 1.0, 1.0))
set_input(gb, ["Transmission Weight", "Transmission"], 1.0)
set_input(gb, ["Roughness"], 0.0)
set_input(gb, ["IOR"], 1.45)
set_input(gb, ["Metallic"], 0.0)

# Gold
gold_mat, au = make_principled("Gold")
set_input(au, ["Base Color"], (1.0, 0.766, 0.336, 1.0))
set_input(au, ["Metallic"], 1.0)
set_input(au, ["Roughness"], 0.18)

# Checker floor
floor_mat = bpy.data.materials.new("Checker")
floor_mat.use_nodes = True
nt = floor_mat.node_tree
fb = nt.nodes.get("Principled BSDF")
checker = nt.nodes.new("ShaderNodeTexChecker")
checker.inputs["Scale"].default_value = 12.0
checker.inputs["Color1"].default_value = (0.9, 0.9, 0.9, 1.0)
checker.inputs["Color2"].default_value = (0.05, 0.05, 0.05, 1.0)
checker.location = (-300, 200)
nt.links.new(checker.outputs["Color"], fb.inputs["Base Color"])
set_input(fb, ["Roughness"], 0.35)

# ---------- Geometry ----------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)

bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(-1.2, 0, 1.0))
glass = bpy.context.active_object
glass.name = "GlassSphere"
bpy.ops.object.shade_smooth()
glass.data.materials.append(glass_mat)

bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(1.2, 0.6, 1.0))
gold = bpy.context.active_object
gold.name = "GoldSphere"
bpy.ops.object.shade_smooth()
gold.data.materials.append(gold_mat)

# ---------- World with Sky Texture ----------
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
world.use_nodes = True
wnt = world.node_tree
bg = wnt.nodes.get("Background")
if bg is None:
    bg = wnt.nodes.new("ShaderNodeBackground")
out = wnt.nodes.get("World Output")
if out is None:
    out = wnt.nodes.new("ShaderNodeOutputWorld")
sky = wnt.nodes.new("ShaderNodeTexSky")
sky.location = (-300, 300)
for attr, val in (("sun_elevation", math.radians(25)),
                  ("sun_rotation", math.radians(135)),
                  ("altitude", 100.0),
                  ("air_density", 1.0),
                  ("dust_density", 1.0)):
    if hasattr(sky, attr):
        try:
            setattr(sky, attr, val)
        except Exception:
            pass
wnt.links.new(sky.outputs[0], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.3
wnt.links.new(bg.outputs[0], out.inputs["Surface"])

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(0, -7.5, 3.0))
cam = bpy.context.active_object
cam.data.lens = 45
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0.3, 0.9)
scene.collection.objects.link(target)
track = cam.constraints.new('TRACK_TO')
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'
scene.camera = cam

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
