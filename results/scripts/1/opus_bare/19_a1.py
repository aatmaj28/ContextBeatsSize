import bpy, random, math
from mathutils import Vector

random.seed(42)
scene = bpy.context.scene

# Clear scene
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Render engine
try:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
except Exception:
    pass

# Materials
def make_mat(name, color, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return m

ground_mat = make_mat("Ground", (0.08, 0.1, 0.05), 0.95)
trunk_mat = make_mat("Trunk", (0.12, 0.07, 0.04), 0.9)
leaf_mats = [make_mat(f"Leaves{i}", c, 0.85) for i, c in enumerate(
    [(0.03, 0.12, 0.04), (0.05, 0.16, 0.06), (0.04, 0.1, 0.05), (0.07, 0.14, 0.04)])]

# Ground
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(ground_mat)

# Trees
def make_tree(x, y, scale):
    th = 1.2 * scale
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.15 * scale, depth=th,
                                        location=(x, y, th / 2))
    trunk = bpy.context.active_object
    trunk.data.materials.append(trunk_mat)
    mat = random.choice(leaf_mats)
    layers = random.randint(2, 3)
    base = th * 0.7
    for i in range(layers):
        r = (1.4 - i * 0.35) * scale
        h = (2.4 - i * 0.4) * scale
        z = base + i * 1.1 * scale + h / 2
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=r, radius2=0, depth=h,
                                        location=(x, y, z),
                                        rotation=(0, 0, random.uniform(0, math.pi)))
        cone = bpy.context.active_object
        cone.data.materials.append(mat)
        bpy.ops.object.shade_smooth()

placed = []
attempts = 0
while len(placed) < 140 and attempts < 3000:
    attempts += 1
    x = random.uniform(-35, 35)
    y = random.uniform(-15, 50)
    # keep a clearing near the camera path
    if abs(x) < 2.0 and y < 10:
        continue
    if any((x - px) ** 2 + (y - py) ** 2 < 4.0 for px, py in placed):
        continue
    placed.append((x, y))
    make_tree(x, y, random.uniform(0.8, 1.8))

# World with volumetric fog
world = bpy.data.worlds.new("FogWorld")
scene.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.55, 0.6, 0.65, 1)
bg.inputs["Strength"].default_value = 0.6
vol = nt.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Color"].default_value = (0.8, 0.85, 0.9, 1)
vol.inputs["Density"].default_value = 0.04
vol.inputs["Anisotropy"].default_value = 0.3
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])

# Lighting
bpy.ops.object.light_add(type='SUN', location=(10, -10, 30))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.data.color = (1.0, 0.95, 0.85)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))

# Camera
bpy.ops.object.camera_add(location=(0, -18, 2.2))
cam = bpy.context.active_object
cam.data.lens = 32
direction = Vector((0, 20, 3.5)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.frame_start = 1
scene.frame_end = 1
