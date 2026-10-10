import bpy
import math
from mathutils import Vector

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

scene = bpy.context.scene

# ---------- Render settings ----------
scene.render.engine = 'CYCLES'
try:
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
except Exception:
    pass
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

# ---------- World with Sky Texture ----------
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
world.use_nodes = True  # no effect in 5.x, nodes always exist
wtree = world.node_tree
wnodes = wtree.nodes
wlinks = wtree.links

bg = None
for n in wnodes:
    if n.type == 'BACKGROUND':
        bg = n
        break
if bg is None:
    bg = wnodes.new("ShaderNodeBackground")

sky = wnodes.new("ShaderNodeTexSky")
sky.location = (-400, 0)
try:
    sky.sky_type = 'NISHITA'
    sky.sun_elevation = math.radians(35)
    sky.sun_rotation = math.radians(120)
    sky.sun_intensity = 1.0
    sky.altitude = 100.0
    sky.air_density = 1.0
    sky.dust_density = 1.0
except Exception:
    pass

bg.inputs["Strength"].default_value = 1.0
wlinks.new(sky.outputs["Color"], bg.inputs["Color"])

# ---------- Helper: material output ----------
def get_output(tree):
    for n in tree.nodes:
        if n.type == 'OUTPUT_MATERIAL':
            return n
    return tree.nodes.new("ShaderNodeOutputMaterial")

# ---------- Checkered floor material ----------
floor_mat = bpy.data.materials.new("CheckerFloor")
ft = floor_mat.node_tree
fn = ft.nodes
fl = ft.links
fn.clear()
f_out = fn.new("ShaderNodeOutputMaterial")
f_out.location = (400, 0)
f_bsdf = fn.new("ShaderNodeBsdfPrincipled")
f_bsdf.location = (100, 0)
f_checker = fn.new("ShaderNodeTexChecker")
f_checker.location = (-300, 0)
f_checker.inputs["Color1"].default_value = (0.8, 0.8, 0.8, 1.0)
f_checker.inputs["Color2"].default_value = (0.05, 0.05, 0.05, 1.0)
f_checker.inputs["Scale"].default_value = 20.0
f_bsdf.inputs["Roughness"].default_value = 0.35
fl.new(f_checker.outputs["Color"], f_bsdf.inputs["Base Color"])
fl.new(f_bsdf.outputs["BSDF"], f_out.inputs["Surface"])

# ---------- Gold material ----------
gold_mat = bpy.data.materials.new("Gold")
gt = gold_mat.node_tree
gn = gt.nodes
gl = gt.links
gn.clear()
g_out = gn.new("ShaderNodeOutputMaterial")
g_out.location = (400, 0)
g_bsdf = gn.new("ShaderNodeBsdfPrincipled")
g_bsdf.location = (100, 0)
g_bsdf.inputs["Base Color"].default_value = (1.0, 0.766, 0.336, 1.0)
g_bsdf.inputs["Metallic"].default_value = 1.0
g_bsdf.inputs["Roughness"].default_value = 0.18
gl.new(g_bsdf.outputs["BSDF"], g_out.inputs["Surface"])

# ---------- Glass material ----------
glass_mat = bpy.data.materials.new("Glass")
lt = glass_mat.node_tree
ln = lt.nodes
ll = lt.links
ln.clear()
l_out = ln.new("ShaderNodeOutputMaterial")
l_out.location = (400, 0)
l_glass = ln.new("ShaderNodeBsdfGlass")
l_glass.location = (100, 0)
l_glass.inputs["Color"].default_value = (0.85, 0.95, 1.0, 1.0)
l_glass.inputs["Roughness"].default_value = 0.02
l_glass.inputs["IOR"].default_value = 1.45
ll.new(l_glass.outputs["BSDF"], l_out.inputs["Surface"])

# ---------- Floor ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)

# ---------- Spheres ----------
def make_sphere(name, loc, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=64, ring_count=32, radius=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    return obj

glass_ball = make_sphere("GlassSphere", (-1.7, 0.0, 1.0), glass_mat)
gold_ball = make_sphere("GoldSphere", (1.7, 0.0, 1.0), gold_mat)

# ---------- Lighting ----------
bpy.ops.object.light_add(type='SUN', location=(4, -4, 8))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 3.0
sun.data.angle = math.radians(3)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(120))

# ---------- Camera ----------
bpy.ops.object.camera_add(location=(0.0, -11.0, 4.0))
cam = bpy.context.active_object
cam.name = "Camera"
cam.data.lens = 50

target = Vector((0.0, 0.0, 0.9))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam
