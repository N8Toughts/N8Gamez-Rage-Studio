# RAGE Studio Suite - Professional UI Panel System
import bpy
import os
from bpy.types import Panel, Menu, UIList
from bpy.props import StringProperty, BoolProperty, IntProperty

class RAGE_PT_MainPanel(Panel):
    bl_label = "RAGE Studio Suite"
    bl_idname = "RAGE_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        props = context.scene.rage_studio
       
        # Connection Status
        box = layout.box()
        row = box.row()
        if props.bridge_connected:
            row.label(text="✅ Bridge Connected", icon='CHECKMARK')
            row.operator("rage.disconnect_bridge", text="", icon='UNLINKED')
        else:
            row.label(text="❌ Bridge Disconnected", icon='ERROR')
            row.operator("rage.connect_bridge", text="", icon='LINKED')
       
        # Quick Actions
        col = layout.column(align=True)
        col.operator("rage.import_rdr_model", icon='IMPORT', text="Import Model")
        col.operator("rage.export_selected", icon='EXPORT', text="Export Selected")
       
        # Essential Settings
        box = layout.box()
        box.label(text="Essential Settings", icon='SETTINGS')
        box.prop(props, "game_directory")
        if props.game_directory and not os.path.exists(props.game_directory):
            box.label(text="⚠️ Game directory not found", icon='ERROR')
       
        box.prop(props, "export_path")
        if props.export_path and not os.path.exists(props.export_path):
            box.label(text="⚠️ Export path not found", icon='ERROR')

class RAGE_PT_ImportPanel(Panel):
    bl_label = "Import Tools"
    bl_idname = "RAGE_PT_import_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        props = context.scene.rage_studio
       
        # File Import
        box = layout.box()
        box.label(text="File Import", icon='IMPORT')
        col = box.column(align=True)
        col.operator("rage.import_rdr_model", icon='MESH_DATA', text="Import RDR1 Model")
        col.operator("rage.import_codewalker_xml", icon='WORLD_DATA', text="Import CodeWalker XML")
        col.operator("rage.import_heightmap", icon='TEXTURE', text="Import Heightmap")
       
        # Import Settings
        box = layout.box()
        box.label(text="Import Settings", icon='PREFERENCES')
        box.prop(props.import_settings, "auto_scale")
        box.prop(props.import_settings, "import_textures")
        box.prop(props.import_settings, "create_materials")
        box.prop(props.import_settings, "import_lods")
        box.prop(props.import_settings, "import_collision")
        box.prop(props.import_settings, "merge_vertices")

class RAGE_PT_ExportPanel(Panel):
    bl_label = "Export Tools"
    bl_idname = "RAGE_PT_export_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"
    bl_order = 3

    def draw(self, context):
        layout = self.layout
        props = context.scene.rage_studio
       
        # Export Operators
        box = layout.box()
        box.label(text="Export Operations", icon='EXPORT')
        col = box.column(align=True)
        col.operator("rage.export_selected", icon='EXPORT', text="Export Selected")
        col.operator("rage.export_collision_mesh", icon='MOD_PHYSICS', text="Export Collision")
        col.operator("rage.export_to_codewalker", icon='WORLD_DATA', text="Export to CodeWalker")
       
        # Export Settings
        box = layout.box()
        box.label(text="Export Settings", icon='SETTINGS')
        box.prop(props.export_settings, "scale_factor")
        box.prop(props.export_settings, "apply_modifiers")
        box.prop(props.export_settings, "export_lods")
        box.prop(props.export_settings, "optimize_mesh")
        box.prop(props.export_settings, "export_collision")
       
        # Advanced Export
        box = layout.box()
        box.label(text="Advanced Settings", icon='MODIFIER')
        box.prop(props.export_settings, "split_large_meshes")
        if props.export_settings.split_large_meshes:
            box.prop(props.export_settings, "mesh_split_threshold")

