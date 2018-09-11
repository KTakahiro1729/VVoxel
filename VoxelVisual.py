import bpy
import itertools, math
import numpy as np
import os
import datetime
print(np.__version__)
now = datetime.datetime.now
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
    print("start")
    start = now()
    zerostart = np.zeros(np.add(voxel.shape,(2,2,2)))
    zerostart[1:-1,1:-1,1:-1] = voxel
    z_diff = np.diff(zerostart,axis=0)
    y_diff = np.diff(zerostart,axis=1)
    x_diff = np.diff(zerostart,axis=2)

    z_vs = vs(z_diff,"z")
    y_vs = vs(y_diff,"y")
    x_vs = vs(x_diff,"x")
    vs_ = np.concatenate((z_vs,y_vs,x_vs))
    vs_ = np.fliplr(vs_)
    fs = np.arange(len(vs_))
    vs_, fs = remove_doubles(vs_,fs)
    add_obj(vs_,fs.reshape(fs.size//4,4).tolist(),"voxel")
    print("took {0}secs".format((datetime.datetime.now() - start).total_seconds()))
def add_obj(vs,fs,name="voxel"):
    mesh_data = bpy.data.meshes.new(name+"_mesh_data")
    mesh_data.from_pydata(vs,[],fs)
    mesh_data.update()
    obj = bpy.data.objects.new(name+"_object", mesh_data)
    scene = bpy.context.scene
    scene.objects.link(obj)
    obj.select = True

def vs(diff,axis):
    before = now()
    loc=np.mgrid[:diff.shape[0],:diff.shape[1],:diff.shape[2]]
    loc = np.swapaxes(np.rollaxis(loc,0,-1),-1,-2)
    flat_loc = loc.flatten().reshape(loc.size//3,3)
    del loc
    flat_diff = diff.flatten()
    del diff
    skip_loc = flat_loc[flat_diff!=np.array(0)]
    del flat_loc
    skip_loc[:,:-1] = -skip_loc[:,:-1]

    skip_diff = flat_diff[flat_diff != np.array(0)]
    del flat_diff
    minus_idx = np.where(skip_diff == -1)
    del skip_diff
    center_off = np.array({"z":[0.0,0.5,-0.5],"y":[0.5,0.0,-0.5], "x":[0.5,0.5,0.0]}[axis])
    print(1,now()-before)
    before = now()
    centers = np.empty(skip_loc.shape)
    for i in range(3):
        centers[...,i] = skip_loc[...,i] + center_off[i]
    result = np.empty(centers.shape[:-1]+(4,3))
    print(2,now()-before)
    before = now()
    around_off ={'z': [[0, -0.5, 0.5], [0, 0.5, 0.5], [0, 0.5, -0.5], [0, -0.5, -0.5]],
 'y': [[0.5, 0, 0.5], [-0.5, 0, 0.5], [-0.5, 0, -0.5], [0.5, 0, -0.5]],
 'x': [[0.5, -0.5, 0], [0.5, 0.5, 0], [-0.5, 0.5, 0], [-0.5, -0.5, 0]]}[axis]
    for i in range(4):
        for j in range(3):
            result[...,i,j] = around_off[i][j] + centers[...,j]
    print(3,now()-before)
    before = now()
    result[minus_idx] = np.flip(result[minus_idx],1)
    result = result.flatten().reshape(result.size//3,3)
    print(4,now()-before)
    before = now()

    return result
def remove_doubles(vs, fs):
    print("number of verteces: ",len(vs))
    start = now()
    usedvs_index = dict([])
    new_vs = []
    old_new = []

    for i, v in enumerate(vs):
        v = tuple(v)
        if v in usedvs_index.keys():
            old_new.append(old_new[usedvs_index[v]])
        else:
            usedvs_index[v] = i
            old_new.append(len(new_vs))
            new_vs.append(v)
    new_fs = np.vectorize(lambda i:old_new[i])(fs)
    print("number of verteces: ",len(new_vs))
    print("remove doubles took: ",now()-start)
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
