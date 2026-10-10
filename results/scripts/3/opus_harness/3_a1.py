import bpy, math, mathutils

scene = bpy.context.scene

def mat(name, color, rough=0.5, sss=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if sss > 0:
        try:
            b.inputs["Subsurface Weight"].default_value = sss
        except Exception:
            pass
    return m

snow = mat("Snow", (0.92, 0.95, 1.0), 0.6, 0.2)
carrot = mat("Carrot", (0.9, 0.35, 0.05), 0.5)
wood = mat("Wood", (0.25, 0.14, 0.06), 0.8)
black = mat("Black", (0.02, 0.02, 0.02), 0.4)
coal = mat("Coal", (0.03, 0.03, 0.03), 0.9)
red = mat("Scarf", (0.7, 0.05, 0.05), 0.7)

def add(obj, m):
    obj.data.materials.append(m)
    return obj

def sphere(loc, r, m, scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.active_object
    o.scale = scale
    bpy.ops.object.shade_smooth()
    return add(o, m)

# Ground
bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,0))
g = bpy.context.active_object
add(g, snow)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=40)
bpy.ops.object.mode_set(mode='OBJECT')
tex = bpy.data.textures.new("SnowNoise", 'CLOUDS')
tex.noise_scale = 2.0
d = g.modifiers.new("Disp", 'DISPLACE'); d.texture = tex; d.strength = 0.3
bpy.ops.object.shade_smooth()

# Body
sphere((0,0,0.9), 1.0, snow, (1,1,0.92))
sphere((0,0,2.25), 0.72, snow)
sphere((0,0,3.3), 0.5, snow)

# Nose
bpy.ops.mesh.primitive_cone_add(radius1=0.08, radius2=0.005, depth=0.5, location=(0,-0.7,3.3), rotation=(math.radians(90),0,0))
add(bpy.context.active_object, carrot)
bpy.ops.object.shade_smooth()

# Eyes
for x in (-0.17, 0.17):
    sphere((x, -0.44, 3.45), 0.055, coal)
# Mouth
for i in range(5):
    a = math.radians(-40 + i*20)
    x = 0.25*math.sin(a); z = 3.2 - 0.08*math.cos(a)
    sphere((x, -0.47 + abs(x)*0.25, z - 0.02), 0.035, coal)
# Buttons
for z, y in ((2.55, -0.66), (2.25, -0.72), (1.95, -0.67)):
    sphere((0, y, z), 0.06, coal)

# Scarf
bpy.ops.mesh.primitive_torus_add(major_radius=0.48, minor_radius=0.09, location=(0,0,2.88))
add(bpy.context.active_object, red); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.25,-0.45,2.6), rotation=(0.2,0,0.15))
s = bpy.context.active_object; s.scale = (0.16,0.05,0.5); add(s, red)

# Hat
bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=0.05, location=(0,0,3.72))
add(bpy.context.active_object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=0.38, depth=0.7, location=(0,0,4.08))
add(bpy.context.active_object, black)
bpy.ops.mesh.primitive_cylinder_add(radius=0.385, depth=0.1, location=(0,0,3.82))
add(bpy.context.active_object, red)

# Stick arms
def stick(p1, p2, r=0.035):
    p1 = mathutils.Vector(p1); p2 = mathutils.Vector(p2)
    v = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=v.length, location=(p1+p2)/2)
    o = bpy.context.active_object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = v.to_track_quat('Z', 'Y')
    add(o, wood)
for sgn in (1, -1):
    base = (sgn*0.6, 0, 2.35)
    end = (sgn*1.7, -0.1, 3.0)
    stick(base, end)
    mid = (sgn*1.3, -0.07, 2.76)
    stick(mid, (sgn*1.55, -0.1, 3.15), 0.022)
    stick(end, (sgn*1.95, -0.1, 3.05), 0.02)
    stick(end, (sgn*1.8, -0.1, 3.3), 0.02)

# Lighting
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(-30)))
sun = bpy.context.active_object; sun.data.energy = 3.5; sun.data.color = (1, 0.95, 0.88)
bpy.ops.object.light_add(type='AREA', location=(-4, -5, 5))
fill = bpy.context.active_object; fill.data.energy = 400; fill.data.size = 4
fill.data.color = (0.75, 0.85, 1.0)
fill.rotation_euler = (mathutils.Vector((0,0,2)) - fill.location).to_track_quat('-Z','Y').to_euler()

world = bpy.data.worlds.new("World"); scene.world = world
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.55, 0.68, 0.9, 1); bg.inputs["Strength"].default_value = 0.8

# Camera
bpy.ops.object.camera_add(location=(3.5, -8.5, 3.2))
cam = bpy.context.active_object
cam.data.lens = 45
cam.rotation_euler = (mathutils.Vector((0,0,2.2)) - cam.location).to_track_quat('-Z','Y').to_euler()
scene.camera = cam
scene.render.resolution_x = 1080; scene.render.resolution_y = 1350
