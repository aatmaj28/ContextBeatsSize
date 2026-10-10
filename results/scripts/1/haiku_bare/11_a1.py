import bpy
import math
from mathutils import Vector

# Clear any existing scene content
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128

def set_input(node, names, value):
    """Set the first matching input socket name (handles Blender version differences)."""
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return True
    return False

def smooth_object(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True

# ---------- World with Sky Texture ----------
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
world.use_nodes = True
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links
wnodes.clear()

sky = wnodes.new("ShaderNodeTexSky")
try:
    sky.sky_type = 'NISHITA'
except Exception:
    pass
sky.sun_elevation = math.radians(35)
sky.sun_rotation = math.radians(120)
sky.sun_intensity = 1.0
sky.altitude = 0.0

bg = wnodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.0
world_out = wnodes.new("ShaderNodeOutputWorld")

wlinks.new(sky.outputs["Color"], bg.inputs["Color"])
wlinks.new(bg.outputs["Background"], world_out.inputs["Surface"])

# ---------- Checkered Floor ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"

floor_mat = bpy.data.materials.new("CheckerFloor")
floor_mat.use_nodes = True
fnodes = floor_mat.node_tree.nodes
flinks = floor_mat.node_tree.links
fnodes.clear()

f_out = fnodes.new("ShaderNodeOutputMaterial")
f_bsdf = fnodes.new("ShaderNodeBsdfPrincipled")
f_checker = fnodes.new("ShaderNodeTexChecker")
f_checker.inputs["Color1"].default_value = (0.9, 0.9, 0.9, 1.0)
f_checker.inputs["Color2"].default_value = (0.05, 0.05, 0.05, 1.0)
f_checker.inputs["Scale"].default_value = 15.0
set_input(f_bsdf, ["Roughness"], 0.35)

flinks.new(f_checker.outputs["Color"], f_bsdf.inputs["Base Color"])
flinks.new(f_bsdf.outputs["BSDF"], f_out.inputs["Surface"])
floor.data.materials.append(floor_mat)

# ---------- Glass Sphere ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=96, ring_count=48,
                                     location=(-1.3, 0, 1.0))
glass = bpy.context.active_object
glass.name = "GlassSphere"
smooth_object(glass)

glass_mat = bpy.data.materials.new("Glass")
glass_mat.use_nodes = True
gnodes = glass_mat.node_tree.nodes
glinks = glass_mat.node_tree.links
gnodes.clear()

g_out = gnodes.new("ShaderNodeOutputMaterial")
g_bsdf = gnodes.new("ShaderNodeBsdfPrincipled")
g_bsdf.inputs["Base Color"].default_value = (0.95, 0.98, 1.0, 1.0)
set_input(g_bsdf, ["Roughness"], 0.02)
set_input(g_bsdf, ["IOR"], 1.5)
set_input(g_bsdf, ["Transmission Weight", "Transmission"], 1.0)
glinks.new(g_bsdf.outputs["BSDF"], g_out.inputs["Surface"])
glass.data.materials.append(glass_mat)

# ---------- Gold Sphere ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=96, ring_count=48,
                                     location=(1.3, 0, 1.0))
gold = bpy.context.active_object
gold.name = "GoldSphere"
smooth_object(gold)

gold_mat = bpy.data.materials.new("Gold")
gold_mat.use_nodes = True
gonodes = gold_mat.node_tree.nodes
golinks = gold_mat.node_tree.links
gonodes.clear()

go_out = gonodes.new("ShaderNodeOutputMaterial")
go_bsdf = gonodes.new("ShaderNodeBsdfPrincipled")
go_bsdf.inputs["Base Color"].default_value = (1.0, 0.766, 0.336, 1.0)
set_input(go_bsdf, ["Metallic"], 1.0)
set_input(go_bsdf, ["Roughness"], 0.2)
golinks.new(go_bsdf.outputs["BSDF"], go_out.inputs["Surface"])
gold.data.materials.append(gold_mat)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((0.0, -10.0, 4.0))

target = Vector((0.0, 0.0, 0.9))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Render settings (no render is triggered) ----------
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