class RAGE_PT_TerrainPanel(Panel):
    bl_label = "Terrain Tools"
    bl_idname = "RAGE_PT_terrain_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"
    bl_order = 4

    def draw(self, context):
        layout = self.layout
        props = context.scene.rage_studio
       
        # Terrain Creation
        box = layout.box()
        box.label(text="Terrain Creation", icon='MOD_OCEAN')
        col = box.column(align=True)
        col.operator("rage.import_heightmap", icon='TEXTURE', text="Import Heightmap")
        col.operator("rage.create_terrain_grid", icon='MESH_GRID', text="Create Terrain Grid")
        col.operator("rage.generate_terrain_lods", icon='MOD_SUBSURF', text="Generate LODs")
       
        # Terrain Editing
        box = layout.box()
        box.label(text="Terrain Editing", icon='SCULPTMODE_HLT')
        col = box.column(align=True)
        col.operator("rage.bore_tunnel", icon='CONE', text="Bore Tunnel")
        col.operator("rage.excavate_area", icon='MESH_CUBE', text="Excavate Area")
       
        # Terrain Settings
        box = layout.box()
        box.label(text="Terrain Settings", icon='PREFERENCES')
        box.prop(props.terrain_settings, "heightmap_resolution")
        box.prop(props.terrain_settings, "height_scale")
        box.prop(props.terrain_settings, "tile_size")
        box.prop(props.terrain_settings, "lod_levels")
        box.prop(props.terrain_settings, "auto_generate_collision")
       
        # Active Terrain
        if props.terrain_object:
            box = layout.box()
            box.label(text="Active Terrain", icon='OBJECT_DATA')
            box.prop_search(props, "terrain_object", bpy.data, "objects", text="")
            if props.terrain_object in bpy.data.objects:
                obj = bpy.data.objects[props.terrain_object]
                if obj.get("rage_terrain"):
                    box.label(text=f"✅ Valid terrain object", icon='CHECKMARK')
                else:
                    box.label(text=f"⚠️ Not a terrain object", icon='ERROR')

class RAGE_PT_RoadPanel(Panel):
    bl_label = "Road & Path Tools"
    bl_idname = "RAGE_PT_road_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"
    bl_order = 5

    def draw(self, context):
        layout = self.layout
        props = context.scene.rage_studio
       
        # Road Creation
        box = layout.box()
        box.label(text="Road Creation", icon='MOD_CURVE')
        col = box.column(align=True)
        col.operator("rage.create_road_from_curve", icon='CURVE_DATA', text="Create Road from Curve")
        col.operator("rage.generate_road_network", icon='AUTOMERGE_ON', text="Generate Road Network")
        col.operator("rage.convert_curve_to_road", icon='CURVE_PATH', text="Convert Curve to Road")
        col.operator("rage.generate_path", icon='CON_FOLLOWPATH', text="Generate Path")
        col.operator("rage.generate_river", icon='MOD_OCEAN', text="Generate River")
       
        # Road Settings
        box = layout.box()
        box.label(text="Road Settings", icon='SETTINGS')
        box.prop(props.road_settings, "road_width")
        box.prop(props.road_settings, "road_segments")
        box.prop(props.road_settings, "bevel_depth")
        box.prop(props.road_settings, "auto_uv")
        box.prop(props.road_settings, "create_collision")
       
        # Active Road
        if props.active_road_curve:
            box = layout.box()
            box.label(text="Active Road", icon='CURVE_DATA')
            box.prop_search(props, "active_road_curve", bpy.data, "objects", text="")
            if props.active_road_curve in bpy.data.objects:
                obj = bpy.data.objects[props.active_road_curve]
                if obj.type == 'CURVE':
                    box.label(text=f"✅ Valid curve object", icon='CHECKMARK')
                else:
                    box.label(text=f"⚠️ Not a curve object", icon='ERROR')

class RAGE_PT_CodeWalkerPanel(Panel):
    bl_label = "CodeWalker Tools"
    bl_idname = "RAGE_PT_codewalker_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"
    bl_order = 6

    def draw(self, context):
        layout = self.layout
        props = context.scene.rage_studio
       
        # CodeWalker Integration
        box = layout.box()
        box.label(text="CodeWalker Integration", icon='SCRIPT')
        col = box.column(align=True)
        col.operator("rage.import_codewalker_xml", icon='IMPORT', text="Import CodeWalker XML")
        col.operator("rage.export_to_codewalker", icon='EXPORT', text="Export to CodeWalker")
        col.operator("rage.analyze_ymap", icon='FILE_SCRIPT', text="Analyze YMAP File")
       
        # CodeWalker Settings
        box = layout.box()
        box.label(text="CodeWalker Settings", icon='PREFERENCES')
        box.prop(props, "codewalker_directory")
        if props.codewalker_directory and not os.path.exists(props.codewalker_directory):
            box.label(text="⚠️ CodeWalker directory not found", icon='ERROR')
        elif props.codewalker_directory and os.path.exists(props.codewalker_directory):
            box.label(text="✅ CodeWalker directory found", icon='CHECKMARK')

