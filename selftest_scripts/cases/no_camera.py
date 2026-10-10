# category: basic
# expect: check_failed
# expect_message: camera
import bpy
bpy.ops.mesh.primitive_cube_add()
bpy.ops.object.camera_add(location=(0, -8, 0))  # camera exists but scene.camera is never set
