import bpy
import math
import numpy as np
import random
import bmesh
from dataclasses import dataclass, field

# position of the whole tree
START_POS = np.array([0,0,0])
max_length = 2
# condition when recursion should stop
stop_cond = 6

@dataclass
class TreeNode:
    elevation: float # angle, how much a branch bends away from its parent
    azimuth: float # angle, which direction the branch points
    length: float
    children: list['TreeNode'] = field(default_factory=list)

    # logic
    def grow_tree(self, generation):
        if generation == stop_cond:
            return
        else:
            new_length = max_length - (max_length * generation / 10)
            children_num = random.randint(1, 3)
            for child in range(children_num):
                new_elevation = random.randint(10, 35)
                base_azimuth = random.randint(0, 359)
                new_azimuth = base_azimuth + 360/children_num * child + random.uniform(-20, 20)
                self.children.append(TreeNode(new_elevation, new_azimuth, new_length * random.uniform(0.7, 1.3)))
            
            for child in self.children:
                child.grow_tree(generation + 1)
# tree drawing
def draw_tree(node, pos, generation, bm, skin_layer, v_start=None, parent_dir=np.array([0, 0, 1])):
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
    radius = max(0.02, 0.2 - (0.2 * generation / stop_cond))
    v_end[skin_layer].radius = (radius, radius)

    # make an edge from start vertex to end vertex
    bm.edges.new([v_start, v_end])

    for child in node.children:
        draw_tree(child, anchor, generation + 1, bm, skin_layer, v_end, child_normal)        

def rotate_by_axis(vec, axis_vec, ang):
    vector = np.array(vec)
    axis = np.array(axis_vec)
    angle = np.radians(ang)
    axis = axis / np.linalg.norm(axis)
    rotated = (
        vector * np.cos(angle) + np.cross(axis, vector) * np.sin(angle) + axis * np.dot(axis, vector) * (1 - np.cos(angle))
    )
    return rotated

# delete previously generated meshes
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

root = TreeNode(0, 0, max_length)
root.grow_tree(0)

tree_mesh = bpy.data.meshes.new('Tree_mesh')  # add a new mesh
bm = bmesh.new() # make a new BMesh (draft) 

tree_obj = bpy.data.objects.new('Tree_object', tree_mesh)  # add a new object using the mesh
bpy.context.collection.objects.link(tree_obj)

# select and make active
bpy.context.view_layer.objects.active = tree_obj
tree_obj.select_set(True)

skin_layer = bm.verts.layers.skin.verify()
draw_tree(root, START_POS, 0, bm, skin_layer)

bm.to_mesh(tree_mesh) # put draft into tree_mesh mesh 
bm.free() # delete draft
tree_mesh.update()
tree_mesh.skin_vertices[0].data[0].use_root = True
bpy.ops.object.modifier_add(type='SKIN')