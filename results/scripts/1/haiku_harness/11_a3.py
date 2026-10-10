import bpy
import math
from mathutils import Vector

# ---------- Clean the default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)

scene = bpy.context.scene

# ---------- Render engine ----------
scene.render.engine = 'CYCLES'
try:
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 12
    scene.cycles.transmission_bounces = 12
except Exception:
    pass


# ---------- Helper: set a Sky Texture option whether it is a property or an input socket ----------
def set_sky_option(node, attr_name, socket_names, value):
    # Try as a node property first (older API)
    if hasattr(node, attr_name):
        try:
            setattr(node, attr_name, value)
            return True
        except Exception:
            pass
    # Fall back to an input socket (newer API)
    for sname in socket_names:
        if sname in node.inputs:
            try:
                node.inputs[sname].default_value = value
                return True
            except Exception:
                pass
    return False


# ---------- World: Sky Texture background and lighting ----------
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links

bg = wnodes.get("Background")
world_out = wnodes.get("World Output")
if bg is None:
    bg = wnodes.new("ShaderNodeBackground")
if world_out is None:
    world_out = wnodes.new("ShaderNodeOutputWorld")

sky = wnodes.new("ShaderNodeTexSky")

# Sky type enum names changed in Blender 5.x; pick whichever is valid.
try:
    sky_type_prop = sky.bl_rna.properties.get("sky_type")
    if sky_type_prop is not None:
        sky_type_items = [item.identifier for item in sky_type_prop.enum_items]
        if "MULTIPLE_SCATTERING" in sky_type_items:
            sky.sky_type = 'MULTIPLE_SCATTERING'
        elif "SINGLE_SCATTERING" in sky_type_items:
            sky.sky_type = 'SINGLE_SCATTERING'
except Exception:
    pass

set_sky_option(sky, "sun_elevation", ["Sun Elevation"], math.radians(28.0))
set_sky_option(sky, "sun_rotation", ["Sun Rotation"], math.radians(35.0))
set_sky_option(sky, "altitude", ["Altitude"], 0.0)
set_sky_option(sky, "air_density", ["Air", "Air Density"], 1.0)
set_sky_option(sky, "dust_density", ["Dust", "Dust Density"], 1.0)
set_sky_option(sky, "ozone_density", ["Ozone", "Ozone Density"], 1.0)

wlinks.new(sky.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0
if not world_out.inputs["Surface"].is_linked:
    wlinks.new(bg.outputs["Background"], world_out.inputs["Surface"])


# ---------- Materials ----------
def make_principled_material(name):
    mat = bpy.data.materials.new(name)
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    return mat, bsdf

# Checkered floor
floor_mat, floor_bsdf = make_principled_material("CheckerFloor")
fnodes = floor_mat.node_tree.nodes
flinks = floor_mat.node_tree.links
checker = fnodes.new("ShaderNodeTexChecker")
checker.inputs["Scale"].default_value = 10.0
checker.inputs["Color1"].default_value = (0.80, 0.80, 0.78, 1.0)
checker.inputs["Color2"].default_value = (0.05, 0.05, 0.06, 1.0)
flinks.new(checker.outputs["Color"], floor_bsdf.inputs["Base Color"])
floor_bsdf.inputs["Roughness"].default_value = 0.35

# Glass sphere
glass_mat, glass_bsdf = make_principled_material("Glass")
glass_bsdf.inputs["Base Color"].default_value = (0.9, 0.97, 1.0, 1.0)
glass_bsdf.inputs["Metallic"].default_value = 0.0
glass_bsdf.inputs["Roughness"].default_value = 0.02
glass_bsdf.inputs["IOR"].default_value = 1.45
glass_bsdf.inputs["Transmission Weight"].default_value = 1.0

# Gold sphere
gold_mat, gold_bsdf = make_principled_material("Gold")
gold_bsdf.inputs["Base Color"].default_value = (1.0, 0.766, 0.336, 1.0)
gold_bsdf.inputs["Metallic"].default_value = 1.0
gold_bsdf.inputs["Roughness"].default_value = 0.22


# ---------- Geometry ----------
def assign_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# Floor
bpy.ops.mesh.primitive_plane_add(size=30.0, location=(0.0, 0.0, 0.0))
floor = bpy.context.active_object
floor.name = "Floor"
assign_material(floor, floor_mat)

# Glass sphere (left)
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48,
                                     radius=0.9, location=(-1.25, 0.0, 0.9))
glass_sphere = bpy.context.active_object
glass_sphere.name = "GlassSphere"
bpy.ops.object.shade_smooth()
assign_material(glass_sphere, glass_mat)

# Gold sphere (right)
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48,
                                     radius=0.9, location=(1.25, 0.4, 0.9))
gold_sphere = bpy.context.active_object
gold_sphere.name = "GoldSphere"
bpy.ops.object.shade_smooth()
assign_material(gold_sphere, gold_mat)


# ---------- Extra lighting ----------
# A sun lamp adds crisp shadows on top of the sky's illumination
bpy.ops.object.light_add(type='SUN', location=(0.0, 0.0, 10.0))
sun = bpy.context.active_object
sun.name = "KeySun"
sun.data.energy = 3.5
sun.data.angle = math.radians(2.0)
sun.rotation_euler = (math.radians(50.0), 0.0, math.radians(35.0))


# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 55.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)

cam_loc = Vector((0.0, -7.5, 3.2))
target = Vector((0.0, 0.0, 0.8))
cam.location = cam_loc
direction = target - cam_loc
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = direction.to_track_quat('-Z', 'Y')

scene.camera = cam

# ---------- Animation range (static still) ----------
scene.frame_start = 1
scene.frame_end = 1

# ---------- Output resolution ----------
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
