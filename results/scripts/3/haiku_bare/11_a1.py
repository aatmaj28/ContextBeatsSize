import bpy
import math
from mathutils import Vector

scene = bpy.context.scene

# ---------- Clear default scene ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

# Cycles is needed for real glass refraction
scene.render.engine = 'CYCLES'


# ---------- Helpers ----------
def new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    return mat, nodes, links


def add_output(nodes, links, shader_socket):
    out = nodes.new('ShaderNodeOutputMaterial')
    links.new(shader_socket, out.inputs['Surface'])
    return out


def smooth_mesh(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


# ---------- Floor with checker material ----------
floor_mat, fn, fl = new_material("CheckerFloor")
checker = fn.new('ShaderNodeTexChecker')
checker.inputs['Color1'].default_value = (0.82, 0.82, 0.80, 1.0)
checker.inputs['Color2'].default_value = (0.04, 0.04, 0.05, 1.0)
checker.inputs['Scale'].default_value = 10.0
floor_bsdf = fn.new('ShaderNodeBsdfPrincipled')
floor_bsdf.inputs['Roughness'].default_value = 0.35
fl.new(checker.outputs['Color'], floor_bsdf.inputs['Base Color'])
add_output(fn, fl, floor_bsdf.outputs['BSDF'])

bpy.ops.mesh.primitive_plane_add(size=24, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(floor_mat)


# ---------- Glass sphere ----------
glass_mat, gn, gl = new_material("GlassMat")
glass = gn.new('ShaderNodeBsdfGlass')
glass.inputs['Color'].default_value = (0.9, 0.97, 1.0, 1.0)
glass.inputs['Roughness'].default_value = 0.02
glass.inputs['IOR'].default_value = 1.45
add_output(gn, gl, glass.outputs['BSDF'])

bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48,
                                     radius=1.0, location=(-1.25, 0.0, 1.0))
glass_obj = bpy.context.active_object
glass_obj.name = "GlassSphere"
smooth_mesh(glass_obj)
glass_obj.data.materials.append(glass_mat)


# ---------- Gold sphere ----------
gold_mat, mn, ml = new_material("GoldMat")
gold = mn.new('ShaderNodeBsdfPrincipled')
gold.inputs['Base Color'].default_value = (1.0, 0.766, 0.336, 1.0)
gold.inputs['Metallic'].default_value = 1.0
gold.inputs['Roughness'].default_value = 0.22
add_output(mn, ml, gold.outputs['BSDF'])

bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48,
                                     radius=0.8, location=(1.4, 0.5, 0.8))
gold_obj = bpy.context.active_object
gold_obj.name = "GoldSphere"
smooth_mesh(gold_obj)
gold_obj.data.materials.append(gold_mat)


# ---------- World: Sky Texture drives background and lighting ----------
world = bpy.data.worlds.new("SkyWorld")
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()

sky = wn.new('ShaderNodeTexSky')
sky.sky_type = 'NISHITA'
sky.sun_elevation = math.radians(38.0)
sky.sun_rotation = math.radians(25.0)
sky.altitude = 100.0
sky.air_density = 1.0
sky.dust_density = 1.0

bg = wn.new('ShaderNodeBackground')
bg.inputs['Strength'].default_value = 1.0
wl.new(sky.outputs['Color'], bg.inputs['Color'])

world_out = wn.new('ShaderNodeOutputWorld')
wl.new(bg.outputs['Background'], world_out.inputs['Surface'])


# ---------- Camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_data.dof.use_dof = False
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)

cam_loc = Vector((7.0, -7.5, 4.2))
target = Vector((0.0, 0.0, 0.9))
cam_obj.location = cam_loc
direction = target - cam_loc
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.camera = cam_obj

# Single still frame (no animation)
scene.frame_start = 1
scene.frame_end = 1
