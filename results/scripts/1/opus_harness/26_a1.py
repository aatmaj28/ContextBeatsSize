import bpy
import math

scene = bpy.context.scene

# Clear any existing objects
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

scene.frame_start = 1
scene.frame_end = 96
scene.render.fps = 24

# --- World (dim so the pulse reads clearly) ---
world = bpy.data.worlds.new("DimWorld")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1.0)
    bg.inputs["Strength"].default_value = 0.5

# --- Materials ---
def make_mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1.0)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    return m

floor_mat = make_mat("Floor", (0.35, 0.33, 0.3), 0.7)
red_mat = make_mat("Red", (0.7, 0.08, 0.06), 0.4)
blue_mat = make_mat("Blue", (0.1, 0.25, 0.7), 0.3)
metal_mat = make_mat("Metal", (0.9, 0.85, 0.75), 0.2, 1.0)

# --- Geometry ---
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
bpy.context.object.data.materials.append(floor_mat)

bpy.ops.mesh.primitive_cube_add(size=1.2, location=(-1.8, 0.5, 0.6))
cube = bpy.context.object
cube.rotation_euler = (0, 0, math.radians(30))
cube.data.materials.append(red_mat)

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(1.6, 0.8, 0.7), segments=48, ring_count=24)
bpy.ops.object.shade_smooth()
bpy.context.object.data.materials.append(blue_mat)

bpy.ops.mesh.primitive_torus_add(location=(0.2, -1.4, 0.25), major_radius=0.6, minor_radius=0.22)
bpy.ops.object.shade_smooth()
bpy.context.object.data.materials.append(metal_mat)

# --- Glowing bulb marking the light position ---
light_pos = (0, 0, 2.6)
bulb_mat = bpy.data.materials.new("Bulb")
nt = bulb_mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
emit = nt.nodes.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (1.0, 0.8, 0.55, 1.0)
nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=light_pos)
bpy.ops.object.shade_smooth()
bulb = bpy.context.object
bulb.data.materials.append(bulb_mat)
bulb.visible_shadow = False

# --- Point light ---
light_data = bpy.data.lights.new("PulseLight", type='POINT')
light_data.color = (1.0, 0.8, 0.55)
light_data.shadow_soft_size = 0.15
light_obj = bpy.data.objects.new("PulseLight", light_data)
scene.collection.objects.link(light_obj)
light_obj.location = light_pos

# Animate: dim -> bright -> dim, period 48 frames
dim, bright = 20.0, 1500.0
emit_dim, emit_bright = 1.0, 40.0
for f in range(1, 98, 24):
    phase = ((f - 1) // 24) % 2  # 0 = dim, 1 = bright
    light_data.energy = bright if phase else dim
    light_data.keyframe_insert("energy", frame=f)
    emit.inputs["Strength"].default_value = emit_bright if phase else emit_dim
    emit.inputs["Strength"].keyframe_insert("default_value", frame=f)

# Faint fill so the scene isn't pure black at the dim point
fill = bpy.data.lights.new("Fill", type='AREA')
fill.energy = 15
fill.size = 5
fill_obj = bpy.data.objects.new("Fill", fill)
scene.collection.objects.link(fill_obj)
fill_obj.location = (4, -4, 5)
fill_obj.rotation_euler = (math.radians(50), 0, math.radians(45))

# --- Camera ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (6.5, -6.5, 4.2)
target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
target.location = (0, 0, 0.8)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.frame_set(1)
