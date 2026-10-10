import bpy, bmesh, math, random
from mathutils import Vector, Matrix

random.seed(42)
scene = bpy.context.scene

# Clean
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# Materials
def make_crystal_mat():
    m = bpy.data.materials.new("Amethyst")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.55, 0.2, 0.9, 1)
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["IOR"].default_value = 1.55
    if "Transmission Weight" in b.inputs:
        b.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in b.inputs:
        b.inputs["Transmission"].default_value = 1.0
    return m

def make_rock_mat():
    m = bpy.data.materials.new("Rock")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Roughness"].default_value = 0.9
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.0
    noise.inputs["Detail"].default_value = 10.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.015, 0.014, 0.013, 1)
    ramp.color_ramp.elements[1].color = (0.08, 0.07, 0.065, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m

crystal_mat = make_crystal_mat()
rock_mat = make_rock_mat()

# Rock
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.5, location=(0, 0, 0))
rock = bpy.context.active_object
rock.name = "Rock"
rock.scale = (1.6, 1.2, 0.55)
tex = bpy.data.textures.new("RockNoise", type='VORONOI')
tex.noise_scale = 0.8
d = rock.modifiers.new("Disp", 'DISPLACE')
d.texture = tex
d.strength = 0.35
tex2 = bpy.data.textures.new("RockClouds", type='CLOUDS')
tex2.noise_scale = 0.3
d2 = rock.modifiers.new("Disp2", 'DISPLACE')
d2.texture = tex2
d2.strength = 0.12
rock.data.materials.append(rock_mat)
bpy.ops.object.shade_smooth()

# Crystal mesh builder (hexagonal prism with pointed tip)
def crystal_mesh(name, r, h, tip):
    bm = bmesh.new()
    n = 6
    bot, top = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * random.uniform(0.85, 1.1)
        bot.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), -0.3)))
        top.append(bm.verts.new((rr * 0.95 * math.cos(a), rr * 0.95 * math.sin(a), h)))
    apex = bm.verts.new((random.uniform(-0.1, 0.1) * r, random.uniform(-0.1, 0.1) * r, h + tip))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
        bm.faces.new((top[i], top[j], apex))
    bm.faces.new(list(reversed(bot)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me

col_center = Vector((0.0, 0.0, 0.55))
for k in range(16):
    r = random.uniform(0.08, 0.22)
    h = r * random.uniform(4, 8)
    me = crystal_mesh(f"Crystal{k}", r, h, r * random.uniform(1.2, 2.0))
    me.materials.append(crystal_mat)
    ob = bpy.data.objects.new(f"Crystal{k}", me)
    scene.collection.objects.link(ob)
    ang = random.uniform(0, 2 * math.pi)
    dist = random.uniform(0, 0.7) if k > 0 else 0
    ob.location = col_center + Vector((math.cos(ang) * dist, math.sin(ang) * dist * 0.8, 0))
    tilt = dist * 0.9 + random.uniform(-0.1, 0.1)
    ob.rotation_euler = (0, tilt, ang)
    ob.rotation_mode = 'XYZ'
    # tilt outward: rotate around axis perpendicular to direction
    axis = Vector((-math.sin(ang), math.cos(ang), 0))
    ob.rotation_euler = (Matrix.Rotation(tilt, 4, axis) @ Matrix.Rotation(random.uniform(0, 1), 4, 'Z')).to_euler()

# Ground
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.75))
g = bpy.context.active_object
gm = bpy.data.materials.new("Ground")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1)
gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
g.data.materials.append(gm)

# Lights
def light(name, typ, loc, energy, color, size=1):
    ld = bpy.data.lights.new(name, typ)
    ld.energy = energy
    ld.color = color
    if typ == 'AREA':
        ld.size = size
    o = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 0.8)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o

light("Key", 'AREA', (4, -4, 5), 800, (1, 0.95, 0.9), 3)
light("Rim", 'AREA', (-3, 4, 3), 600, (0.7, 0.6, 1.0), 2)
light("Fill", 'AREA', (-5, -3, 2), 150, (0.8, 0.85, 1.0), 4)
light("Under", 'POINT', (0, 0, 2.8), 60, (0.8, 0.5, 1.0))

# World
w = bpy.data.worlds.new("World")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.005, 0.004, 0.01, 1)

# Camera
cd = bpy.data.cameras.new("Cam")
cd.lens = 55
cam = bpy.data.objects.new("Camera", cd)
scene.collection.objects.link(cam)
cam.location = (5.5, -6.0, 3.2)
cam.rotation_euler = (Vector((0, 0, 0.9)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
