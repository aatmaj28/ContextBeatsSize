import bpy
import bmesh
import math
import mathutils

# ---------- Clear the scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

scene = bpy.context.scene
collection = scene.collection


# ---------- Helpers ----------
def make_material(name, color, roughness=0.5, emission=None, emission_strength=0.0,
                  alpha=1.0, metallic=0.0):
    mat = bpy.data.materials.new(name)  # node tree is created automatically in 5.x
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.surface_render_method = 'BLENDED'
    return mat


def link_object(obj):
    collection.objects.link(obj)
    return obj


def make_sphere(name, radius, material, location=(0, 0, 0), segments=48, rings=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    return link_object(obj)


def make_ring(name, r_inner, r_outer, material, location=(0, 0, 0),
              rotation=(0, 0, 0), segments=128):
    bm = bmesh.new()
    inner_verts, outer_verts = [], []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        ca, sa = math.cos(a), math.sin(a)
        inner_verts.append(bm.verts.new((r_inner * ca, r_inner * sa, 0.0)))
        outer_verts.append(bm.verts.new((r_outer * ca, r_outer * sa, 0.0)))
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((inner_verts[i], outer_verts[i], outer_verts[j], inner_verts[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler = rotation
    return link_object(obj)


# ---------- World ----------
world = bpy.data.worlds.new("SpaceWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.004, 0.005, 0.012, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# ---------- Materials ----------
sun_mat = make_material("Sun", (1.0, 0.6, 0.15), roughness=0.4,
                        emission=(1.0, 0.65, 0.2), emission_strength=25.0)
halo_mat = make_material("SunHalo", (1.0, 0.5, 0.1), roughness=1.0,
                         emission=(1.0, 0.45, 0.1), emission_strength=3.0,
                         alpha=0.08)
orbit_mat = make_material("OrbitLine", (0.2, 0.25, 0.35), roughness=1.0,
                          emission=(0.2, 0.3, 0.5), emission_strength=0.6)

planet_specs = [
    # name,      distance, radius, color,                 roughness, angle
    ("Mercury",  3.2,      0.22,   (0.55, 0.52, 0.50),    0.90,      0.25),
    ("Earth",    5.2,      0.36,   (0.15, 0.45, 0.85),    0.55,      0.90),
    ("Mars",     7.4,      0.28,   (0.85, 0.32, 0.15),    0.80,      0.45),
    ("Saturn",   11.0,     0.85,   (0.88, 0.75, 0.50),    0.45,      0.15),
]

# ---------- Sun ----------
sun = make_sphere("Sun", 1.1, sun_mat, segments=64, rings=32)
halo = make_sphere("SunHalo", 1.9, halo_mat, segments=48, rings=24)

# Sun light (shadows disabled so the light escapes the emissive sphere)
sun_light_data = bpy.data.lights.new("SunLight", type='POINT')
sun_light_data.energy = 6000.0
sun_light_data.color = (1.0, 0.85, 0.65)
sun_light_data.shadow_soft_size = 0.6
sun_light_data.use_shadow = False
sun_light = bpy.data.objects.new("SunLight", sun_light_data)
sun_light.location = (0, 0, 0)
link_object(sun_light)

# ---------- Orbit guide lines ----------
for _, dist, _, _, _, _ in planet_specs:
    make_ring(f"Orbit_{dist}", dist - 0.012, dist + 0.012, orbit_mat,
              location=(0, 0, 0), segments=160)

# ---------- Planets ----------
for name, dist, radius, color, rough, angle in planet_specs:
    mat = make_material(f"{name}_Mat", color, roughness=rough, metallic=0.0)
    pos = (dist * math.cos(angle), dist * math.sin(angle), 0.0)
    make_sphere(name, radius, mat, location=pos, segments=48, rings=24)

    if name == "Saturn":
        ring_mat = make_material("SaturnRing_Mat", (0.85, 0.78, 0.6),
                                 roughness=0.7)
        make_ring("SaturnRing",
                  r_inner=radius * 1.45,
                  r_outer=radius * 2.4,
                  material=ring_mat,
                  location=pos,
                  rotation=(math.radians(22), 0.0, 0.0),
                  segments=160)

# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
link_object(cam_obj)

cam_location = mathutils.Vector((4.0, -30.0, 14.0))
look_at = mathutils.Vector((4.5, 0.0, 0.0))
cam_obj.location = cam_location
direction = look_at - cam_location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# ---------- Render settings (no render performed) ----------
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_start = 1
scene.frame_end = 1
