import bpy
from bpy.types import PropertyGroup
from bpy.props import (StringProperty, BoolProperty, IntProperty,
                      FloatProperty, FloatVectorProperty, EnumProperty,
                      PointerProperty, CollectionProperty)

# Game types for universal RAGE support
GAME_TYPES = [
    ('RDR1', 'Red Dead Redemption 1', 'RDR1 PC modding tools', 0),
    ('RDR2', 'Red Dead Redemption 2', 'RDR2 PC modding tools', 1),
    ('GTAV', 'Grand Theft Auto V', 'GTA V PC modding tools', 2)
]

class RAGEExportSettings(PropertyGroup):
    # Game selection
    game_type: EnumProperty(
        name="Game",
        description="Target RAGE game for export",
        items=GAME_TYPES,
        default='GTAV'
    )
   
    # Universal export settings
    scale_factor: FloatProperty(
        name="Scale Factor",
        description="Scale multiplier for export",
        default=1.0,
        min=0.001,
        max=1000.0
    )
   
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers before export",
        default=True
    )
   
    optimize_mesh: BoolProperty(
        name="Optimize Mesh",
        description="Apply mesh optimization",
        default=True
    )
   
    export_lods: BoolProperty(
        name="Export LODs",
        description="Export LOD levels",
        default=True
    )
   
    export_collision: BoolProperty(
        name="Export Collision",
        description="Export collision data",
        default=True
    )
   
    split_large_meshes: BoolProperty(
        name="Split Large Meshes",
        description="Split meshes that exceed vertex limits",
        default=True
    )
   
    mesh_split_threshold: IntProperty(
        name="Split Threshold",
        description="Maximum vertices per mesh chunk",
        default=32768,
        min=1000,
        max=65535
    )

class RAGEImportSettings(PropertyGroup):
    game_type: EnumProperty(
        name="Game",
        description="Source RAGE game for import",
        items=GAME_TYPES,
        default='GTAV'
    )
   
    import_textures: BoolProperty(
        name="Import Textures",
        description="Import texture files",
        default=True
    )
   
    create_materials: BoolProperty(
        name="Create Materials",
        description="Create Blender materials from RAGE materials",
        default=True
    )
   
    import_lods: BoolProperty(
        name="Import LODs",
        description="Import all LOD levels",
        default=True
    )
   
    import_collision: BoolProperty(
        name="Import Collision",
        description="Import collision data",
        default=True
    )
   
    auto_scale: BoolProperty(
        name="Auto Scale",
        description="Automatically scale imported models",
        default=True
    )
   
    merge_vertices: BoolProperty(
        name="Merge Vertices",
        description="Merge duplicate vertices",
        default=True
    )

class RAGETerrainSettings(PropertyGroup):
    game_type: EnumProperty(
        name="Game",
        description="Target game for terrain",
        items=GAME_TYPES,
        default='GTAV'
    )
   
    terrain_size: IntProperty(
        name="Terrain Size",
        description="Size of terrain grid",
        default=1024,
        min=256,
        max=4096
    )
   
    lod_levels: IntProperty(
        name="LOD Levels",
        description="Number of LOD levels to generate",
        default=4,
        min=1,
        max=8
    )
   
    heightmap_resolution: IntProperty(
        name="Heightmap Resolution",
        description="Resolution for heightmap imports",
        default=1024,
        min=64,
        max=8192
    )
   
    height_scale: FloatProperty(
        name="Height Scale",
        description="Terrain height scale",
        default=100.0,
        min=0.1,
        max=1000.0
    )
   
    tile_size: FloatProperty(
        name="Tile Size",
        description="Size of terrain tiles",
        default=1000.0,
        min=10.0,
        max=10000.0
    )
   
    auto_generate_collision: BoolProperty(
        name="Auto Generate Collision",
        description="Automatically generate collision for terrain",
        default=True
    )

