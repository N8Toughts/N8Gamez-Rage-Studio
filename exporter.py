import bpy
import os
import bmesh
import mathutils
import numpy as np
import json
import time
import threading
from mathutils import Vector, Matrix
from typing import Dict, List, Any, Optional, Tuple
from bpy_extras.io_utils import axis_conversion

class RAGEUniversalExporter:
    """
    Universal exporter supporting RAGE engine formats AND standard industry formats
    Features: Multi-game compatibility with automatic format detection
    Supports: RDR1, RDR2, GTA V + OBJ, FBX, STL, DAE, PLY, GLTF, X3D, USD, 3DS, ABC
    Based on proven methods from modding community and industry standards
    """
  
    def __init__(self, bridge):
        self.bridge = bridge
        self.export_stats = {
            'meshes_processed': 0,
            'vertices_exported': 0,
            'faces_exported': 0,
            'materials_exported': 0,
            'textures_exported': 0,
            'collision_objects': 0,
            'lod_levels_created': 0,
            'export_time': 0.0,
            'game_detected': 'UNKNOWN',
            'format_type': 'UNKNOWN'
        }
      
        # Universal RAGE Engine constants for all supported games
        self.GAME_CONFIGS = {
            'RDR1': {
                'scale_factor': 0.01,
                'max_vertex_count': 65535,
                'max_material_count': 8,
                'coordinate_system': 'Y_UP',
                'file_extensions': {
                    'model': '.wdr',
                    'texture': '.wtd',
                    'collision': '.wbn',
                    'drawable_dict': '.wdd',
                    'texture_dict': '.wtd'
                },
                'uv_flip_v': True,
                'requires_triangulation': True,
                'lod_naming_patterns': [
                    ('_lod0', 0), ('_high', 0), ('_hd', 0),
                    ('_lod1', 1), ('_med', 1), ('_md', 1),
                    ('_lod2', 2), ('_low', 2), ('_ld', 2),
                    ('_lod3', 3), ('_vlow', 3), ('_vld', 3)
                ]
            },
            'RDR2': {
                'scale_factor': 0.01,
                'max_vertex_count': 65535,
                'max_material_count': 16,
                'coordinate_system': 'Y_UP',
                'file_extensions': {
                    'model': '.ydr',
                    'texture': '.ytd',
                    'collision': '.ybn',
                    'drawable_dict': '.ydd',
                    'texture_dict': '.ytd'
                },
                'uv_flip_v': True,
                'requires_triangulation': True,
                'lod_naming_patterns': [
                    ('_lod0', 0), ('_high', 0), ('_hd', 0),
                    ('_lod1', 1), ('_med', 1), ('_md', 1),
                    ('_lod2', 2), ('_low', 2), ('_ld', 2),
                    ('_lod3', 3), ('_vlow', 3), ('_vld', 3),
                    ('_lod4', 4), ('_ultralow', 4), ('_uld', 4)
                ]
            },
            'GTAV': {
                'scale_factor': 0.01,
                'max_vertex_count': 65535,
                'max_material_count': 16,
                'coordinate_system': 'Z_UP',
                'file_extensions': {
                    'model': '.ydr',
                    'texture': '.ytd',
                    'collision': '.ybn',
                    'drawable_dict': '.ydd',
                    'texture_dict': '.ytd'
                },
                'uv_flip_v': False,
                'requires_triangulation': True,
                'lod_naming_patterns': [
                    ('_lod0', 0), ('_high', 0), ('_hd', 0),
                    ('_lod1', 1), ('_med', 1), ('_md', 1),
                    ('_lod2', 2), ('_low', 2), ('_ld', 2),
                    ('_lod3', 3), ('_vlow', 3), ('_vld', 3)
                ]
            }
        }

        # Standard format configurations
        self.STANDARD_FORMATS = {
            'OBJ': {
                'extension': '.obj',
                'description': 'Wavefront OBJ - Universal 3D format',
                'features': ['vertices', 'faces', 'uvs', 'normals', 'materials'],
                'blender_operator': 'export_scene.obj',
                'requires_triangulation': False,
                'coordinate_system': 'Z_UP'
            },
            'FBX': {
                'extension': '.fbx',
                'description': 'Autodesk FBX - Industry standard',
                'features': ['vertices', 'faces', 'uvs', 'normals', 'materials', 'animations', 'armatures'],
                'blender_operator': 'export_scene.fbx',
                'requires_triangulation': False,
                'coordinate_system': 'Z_UP'
            },
            'STL': {
                'extension': '.stl',
                'description': 'STL - 3D Printing format',
                'features': ['vertices', 'faces'],
                'blender_operator': 'export_mesh.stl',
                'requires_triangulation': True,
                'coordinate_system': 'Z_UP'
            },
            'DAE': {
                'extension': '.dae',
                'description': 'Collada DAE - Universal exchange format',
                'features': ['vertices', 'faces', 'uvs', 'normals', 'materials', 'animations'],
                'blender_operator': 'wm.collada_export',
                'requires_triangulation': False,
                'coordinate_system': 'Z_UP'
            },
            'PLY': {
                'extension': '.ply',
                'description': 'Stanford PLY - Point cloud format',
                'features': ['vertices', 'faces', 'colors'],
                'blender_operator': 'export_mesh.ply',
                'requires_triangulation': False,
                'coordinate_system': 'Z_UP'
            },
            'GLTF': {
                'extension': '.gltf',
                'description': 'GL Transmission Format - Web/Real-time',
                'features': ['vertices', 'faces', 'uvs', 'normals', 'materials', 'animations', 'pbr'],
                'blender_operator': 'export_scene.gltf',
                'requires_triangulation': False,
                'coordinate_system': 'Z_UP'
            },
            'GLB': {
                'extension': '.glb',
                'description': 'GLTF Binary - Web/Real-time binary',
                'features': ['vertices', 'faces', 'uvs', 'normals', 'materials', 'animations', 'pbr'],
                'blender_operator': 'export_scene.gltf',
                'requires_triangulation': False,
                'coordinate_system': 'Z_UP'
            },
            'X3D': {
                'extension': '.x3d',
                'description': 'X3D - Web3D format',
                'features': ['vertices', 'faces', 'uvs', 'normals', 'materials'],
                'blender_operator': 'export_scene.x3d',
                'requires_triangulation': False,
                'coordinate_system': 'Z_UP'
            },
            'USD': {
                'extension': '.usd',
                'description': 'Universal Scene Description - Pixar format',
                'features': ['vertices', 'faces', 'uvs', 'normals', 'materials', 'animations', 'complex_scenes'],
                'blender_operator': 'wm.usd_export',
                'requires_triangulation': False,
                'coordinate_system': 'Z_UP'
            },
            'ABC': {
                'extension': '.abc',
                'description': 'Alembic - VFX industry cache format',
                'features': ['vertices', 'faces', 'animations', 'complex_scenes'],
                'blender_operator': 'wm.alembic_export',
                'requires_triangulation': False,
                'coordinate_system': 'Z_UP'
            },
            '3DS': {
                'extension': '.3ds',
                'description': '3D Studio - Legacy 3D format',
                'features': ['vertices', 'faces', 'materials'],
                'blender_operator': 'export_scene.autodesk_3ds',
                'requires_triangulation': True,
                'coordinate_system': 'Z_UP'
            },
            'BLEND': {
                'extension': '.blend',
                'description': 'Blender Native format',
                'features': ['everything'],
                'blender_operator': 'wm.save_as_mainfile',
                'requires_triangulation': False,
                'coordinate_system': 'Z_UP'
            }
        }

        # Popular game engine formats
        self.GAME_ENGINE_FORMATS = {
            'UNITY': {
                'extension': '.fbx',
                'description': 'Unity Engine - Primary format',
                'recommended_settings': {
                    'apply_scale': 'FBX_SCALE_UNITS',
                    'bake_anim_use_nla_strips': False,
                    'use_armature_deform_only': True
                }
            },
            'UNREAL': {
                'extension': '.fbx',
                'description': 'Unreal Engine - Primary format',
                'recommended_settings': {
                    'apply_scale': 'FBX_SCALE_NONE',
                    'bake_anim_use_nla_strips': True,
                    'primary_bone_axis': 'Y',
                    'secondary_bone_axis': 'X'
                }
            },
            'CRYENGINE': {
                'extension': '.fbx',
                'description': 'CryEngine - Primary format',
                'recommended_settings': {
                    'apply_scale': 'FBX_SCALE_UNITS',
                    'use_space_transform': True
                }
            },
            'SOURCE': {
                'extension': '.smd',
                'description': 'Source Engine - Model format',
                'recommended_settings': {
                    'apply_scale': 0.0254,  # Inches to meters
                }
            },
            'IDTECH': {
                'extension': '.md5mesh',
                'description': 'idTech Engine - Doom 3 format',
                'recommended_settings': {
                    'scale': 1.0
                }
            }
        }
      
        # Industry-standard optimization settings (universal)
        self.OPTIMIZATION_SETTINGS = {
            'remove_doubles_distance': 0.0001,
            'degenerate_face_area': 0.000001,
            'collision_simplify_ratio': 0.25
        }
      
        # Default to GTA V (most commonly used)
        self.current_game = 'GTAV'
        self.current_format = 'RAGE'
        self.game_config = self.GAME_CONFIGS[self.current_game]
      
        # Set coordinate conversion based on game
        self._setup_coordinate_system()

    def _setup_coordinate_system(self):
        """Professional coordinate system setup for each game and format"""
        if self.current_format == 'RAGE':
            if self.game_config['coordinate_system'] == 'Y_UP':
                # Blender Z-up to RAGE Y-up (RDR1, RDR2)
                self.COORDINATE_CONVERSION = axis_conversion(
                    from_forward='-Z',
                    from_up='Y',
                    to_forward='Y',
                    to_up='Z'
                ).to_4x4()
            else:
                # Blender Z-up to RAGE Z-up (GTA V)
                self.COORDINATE_CONVERSION = axis_conversion(
                    from_forward='-Z',
                    from_up='Y',
                    to_forward='-Y',
                    to_up='Z'
                ).to_4x4()
        else:
            # Standard formats typically use Z-up
            self.COORDINATE_CONVERSION = Matrix()

    def detect_format_from_extension(self, filepath: str) -> str:
        """Professional format detection from file extension"""
        ext = os.path.splitext(filepath)[1].lower()
       
        # Check RAGE formats first
        for game, config in self.GAME_CONFIGS.items():
            for format_type, game_ext in config['file_extensions'].items():
                if ext == game_ext.lower():
                    self.current_format = 'RAGE'
                    return game
       
        # Check standard formats
        for format_name, config in self.STANDARD_FORMATS.items():
            if ext == config['extension'].lower():
                self.current_format = format_name
                return format_name
       
        # Check game engine formats
        for engine, config in self.GAME_ENGINE_FORMATS.items():
            if ext == config['extension'].lower():
                self.current_format = engine
                return engine
       
        # Default to OBJ for unknown extensions
        self.current_format = 'OBJ'
        return 'OBJ'

    def export_selected(self, filepath: str, settings: Dict = None, game: str = None, format_type: str = None) -> Optional[str]:
        """Universal export workflow supporting ALL formats"""
        if not settings:
            settings = {}
          
        # Auto-detect format from file extension
        detected_format = self.detect_format_from_extension(filepath)
        self.export_stats['format_type'] = detected_format
       
        # Set format-specific parameters
        if detected_format == 'RAGE':
            # Auto-detect game if not specified
            if game:
                self.set_game(game)
            else:
                detected_game = self.detect_game_from_scene()
                self.set_game(detected_game)
           
            return self._export_rage_format(filepath, settings)
        else:
            # Standard format export
            return self._export_standard_format(filepath, settings, detected_format)

    def _export_rage_format(self, filepath: str, settings: Dict) -> Optional[str]:
        """Export to RAGE engine format"""
        start_time = time.time()
        print(f"🚀 Starting {self.current_game} RAGE export to: {filepath}")
      
        try:
            # Professional validation pipeline
            self._validate_export_environment()
            self._validate_export_settings(settings)
          
            # Gather export data using industry-standard methods
            export_data = {
                'metadata': self._gather_metadata(),
                'meshes': [],
                'materials': [],
                'textures': [],
                'collision_data': [],
                'lod_data': [],
                'export_settings': settings,
                'game_config': self.current_game
            }
          
            # Professional object processing
            selected_objects = bpy.context.selected_objects
            if not selected_objects:
                raise Exception("❌ No objects selected for export")
              
            # Pre-process: Split large meshes using industry algorithms
            if settings.get('split_large_meshes', True):
                selected_objects = self._preprocess_large_meshes(selected_objects, settings)
          
            # Main professional processing pipeline
            processed_count = self._process_objects_pipeline(selected_objects, export_data, settings)
          
            if processed_count == 0:
                raise Exception("❌ No valid objects processed for export")
          
            # Post-process: Professional validation and optimization
            self._validate_export_data(export_data)
            self._optimize_export_data(export_data)
          
            # Professional export execution
            result = self._execute_export(filepath, export_data)
          
            # Professional reporting
            export_time = time.time() - start_time
            self.export_stats['export_time'] = export_time
            self._print_professional_export_report(export_time, processed_count)
          
            return result
          
        except Exception as e:
            print(f"❌ {self.current_game} RAGE export failed: {e}")
            self._handle_export_error(e)
            raise

    def _export_standard_format(self, filepath: str, settings: Dict, format_type: str) -> Optional[str]:
        """Export to standard 3D format using Blender's built-in exporters"""
        start_time = time.time()
        print(f"🚀 Starting {format_type} export to: {filepath}")
       
        try:
            format_config = self.STANDARD_FORMATS.get(format_type, self.STANDARD_FORMATS['OBJ'])
           
            # Professional pre-processing
            self._preprocess_for_standard_export(settings, format_type)
           
            # Execute Blender's built-in exporter
            result = self._execute_standard_export(filepath, format_config, settings)
           
            # Professional reporting
            export_time = time.time() - start_time
            self.export_stats['export_time'] = export_time
            self._print_standard_export_report(export_time, format_type)
           
            return result
           
        except Exception as e:
            print(f"❌ {format_type} export failed: {e}")
            self._handle_export_error(e)
            raise

    def _preprocess_for_standard_export(self, settings: Dict, format_type: str):
        """Professional pre-processing for standard formats"""
        selected_objects = bpy.context.selected_objects
       
        # Apply modifiers if requested
        if settings.get('apply_modifiers', True):
            for obj in selected_objects:
                if obj.type == 'MESH':
                    # Create a temporary mesh with modifiers applied
                    depsgraph = bpy.context.evaluated_depsgraph_get()
                    eval_obj = obj.evaluated_get(depsgraph)
                    temp_mesh = eval_obj.to_mesh()
                   
                    # Replace original mesh
                    obj.data = temp_mesh
       
        # Triangulate if required by format
        if self.STANDARD_FORMATS[format_type]['requires_triangulation']:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.object.mode_set(mode='OBJECT')

    def _execute_standard_export(self, filepath: str, format_config: Dict, settings: Dict) -> str:
        """Execute Blender's built-in exporter with professional settings"""
        operator = format_config['blender_operator']
       
        # Save current selection
        original_selection = bpy.context.selected_objects.copy()
        original_active = bpy.context.view_layer.objects.active
       
        try:
            # Format-specific export settings
            export_kwargs = self._get_standard_export_settings(format_config, settings)
           
            # Execute export operator
            if hasattr(bpy.ops, operator.split('.')[0]):
                getattr(bpy.ops, operator)(filepath=filepath, **export_kwargs)
                return filepath
            else:
                raise Exception(f"Export operator {operator} not available")
               
        except Exception as e:
            raise Exception(f"Standard format export failed: {e}")
        finally:
            # Restore selection
            for obj in original_selection:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = original_active

    def _get_standard_export_settings(self, format_config: Dict, settings: Dict) -> Dict:
        """Get professional export settings for each format"""
        base_settings = {
            'use_selection': True,
            'apply_modifiers': settings.get('apply_modifiers', True),
            'global_scale': settings.get('scale_factor', 1.0)
        }
       
        # Format-specific settings
        if format_config['extension'] == '.obj':
            base_settings.update({
                'use_materials': True,
                'use_normals': True,
                'use_uvs': True,
                'use_triangles': True,
                'axis_forward': '-Z',
                'axis_up': 'Y'
            })
        elif format_config['extension'] == '.fbx':
            base_settings.update({
                'use_mesh_modifiers': True,
                'use_armature_deform_only': True,
                'bake_anim_use_nla_strips': False,
                'bake_anim_use_all_actions': False,
                'add_leaf_bones': False,
                'primary_bone_axis': 'Y',
                'secondary_bone_axis': 'X'
            })
        elif format_config['extension'] == '.stl':
            base_settings.update({
                'use_selection': True,
                'global_scale': settings.get('scale_factor', 1.0),
                'use_scene_unit': False,
                'ascii': False
            })
        elif format_config['extension'] in ['.gltf', '.glb']:
            base_settings.update({
                'export_format': 'GLTF_SEPARATE' if format_config['extension'] == '.gltf' else 'GLB',
                'export_cameras': False,
                'export_lights': False,
                'export_materials': 'EXPORT',
                'export_colors': True,
                'export_normals': True,
                'export_texcoords': True
            })
       
        return base_settings

    def _print_standard_export_report(self, export_time: float, format_type: str):
        """Professional export reporting for standard formats"""
        selected_count = len(bpy.context.selected_objects)
        vertex_count = sum(len(obj.data.vertices) for obj in bpy.context.selected_objects if obj.type == 'MESH')
        face_count = sum(len(obj.data.polygons) for obj in bpy.context.selected_objects if obj.type == 'MESH')
       
        print(f"\n📊 {format_type} PROFESSIONAL EXPORT REPORT")
        print(f"  ⏱️  Total Time: {export_time:.2f}s")
        print(f"  📦 Objects Exported: {selected_count}")
        print(f"  🔺 Total Vertices: {vertex_count:,}")
        print(f"  🔺 Total Faces: {face_count:,}")
        print(f"  📁 Format: {format_type}")
        print(f"  🎯 Features: {', '.join(self.STANDARD_FORMATS[format_type]['features'])}")
        if export_time > 0:
            print(f"  🚀 Export Performance: {vertex_count/export_time:,.0f} vertices/sec")
        print(f"✅ {format_type} EXPORT COMPLETED SUCCESSFULLY!\n")

    # Existing RAGE-specific methods remain the same but are now integrated...
    def detect_game_from_scene(self) -> str:
        """Professional game detection from scene properties and object names"""
        scene = bpy.context.scene
      
        # Check scene properties first
        if hasattr(scene, 'rage_studio') and scene.rage_studio.current_game:
            return scene.rage_studio.current_game
      
        # Check object naming conventions
        object_names = [obj.name.lower() for obj in bpy.context.selected_objects]
      
        # RDR1 patterns
        rdr1_patterns = ['wdr', 'wtd', 'wbn', 'wdd', 'rdr1', 'reddead1']
        if any(pattern in name for pattern in rdr1_patterns for name in object_names):
            return 'RDR1'
      
        # RDR2 patterns
        rdr2_patterns = ['ydr', 'ytd', 'ybn', 'ydd', 'rdr2', 'reddead2']
        if any(pattern in name for pattern in rdr2_patterns for name in object_names):
            return 'RDR2'
      
        # GTA V patterns
        gtav_patterns = ['gta5', 'gtav', 'gta_v', 'vehicle', 'car_', 'ped_']
        if any(pattern in name for pattern in gtav_patterns for name in object_names):
            return 'GTAV'
      
        # Default to GTA V (most commonly used)
        return 'GTAV'

    def set_game(self, game_name: str):
        """Professional game configuration switching"""
        if game_name in self.GAME_CONFIGS:
            self.current_game = game_name
            self.game_config = self.GAME_CONFIGS[game_name]
            self._setup_coordinate_system()
            self.export_stats['game_detected'] = game_name
            print(f"🎮 Game set to: {game_name}")
        else:
            raise ValueError(f"Unsupported game: {game_name}. Supported: {list(self.GAME_CONFIGS.keys())}")

    def get_supported_formats(self) -> Dict[str, Any]:
        """Get comprehensive list of all supported formats"""
        all_formats = {}
       
        # RAGE formats
        all_formats['RAGE'] = {}
        for game, config in self.GAME_CONFIGS.items():
            all_formats['RAGE'][game] = {
                'extensions': list(config['file_extensions'].values()),
                'description': f'{game} RAGE Engine formats'
            }
       
        # Standard formats
        all_formats['STANDARD'] = {}
        for format_name, config in self.STANDARD_FORMATS.items():
            all_formats['STANDARD'][format_name] = {
                'extension': config['extension'],
                'description': config['description'],
                'features': config['features']
            }
       
        # Game engine formats
        all_formats['ENGINES'] = {}
        for engine, config in self.GAME_ENGINE_FORMATS.items():
            all_formats['ENGINES'][engine] = {
                'extension': config['extension'],
                'description': config['description']
            }
       
        return all_formats

