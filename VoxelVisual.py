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
        IntProperty,
        FloatVectorProperty
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
def add_obj(vs,es,fs,name):
    mesh_data = bpy.data.meshes.new(name+"_mesh_data")
    mesh_data.from_pydata(vs,es,fs)
    mesh_data.update()
    obj = bpy.data.objects.new(name+"_object", mesh_data)
    scene = bpy.context.scene
    scene.objects.link(obj)
    return obj
def add_outline(shape, voxel_obj, self):
    vs = np.multiply(list(itertools.product(*[[0,1]]*3)),shape[::-1]).tolist()
    es =  np.matrix("0,1;0,2;0,4;1,3;1,5;2,3;2,6;3,7;4,5;4,6;5,7;6,7").tolist()
    outline_obj = add_obj(vs,es,[],"outline")
    voxel_obj.parent = outline_obj
    voxel_obj.rotation_euler[0] = np.pi
    voxel_obj.location = (0,shape[1],shape[0])
    outline_obj.location = bpy.context.scene.cursor_location
    outline_obj.scale = self.rescale
    return outline_obj

def add_voxel_surface(array3d, self):
    print("start")
    start = now()

    result = calc_vs(array3d, complexity = self.complexity)
    if result == "TOO_MANY_VERTS":
        self.report({"ERROR"},"The voxel is too complex.")
        return result
    vs, fs = result

    # add object to blender
    voxel_obj = add_obj(vs,[],fs,"voxel_surface")
    voxel_obj.select = True
    outline_obj = add_outline(array3d.shape, voxel_obj, self)
    outline_obj.select = True

    print("took {0}secs".format((datetime.datetime.now() - start).total_seconds()))
    return "FINISHED"

def calc_vs(voxel, complexity=10):
    zerostart = np.zeros(np.add(voxel.shape,(2,2,2)),dtype=int)
    zerostart[1:-1,1:-1,1:-1] = voxel
    z_diff = np.diff(zerostart,axis=0)
    if z_diff[z_diff!=0].size > complexity*10000:
        return "TOO_MANY_VERTS"
    y_diff = np.diff(zerostart,axis=1)
    x_diff = np.diff(zerostart,axis=2)

    z_vs = calc_axis_vs(z_diff,"z")
    y_vs = calc_axis_vs(y_diff,"y")
    x_vs = calc_axis_vs(x_diff,"x")
    vs = np.concatenate((z_vs,y_vs,x_vs))
    vs = np.fliplr(vs)
    fs = np.arange(len(vs))
    vs, fs = remove_doubles(vs,fs)
    vs = vs.tolist()
    fs = fs.reshape(fs.size//4,4).tolist()
    return vs, fs

def calc_axis_vs(diff,axis):
    before = now()
    ds = diff.shape
    loc = np.mgrid[:ds[0],:ds[1],:ds[2]].astype(np.uint16)
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
    around_off ={'z': [[0, 0, -1], [0, 0, 0], [0, -1, 0], [0, -1, -1]],
 'y': [[0, 0, 0], [0, 0, -1], [-1, 0, -1], [-1, 0, 0]],
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
    print("number of vertices: ",len(vs))
    start = now()
    new_vs, inverse = np.unique(vs,return_inverse=True,axis=0)
    new_fs = inverse[fs]
    print("number of vertices: ",len(new_vs))
    print("remove doubles took: ",now()-start)
    return new_vs, new_fs

class AddVoxelSurface(bpy.types.Operator,ImportHelper):
    bl_idname  = "object.add_voxel_surface"
    bl_label = "Voxel Surface From .npy"
    bl_description = "outputs the locations of the markers in the 3DView"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".npy"
    filter_glob = StringProperty(default="*.npy", options={'HIDDEN'})

    complexity = IntProperty(name="complexity", description = "Maximum computable complexity voxel", default = 10)
    rescale = FloatVectorProperty(name="rescale", description = "rescale the voxel", default=(1.0,1.0,1.0),subtype="XYZ")
    def execute(self, context):
        import os
        fname = bpy.path.abspath(self.properties.filepath)
        print("reading: ", fname)
        if os.path.isfile(fname):
            array3d = np.load(fname)
            if array3d.dtype != bool:
                self.report({"ERROR"}, "Please set a array of bool. It is currently: {0}".format(array3d.dtype))
                return {"CANCELLED"}
            result = add_voxel_surface(array3d, self)
            if result =="FINISHED":
                return {'FINISHED'}
            else:
                return {"CANCELLED"}
        else:
            self.report({"ERROR"},"No such File")
            return{"CANCELLED"}
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def add_voxel_verts(array3d, self):
    ars = array3d.shape
    locs = np.mgrid[:ars[0],:ars[1],:ars[2]]
    locs = np.moveaxis(locs,0,-1)
    # print(locs)
    # print(ars)
    verts_object = add_obj(np.fliplr(locs[array3d]).tolist(),[],[],"voxel_verts")
    verts_object.select = True
    verts_object.dupli_type = "VERTS"
    # primitive cube that is the min unit
    atom_vs,atom_fs = calc_vs(np.array([[[1]]]))
    atom_obj = add_obj(atom_vs, [], atom_fs, "atomic_cube")
    atom_obj.parent = verts_object

    outline_obj = add_outline(array3d.shape, verts_object, self)
    outline_obj.select = True
    return "FINISHED"
class AddVoxelDupliVerts(bpy.types.Operator,ImportHelper):
    bl_idname  = "object.add_voxel_dupli_verts"
    bl_label = "Voxel Dupliverts From .npy "
    bl_description = "Visualize Voxel From .npy using dupliverts"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".npy"
    filter_glob = StringProperty(default="*.npy", options={'HIDDEN'})

    rescale = FloatVectorProperty(name="rescale", description = "rescale the voxel", default=(1.0,1.0,1.0),subtype="XYZ")
    def execute(self, context):
        import os
        fname = bpy.path.abspath(self.properties.filepath)
        print("reading: ", fname)
        if os.path.isfile(fname):
            array3d = np.load(fname)
            if array3d.dtype != bool:
                self.report({"ERROR"}, "Please set a array of bool. It is currently: {0}".format(array3d.dtype))
                return {"CANCELLED"}
            result = add_voxel_verts(array3d, self)
            return {'FINISHED'}
        else:
            self.report({"ERROR"},"No such File")
            return{"CANCELLED"}
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_fn(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.separator()
    self.layout.operator(AddVoxelSurface.bl_idname)
    self.layout.operator(AddVoxelDupliVerts.bl_idname)
def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_add.append(menu_fn)

def unregister():
    bpy.types.INFO_MT_add.remove(menu_fn)
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
