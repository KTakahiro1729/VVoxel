import bpy
from bpy_extras.io_utils import ImportHelper
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
    add_obj(vs_.tolist(),fs.reshape(fs.size//4,4).tolist(),"voxel")
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
    ds = diff.shape
    loc = np.mgrid[ds[0]-1:-1:-1,ds[1]-1:-1:-1,:ds[2]].astype(np.uint16)
    loc = np.swapaxes(np.rollaxis(loc,0,-1),-1,-2)
    flat_loc = loc.flatten().reshape(loc.size//3,3)
    del loc
    flat_diff = diff.flatten()
    del diff
    skip_loc = flat_loc[flat_diff!=np.array(0)]
    del flat_loc

    skip_diff = flat_diff[flat_diff != np.array(0)]
    del flat_diff
    minus_idx = np.where(skip_diff == -1)
    del skip_diff
    print(1,now()-before)
    before = now()
    result = np.empty(skip_loc.shape[:-1]+(4,3)).astype(np.uint16)
    around_off ={'z': [[0, -1, 0], [0, 0, 0], [0, 0, -1], [0, -1, -1]],
 'y': [[0, 0, 0], [-1, 0, 0], [-1, 0, -1], [0, 0, -1]],
 'x': [[0, -1, 0], [0, 0, 0], [-1, 0, 0], [-1, -1, 0]]}[axis]
    for i in range(4):
        for j in range(3):
            result[...,i,j] = around_off[i][j] + skip_loc[...,j]
    print(2,now()-before)
    before = now()
    result[minus_idx] = np.flip(result[minus_idx],1)
    result = result.flatten().reshape(result.size//3,3)
    print(3,now()-before)
    before = now()
    return result
def remove_doubles(vs,fs):
    print("number of verteces: ",len(vs))
    start = now()
    new_vs, inverse = np.unique(vs,return_inverse=True,axis=0)
    new_fs = inverse[fs]
    print("number of verteces: ",len(new_vs))
    print("remove doubles took: ",now()-start)
    return new_vs, new_fs

class AddVoxel(bpy.types.Operator,ImportHelper):
    bl_idname  = "object.add_voxel"
    bl_label = "Voxel From .npy"
    bl_description = "outputs the locations of the markers in the 3DView"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".npy"
    filter_glob = StringProperty(default="*.npy", options={'HIDDEN'})


    def execute(self, context):
        import os
        fname = bpy.path.abspath(self.properties.filepath)
        print(fname)
        if os.path.isfile(fname):
            array3d = np.load(fname)
            add_voxel(array3d)
        return {'FINISHED'}
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


        return {"FINISHED"}
def menu_fn(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
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
