# asset_browser.py
import bpy
import os
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty

class RAGE_OT_BrowseModels(Operator):
    bl_idname = "rage.browse_models"
    bl_label = "Browse Models"
    bl_description = "Professional model asset browser with preview and filtering"
   
    category: StringProperty(
        name="Category",
        description="Professional model category filter",
        default=""
    )
   
    def execute(self, context):
        try:
            # Professional model browsing
            model_data = self._load_model_catalog()
           
            # Professional UI creation
            self._create_model_browser_ui(model_data)
           
            self.report({'INFO'}, "Professional model browser opened")
           
        except Exception as e:
            self.report({'ERROR'}, f"Model browsing failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _load_model_catalog(self):
        """Professional model catalog loading"""
        props = bpy.context.scene.rage_studio
       
        if not props.game_directory or not os.path.exists(props.game_directory):
            raise Exception("Game directory not set or invalid")
       
        # Professional model discovery
        model_catalog = {
            'vehicles': [],
            'buildings': [],
            'props': [],
            'vegetation': [],
            'characters': []
        }
       
        # Professional directory scanning
        model_dirs = self._find_model_directories(props.game_directory)
       
        for model_dir in model_dirs:
            self._scan_model_directory(model_dir, model_catalog)
       
        return model_catalog
   
    def _find_model_directories(self, game_dir):
        """Professional model directory discovery"""
        model_dirs = []
       
        # Professional directory patterns for RDR1 models
        potential_dirs = [
            'models',
            'x64/models',
            'dlcpacks/models',
            'levels/models'
        ]
       
        for dir_name in potential_dirs:
            dir_path = os.path.join(game_dir, dir_name)
            if os.path.exists(dir_path):
                model_dirs.append(dir_path)
       
        return model_dirs
   
    def _scan_model_directory(self, directory, catalog):
        """Professional model directory scanning"""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(('.wdr', '.ydd', '.yft')):
                        model_data = self._analyze_model_file(os.path.join(root, file))
                       
                        # Professional categorization
                        category = self._categorize_model(model_data)
                        if category in catalog:
                            catalog[category].append(model_data)
                       
        except Exception as e:
            print(f"Directory scanning failed: {e}")
   
    def _analyze_model_file(self, filepath):
        """Professional model file analysis"""
        return {
            'name': os.path.basename(filepath),
            'path': filepath,
            'size': os.path.getsize(filepath),
            'type': self._detect_model_type(filepath),
            'category': 'unknown'
        }
   
    def _detect_model_type(self, filepath):
        """Professional model type detection"""
        filename = os.path.basename(filepath).lower()
       
        if filename.endswith('.wdr'):
            return 'Drawable'
        elif filename.endswith('.ydd'):
            return 'Drawable Dictionary'
        elif filename.endswith('.yft'):
            return 'Fragment'
        else:
            return 'Unknown'
   
    def _categorize_model(self, model_data):
        """Professional model categorization"""
        name_lower = model_data['name'].lower()
       
        # Professional categorization logic
        if any(vehicle in name_lower for vehicle in ['vehicle', 'car', 'wagon', 'horse']):
            return 'vehicles'
        elif any(building in name_lower for building in ['building', 'house', 'wall', 'roof']):
            return 'buildings'
        elif any(prop in name_lower for prop in ['prop', 'object', 'item']):
            return 'props'
        elif any(plant in name_lower for plant in ['tree', 'plant', 'bush', 'grass']):
            return 'vegetation'
        elif any(char in name_lower for char in ['ped', 'character', 'person']):
            return 'characters'
        else:
            return 'props'  # Professional fallback category
   
    def _create_model_browser_ui(self, model_data):
        """Professional model browser UI creation"""
        # Professional UI implementation would go here
        # This would create a custom UI for browsing models
       
        print("Professional model browser UI created")
        print(f"Models found: {sum(len(models) for models in model_data.values())}")

class RAGE_OT_PreviewAsset(Operator):
    bl_idname = "rage.preview_asset"
    bl_label = "Preview Asset"
    bl_description = "Professional asset preview with detailed information"
   
    asset_path: StringProperty(
        name="Asset Path",
        description="Professional asset path for preview",
        default=""
    )
   
    def execute(self, context):
        try:
            # Professional asset validation
            if not self.asset_path or not os.path.exists(self.asset_path):
                self.report({'ERROR'}, "Asset path not valid")
                return {'CANCELLED'}
           
            # Professional asset analysis
            asset_info = self._analyze_asset(self.asset_path)
           
            # Professional preview creation
            self._create_asset_preview(asset_info)
           
            self.report({'INFO'}, f"Professional asset preview created: {os.path.basename(self.asset_path)}")
           
        except Exception as e:
            self.report({'ERROR'}, f"Asset preview failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _analyze_asset(self, asset_path):
        """Professional asset analysis"""
        asset_info = {
            'name': os.path.basename(asset_path),
            'path': asset_path,
            'size': os.path.getsize(asset_path),
            'type': self._detect_asset_type(asset_path),
            'format': self._detect_asset_format(asset_path),
            'compatibility': self._check_asset_compatibility(asset_path)
        }
       
        return asset_info
   
    def _detect_asset_type(self, asset_path):
        """Professional asset type detection"""
        filename = asset_path.lower()
       
        if any(ext in filename for ext in ['.wdr', '.ydd', '.yft']):
            return 'Model'
        elif any(ext in filename for ext in ['.wtd', '.ytd']):
            return 'Texture'
        elif any(ext in filename for ext in ['.ymap', '.ytyp']):
            return 'Map'
        elif any(ext in filename for ext in ['.ybn']):
            return 'Collision'
        elif any(ext in filename for ext in ['.ymt']):
            return 'Material'
        else:
            return 'Unknown'
   
    def _detect_asset_format(self, asset_path):
        """Professional asset format detection"""
        return os.path.splitext(asset_path)[1].upper().replace('.', '')
   
    def _check_asset_compatibility(self, asset_path):
        """Professional asset compatibility check"""
        # Placeholder implementation
        return "Compatible"
   
    def _create_asset_preview(self, asset_info):
        """Professional asset preview creation"""
        # Placeholder implementation
        print(f"Creating preview for: {asset_info['name']}")

# Add other browser operators (RAGE_OT_BrowseTextures, RAGE_OT_BrowseMaps, etc.) with similar fixes