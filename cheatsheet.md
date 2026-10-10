# Blender 5.0 to 5.2 API changes

Sources (official Blender release notes only):
- 5.0: https://developer.blender.org/docs/release_notes/5.0/python_api/ · https://developer.blender.org/docs/release_notes/5.0/compositor/ · https://developer.blender.org/docs/release_notes/5.0/rendering/ · https://developer.blender.org/docs/release_notes/5.0/animation_rigging/ · https://developer.blender.org/docs/release_notes/5.0/geometry_nodes/
- 5.1: https://developer.blender.org/docs/release_notes/5.1/python_api/ · https://developer.blender.org/docs/release_notes/5.1/compositor/ · https://developer.blender.org/docs/release_notes/5.1/rendering/ · https://developer.blender.org/docs/release_notes/5.1/animation_rigging/ · https://developer.blender.org/docs/release_notes/5.1/geometry_nodes/
- 5.2: https://developer.blender.org/docs/release_notes/5.2/python_api/ · https://developer.blender.org/docs/release_notes/5.2/compositor/ · https://developer.blender.org/docs/release_notes/5.2/rendering/ · https://developer.blender.org/docs/release_notes/5.2/animation_rigging/ · https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/

## Materials and worlds always use nodes (5.0)

- "Use Nodes" was removed for materials and worlds; they always use nodes. `material.use_nodes` and `world.use_nodes` are deprecated (removal planned for 6.0): they always return `True` and setting them has no effect.
- Creating the data-block now creates the default node tree:

```python
# Old
mat = bpy.data.materials.new("MyMaterial")
mat.use_nodes = True  # created the default node tree

# New
mat = bpy.data.materials.new("MyMaterial")  # default node tree is created here

# Old
scene.world = bpy.data.worlds.new("MyWorld")
scene.world.use_nodes = True  # created the default nodes

# New
scene.world = bpy.data.worlds.new("MyWorld")  # default nodes are created here
```

## Compositor node tree (5.0)

- `scene.node_tree` was removed. Use `scene.compositing_node_group`. The compositing node tree is its own data-block: a `CompositorNodeTree` node group assigned to the scene.
- `scene.use_nodes` is deprecated (removal planned for 6.0). It always returns `True`, setting it has no effect, and it no longer creates a node tree.
- The Composite node was removed. The compositor result is a Group Output node (`NodeGroupOutput`) whose first input must be a Color socket; other inputs are ignored.
- Most nodes now expose their options as input sockets (menu, value and boolean inputs), and most node options deprecated in 4.5 were removed. For example, the Blur node's filter type and size are its `Type` and `Size` inputs (`blur.filter_type`, `blur.size_x` and `blur.size_y` were removed), and the Glare node's type, quality, threshold and size are inputs too (`glare.glare_type` and similar properties were removed).

```python
# Old
scene.use_nodes = True  # node tree with default nodes was created here
blur = scene.node_tree.nodes.new("CompositorNodeBlur")
blur.filter_type = 'GAUSS'
blur.size_x = 10

# New
tree = bpy.data.node_groups.new("MyGroup", "CompositorNodeTree")
scene.compositing_node_group = tree
rlayers = tree.nodes.new(type="CompositorNodeRLayers")
blur = tree.nodes.new(type="CompositorNodeBlur")
blur.inputs["Type"].default_value = "Gaussian"
blur.inputs["Size"].default_value = (10, 10)
output = tree.nodes.new(type="NodeGroupOutput")
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
tree.links.new(blur.inputs["Image"], rlayers.outputs["Image"])
tree.links.new(output.inputs["Image"], blur.outputs["Image"])
```

## Compositor nodes (5.0 to 5.2)

- Many compositor nodes were removed in favor of their Shader Node counterparts, which are used directly in the compositor tree:

```python
# Old
n = scene.node_tree.nodes.new("CompositorNodeGamma")
# New
n = tree.nodes.new("ShaderNodeGamma")
```

