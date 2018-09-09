import bpy
import itertools, math
import numpy as np
import os
from bpy_extras.io_utils import ExportHelper
from bpy.props import (
        StringProperty,
        CollectionProperty,
        )
from bpy.types import (
        Operator,
        OperatorFileListElement,
        )
bl_info = {
    "name" : "VVoxel",
    "author" : "Allosteric",
    "version" : (1,0),
    "blender" : (2, 79, 0),
    "location" : "3DView > Object",
    "description" : "read numpy array and add voxel",
    "warning" : "",
    "support" : "TESTING",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "Object",
}


def add_voxel(voxel):
    zerostart = np.zeros(np.add(voxel.shape,(2,2,2)))
    zerostart[1:-1,1:-1,1:-1] = voxel
    z_diff = np.diff(zerostart,axis=0)
    y_diff = np.diff(zerostart,axis=1)
    x_diff = np.diff(zerostart,axis=2)
    vs = []
    vs.append(add_planes(z_diff, "z"))
    vs.append(add_planes(y_diff, "y"))
    vs.append(add_planes(x_diff, "x"))
    vs = list(itertools.chain(*[i for i in itertools.chain(*vs) if i != None]))
    fs = np.arange(len(vs)).reshape(len(vs)//4,4)
    vs, fs = remove_doubles(vs,fs)
    add_obj(vs,fs,"voxel")
def add_obj(vs,fs,name="voxel"):
    mesh_data = bpy.data.meshes.new(name+"_mesh_data")
    mesh_data.from_pydata(vs,[],fs)
    mesh_data.update()
    obj = bpy.data.objects.new(name+"_object", mesh_data)
    scene = bpy.context.scene
    scene.objects.link(obj)
def add_planes(normals_array, axis):
    ns = normals_array.shape
    z,y,x = np.mgrid[:ns[0],:ns[1],:ns[2]]
    vs = np.vectorize(add_plane)(x,y,z,axis,normals_array).flatten()

    return vs
def add_plane(x,y,z,axis,normal):
    if axis == "x":
        offset = (0,-0.5,-0.5)
    elif axis == "y":
        offset = (-0.5, 0, -0.5)
    elif axis == "z":
        offset = (-0.5,-0.5,0)
    loc = np.multiply((1,-1,-1), np.add((x,y,z),offset))
    if normal != 0:
        return add_face(loc, axis, normal)
def parse_offset(offs):
    dict_ = {"0":0,"+":0.5,"-":-0.5}
    return [tuple(dict_[i] for i in off) for off in offs.split(";")]
def add_face(loc, axis, normal):
    if axis == "x":
        v_offs = parse_offset("0-+;0++;0+-;0--")
    elif axis == "y":
        v_offs = parse_offset("+0+;+0-;-0-;-0+")
    elif axis == "z":
        v_offs = parse_offset("+-0;++0;-+0;--0")
    if normal == -1:
        v_offs = v_offs[::-1]
    vs = [add_vec(loc,v_off) for v_off in v_offs]
    return vs

def add_vec(x,y):
    return tuple(x[i]+y[i] for i in range(len(x)))
def remove_doubles(vs, fs):
    usedvs_index = dict([])
    new_vs = []
    old_new = []
    for i, v in enumerate(vs):
        if v in usedvs_index.keys():
            old_new.append(old_new[usedvs_index[v]])
        else:
            usedvs_index[v] = i
            old_new.append(len(new_vs))
            new_vs.append(v)
    new_fs = [tuple(old_new[v] for v in f) for f in fs]

    return new_vs, new_fs

class AddVoxel(bpy.types.Operator):
    bl_idname  = "object.add_voxel"
    bl_label = "Voxel From .npy"
    bl_description = "outputs the locations of the markers in the 3DView"
    bl_options = {"REGISTER", "UNDO"}

    # files = CollectionProperty(
    #         name="File Path",
    #         type=OperatorFileListElement,
    #         )
    fname = StringProperty(
            subtype='FILE_PATH',
            )

    filename_ext = ""

    def execute(self, context):
        import os
        fname = bpy.path.abspath(self.fname)
        if os.path.isfile(fname):
            array3d = np.load(fname)
            add_voxel(array3d)
        return {'FINISHED'}
    #
    # def execute(self, context):
    #     # read .npy
    #     directory = self.directory
    #     # filename =self.array3d_fname
    #     filename = "temp.npy"
    #     print(self.new_num)
    #     array3d = np.load(filename)
    #     add_voxel(array3d)



        return {"FINISHED"}
def menu_fn(self, context):
    self.layout.separator()
    self.layout.operator(AddVoxel.bl_idname)
def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_add.append(menu_fn)

def unregister():
    bpy.types.INFO_MT_add.remove(menu_fn)
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
