import bpy
import math

# ---------- Clean up any existing mesh/light/camera objects ----------
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
collection = scene.collection


# ---------- Helpers ----------
def new_material(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def wood_material(name, dark, light, roughness=0.45):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4.0
    noise.inputs["Detail"].default_value = 8.0

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (dark[0], dark[1], dark[2], 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (light[0], light[1], light[2], 1.0)

    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def make_box(name, location, dims, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = dims
    obj.data.materials.append(material)
    return obj


# ---------- Materials ----------
wall_mat = new_material("WallMat", (0.85, 0.82, 0.74), 0.9)
floor_mat = wood_material("FloorMat", (0.18, 0.10, 0.05), (0.35, 0.21, 0.11), 0.6)
ceiling_mat = new_material("CeilingMat", (0.92, 0.92, 0.9), 0.9)
table_mat = wood_material("TableWood", (0.30, 0.16, 0.07), (0.55, 0.34, 0.18), 0.4)
chair_mat = wood_material("ChairWood", (0.25, 0.13, 0.06), (0.48, 0.28, 0.14), 0.45)
cushion_mat = new_material("CushionMat", (0.55, 0.12, 0.10), 0.85)
vase_mat = new_material("VaseMat", (0.2, 0.45, 0.6), 0.2)

# ---------- Room (open front for camera view) ----------
ROOM_W = 5.0   # x
ROOM_D = 4.0   # y
ROOM_H = 2.8   # z

make_box("Floor", (0, 0, -0.05), (ROOM_W, ROOM_D, 0.1), floor_mat)
make_box("Ceiling", (0, 0, ROOM_H + 0.05), (ROOM_W, ROOM_D, 0.1), ceiling_mat)
make_box("WallBack", (0, ROOM_D / 2 + 0.05, ROOM_H / 2), (ROOM_W + 0.1, 0.1, ROOM_H), wall_mat)
make_box("WallLeft", (-ROOM_W / 2 - 0.05, 0, ROOM_H / 2), (0.1, ROOM_D, ROOM_H), wall_mat)
make_box("WallRight", (ROOM_W / 2 + 0.05, 0, ROOM_H / 2), (0.1, ROOM_D, ROOM_H), wall_mat)

# Baseboards for a bit of detail
make_box("BaseBack", (0, ROOM_D / 2 - 0.01, 0.06), (ROOM_W, 0.02, 0.12), table_mat)
make_box("BaseLeft", (-ROOM_W / 2 + 0.01, 0, 0.06), (0.02, ROOM_D, 0.12), table_mat)
make_box("BaseRight", (ROOM_W / 2 - 0.01, 0, 0.06), (0.02, ROOM_D, 0.12), table_mat)

# ---------- Table ----------
TABLE_TOP_Z = 0.75
make_box("TableTop", (0, 0, TABLE_TOP_Z - 0.025), (1.6, 0.9, 0.05), table_mat)
leg_h = TABLE_TOP_Z - 0.05
for sx in (-1, 1):
    for sy in (-1, 1):
        make_box(
            "TableLeg",
            (sx * 0.7, sy * 0.36, leg_h / 2),
            (0.07, 0.07, leg_h),
            table_mat,
        )

# Small decorative vase on the table
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.07, depth=0.22, location=(0.45, 0.0, TABLE_TOP_Z + 0.11)
)
vase = bpy.context.active_object
vase.name = "Vase"
vase.data.materials.append(vase_mat)


# ---------- Chairs ----------
def make_chair(name, location, rot_z):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    root = bpy.context.active_object
    root.name = name + "_Root"
    root.rotation_euler = (0, 0, rot_z)

    parts = []
    seat_z = 0.45
    # Seat
    parts.append(make_box(name + "_Seat", (0, 0, seat_z), (0.45, 0.45, 0.05), chair_mat))
    # Cushion on seat
    parts.append(make_box(name + "_Cushion", (0, 0, seat_z + 0.03), (0.40, 0.40, 0.03), cushion_mat))
    # Legs
    for lx in (-0.19, 0.19):
        for ly in (-0.19, 0.19):
            parts.append(make_box(
                name + "_Leg", (lx, ly, seat_z / 2 - 0.01), (0.035, 0.035, seat_z - 0.02), chair_mat
            ))
    # Backrest posts and panel (back toward local -Y, away from table)
    back_y = -0.205
    for lx in (-0.19, 0.19):
        parts.append(make_box(
            name + "_Post", (lx, back_y, seat_z + 0.27), (0.035, 0.035, 0.55), chair_mat
        ))
    parts.append(make_box(name + "_Back", (0, back_y, seat_z + 0.35), (0.40, 0.03, 0.14), chair_mat))
    parts.append(make_box(name + "_TopRail", (0, back_y, seat_z + 0.55), (0.42, 0.04, 0.05), chair_mat))

    for p in parts:
        p.parent = root
    return root


# Two chairs on each long side of the table
make_chair("ChairFrontL", (-0.5, -0.85, 0.0), 0.0)
make_chair("ChairFrontR", (0.5, -0.85, 0.0), 0.0)
make_chair("ChairBackL", (-0.5, 0.85, 0.0), math.pi)
make_chair("ChairBackR", (0.5, 0.85, 0.0), math.pi)


# ---------- Lighting ----------
light_data = bpy.data.lights.new(name="CeilingLight", type='AREA')
light_data.energy = 350.0
light_data.size = 2.0
light_data.size_y = 1.5
light_obj = bpy.data.objects.new("CeilingLight", light_data)
light_obj.location = (0.0, 0.0, ROOM_H - 0.15)
collection.objects.link(light_obj)

fill_data = bpy.data.lights.new(name="FillLight", type='POINT')
fill_data.energy = 60.0
fill_obj = bpy.data.objects.new("FillLight", fill_data)
fill_obj.location = (-1.8, -1.2, 2.0)
collection.objects.link(fill_obj)

# Soft ambient world
world = bpy.data.worlds.new("RoomWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.08, 0.08, 0.09, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world


# ---------- Camera ----------
cam_data = bpy.data.cameras.new("MainCamera")
cam_data.lens = 24.0
cam_obj = bpy.data.objects.new("MainCamera", cam_data)
cam_obj.location = (0.0, -3.6, 1.7)
collection.objects.link(cam_obj)

target = (0.0, 0.0, 0.75)
direction = [target[i] - cam_obj.location[i] for i in range(3)]
from mathutils import Vector
rot_quat = Vector(direction).to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

scene.camera = cam_obj

# Single still frame setup
scene.frame_start = 1
scene.frame_end = 1
