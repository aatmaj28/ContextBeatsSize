import bpy
import math

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 96
scene.render.fps = 24

# World: very dim
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.01, 0.015, 1.0)
    bg.inputs["Strength"].default_value = 0.3

def make_mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1.0)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    return m

# Floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.active_object
floor.data.materials.append(make_mat("Floor", (0.35, 0.33, 0.3), 0.7))

# Back wall
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 5, 5), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.data.materials.append(make_mat("Wall", (0.3, 0.3, 0.35), 0.8))

# Objects around the light
mats = [make_mat("Red", (0.8, 0.1, 0.1), 0.4),
        make_mat("Blue", (0.1, 0.25, 0.8), 0.3),
        make_mat("Gold", (0.9, 0.7, 0.3), 0.25, 1.0)]
for i, ang in enumerate([0, 120, 240]):
    a = math.radians(ang + 30)
    x, y = 2.5 * math.cos(a), 2.5 * math.sin(a)
    if i == 0:
        bpy.ops.mesh.primitive_cube_add(size=1.2, location=(x, y, 0.6))
    elif i == 1:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(x, y, 0.7))
        bpy.ops.object.shade_smooth()
    else:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.6, location=(x, y, 0.8))
        bpy.ops.object.shade_smooth()
    bpy.context.active_object.data.materials.append(mats[i])

# Glowing bulb mesh at the light position
light_loc = (0, 0, 1.8)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=light_loc)
bulb = bpy.context.active_object
bpy.ops.object.shade_smooth()
bulb_mat = bpy.data.materials.new("BulbEmission")
nt = bulb_mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
emit = nt.nodes.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (1.0, 0.8, 0.5, 1.0)
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
bulb.data.materials.append(bulb_mat)
bulb.visible_shadow = False

# Point light
light_data = bpy.data.lights.new("PulseLight", type='POINT')
light_data.color = (1.0, 0.8, 0.5)
light_data.shadow_soft_size = 0.15
light_obj = bpy.data.objects.new("PulseLight", light_data)
light_obj.location = light_loc
scene.collection.objects.link(light_obj)

# Pulse keyframes: dim at 1, 49, 97; bright at 25, 73 (period 48)
dim_e, bright_e = 20.0, 1500.0
dim_s, bright_s = 0.5, 30.0
for f, bright in [(1, False), (25, True), (49, False), (73, True), (97, False)]:
    light_data.energy = bright_e if bright else dim_e
    light_data.keyframe_insert("energy", frame=f)
    emit.inputs["Strength"].default_value = bright_s if bright else dim_s
    emit.inputs["Strength"].keyframe_insert("default_value", frame=f)

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -8.5, 4.0)
target = bpy.data.objects.new("CamTarget", None)
target.location = (0, 0, 1.0)
scene.collection.objects.link(target)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

scene.render.engine = 'BLENDER_EEVEE'
scene.frame_set(1)
