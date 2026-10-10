import bpy
import math

scene = bpy.context.scene

# Clean scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene.render.engine = 'BLENDER_EEVEE'
scene.frame_start = 1
scene.frame_end = 96
scene.render.fps = 24

# World: very dim so the pulse reads clearly
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1.0)
    bg.inputs["Strength"].default_value = 1.0

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
floor.data.materials.append(make_mat("Floor", (0.35, 0.33, 0.3), 0.6))

# Back wall
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 5, 5), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.data.materials.append(make_mat("Wall", (0.4, 0.38, 0.36), 0.8))

# Some objects around the light
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(-2, 1, 0.6), rotation=(0, 0, math.radians(25)))
bpy.context.active_object.data.materials.append(make_mat("Red", (0.7, 0.1, 0.08), 0.4))

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=(2, 0.8, 0.8), segments=48, ring_count=24)
bpy.ops.object.shade_smooth()
bpy.context.active_object.data.materials.append(make_mat("Metal", (0.8, 0.8, 0.85), 0.2, 1.0))

bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.6, location=(0, 2.2, 0.8))
bpy.context.active_object.data.materials.append(make_mat("Blue", (0.1, 0.25, 0.7), 0.5))

# Visible bulb
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, 0.5, 2.0))
bulb = bpy.context.active_object
bpy.ops.object.shade_smooth()
bulb_mat = bpy.data.materials.new("Bulb")
bnodes = bulb_mat.node_tree.nodes
p = bnodes.get("Principled BSDF")
p.inputs["Base Color"].default_value = (1.0, 0.8, 0.5, 1.0)
p.inputs["Emission Color"].default_value = (1.0, 0.75, 0.45, 1.0)
emit_sock = p.inputs["Emission Strength"]
bulb.data.materials.append(bulb_mat)

# Point light
light_data = bpy.data.lights.new("PulseLight", type='POINT')
light_data.color = (1.0, 0.8, 0.55)
light_data.shadow_soft_size = 0.15
light_obj = bpy.data.objects.new("PulseLight", light_data)
scene.collection.objects.link(light_obj)
light_obj.location = (0, 0.5, 2.0)

# Pulse keyframes: dim -> bright -> dim every 48 frames
dim_e, bright_e = 20.0, 1500.0
dim_s, bright_s = 0.5, 30.0
for f in range(1, 98, 24):
    bright = ((f - 1) // 24) % 2 == 1
    light_data.energy = bright_e if bright else dim_e
    light_data.keyframe_insert("energy", frame=f)
    emit_sock.default_value = bright_s if bright else dim_s
    emit_sock.keyframe_insert("default_value", frame=f)

# Smooth easing
for idblock in (light_data, bulb_mat.node_tree):
    ad = idblock.animation_data
    if ad and ad.action:
        try:
            from bpy_extras import anim_utils
            cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
            if cb:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'SINE'
                        kp.easing = 'EASE_IN_OUT'
        except Exception:
            pass

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -8, 3.5)
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
target.location = (0, 1, 1.0)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam

scene.frame_set(1)