class RAGE_PT_AssetBrowserPanel(Panel):
    bl_label = "Asset Browser"
    bl_idname = "RAGE_PT_asset_browser_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"
    bl_order = 7

    def draw(self, context):
        layout = self.layout
        props = context.scene.rage_studio
       
        # Asset Management
        box = layout.box()
        box.label(text="Asset Management", icon='ASSET_MANAGER')
       
        if props.game_directory and os.path.exists(props.game_directory):
            col = box.column(align=True)
            col.operator("rage.scan_game_assets", icon='FILE_FOLDER', text="Scan Game Assets")
            col.operator("rage.build_asset_library", icon='OUTLINER', text="Build Asset Library")
        else:
            box.label(text="Set Game Directory First", icon='ERROR')
       
        # Quick Asset Access
        box = layout.box()
        box.label(text="Quick Access", icon='RESTRICT_SELECT_OFF')
        row = box.row()
        row.operator("rage.browse_models", text="Models", icon='MESH_DATA')
        row.operator("rage.browse_textures", text="Textures", icon='TEXTURE')
       
        row = box.row()
        row.operator("rage.browse_maps", text="Maps", icon='WORLD_DATA')
        row.operator("rage.browse_vehicles", text="Vehicles", icon='CAR')

class RAGE_PT_AdvancedPanel(Panel):
    bl_label = "Advanced Tools"
    bl_idname = "RAGE_PT_advanced_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"
    bl_order = 8

    def draw(self, context):
        layout = self.layout
        props = context.scene.rage_studio
       
        # Analysis Tools
        box = layout.box()
        box.label(text="File Analysis", icon='FILE_SCRIPT')
        col = box.column(align=True)
        col.operator("rage.analyze_file", icon='TEXT', text="Analyze RDR1 File")
       
        if props.last_analyzed_file:
            box.label(text=f"Last: {os.path.basename(props.last_analyzed_file)}", icon='FILE_BLANK')
       
        # Mesh Processing
        box = layout.box()
        box.label(text="Mesh Processing", icon='MESH_DATA')
        col = box.column(align=True)
        col.operator("rage.split_mesh_for_collision", icon='MOD_PHYSICS', text="Split for Collision")
       
        # Bridge Configuration
        box = layout.box()
        box.label(text="Bridge Configuration", icon='LINKED')
        box.prop(props, "bridge_host")
        box.prop(props, "bridge_port")
        box.prop(props, "auto_connect")
       
        # Development
        box = layout.box()
        box.label(text="Development", icon='CONSOLE')
        box.prop(props, "debug_mode")
        if props.debug_mode:
            col = box.column(align=True)
            col.operator("rage.reload_scripts", text="Reload Scripts", icon='FILE_REFRESH')

class RAGE_UL_AssetList(UIList):
    """Professional asset list for displaying game assets"""
   
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon=self._get_asset_icon(item.type))
            layout.label(text=item.type)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=self._get_asset_icon(item.type))

    def _get_asset_icon(self, asset_type):
        """Get appropriate icon for asset type"""
        icons = {
            'MODEL': 'MESH_DATA',
            'TEXTURE': 'TEXTURE',
            'MAP': 'WORLD_DATA',
            'VEHICLE': 'CAR',
            'WEAPON': 'OBJECT_DATA',
            'PED': 'USER',
            'TERRAIN': 'MOD_OCEAN',
            'ROAD': 'MOD_CURVE',
        }
        return icons.get(asset_type, 'ASSET_MANAGER')

class RAGE_MT_AssetMenu(Menu):
    bl_label = "Asset Operations"
    bl_idname = "RAGE_MT_asset_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("rage.import_asset", icon='IMPORT')
        layout.operator("rage.export_asset", icon='EXPORT')
        layout.separator()
        layout.operator("rage.preview_asset", icon='VIEWZOOM')
        layout.operator("rage.analyze_asset", icon='SCRIPT')

# Professional registration
classes = (
    RAGE_PT_MainPanel,
    RAGE_PT_ImportPanel,
    RAGE_PT_ExportPanel,
    RAGE_PT_TerrainPanel,
    RAGE_PT_RoadPanel,
    RAGE_PT_CodeWalkerPanel,
    RAGE_PT_AssetBrowserPanel,
    RAGE_PT_AdvancedPanel,
    RAGE_UL_AssetList,
    RAGE_MT_AssetMenu,
)

def register():
    """Professional UI registration"""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"❌ Failed to register UI panel {cls.__name__}: {e}")
            raise

def unregister():
    """Professional UI unregistration"""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"⚠️ Failed to unregister UI panel {cls.__name__}: {e}")