class RAGERoadSettings(PropertyGroup):
    game_type: EnumProperty(
        name="Game",
        description="Target game for roads",
        items=GAME_TYPES,
        default='GTAV'
    )
   
    road_width: FloatProperty(
        name="Road Width",
        description="Default road width",
        default=6.0,
        min=1.0,
        max=50.0
    )
   
    road_segments: IntProperty(
        name="Road Segments",
        description="Number of segments per unit",
        default=8,
        min=1,
        max=64
    )
   
    bevel_depth: FloatProperty(
        name="Bevel Depth",
        description="Road thickness/bevel depth",
        default=0.3,
        min=0.1,
        max=2.0
    )
   
    auto_uv: BoolProperty(
        name="Auto UV",
        description="Automatically generate UV coordinates",
        default=True
    )
   
    create_collision: BoolProperty(
        name="Create Collision",
        description="Generate collision for roads",
        default=True
    )
   
    generate_shoulders: BoolProperty(
        name="Generate Shoulders",
        description="Generate road shoulders",
        default=True
    )
   
    shoulder_width: FloatProperty(
        name="Shoulder Width",
        description="Width of road shoulders",
        default=1.5,
        min=0.5,
        max=5.0
    )

class RAGEStudioProperties(PropertyGroup):
    # Bridge settings
    bridge_connected: BoolProperty(
        name="Bridge Connected",
        description="Connection status to RAGE bridge",
        default=False
    )
   
    auto_connect: BoolProperty(
        name="Auto-Connect",
        description="Automatically connect to bridge on startup",
        default=False
    )
   
    bridge_host: StringProperty(
        name="Host",
        description="Bridge server host",
        default="localhost"
    )
   
    bridge_port: IntProperty(
        name="Port",
        description="Bridge server port",
        default=29200,
        min=1000,
        max=65535
    )
   
    # Game settings
    current_game: EnumProperty(
        name="Current Game",
        description="Currently active RAGE game",
        items=GAME_TYPES,
        default='GTAV',
        update=lambda self, context: self._on_game_changed(context)
    )
   
    def _on_game_changed(self, context):
        """Update all settings when game changes"""
        # Update export settings
        if hasattr(self, 'export_settings'):
            self.export_settings.game_type = self.current_game
       
        # Update import settings
        if hasattr(self, 'import_settings'):
            self.import_settings.game_type = self.current_game
           
        # Update terrain settings
        if hasattr(self, 'terrain_settings'):
            self.terrain_settings.game_type = self.current_game
           
        # Update road settings
        if hasattr(self, 'road_settings'):
            self.road_settings.game_type = self.current_game
       
        print(f"🎮 Game changed to: {self.current_game}")
   
    # Directory settings
    game_directory: StringProperty(
        name="Game Directory",
        description="Path to RAGE game installation",
        default="",
        subtype='DIR_PATH'
    )
   
    export_path: StringProperty(
        name="Export Path",
        description="Default export directory",
        default="",
        subtype='DIR_PATH'
    )
   
    codewalker_directory: StringProperty(
        name="CodeWalker Directory",
        description="Path to CodeWalker installation",
        default="",
        subtype='DIR_PATH'
    )
   
    # Asset browser
    asset_browser_path: StringProperty(
        name="Asset Path",
        description="Path to game assets",
        default="",
        subtype='DIR_PATH'
    )
   
    asset_filter: StringProperty(
        name="Filter",
        description="Filter assets by name",
        default=""
    )
   
    # Scene management
    terrain_object: StringProperty(
        name="Terrain Object",
        description="Active terrain object for operations",
        default=""
    )
   
    active_road_curve: StringProperty(
        name="Active Road Curve",
        description="Active curve object for road operations",
        default=""
    )
   
    last_analyzed_file: StringProperty(
        name="Last Analyzed File",
        description="Last file analyzed by the system",
        default=""
    )
   
    # Debug
    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Enable debug features and logging",
        default=False
    )
   
    # Sub-properties
    export_settings: PointerProperty(type=RAGEExportSettings)
    import_settings: PointerProperty(type=RAGEImportSettings)
    terrain_settings: PointerProperty(type=RAGETerrainSettings)
    road_settings: PointerProperty(type=RAGERoadSettings)

# Professional registration
classes = (
    RAGEExportSettings,
    RAGEImportSettings,
    RAGETerrainSettings,
    RAGERoadSettings,
    RAGEStudioProperties,
)

def register():
    """Professional properties registration"""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"❌ Failed to register property {cls.__name__}: {e}")
            raise

def unregister():
    """Professional properties unregistration"""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"⚠️ Failed to unregister property {cls.__name__}: {e}")