import bpy
import math

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 24

# Clear scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

def make_mat(name, color, rough=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*color, 1.0)
    return m

mat_ground = make_mat("Grass", (0.15, 0.35, 0.1), 0.9)
mat_tower = make_mat("Stone", (0.85, 0.8, 0.7), 0.8)
mat_roof = make_mat("Roof", (0.45, 0.12, 0.08), 0.6)
mat_wood = make_mat("Wood", (0.35, 0.2, 0.1), 0.7)
mat_sail = make_mat("Sail", (0.95, 0.93, 0.88), 0.9)
mat_door = make_mat("Door", (0.25, 0.13, 0.06), 0.7)

def assign(ob, mat):
    ob.data.materials.append(mat)

# Ground
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
ground = bpy.context.active_object
assign(ground, mat_ground)

# Tower
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=2.0, radius2=1.3, depth=8, location=(0, 0, 4))
tower = bpy.context.active_object
tower.name = "Tower"
assign(tower, mat_tower)
bpy.ops.object.shade_smooth()

# Roof
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.6, radius2=0.0, depth=2.2, location=(0, 0, 9.1))
roof = bpy.context.active_object
roof.name = "Roof"
assign(roof, mat_roof)
bpy.ops.object.shade_smooth()

# Door
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.93, 0.9))
door = bpy.context.active_object
door.scale = (0.9, 0.2, 1.8)
assign(door, mat_door)

# Windows
for z in (3.5, 5.8):
    r = 2.0 - (2.0 - 1.3) * (z / 8.0)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -r + 0.02, z))
    w = bpy.context.active_object
    w.scale = (0.5, 0.2, 0.7)
    assign(w, mat_door)

# Axle
hub_loc = (0, -1.9, 8.3)
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.15, depth=1.2,
                                    location=(0, -1.4, 8.3), rotation=(math.radians(90), 0, 0))
axle = bpy.context.active_object
assign(axle, mat_wood)

# Rotor empty
bpy.ops.object.empty_add(type='PLAIN_AXES', location=hub_loc)
rotor = bpy.context.active_object
rotor.name = "Rotor"
rotor.rotation_mode = 'XYZ'

def parent_to_rotor(ob):
    ob.parent = rotor
    ob.matrix_parent_inverse = rotor.matrix_world.inverted()

# Hub
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.35, depth=0.4,
                                    location=hub_loc, rotation=(math.radians(90), 0, 0))
hub = bpy.context.active_object
assign(hub, mat_wood)
parent_to_rotor(hub)

# Blades
blade_len = 5.5
for i in range(4):
    ang = i * math.pi / 2
    dx = math.sin(ang)
    dz = math.cos(ang)
    # spar
    c = blade_len / 2 + 0.2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(hub_loc[0] + dx * c, hub_loc[1] - 0.1, hub_loc[2] + dz * c),
                                    rotation=(0, ang, 0))
    spar = bpy.context.active_object
    spar.scale = (0.15, 0.12, blade_len)
    assign(spar, mat_wood)
    parent_to_rotor(spar)
    # sail
    off = 0.55
    px, pz = math.cos(ang), -math.sin(ang)  # perpendicular in XZ plane
    sc = blade_len / 2 + 0.9
    bpy.ops.mesh.primitive_cube_add(size=1,
        location=(hub_loc[0] + dx * sc + px * off, hub_loc[1] - 0.05, hub_loc[2] + dz * sc + pz * off),
        rotation=(0, ang, 0))
    sail = bpy.context.active_object
    sail.scale = (0.95, 0.04, blade_len - 1.4)
    assign(sail, mat_sail)
    parent_to_rotor(sail)

# Animation: constant speed, one full turn per 120 frames (loops seamlessly)
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
except Exception:
    pass
rotor.rotation_euler = (0, 0, 0)
rotor.keyframe_insert(data_path="rotation_euler", index=1, frame=1)
rotor.rotation_euler = (0, 2 * math.pi, 0)
rotor.keyframe_insert(data_path="rotation_euler", index=1, frame=121)

def collect_fcurves(action):
    fcs = []
    try:
        fcs.extend(action.fcurves)
    except Exception:
        pass
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    fcs.extend(cb.fcurves)
    except Exception:
        pass
    return fcs

ad = rotor.animation_data
if ad and ad.action:
    for fc in collect_fcurves(ad.action):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# Lighting
bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1.0)
    bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 5.5))
target = bpy.context.active_object
target.name = "CamTarget"

bpy.ops.object.camera_add(location=(11, -22, 6))
cam = bpy.context.active_object
cam.data.lens = 35
con = cam.constraints.new(type='TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
scene.camera = cam
