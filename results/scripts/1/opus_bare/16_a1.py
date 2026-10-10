import bpy, bmesh, math, random
from mathutils import Vector, Matrix

random.seed(7)
scene = bpy.context.scene

# Clear scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- Materials ----------
def crystal_mat():
    m = bpy.data.materials.new("PurpleCrystal")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.55, 0.2, 0.9, 1)
    b.inputs["Roughness"].default_value = 0.03
    b.inputs["IOR"].default_value = 1.55
    if "Transmission Weight" in b.inputs:
        b.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in b.inputs:
        b.inputs["Transmission"].default_value = 1.0
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    return m

def rock_mat():
    m = bpy.data.materials.new("DarkRock")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Roughness"].default_value = 0.9
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.0
    noise.inputs["Detail"].default_value = 10.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.015, 0.014, 0.013, 1)
    ramp.color_ramp.elements[1].color = (0.08, 0.075, 0.07, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m

cmat = crystal_mat()
rmat = rock_mat()

# ---------- Rock ----------
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
for v in bm.verts:
    p = v.co.copy()
    n = (math.sin(p.x*3.1)+math.sin(p.y*2.7+1)+math.sin(p.z*3.5+2))*0.08
    n += random.uniform(-0.04, 0.04)
    v.co = p * (1 + n)
    v.co.x *= 1.6; v.co.y *= 1.3; v.co.z *= 0.55
rock_me = bpy.data.meshes.new("Rock")
bm.to_mesh(rock_me); bm.free()
rock = bpy.data.objects.new("Rock", rock_me)
scene.collection.objects.link(rock)
rock_me.materials.append(rmat)
for p in rock_me.polygons:
    p.use_smooth = True

# ---------- Crystal ----------
def make_crystal(name, radius, length, tip):
    bm = bmesh.new()
    sides = 6
    bottom, top = [], []
    for i in range(sides):
        a = 2*math.pi*i/sides
        r = radius*random.uniform(0.85, 1.1)
        bottom.append(bm.verts.new((r*math.cos(a), r*math.sin(a), -0.2)))
        top.append(bm.verts.new((r*math.cos(a)*0.9, r*math.sin(a)*0.9, length)))
    apex = bm.verts.new((random.uniform(-0.1,0.1)*radius, random.uniform(-0.1,0.1)*radius, length+tip))
    for i in range(sides):
        j = (i+1) % sides
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
        bm.faces.new((top[i], top[j], apex))
    bm.faces.new(list(reversed(bottom)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    me.materials.append(cmat)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    bev = ob.modifiers.new("Bevel", 'BEVEL')
    bev.width = 0.008; bev.segments = 2
    return ob

center = Vector((0.1, 0.0, 0.45))
for k in range(16):
    if k == 0:
        r, L, tilt, az, off = 0.22, 1.6, 0.05, 0, Vector((0,0,0))
    else:
        r = random.uniform(0.07, 0.17)
        L = random.uniform(0.4, 1.2)
        tilt = random.uniform(0.25, 0.9)
        az = random.uniform(0, 2*math.pi)
        d = random.uniform(0.1, 0.45)
        off = Vector((math.cos(az)*d, math.sin(az)*d*0.8, -d*0.25))
    c = make_crystal(f"Crystal_{k}", r, L, r*random.uniform(1.4, 2.2))
    c.location = center + off
    c.rotation_euler = (0, tilt, az)
    c.rotation_mode = 'ZYX'
    c.rotation_euler = (0, tilt, az)

# ---------- Ground ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.45))
g = bpy.context.active_object
gm = bpy.data.materials.new("Ground")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1)
gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
g.data.materials.append(gm)

# ---------- World ----------
w = bpy.data.worlds.new("World")
scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.01, 0.008, 0.015, 1)
bg.inputs["Strength"].default_value = 1.0

# ---------- Lights ----------
def area(name, loc, energy, color, size):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy; ld.color = color; ld.size = size
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    scene.collection.objects.link(o)
    d = Vector((0, 0, 0.6)) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
area("Key", (3, -3, 4), 600, (1, 0.95, 0.9), 2)
area("Rim", (-3, 3, 2.5), 500, (0.7, 0.5, 1.0), 1.5)
area("Fill", (-3, -2, 1.5), 120, (0.8, 0.85, 1.0), 3)
area("Back", (0.5, 4, 1.0), 300, (0.9, 0.6, 1.0), 1)

# ---------- Camera ----------
cd = bpy.data.cameras.new("Camera")
cd.lens = 55
cam = bpy.data.objects.new("Camera", cd)
scene.collection.objects.link(cam)
cam.location = (4.2, -4.6, 2.4)
target = Vector((0.1, 0, 0.75))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------- Render settings ----------
try:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
except Exception:
    pass
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.frame_start = 1
scene.frame_end = 1