- Other compositor node types that no longer exist on 5.2 and their shader counterparts: `CompositorNodeMixRGB` → `ShaderNodeMix`, `CompositorNodeMath` → `ShaderNodeMath`, `CompositorNodeValToRGB` → `ShaderNodeValToRGB`, `CompositorNodeMapRange` → `ShaderNodeMapRange`, `CompositorNodeValue` → `ShaderNodeValue`.
- Removed: the Texture node, the Dot output of the Normal node (use a Vector Math Dot Product node), and the scale inputs of the Displace node.
- Renamed sockets: the Color node output `"RGBA"` is now `"Color"`; the Alpha Over inputs are now `"Background"` and `"Foreground"`; the Lift inputs of the Color Correction node are now Offset.
- The Z Combine node was renamed Depth Combine (type name still `CompositorNodeZcombine`).
- 5.2: the Image Coordinates node's Pixel output and the Image Info node's Dimensions and Resolution outputs are now Integer Vector sockets.
- File Output node: `file_slots`, `layer_slots` and `base_path` were removed. Use `directory`, `file_name` and `file_output_items` (`file_output_node.file_output_items[0].name = "..."`).

## Shader nodes and rendering (5.0 to 5.2)

- Deprecated Combine and Separate nodes were removed.
- The Point Density texture node was removed.
- The Sky Texture node has a new multiple scattering mode (`sky_type = 'MULTIPLE_SCATTERING'`).
- 5.2: the Principled BSDF has a new boolean input "Thin Wall".
- The EEVEE render engine identifier changed from `BLENDER_EEVEE_NEXT` to `BLENDER_EEVEE`.
- `scene.eevee.gtao_distance` moved to the view layer and was renamed `view_layer.eevee.ambient_occlusion_distance`. `scene.eevee.use_gtao` and `scene.eevee.gtao_quality` were removed.
- Many render passes were renamed to avoid abbreviations, for example `DiffCol` to `Diffuse Color` and `Z` to `Depth` (also the Render Layers node outputs).
- `ImageFormatSettings` has a `media_type` member that must be set before `file_format`.

## Animation: legacy Action API removed (5.0)

- `action.fcurves`, `action.groups` and `action.id_root` were removed. Actions are layered: F-Curves live in a channelbag, one per action slot. `action.id_root` is replaced by `action_slot.target_id_type`.
- `action_slot` is the slot assigned to the animated data-block, for example `obj.animation_data.action_slot` (the action itself is `obj.animation_data.action`).
- Use `bpy_extras.anim_utils` to get or create the channelbag for a slot:

```python
from bpy_extras import anim_utils

# Old: finding
fcurve = action.fcurves.find("location", index=2)
# New: finding
channelbag = anim_utils.action_get_channelbag_for_slot(action, action_slot)
fcurve = channelbag.fcurves.find("location", index=2)

# Old: creating
fcurve = action.fcurves.new("location", index=2, action_group="MyGroup")
# New: creating (creates a layer and keyframe strip if needed)
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, action_slot)
fcurve = channelbag.fcurves.new("location", index=2, group_name="MyGroup")

# Old: ensuring the F-Curve exists
fcurve = action.fcurves.find("location", index=2, action_group="MyGroup")
if not fcurve:
    fcurve = action.fcurves.new("location", index=2, action_group="MyGroup")
# New: ensuring the F-Curve exists
channelbag = anim_utils.action_ensure_channelbag_for_slot(action, action_slot)
fcurve = channelbag.fcurves.ensure("location", index=2, group_name="MyGroup")
```

- The group parameter is now `group_name` (it was `action_group`): the group's name, not a reference to the group. Use `channelbag.groups` instead of `action.groups`. `action.fcurve_ensure_for_datablock()` also takes `group_name`.
- Creating a driver from Python (`driver_add()`) no longer adds an F-Curve modifier; the driver F-Curve gets 2 keyframes instead.
- The `INSERTKEY_XYZ_TO_RGB` flag for `keyframe_insert()`'s `options` parameter was removed.
- `context.space_data.action` was removed from the Dope Sheet context. Use `context.active_action`.
- The `action.layer_prev` and `action.layer_next` operators were removed. 5.1: the `anim.convert_legacy_action` operator was removed (all actions are layered).
- Bones: visibility and selection in Object and Pose mode are stored on the pose bone: `pose_bone.hide` and `pose_bone.select` (`bone.hide` on the armature now affects edit bones). `bone.select`, `bone.select_head` and `bone.select_tail` were removed; use the edit bone's properties.
- "Copy Global Transform" is built in, no longer an add-on. Its old add-on properties are now registered on `scene.tool_settings`.

