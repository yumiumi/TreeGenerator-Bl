bl_info = {
    "name": "Tree Generator",
    "author": "Yumi",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "category": "Add Mesh",
}
import bpy
import os
import math
import numpy as np
import random
import bmesh
from dataclasses import dataclass, field

START_POS = np.array([0,0,0])
max_length = 2

@dataclass
class TreeNode:
    elevation: float # angle, how much a branch bends away from its parent
    azimuth: float # angle, which direction the branch points
    length: float
    children: list['TreeNode'] = field(default_factory=list)
    # logic
    def grow_tree(self, generation, settings):
        current_gen = [self]
        for g in range(settings.stop_cond):
            next_gen = []
            for this_node in current_gen:
                new_length = max_length - (max_length * g/10)
                children_num = random.randint(1,3)
                for child in range(children_num):
                    new_elevation = random.randint(10, 35)
                    base_azimuth = random.randint(0, 359)
                    new_azimuth = base_azimuth + 360/children_num * child + random.uniform(-20, 20)
                    new_node = TreeNode(new_elevation, new_azimuth, new_length * random.uniform(0.7, 1.3))
                    this_node.children.append(new_node)
                    next_gen.append(new_node)
            current_gen = next_gen

# tree drawing
def draw_tree(node, pos, generation, bm, skin_layer, settings, v_start=None, parent_dir=np.array([0, 0, 1])):
    parent_normal = parent_dir
    # vector to find a perpendicular axis
    arbitrary = np.array([0, 0, 1])
    # if parent_normal is nearly parallel to arbitrary, cross product would break
    # so swap to a different arbitrary vector
    if abs(np.dot(parent_normal, arbitrary)) > 0.95:
        arbitrary = np.array([0, 1, 0])
    # perpendicular axis to parent, used as rotation axis for elevation
    parent_perpendicular = np.cross(parent_normal, arbitrary)
    parent_perpendicular = parent_perpendicular / np.linalg.norm(parent_perpendicular)
    child_normal = parent_normal
    child_normal = rotate_by_axis(child_normal, parent_perpendicular, node.elevation)
    child_normal = rotate_by_axis(child_normal, parent_normal, node.azimuth)
    anchor = pos + child_normal * node.length
    
    # v_start is None only on the very first call (the root)
    if v_start is None:
        v_start = bm.verts.new(pos)
        v_start[skin_layer].radius = (0.2, 0.2) # root thickness
    
    # end vertex of this branch
    v_end = bm.verts.new(anchor)
    radius = max(0.02, 0.2 - (0.2 * generation / settings.stop_cond))
    v_end[skin_layer].radius = (radius, radius)
    bm.edges.new([v_start, v_end])

    for child in node.children:
        draw_tree(child, anchor, generation + 1, bm, skin_layer, settings, v_end, child_normal)        

def rotate_by_axis(vec, axis_vec, ang):
    vector = np.array(vec)
    axis = np.array(axis_vec)
    angle = np.radians(ang)
    axis = axis / np.linalg.norm(axis)
    rotated = (
        vector * np.cos(angle) + np.cross(axis, vector) * np.sin(angle) + axis * np.dot(axis, vector) * (1 - np.cos(angle))
    )
    return rotated

# hardcode path for now
# find material for bark
def append_material():
    addon_dir = os.path.dirname(__file__)
    blend_path = "/home/yumi/Desktop/scr_blpy/tree_material.blend"
    #blend_path = os.path.join(addon_dir, "tree_material.blend")
    with bpy.data.libraries.load(blend_path) as (data_from, data_to):
        data_to.materials = ["Bark_Material"]
    print("Loaded material:", bpy.data.materials.keys())
    print(blend_path)

def rebuild_tree(self, context):
    random.seed(self.seed)
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()
    
    root = TreeNode(0, 0, max_length)
    root.grow_tree(0, self)
    
    old_mesh = bpy.data.meshes.get("Tree_mesh")
    if old_mesh:
        bpy.data.meshes.remove(old_mesh)
    
    tree_mesh = bpy.data.meshes.new('Tree_mesh')  # add a new mesh
    bm = bmesh.new() # make a new BMesh (draft) 

    tree_obj = bpy.data.objects.new('Tree_object', tree_mesh)  # add a new object using the mesh
    bpy.context.collection.objects.link(tree_obj)

    # select and make active
    bpy.context.view_layer.objects.active = tree_obj
    tree_obj.select_set(True)

    skin_layer = bm.verts.layers.skin.verify()
    draw_tree(root, START_POS, 0, bm, skin_layer, self)

    bm.to_mesh(tree_mesh) # put draft into tree_mesh mesh 
    bm.free() # delete draft
    tree_mesh.update()
    tree_mesh.skin_vertices[0].data[0].use_root = True
    bpy.ops.object.modifier_add(type='SKIN')
    
class TreeSettings_UI(bpy.types.PropertyGroup):
    stop_cond: bpy.props.IntProperty(
    name="Generations",
    default=6,
    min=1,
    max=10,
    update=rebuild_tree
    )
    seed: bpy.props.IntProperty(
    name="Seed",
    default=10,
    min=0,
    max=999999,
    update=rebuild_tree
    )
   
append_material() 

# the visible UI panel
class Tree_PT_panel(bpy.types.Panel):
    bl_label = "Tree Generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tree"
    
    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.tree_settings, "stop_cond")
        layout.prop(context.scene.tree_settings, "seed")

def register():
    bpy.utils.register_class(TreeSettings_UI)
    bpy.types.Scene.tree_settings = bpy.props.PointerProperty(type=TreeSettings_UI)
    bpy.utils.register_class(Tree_PT_panel)

def unregister():
    bpy.utils.unregister_class(Tree_PT_panel)
    del bpy.types.Scene.tree_settings
    bpy.utils.unregister_class(TreeSettings_UI)
    
if __name__ == "__main__":
    register()