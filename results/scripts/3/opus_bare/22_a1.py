import bpy, bmesh, math
from mathutils import Vector, Matrix

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

m_ground = mat("Grass", (0.15, 0.35, 0.1))
m_tower = mat("Stone", (0.8, 0.75, 0.65))
m_roof = mat("Roof", (0.45, 0.12, 0.08))
m_wood = mat("Wood", (0.35, 0.2, 0.1))
m_sail = mat("Sail", (0.92, 0.9, 0.82), 0.9)
m_dark = mat("Dark", (0.05, 0.04, 0.03))

# Ground
bpy.ops.mesh.primitive_plane_add(size=80)
bpy.context.active_object.data.materials.append(m_ground)

# Tower
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=2.2, radius2=1.4, depth=8, location=(0, 0, 4))
tower = bpy.context.active_object
tower.data.materials.append(m_tower)

# Roof cap
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.8, radius2=0.0, depth=2.2, location=(0, 0, 9.1))
bpy.context.active_object.data.materials.append(m_roof)

# Door and window
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2.05, 1.0))
d = bpy.context.active_object
d.scale = (0.9, 0.2, 2.0)
d.data.materials.append(m_wood)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.75, 5.0))
w = bpy.context.active_object
w.scale = (0.6, 0.2, 0.8)
w.data.materials.append(m_dark)

# Axle
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.6, location=(0, -1.6, 7.6),
                                    rotation=(math.radians(90), 0, 0))
bpy.context.active_object.data.materials.append(m_wood)

# Hub (rotating parent)
hub_loc = Vector((0, -2.4, 7.6))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=hub_loc)
hub = bpy.context.active_object
hub.name = "Hub"
hub.data.materials.append(m_wood)
bpy.ops.object.shade_smooth()

# Blades mesh built around origin (hub local space), rotation axis = Y
def add_box(bm, center, size, rot, mat_index):
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res["verts"]
    for v in verts:
        p = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(center)
        v.co = rot @ p
    for f in {f for v in verts for f in v.link_faces}:
        f.material_index = mat_index

bm = bmesh.new()
L = 6.0
for i in range(4):
    rot = Matrix.Rotation(i * math.pi / 2, 3, 'Y')
    add_box(bm, (0, 0, L / 2 + 0.2), (0.18, 0.18, L), rot, 0)       # spar
    add_box(bm, (0.65, -0.05, L / 2 + 1.0), (1.1, 0.04, L - 1.6), rot, 1)  # sail
    for k in range(5):  # lattice cross bars
        z = 1.2 + k * (L - 1.6) / 4
        add_box(bm, (0.6, -0.1, z), (1.3, 0.06, 0.06), rot, 0)
me = bpy.data.meshes.new("BladesMesh")
bm.to_mesh(me)
bm.free()
me.materials.append(m_wood)
me.materials.append(m_sail)
blades = bpy.data.objects.new("Blades", me)
scene.collection.objects.link(blades)
blades.parent = hub
blades.location = (0, 0, 0)

# Animation: constant speed, seamless loop over 120 frames
scene.frame_start = 1
scene.frame_end = 120
prefs = bpy.context.preferences.edit
old_interp = prefs.keyframe_new_interpolation_type
prefs.keyframe_new_interpolation_type = 'LINEAR'
hub.rotation_mode = 'XYZ'
hub.rotation_euler = (0, 0, 0)
hub.keyframe_insert(data_path="rotation_euler", index=1, frame=1)
hub.rotation_euler = (0, -2 * math.pi, 0)
hub.keyframe_insert(data_path="rotation_euler", index=1, frame=121)
prefs.keyframe_new_interpolation_type = old_interp

# Lighting
bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
sun = bpy.context.active_object
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.45, 0.65, 0.95, 1)
    bg.inputs["Strength"].default_value = 1.0

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = Vector((11, -22, 5.5))
target = Vector((0, 0, 6.0))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
