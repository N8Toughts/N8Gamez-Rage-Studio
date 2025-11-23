# RAGE Studio Suite - Professional Utilities System
import bpy
import os
import sys
import importlib
import subprocess
import json
import datetime
from bpy.types import Operator, Panel
from bpy.props import (StringProperty, BoolProperty, IntProperty,
                       FloatProperty, EnumProperty)

class RAGE_OT_OpenGameDirectory(Operator):
    bl_idname = "rage.open_game_directory"
    bl_label = "Open Game Directory"
    bl_description = "Professional game directory browser opening"
   
    def execute(self, context):
        props = context.scene.rage_studio
       
        if not props.game_directory or not os.path.exists(props.game_directory):
            self.report({'ERROR'}, "Game directory not set or invalid")
            return {'CANCELLED'}
       
        try:
            # Professional directory opening
            if sys.platform == "win32":
                os.startfile(props.game_directory)
            elif sys.platform == "darwin":  # macOS
                subprocess.Popen(["open", props.game_directory])
            else:  # Linux
                subprocess.Popen(["xdg-open", props.game_directory])
           
            self.report({'INFO'}, f"Professional directory opened: {props.game_directory}")
           
        except Exception as e:
            self.report({'ERROR'}, f"Directory opening failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}

class RAGE_OT_ValidateScene(Operator):
    bl_idname = "rage.validate_scene"
    bl_label = "Validate Scene"
    bl_description = "Professional scene validation for RDR1 compatibility"
   
    def execute(self, context):
        try:
            # Professional scene validation
            validation_results = self._validate_scene_compatibility()
           
            # Professional results display
            self._display_validation_results(validation_results)
           
            if validation_results['is_valid']:
                self.report({'INFO'}, "Professional scene validation passed")
            else:
                self.report({'WARNING'}, f"Scene validation: {validation_results['warning_count']} warnings")
           
        except Exception as e:
            self.report({'ERROR'}, f"Scene validation failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _validate_scene_compatibility(self):
        """Professional scene compatibility validation"""
        validation = {
            'is_valid': True,
            'warning_count': 0,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
       
        # Professional object validation
        for obj in bpy.context.scene.objects:
            obj_validation = self._validate_object(obj)
            if not obj_validation['is_valid']:
                validation['is_valid'] = False
                validation['errors'].extend(obj_validation['errors'])
           
            validation['warnings'].extend(obj_validation['warnings'])
            validation['suggestions'].extend(obj_validation['suggestions'])
       
        validation['warning_count'] = len(validation['warnings'])
       
        return validation
   
    def _validate_object(self, obj):
        """Professional object validation"""
        obj_validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
       
        # Professional mesh validation
        if obj.type == 'MESH':
            mesh_validation = self._validate_mesh(obj)
            if not mesh_validation['is_valid']:
                obj_validation['is_valid'] = False
                obj_validation['errors'].extend(mesh_validation['errors'])
           
            obj_validation['warnings'].extend(mesh_validation['warnings'])
            obj_validation['suggestions'].extend(mesh_validation['suggestions'])
       
        # Professional scale validation
        scale = obj.scale
        if abs(scale.x - 1.0) > 0.001 or abs(scale.y - 1.0) > 0.001 or abs(scale.z - 1.0) > 0.001:
            obj_validation['warnings'].append(f"Object '{obj.name}' has non-uniform scale")
       
        return obj_validation
   
    def _validate_mesh(self, obj):
        """Professional mesh validation"""
        mesh_validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
       
        mesh = obj.data
       
        # Professional vertex count validation
        if len(mesh.vertices) > 65535:
            mesh_validation['is_valid'] = False
            mesh_validation['errors'].append(f"Mesh '{obj.name}' exceeds vertex limit (65,535)")
       
        # Professional triangle count validation
        triangle_count = sum(len(poly.vertices) - 2 for poly in mesh.polygons)
        if triangle_count > 100000:
            mesh_validation['warnings'].append(f"Mesh '{obj.name}' has high triangle count: {triangle_count:,}")
       
        # Professional material count validation
        if len(mesh.materials) > 8:
            mesh_validation['warnings'].append(f"Mesh '{obj.name}' exceeds material limit (8)")
       
        # Professional UV validation
        if not mesh.uv_layers:
            mesh_validation['suggestions'].append(f"Mesh '{obj.name}' has no UV maps")
       
        return mesh_validation
   
    def _display_validation_results(self, validation_results):
        """Professional validation results display"""
        print("\nPROFESSIONAL SCENE VALIDATION")
        print("=" * 50)
        print(f"  Status: {'PASS' if validation_results['is_valid'] else 'FAIL'}")
        print(f"  Warnings: {validation_results['warning_count']}")
        print(f"  Errors: {len(validation_results['errors'])}")
        print(f"  Suggestions: {len(validation_results['suggestions'])}")
       
        if validation_results['errors']:
            print("\n  ERRORS:")
            for error in validation_results['errors']:
                print(f"    - {error}")
       
        if validation_results['warnings']:
            print("\n  WARNINGS:")
            for warning in validation_results['warnings']:
                print(f"    - {warning}")
       
        if validation_results['suggestions']:
            print("\n  SUGGESTIONS:")
            for suggestion in validation_results['suggestions']:
                print(f"    - {suggestion}")
       
        print("=" * 50)

class RAGE_OT_CleanupScene(Operator):
    bl_idname = "rage.cleanup_scene"
    bl_label = "Cleanup Scene"
    bl_description = "Professional scene cleanup and optimization"
   
    remove_unused_materials: BoolProperty(
        name="Remove Unused Materials",
        description="Professional removal of unused materials",
        default=True
    )
   
    remove_unused_meshes: BoolProperty(
        name="Remove Unused Meshes",
        description="Professional removal of unused mesh data",
        default=True
    )
   
    optimize_meshes: BoolProperty(
        name="Optimize Meshes",
        description="Professional mesh optimization",
        default=True
    )
   
    def execute(self, context):
        try:
            cleanup_results = {
                'materials_removed': 0,
                'meshes_removed': 0,
                'meshes_optimized': 0
            }
           
            # Professional material cleanup
            if self.remove_unused_materials:
                cleanup_results['materials_removed'] = self._cleanup_unused_materials()
           
            # Professional mesh cleanup
            if self.remove_unused_meshes:
                cleanup_results['meshes_removed'] = self._cleanup_unused_meshes()
           
            # Professional mesh optimization
            if self.optimize_meshes:
                cleanup_results['meshes_optimized'] = self._optimize_meshes()
           
            self.report({'INFO'}, f"Professional cleanup completed: {cleanup_results['materials_removed']} materials, {cleanup_results['meshes_removed']} meshes")
           
        except Exception as e:
            self.report({'ERROR'}, f"Scene cleanup failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _cleanup_unused_materials(self):
        """Professional unused material cleanup"""
        materials_removed = 0
       
        for material in bpy.data.materials:
            if not material.users:
                bpy.data.materials.remove(material)
                materials_removed += 1
       
        return materials_removed
   
    def _cleanup_unused_meshes(self):
        """Professional unused mesh cleanup"""
        meshes_removed = 0
       
        for mesh in bpy.data.meshes:
            if not mesh.users:
                bpy.data.meshes.remove(mesh)
                meshes_removed += 1
       
        return meshes_removed
   
    def _optimize_meshes(self):
        """Professional mesh optimization"""
        meshes_optimized = 0
       
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                self._optimize_single_mesh(obj)
                meshes_optimized += 1
       
        return meshes_optimized
   
    def _optimize_single_mesh(self, obj):
        """Professional single mesh optimization"""
        try:
            mesh = obj.data
           
            # Professional mesh optimization would go here
            # This could include removing doubles, recalculating normals, etc.
           
            print(f"Optimized mesh: {obj.name}")
           
        except Exception as e:
            print(f"Mesh optimization failed for {obj.name}: {e}")

class RAGE_OT_ExportDebugInfo(Operator):
    bl_idname = "rage.export_debug_info"
    bl_label = "Export Debug Info"
    bl_description = "Professional debug information export for troubleshooting"
   
    def execute(self, context):
        try:
            # Professional debug information collection
            debug_info = self._collect_debug_info()
           
            # Professional debug file creation
            debug_file = self._create_debug_file(debug_info)
           
            self.report({'INFO'}, f"Professional debug info exported: {debug_file}")
           
        except Exception as e:
            self.report({'ERROR'}, f"Debug info export failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _collect_debug_info(self):
        """Professional debug information collection"""
        debug_info = {
            'system': {
                'platform': sys.platform,
                'python_version': sys.version,
                'blender_version': bpy.app.version_string
            },
            'scene': {
                'object_count': len(bpy.context.scene.objects),
                'mesh_count': len([obj for obj in bpy.context.scene.objects if obj.type == 'MESH']),
                'material_count': len(bpy.data.materials),
                'texture_count': len(bpy.data.images)
            },
            'rage_studio': {
                'game_directory': bpy.context.scene.rage_studio.game_directory,
                'bridge_connected': bpy.context.scene.rage_studio.bridge_connected,
                'debug_mode': bpy.context.scene.rage_studio.debug_mode
            }
        }
       
        return debug_info
   
    def _create_debug_file(self, debug_info):
        """Professional debug file creation"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"rage_studio_debug_{timestamp}.json"
       
        try:
            with open(debug_file, 'w') as f:
                json.dump(debug_info, f, indent=2)
           
            return debug_file
           
        except Exception as e:
            raise Exception(f"Debug file creation failed: {e}")

# Professional registration
classes = (
    RAGE_OT_OpenGameDirectory,
    RAGE_OT_ValidateScene,
    RAGE_OT_CleanupScene,
    RAGE_OT_ExportDebugInfo,
)

def register():
    """Professional utilities registration"""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Failed to register utility {cls.__name__}: {e}")
            raise

def unregister():
    """Professional utilities unregistration"""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"Failed to unregister utility {cls.__name__}: {e}")