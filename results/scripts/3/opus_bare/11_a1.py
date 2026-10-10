import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clear scene
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

def set_input(node, names, value):
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor_mat = bpy.data.materials.new("CheckerFloor")
floor_mat.use_nodes = True
nt = floor_mat.node_tree
bsdf = nt.nodes.get("Principled BSDF")
checker = nt.nodes.new("ShaderNodeTexChecker")
checker.inputs["Scale"].default_value = 30.0
checker.inputs["Color1"].default_value = (0.9, 0.9, 0.9, 1)
checker.inputs["Color2"].default_value = (0.05, 0.05, 0.05, 1)
texcoord = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(texcoord.outputs["UV"], checker.inputs["Vector"])
nt.links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
set_input(bsdf, ["Roughness"], 0.35)
floor.data.materials.append(floor_mat)

# ---------- Spheres ----------
def make_sphere(name, loc):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=64, ring_count=32, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj

glass = make_sphere("GlassSphere", (-1.25, 0, 1.0))
gmat = bpy.data.materials.new("Glass")
gmat.use_nodes = True
gb = gmat.node_tree.nodes.get("Principled BSDF")
set_input(gb, ["Base Color"], (1, 1, 1, 1))
set_input(gb, ["Transmission Weight", "Transmission"], 1.0)
set_input(gb, ["Roughness"], 0.0)
set_input(gb, ["IOR"], 1.5)
glass.data.materials.append(gmat)

gold = make_sphere("GoldSphere", (1.25, 0.3, 1.0))
aumat = bpy.data.materials.new("Gold")
aumat.use_nodes = True
ab = aumat.node_tree.nodes.get("Principled BSDF")
set_input(ab, ["Base Color"], (1.0, 0.766, 0.336, 1))
set_input(ab, ["Metallic"], 1.0)
set_input(ab, ["Roughness"], 0.18)
gold.data.materials.append(aumat)

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
for attr, val in [("sun_elevation", math.radians(25)),
                  ("sun_rotation", math.radians(200)),
                  ("altitude", 100.0),
                  ("air_density", 1.0),
                  ("sun_disc", True),
                  ("sun_size", math.radians(1.5))]:
    if hasattr(sky, attr):
        try:
            setattr(sky, attr, val)
        except Exception:
            pass
wnt.links.new(sky.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.6
wnt.links.new(bg.outputs["Background"], out.inputs["Surface"])

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(0.5, -7.5, 2.6))
cam = bpy.context.active_object
cam.data.lens = 45
target = Vector((0, 0.1, 0.9))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

try:
    scene.view_settings.view_transform = 'AgX'
except Exception:
    pass