## Geometry Nodes (5.0 to 5.2)

- 5.2: Geometry Nodes modifier inputs and output attribute names are no longer custom properties on the modifier. They are RNA properties under `modifier.properties`, and dict-style access no longer works.

```python
# Before
modifier["identifier"] = 5.0
modifier["identifier_use_attribute"] = True
modifier["identifier_attribute_name"] = "some_input_attribute"
modifier["identifier_attribute_name"] = "some_output_attribute"

# After
modifier.properties.inputs.identifier.value = 5.0
modifier.properties.inputs.identifier.type = "ATTRIBUTE"
modifier.properties.inputs.identifier.attribute_name = "some_input_attribute"
modifier.properties.outputs.identifier.attribute_name = "some_output_attribute"
```

- `identifier` is the socket identifier of the node group's interface item. Tree interface items can be looked up by identifier (`group.interface.items_tree[identifier]`). When the identifier is held in a variable, use `getattr`:

```python
group = bpy.data.node_groups.new("MyGroup", "GeometryNodeTree")
item = group.interface.new_socket("Value", in_out="INPUT", socket_type="NodeSocketFloat")
modifier = cube.modifiers.new("MyGroup", "NODES")
modifier.node_group = group
getattr(modifier.properties.inputs, item.identifier).value = 1.5
```

- 5.2: socket identifiers of the Compare and Random Value nodes changed. Code that relies on their old identifiers needs updating.
- 5.0: some built-in nodes have menu input sockets instead of node properties (for example the Transform node's `Mode` input).
- 5.1: the String to Curves node options were promoted to input sockets, including a new Font socket (`node.font`, `node.align_x`, `node.overflow` and similar properties were removed).

## Properties defined by add-ons (5.0)

- Properties defined with `bpy.props` (for example Cycles' scene settings) are no longer stored with user custom properties and cannot be reached with dict-style access. `bpy.context.scene['cycles']` does not give access to Cycles settings; use the attribute (`scene.cycles`).
- Resetting such a property: `obj.property_unset('cycles')` (not `del obj['cycles']`).

## Modeling and mesh (5.0)

- The `"FAST"` boolean solver was renamed to `"FLOAT"` (Boolean modifier and boolean operator).
- UV selection is shared between all UV maps. `MeshUVLoopLayer.vertex_selection`, `MeshUVLoopLayer.edge_selection`, `bmesh.types.BMLoopUV.select` and `bmesh.types.BMLoopUV.select_edge` were removed. New: `BMLoop.uv_select_vert`, `BMLoop.uv_select_edge`, `BMFace.uv_select` and related `*_set()` methods.
- The UV layer `pin` property no longer creates its attribute when accessed; use `uv_layer.pin_ensure()`.

## Grease Pencil and annotations (5.0)

- `bpy.types.GreasePencilv3` is now `bpy.types.GreasePencil`, and `bpy.data.grease_pencils_v3` is now `bpy.data.grease_pencils`.
- The old annotation types were renamed: `GreasePencil` to `Annotation`, `GPencilLayer` to `AnnotationLayer`, `GPencilFrame` to `AnnotationFrame`, `GPencilStroke` to `AnnotationStroke`, `GPencilStrokePoint` to `AnnotationStrokePoint`. `Scene.grease_pencil` and `NodeTree.grease_pencil` are now `Scene.annotation` and `NodeTree.annotation`.

## Python and mathutils

- 5.1: Blender's Python is 3.13.
- 5.0: `mathutils` types support the buffer protocol; the underlying type of `Vector` and the others is `float32` (was `float64`).
- 5.2: `mathutils` types (`Vector`, `Matrix`, `Color`, `Euler`) and Blender arrays support slice steps, for example `vector[begin:end:step]`.
- 5.2: `bpy.data.all_ids` iterates over all data-blocks.