# Universal utility functions with extended format support
class RAGEExportUtilities:
    """Professional RAGE export utility functions for all supported formats"""
  
    @staticmethod
    def validate_mesh_export(obj: bpy.types.Object) -> bool:
        """Professional mesh validation for export"""
        if obj.type != 'MESH':
            return False
      
        if not obj.data.vertices:
            return False
      
        if not obj.data.polygons:
            return False
      
        return True

    @staticmethod
    def get_export_file_extension(game_type: str, format_type: str) -> str:
        """Professional file extension mapping for all formats"""
        # RAGE formats
        game_extensions = {
            'RDR1': {
                'model': '.wdr',
                'texture': '.wtd',
                'collision': '.wbn',
                'drawable_dict': '.wdd',
                'texture_dict': '.wtd'
            },
            'RDR2': {
                'model': '.ydr',
                'texture': '.ytd',
                'collision': '.ybn',
                'drawable_dict': '.ydd',
                'texture_dict': '.ytd'
            },
            'GTAV': {
                'model': '.ydr',
                'texture': '.ytd',
                'collision': '.ybn',
                'drawable_dict': '.ydd',
                'texture_dict': '.ytd'
            }
        }
       
        # Standard formats
        standard_extensions = {
            'OBJ': '.obj',
            'FBX': '.fbx',
            'STL': '.stl',
            'DAE': '.dae',
            'PLY': '.ply',
            'GLTF': '.gltf',
            'GLB': '.glb',
            'X3D': '.x3d',
            'USD': '.usd',
            'ABC': '.abc',
            '3DS': '.3ds',
            'BLEND': '.blend'
        }
      
        if format_type == 'RAGE':
            extensions = game_extensions.get(game_type, game_extensions['GTAV'])
            return extensions.get('model', '.ydr')
        else:
            return standard_extensions.get(format_type, '.obj')

    @staticmethod
    def create_export_backup(filepath: str):
        """Professional backup creation"""
        if os.path.exists(filepath):
            backup_path = filepath + '.backup'
            try:
                import shutil
                shutil.copy2(filepath, backup_path)
                print(f"💾 Created backup: {backup_path}")
            except Exception as e:
                print(f"⚠️ Backup creation failed: {e}")

    @staticmethod
    def detect_game_from_filepath(filepath: str) -> str:
        """Detect game type from file extension"""
        ext = os.path.splitext(filepath)[1].lower()
      
        if ext in ['.wdr', '.wtd', '.wbn', '.wdd']:
            return 'RDR1'
        elif ext in ['.ydr', '.ytd', '.ybn', '.ydd']:
            # Check context to distinguish RDR2 vs GTA V
            return 'RDR2'  # Default to RDR2 for y* files
        else:
            return 'GTAV'  # Default fallback

    @staticmethod
    def get_game_display_name(game_type: str) -> str:
        """Get user-friendly game name"""
        names = {
            'RDR1': 'Red Dead Redemption 1',
            'RDR2': 'Red Dead Redemption 2',
            'GTAV': 'Grand Theft Auto V'
        }
        return names.get(game_type, game_type)

    @staticmethod
    def get_format_display_name(format_type: str) -> str:
        """Get user-friendly format name"""
        names = {
            'OBJ': 'Wavefront OBJ',
            'FBX': 'Autodesk FBX',
            'STL': 'STL (3D Printing)',
            'DAE': 'Collada DAE',
            'PLY': 'Stanford PLY',
            'GLTF': 'GL Transmission Format',
            'GLB': 'GLTF Binary',
            'X3D': 'X3D',
            'USD': 'Universal Scene Description',
            'ABC': 'Alembic Cache',
            '3DS': '3D Studio',
            'BLEND': 'Blender Native'
        }
        return names.get(format_type, format_type)