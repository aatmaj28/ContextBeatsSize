import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# Clear existing objects
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Render settings
try:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.cycles.max_bounces = 16
    scene.cycles.transmission_bounces = 16
except Exception:
    pass
scene.render.resolution_x = 1600
scene.render.resolution_y = 900

def set_input(node, names, value):
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return True
    return False

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "CheckerFloor"

floor_mat = bpy.data.materials.new("CheckerMat")
floor_mat.use_nodes = True
nt = floor_mat.node_tree
nodes, links = nt.nodes, nt.links
bsdf = nodes.get("Principled BSDF")
texcoord = nodes.new("ShaderNodeTexCoord")
texcoord.location = (-800, 0)
checker = nodes.new("ShaderNodeTexChecker")
checker.location = (-500, 0)
checker.inputs["Scale"].default_value = 20.0
checker.inputs["Color1"].default_value = (0.9, 0.9, 0.9, 1)
checker.inputs["Color2"].default_value = (0.05, 0.05, 0.05, 1)
links.new(texcoord.outputs["UV"], checker.inputs["Vector"])
links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
set_input(bsdf, ["Roughness"], 0.35)
floor.data.materials.append(floor_mat)

# ---------- Glass sphere ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0, location=(-1.2, 0, 1.0))
glass = bpy.context.active_object
glass.name = "GlassSphere"
bpy.ops.object.shade_smooth()

glass_mat = bpy.data.materials.new("GlassMat")
glass_mat.use_nodes = True
gb = glass_mat.node_tree.nodes.get("Principled BSDF")
gb.inputs["Base Color"].default_value = (1, 1, 1, 1)
set_input(gb, ["Transmission Weight", "Transmission"], 1.0)
set_input(gb, ["Roughness"], 0.0)
set_input(gb, ["IOR"], 1.45)
glass.data.materials.append(glass_mat)

# ---------- Gold sphere ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0, location=(1.2, 0.6, 1.0))
gold = bpy.context.active_object
gold.name = "GoldSphere"
bpy.ops.object.shade_smooth()

gold_mat = bpy.data.materials.new("GoldMat")
gold_mat.use_nodes = True
gd = gold_mat.node_tree.nodes.get("Principled BSDF")
gd.inputs["Base Color"].default_value = (1.0, 0.766, 0.336, 1)
set_input(gd, ["Metallic"], 1.0)
set_input(gd, ["Roughness"], 0.15)
gold.data.materials.append(gold_mat)

# ---------- World with Sky Texture ----------
world = bpy.data.worlds.new("SkyWorld") if scene.world is None else scene.world
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
for n in list(wn):
    wn.remove(n)
sky = wn.new("ShaderNodeTexSky")
sky.location = (-400, 0)
for t in ('MULTIPLE_SCATTERING', 'SINGLE_SCATTERING', 'NISHITA', 'HOSEK_WILKIE'):
    try:
        sky.sky_type = t
        break
    except Exception:
        continue
for attr, val in (("sun_elevation", math.radians(25)),
                  ("sun_rotation", math.radians(140)),
                  ("sun_disc", True),
                  ("sun_size", math.radians(0.8)),
                  ("altitude", 100.0),
                  ("sun_direction", (0.5, -0.6, 0.6))):
    if hasattr(sky, attr):
        try:
            setattr(sky, attr, val)
        except Exception:
            pass
bg = wn.new("ShaderNodeBackground")
bg.location = (-100, 0)
is_physical = getattr(sky, "sky_type", "") in ('MULTIPLE_SCATTERING', 'SINGLE_SCATTERING', 'NISHITA')
bg.inputs["Strength"].default_value = 0.3 if is_physical else 1.0
out = wn.new("ShaderNodeOutputWorld")
out.location = (150, 0)
wl.new(sky.outputs["Color"], bg.inputs["Color"])
wl.new(bg.outputs["Background"], out.inputs["Surface"])

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 45
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.5, -8.5, 3.2)
target = Vector((0.0, 0.3, 0.9))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
