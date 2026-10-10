import bpy, bmesh, math, random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene

# Clear
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# Materials
def crystal_mat():
    m = bpy.data.materials.new("Amethyst")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.55, 0.2, 0.9, 1)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["IOR"].default_value = 1.54
    if "Transmission Weight" in b.inputs:
        b.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in b.inputs:
        b.inputs["Transmission"].default_value = 1.0
    return m

def rock_mat():
    m = bpy.data.materials.new("Rock")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Roughness"].default_value = 0.9
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.02, 0.02, 0.025, 1)
    ramp.color_ramp.elements[1].color = (0.12, 0.11, 0.1, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m

cmat = crystal_mat()
rmat = rock_mat()

# Rock
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.5, location=(0, 0, -0.6))
rock = bpy.context.active_object
rock.name = "Rock"
rock.scale = (1.6, 1.2, 0.6)
tex = bpy.data.textures.new("RockNoise", 'CLOUDS')
tex.noise_scale = 0.6
d = rock.modifiers.new("Disp", 'DISPLACE')
d.texture = tex
d.strength = 0.5
rock.data.materials.append(rmat)
bpy.ops.object.shade_smooth()

# Crystal mesh builder
def make_crystal(name, radius, height, tip):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    n = 6
    bot, top = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = radius * random.uniform(0.85, 1.1)
        x, y = math.cos(a) * r, math.sin(a) * r
        bot.append(bm.verts.new((x, y, -0.3)))
        top.append(bm.verts.new((x, y, height)))
    apex = bm.verts.new((random.uniform(-0.05, 0.05) * radius, 0, height + tip))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
        bm.faces.new((top[i], top[j], apex))
    bm.faces.new(list(reversed(bot)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.data.materials.append(cmat)
    return ob

# Cluster
count = 14
for k in range(count):
    if k == 0:
        pos = Vector((0, 0, 0.1)); tilt = 0; h = 2.2; r = 0.32
    else:
        ang = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0.25, 1.1)
        pos = Vector((math.cos(ang) * dist * 1.2, math.sin(ang) * dist, 0.1 - dist * 0.15))
        tilt = min(dist * 0.7, 1.0) + random.uniform(-0.15, 0.15)
        h = random.uniform(0.5, 1.6) * (1.2 - dist * 0.4)
        r = random.uniform(0.1, 0.24)
    c = make_crystal(f"Crystal_{k}", r, h, r * 1.6)
    c.location = pos
    if k == 0:
        c.rotation_euler = (0.05, -0.08, random.uniform(0, 6.28))
    else:
        dirv = Vector((pos.x, pos.y, 0)).normalized()
        axis = Vector((0, 0, 1)).cross(dirv)
        rot = Matrix.Rotation(tilt, 4, axis) @ Matrix.Rotation(random.uniform(0, 6.28), 4, 'Z')
        c.rotation_euler = rot.to_euler()

# Ground
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -1.0))
g = bpy.context.active_object
gm = bpy.data.materials.new("Ground")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.01, 0.01, 0.012, 1)
g.data.materials.append(gm)

# Lights
def light(name, typ, loc, energy, color, size=1):
    ld = bpy.data.lights.new(name, typ)
    ld.energy = energy; ld.color = color
    if typ == 'AREA': ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    scene.collection.objects.link(lo)
    lo.rotation_euler = (Vector((0, 0, 0.5)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
light("Key", 'AREA', (4, -3, 5), 800, (1, 0.95, 0.9), 3)
light("Rim", 'AREA', (-3, 4, 3), 600, (0.7, 0.5, 1), 2)
light("Fill", 'AREA', (-4, -4, 1.5), 150, (0.8, 0.85, 1), 3)
light("Under", 'POINT', (0, 0, 0.4), 30, (0.8, 0.4, 1))

# World
w = bpy.data.worlds.new("World")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.005, 0.004, 0.01, 1)

# Camera
cd = bpy.data.cameras.new("Cam")
cd.lens = 55
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
cam.location = (5.5, -6.0, 3.0)
cam.rotation_euler = (Vector((0, 0, 0.6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
