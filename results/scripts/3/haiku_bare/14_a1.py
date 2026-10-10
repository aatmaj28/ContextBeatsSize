import bpy
import bmesh
import math
import random
from mathutils import Vector

random.seed(7)
scene = bpy.context.scene


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def make_principled_material(name, base_color, roughness, metallic=0.0, specular=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat


def build_sand_mesh(name, size, segments):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=segments, y_segments=segments, size=size)
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        # Gentle slope rising inland from the waterline (y = 0), plus dune undulation
        inland = max(-1.0, y) * 0.0
        slope = 0.10 * y
        dunes = (0.35 * math.sin(x * 0.18) * math.sin(y * 0.12)
                 + 0.12 * math.sin(x * 0.55 + 1.3) * math.cos(y * 0.41))
        ripple = random.uniform(-0.01, 0.01)
        v.co.z = slope + dunes * max(0.0, min(1.0, (y + 4.0) / 10.0)) + ripple + inland
    bm.to_mesh(me)
    bm.free()
    me.update()
    return me


# ---------- Sand ground ----------
sand_mesh = build_sand_mesh("SandGround", 60.0, 120)
sand_obj = bpy.data.objects.new("SandGround", sand_mesh)
bpy.context.collection.objects.link(sand_obj)
sand_mat = make_principled_material("SandMat", (0.86, 0.73, 0.52), roughness=0.85, specular=0.35)
sand_obj.data.materials.append(sand_mat)
for p in sand_obj.data.polygons:
    p.use_smooth = True

# ---------- Ocean plane ----------
bpy.ops.mesh.primitive_plane_add(size=400, location=(0.0, -60.0, 0.0))
ocean = bpy.context.active_object
ocean.name = "Ocean"
ocean_mat = make_principled_material("OceanMat", (0.02, 0.18, 0.38), roughness=0.04, metallic=0.0, specular=0.9)
ocean.data.materials.append(ocean_mat)

# ---------- Sun disc (emissive) low on the horizon ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=7.0, location=(0.0, -150.0, 18.0), segments=48, ring_count=24)
sun_disc = bpy.context.active_object
sun_disc.name = "SunDisc"
sun_mat = bpy.data.materials.new("SunMat")
sun_mat.use_nodes = True
sn = sun_mat.node_tree.nodes
sl = sun_mat.node_tree.links
sn.clear()
emit = sn.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (1.0, 0.62, 0.25, 1.0)
emit.inputs["Strength"].default_value = 40.0
out_s = sn.new("ShaderNodeOutputMaterial")
sl.new(emit.outputs["Emission"], out_s.inputs["Surface"])
sun_disc.data.materials.append(sun_mat)

# ---------- Sky gradient via world nodes ----------
world = bpy.data.worlds.new("SunsetWorld")
scene.world = world
world.use_nodes = True
wnt = world.node_tree
wn = wnt.nodes
wl = wnt.links
wn.clear()

tex_coord = wn.new("ShaderNodeTexCoord")
sep = wn.new("ShaderNodeSeparateXYZ")
map_rng = wn.new("ShaderNodeMapRange")
map_rng.inputs["From Min"].default_value = -0.03
map_rng.inputs["From Max"].default_value = 0.45
map_rng.inputs["To Min"].default_value = 0.0
map_rng.inputs["To Max"].default_value = 1.0
ramp = wn.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
cr.elements[0].position = 0.0
cr.elements[0].color = (0.10, 0.04, 0.22, 1.0)
cr.elements[1].position = 1.0
cr.elements[1].color = (1.00, 0.72, 0.35, 1.0)
for pos, col in [
    (0.30, (0.42, 0.14, 0.45, 1.0)),   # purple
    (0.52, (0.92, 0.36, 0.30, 1.0)),   # magenta-orange
    (0.72, (1.00, 0.52, 0.22, 1.0)),   # orange
]:
    el = cr.elements.new(pos)
    el.color = col
bg = wn.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.0
w_out = wn.new("ShaderNodeOutputWorld")

wl.new(tex_coord.outputs["Position"], sep.inputs["Vector"])
wl.new(sep.outputs["Z"], map_rng.inputs["Value"])
wl.new(map_rng.outputs["Result"], ramp.inputs["Fac"])
wl.new(ramp.outputs["Color"], bg.inputs["Color"])
wl.new(bg.outputs["Background"], w_out.inputs["Surface"])

# ---------- Lighting ----------
sun_data = bpy.data.lights.new(name="LowSun", type='SUN')
sun_data.energy = 4.0
sun_data.color = (1.0, 0.62, 0.35)
sun_data.angle = math.radians(1.5)
sun_obj = bpy.data.objects.new("LowSun", sun_data)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(78.0), 0.0, math.radians(15.0))

rim_data = bpy.data.lights.new(name="RimFill", type='AREA')
rim_data.energy = 300.0
rim_data.color = (0.6, 0.5, 1.0)
rim_data.size = 20.0
rim_obj = bpy.data.objects.new("RimFill", rim_data)
bpy.context.collection.objects.link(rim_obj)
rim_obj.location = (-20.0, 10.0, 15.0)
rim_obj.rotation_euler = (math.radians(60.0), 0.0, math.radians(-30.0))

# ---------- Scattered beach props: driftwood and pebbles ----------
def add_pebble(x, y):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=random.uniform(0.15, 0.35),
                                          location=(x, y, 0.1))
    pb = bpy.context.active_object
    pb.scale = (1.0, random.uniform(0.7, 1.0), random.uniform(0.4, 0.6))
    pb.data.materials.append(make_principled_material(
        f"Pebble_{x:.1f}_{y:.1f}",
        (random.uniform(0.35, 0.5), random.uniform(0.3, 0.4), random.uniform(0.28, 0.36)),
        roughness=0.6))
    return pb

for _ in range(18):
    add_pebble(random.uniform(-4.0, 4.0), random.uniform(0.5, 6.0))

bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=4.5, location=(-1.5, 2.2, 0.25))
log = bpy.context.active_object
log.rotation_euler = (math.radians(90), 0.0, math.radians(35))
log.data.materials.append(make_principled_material("DriftwoodMat", (0.42, 0.33, 0.26), roughness=0.9))

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("BeachCam")
cam_data.lens = 35.0
cam_data.clip_end = 1000.0
cam_obj = bpy.data.objects.new("BeachCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_loc = Vector((0.0, 12.0, 3.2))
target = Vector((0.0, -10.0, 1.2))
cam_obj.location = cam_loc
direction = (target - cam_loc).normalized()
cam_obj.rotation_mode = 'QUATERNION'
cam_obj.rotation_quaternion = direction.to_track_quat('-Z', 'Y')
scene.camera = cam_obj

# ---------- Scene settings ----------
scene.frame_start = 1
scene.frame_end = 1
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
