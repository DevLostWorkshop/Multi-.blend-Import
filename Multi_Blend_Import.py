bl_info = {
    "name": "Multi-.blend Import",
    "category": "Import-Export"
    "author": "The Supreme Sage",
    "version": (1, 5),
    "blender": (4, 4, 3),
    "location": "File > Import > Multi-.blend Import",
    "description": "Import multiple .blend file's objects into current scene",
    "tracker_url": "https://github.com/DevLostWorkshop/Multi-.blend-Import/issues"
}

import bpy
import os
from bpy.types import Operator, PropertyGroup
from bpy.props import StringProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper

class MultiBlendFile(PropertyGroup):
    name: StringProperty(name="File Path", subtype='FILE_PATH')

class MultiBlendAddFileOperator(Operator, ImportHelper):
    """Add a .blend file to the import list"""
    bl_idname = "import_scene.multi_blend_add_file"
    bl_label = "Select .blend Files"
    bl_options = {'INTERNAL'}

    filename: StringProperty(
        name="File Name",
        subtype='FILE_NAME',
        default=""
    )
    files: CollectionProperty(
        name="Files",
        type=bpy.types.OperatorFileListElement
    )
    directory: StringProperty(
        subtype='DIR_PATH',
        default=""
    )

    def execute(self, context):
        file_list = context.scene.multi_blend_files
        # Process multiple selected files
        for file in self.files:
            file_path = os.path.normpath(os.path.join(self.directory, file.name))
            if file_path.lower().endswith(".blend") and os.path.isfile(file_path):
                if not any(os.path.normpath(f.name) == file_path for f in file_list):
                    f = file_list.add()
                    f.name = file_path
                    self.report({'INFO'}, f"Added file: {file.name}")
                else:
                    self.report({'WARNING'}, f"File already added: {file.name}")
            else:
                self.report({'WARNING'}, f"Invalid file: {file.name}")
        return {'FINISHED'}

    def invoke(self, context, event):
        self.directory = ""
        self.filename = ""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class MultiBlendRemoveFileOperator(Operator):
    """Remove a file from the import list"""
    bl_idname = "import_scene.multi_blend_remove_file"
    bl_label = "Remove File"
    bl_options = {'INTERNAL'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        file_list = context.scene.multi_blend_files
        if 0 <= self.index < len(file_list):
            file_list.remove(self.index)
        return {'FINISHED'}

class MultiBlendImportOperator(Operator):
    """Import all objects from selected .blend files"""
    bl_idname = "import_scene.multi_blend"
    bl_label = "Multi-.blend Import"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        file_paths = [file.name for file in context.scene.multi_blend_files if file.name]
        
        if not file_paths:
            self.report({'ERROR'}, "No files selected")
            return {'CANCELLED'}

        for file_path in file_paths:
            if not os.path.exists(file_path):
                self.report({'WARNING'}, f"File not found: {file_path}")
                continue
            try:
                with bpy.data.libraries.load(file_path, link=False) as (data_from, data_to):
                    data_to.objects = data_from.objects
                for obj in data_to.objects:
                    if obj is not None:
                        bpy.context.collection.objects.link(obj)
            except Exception as e:
                self.report({'WARNING'}, f"Failed to import {os.path.basename(file_path)}: {str(e)}")

        self.report({'INFO'}, f"Imported objects from {len(file_paths)} file(s)")
        context.scene.multi_blend_files.clear()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.scene.multi_blend_files.clear()
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Selected .blend Files:")
        file_list = context.scene.multi_blend_files
        for i, file in enumerate(file_list):
            row = layout.row()
            row.label(text=os.path.basename(os.path.normpath(file.name)))
            row.operator("import_scene.multi_blend_remove_file", text="", icon="X").index = i
        layout.operator("import_scene.multi_blend_add_file", text="Add .blend Files")
        layout.separator()
        layout.label(text="Click OK to import from all files")

def menu_func_import(self, context):
    self.layout.operator(
        MultiBlendImportOperator.bl_idname,
        text="Multi-.blend Import",
    )

def register():
    bpy.utils.register_class(MultiBlendFile)
    bpy.utils.register_class(MultiBlendAddFileOperator)
    bpy.utils.register_class(MultiBlendRemoveFileOperator)
    bpy.utils.register_class(MultiBlendImportOperator)
    bpy.types.Scene.multi_blend_files = CollectionProperty(
        type=MultiBlendFile,
        options={'HIDDEN'}
    )
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    del bpy.types.Scene.multi_blend_files
    bpy.utils.unregister_class(MultiBlendImportOperator)
    bpy.utils.unregister_class(MultiBlendRemoveFileOperator)
    bpy.utils.unregister_class(MultiBlendAddFileOperator)
    bpy.utils.unregister_class(MultiBlendFile)

if __name__ == "__main__":
    register()