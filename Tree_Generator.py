import bpy
import math
import numpy as np
import random
from dataclasses import dataclass, field

def draw_line(start, end, col):
    # create a new data block for a 3D curve (Z=0)
    curve_data = bpy.data.curves.new('BranchCurve', type='CURVE')
    curve_data.dimensions = '3D'

    # add a line segment (polyline spline) with 2 points
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(1) # Adds the second point (it starts with 1)

    # the start vector coordinates (X, Y, Z=0.0, W=1.0)
    polyline.points[0].co = (start[0], start[1], start[2], 1.0)

    # the end vector coordinates (X, Y, Z=0.0, W=1.0)
    polyline.points[1].co = (end[0], end[1], end[2], 1.0)

    # link the newly made line into the visible 3D scene
    obj = bpy.data.objects.new('branch', curve_data)
    obj.color = (col[0], col[1], col[2], 1.0)
    bpy.context.collection.objects.link(obj)

# global variable, position of the whole tree or for root node
START_POS = np.array([0,0,0]) 
max_length = 2
# stop_cond is a condition when recursion should stop. Each iteration do generation++
stop_cond = 8

@dataclass
class TreeNode:
    elevation: float
    azimuth: float
    length: float
    children: list['TreeNode'] = field(default_factory=list)

    # recursion func
    def grow_tree(self, generation):
        if generation == stop_cond:
            return
        else:
            new_elevation = random.randint(0, 30)
            new_azimuth = random.randint(0, 359)
            new_length = max_length - (max_length * generation / 10)

            self.children.append(TreeNode(new_elevation, new_azimuth + 360/2 * 0, new_length))
            self.children.append(TreeNode(new_elevation, new_azimuth + 360/2 * 1, new_length))
            for child in self.children:
                child.grow_tree(generation + 1)

'''
def draw_tree2(node, pos):
    x = node.length * math.sin(np.deg2rad(node.elevation)) * math.cos(np.deg2rad(node.azimuth))
    y = node.length * math.sin(np.deg2rad(node.elevation)) * math.sin(np.deg2rad(node.azimuth))
    z = node.length * math.cos(np.deg2rad(node.elevation))
    anchor = pos + np.array([x, y, z])

    #draw_line(pos, pos+(0, 0, 1), (1, 0, 0))
    draw_line(pos, anchor, (0, 0, 0))

    for child in node.children:
        draw_tree2(child, anchor)
'''

def draw_tree(node, pos, parent_dir=np.array([0, 0, 1])):
    parent_normal = parent_dir

    arbitrary = np.array([0, 0, 1])
    if abs(np.dot(parent_normal, arbitrary)) > 0.95:
        arbitrary = np.array([0, 1, 0])

    parent_perpendicular = np.cross(parent_normal, arbitrary)
    parent_perpendicular = parent_perpendicular / np.linalg.norm(parent_perpendicular)

    our_normal = parent_normal
    our_normal = rotate_by_axis(our_normal, parent_perpendicular, node.elevation)
    our_normal = rotate_by_axis(our_normal, parent_normal, node.azimuth)

    anchor = pos + our_normal * node.length
    '''
    x = node.length * math.sin(np.deg2rad(node.elevation)) * math.cos(np.deg2rad(node.azimuth))
    y = node.length * math.sin(np.deg2rad(node.elevation)) * math.sin(np.deg2rad(node.azimuth))
    z = node.length * math.cos(np.deg2rad(node.elevation))
    anchor = pos + np.array([x, y, z])
    '''

    # create a new data block for a 3D curve (Z=0)
    curve_data = bpy.data.curves.new('BranchCurve', type='CURVE')
    curve_data.dimensions = '3D'

    # add a line segment (polyline spline) with 2 points
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(1) # Adds the second point (it starts with 1)

    # the start vector coordinates (X, Y, Z=0.0, W=1.0)
    polyline.points[0].co = (pos[0], pos[1], pos[2], 1.0)

    # the end vector coordinates (X, Y, Z=0.0, W=1.0)
    polyline.points[1].co = (anchor[0], anchor[1], anchor[2], 1.0)

    # link the newly made line into the visible 3D scene
    obj = bpy.data.objects.new('branch', curve_data)
    bpy.context.collection.objects.link(obj)

    for child in node.children:
        draw_tree(child, anchor,our_normal)

def rotate_by_axis(vec, axis_vec, ang):
    vector = np.array(vec)
    axis = np.array(axis_vec)
    angle = np.radians(ang)

    # normalize the axis
    axis = axis / np.linalg.norm(axis)

    rotated = (
        vector * np.cos(angle) + np.cross(axis, vector) * np.sin(angle) + axis * np.dot(axis, vector) * (1 - np.cos(angle))
    )

    return rotated

# delete previously generated curves
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='CURVE')
bpy.ops.object.delete()

root = TreeNode(0, 0, max_length)
root.grow_tree(0)
draw_tree(root, START_POS)