# __init__.py
# RAGE Studio Suite - Universal RAGE Engine Modding Toolkit

bl_info = {
    "name": "RAGE Studio Suite",
    "author": "N8Gamez + RAGE Modding Community",
    "version": (2, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > RAGE",
    "description": "Universal RAGE Engine Toolkit with 100% Binary Export & Real-time Game Integration",
    "category": "Development",
    "warning": "Requires RAGE game files for full functionality",
    "doc_url": "https://github.com/rage-modding/rage-studio-suite",
    "tracker_url": "https://github.com/rage-modding/rage-studio-suite/issues"
}

import bpy
import os
import sys
import importlib
from bpy.app.handlers import persistent

# Add current directory to path for module imports
if __name__ == "__main__" or "__package__" not in globals():
    package_dir = os.path.dirname(os.path.abspath(__file__))
    if package_dir not in sys.path:
        sys.path.insert(0, package_dir)

# Import modules (Ensure these files are present in the same folder)
try:
    from . import file_analyzer
    from . import properties
    from . import ui_panels
    from . import operators
    from . import exporter
    from . import terrain_tools
    from . import road_tools
    from . import codewalker_integration
    from . import asset_browser
    from . import utilities
    # NEW: Import the complete RAGE binary systems
    from . import rage_binary_core
    from . import rage_shader_system
    from . import rage_dll_manager
    from . import rage_game_integration

    # Module reloading for development
    modules = (
        file_analyzer,
        properties,
        ui_panels,
        operators,
        exporter,
        terrain_tools,
        road_tools,
        codewalker_integration,
        asset_browser,
        utilities,
        # NEW: Add the RAGE binary modules
        rage_binary_core,
        rage_shader_system,
        rage_dll_manager,
        rage_game_integration,
    )
except ImportError as e:
    print(f"RAGE Studio Suite: Failed to import modules - {e}")
    modules = ()

def reload_modules():
    """Reload all modules for development"""
    for module in modules:
        try:
            importlib.reload(module)
        except Exception as e:
            print(f"RAGE Studio Suite: Failed to reload {module} - {e}")

# Combined classes from all modules
classes = ()

def get_classes():
    """Dynamically get classes to avoid import issues"""
    class_list = []
   
    # Properties
    try:
        from .properties import (
            RAGEExportSettings,
            RAGEImportSettings,
            RAGETerrainSettings,
            RAGERoadSettings,
            RAGEStudioProperties
        )
        class_list.extend([
            RAGEExportSettings,
            RAGEImportSettings,
            RAGETerrainSettings,
            RAGERoadSettings,
            RAGEStudioProperties,
        ])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import properties - {e}")

    # UI Panels
    try:
        from .ui_panels import (
            RAGE_PT_MainPanel,
            RAGE_PT_ImportPanel,
            RAGE_PT_ExportPanel,
            RAGE_PT_TerrainPanel,
            RAGE_PT_RoadPanel,
            RAGE_PT_CodeWalkerPanel,
            RAGE_PT_AdvancedPanel,
            RAGE_PT_AssetBrowserPanel,
            RAGE_UL_AssetList,
            RAGE_MT_AssetMenu
        )
        class_list.extend([
            RAGE_PT_MainPanel,
            RAGE_PT_ImportPanel,
            RAGE_PT_ExportPanel,
            RAGE_PT_TerrainPanel,
            RAGE_PT_RoadPanel,
            RAGE_PT_CodeWalkerPanel,
            RAGE_PT_AdvancedPanel,
            RAGE_PT_AssetBrowserPanel,
            RAGE_UL_AssetList,
            RAGE_MT_AssetMenu,
        ])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import UI panels - {e}")

    # Core Operators
    try:
        from .operators import (
            RAGE_OT_ConnectBridge,
            RAGE_OT_DisconnectBridge,
            RAGE_OT_AnalyzeFile,
            RAGE_OT_ExportSelected,
            RAGE_OT_ImportRAGEModel,
            RAGE_OT_SplitMeshForCollision,
            RAGE_OT_ExportCollisionMesh,
            RAGE_OT_GenerateRiver,
            RAGE_OT_ScanGameAssets,
            RAGE_OT_ReloadScripts,
            RAGE_OT_SetGameType
        )
        class_list.extend([
            RAGE_OT_ConnectBridge,
            RAGE_OT_DisconnectBridge,
            RAGE_OT_AnalyzeFile,
            RAGE_OT_ExportSelected,
            RAGE_OT_ImportRAGEModel,
            RAGE_OT_SplitMeshForCollision,
            RAGE_OT_ExportCollisionMesh,
            RAGE_OT_GenerateRiver,
            RAGE_OT_ScanGameAssets,
            RAGE_OT_ReloadScripts,
            RAGE_OT_SetGameType,
        ])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import core operators - {e}")

    # Terrain Tools
    try:
        from .terrain_tools import (
            RAGE_OT_ImportHeightmap,
            RAGE_OT_CreateTerrainGrid,
            RAGE_OT_GenerateTerrainLODs,
            RAGE_OT_BoreTunnel,
            RAGE_OT_ExcavateArea
        )
        class_list.extend([
            RAGE_OT_ImportHeightmap,
            RAGE_OT_CreateTerrainGrid,
            RAGE_OT_GenerateTerrainLODs,
            RAGE_OT_BoreTunnel,
            RAGE_OT_ExcavateArea,
        ])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import terrain tools - {e}")

    # Road Tools
    try:
        from .road_tools import (
            RAGE_OT_CreateRoadFromCurve,
            RAGE_OT_GenerateRoadNetwork,
            RAGE_OT_ConvertCurveToRoad,
            RAGE_OT_GeneratePath
        )
        class_list.extend([
            RAGE_OT_CreateRoadFromCurve,
            RAGE_OT_GenerateRoadNetwork,
            RAGE_OT_ConvertCurveToRoad,
            RAGE_OT_GeneratePath,
        ])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import road tools - {e}")

    # CodeWalker Integration
    try:
        from .codewalker_integration import (
            RAGE_OT_ImportCodeWalkerXML,
            RAGE_OT_ExportToCodeWalker,
            RAGE_OT_AnalyzeYmap
        )
        class_list.extend([
            RAGE_OT_ImportCodeWalkerXML,
            RAGE_OT_ExportToCodeWalker,
            RAGE_OT_AnalyzeYmap,
        ])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import CodeWalker integration - {e}")

    # Asset Browser
    try:
        from .asset_browser import (
            RAGE_OT_BrowseModels,
            RAGE_OT_BrowseTextures,
            RAGE_OT_BrowseMaps,
            RAGE_OT_BrowseVehicles,
            RAGE_OT_PreviewAsset
        )
        class_list.extend([
            RAGE_OT_BrowseModels,
            RAGE_OT_BrowseTextures,
            RAGE_OT_BrowseMaps,
            RAGE_OT_BrowseVehicles,
            RAGE_OT_PreviewAsset,
        ])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import asset browser - {e}")

    # NEW: RAGE Binary Core Operators
    try:
        from .rage_binary_core import RAGE_OT_ExportBinarySelected
        class_list.extend([RAGE_OT_ExportBinarySelected])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import binary core - {e}")

    # NEW: Shader System Operators
    try:
        from .rage_shader_system import (
            RAGE_OT_CreateShaderDLL,
            RAGE_OT_LoadShaderDLL
        )
        class_list.extend([
            RAGE_OT_CreateShaderDLL,
            RAGE_OT_LoadShaderDLL,
        ])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import shader system - {e}")

    # NEW: DLL Manager Operators
    try:
        from .rage_dll_manager import (
            RAGE_OT_CreateDLLPackage,
            RAGE_OT_DeployDLLToGame,
            RAGE_PT_DLLManager
        )
        class_list.extend([
            RAGE_OT_CreateDLLPackage,
            RAGE_OT_DeployDLLToGame,
            RAGE_PT_DLLManager,
        ])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import DLL manager - {e}")

    # NEW: Game Integration Operators
    try:
        from .rage_game_integration import (
            RAGE_OT_StartGameStreaming,
            RAGE_OT_StopGameStreaming,
            RAGE_OT_ConnectToGame,
            RAGE_PT_GameIntegration
        )
        class_list.extend([
            RAGE_OT_StartGameStreaming,
            RAGE_OT_StopGameStreaming,
            RAGE_OT_ConnectToGame,
            RAGE_PT_GameIntegration,
        ])
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import game integration - {e}")

    # NEW: Heightmap Import/Export Splitter - Direct registration
    try:
        from .heightmap_import_export_splitter import register_heightmap_tools
        # This function will handle registration of its own classes
        heightmap_classes = register_heightmap_tools()
        class_list.extend(heightmap_classes)
        print("✅ Heightmap Import/Export Splitter integrated")
    except ImportError as e:
        print(f"RAGE Studio Suite: Failed to import heightmap tools - {e}")

    return class_list

@persistent
def load_handler(dummy):
    """Handle scene load and auto-connect to bridge"""
    try:
        props = bpy.context.scene.rage_studio
        if props and props.auto_connect and not props.bridge_connected:
            bpy.ops.rage.connect_bridge()
    except Exception as e:
        print(f"RAGE Studio Suite: Load handler error - {e}")

def register():
    print("=" * 60)
    print("🚀 Initializing RAGE Studio Suite v2.1.0")
    print("🎮 Universal RAGE Engine Toolkit - 100% COMPLETE")
    print("👤 Developed by: N8Gamez + RAGE Modding Community")
    print("📁 Supported: RDR1, RDR2, GTA V with 100% Binary Export")
    print("=" * 60)

    # Reload modules in development mode
    try:
        if (bpy.context.preferences.addons.get(__name__) and
            bpy.context.preferences.addons[__name__].preferences.get('debug_mode', False)):
            print("🔧 Development mode: Reloading modules...")
            reload_modules()
    except Exception as e:
        print(f"Development mode check failed: {e}")

    # Get classes dynamically
    global classes
    classes = get_classes()

    # Register all classes
    registered_count = 0
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            registered_count += 1
        except Exception as e:
            print(f"❌ Failed to register {cls.__name__}: {e}")

    print(f"✅ Registered {registered_count}/{len(classes)} classes")

    # Register properties
    try:
        from .properties import RAGEStudioProperties
        bpy.types.Scene.rage_studio = bpy.props.PointerProperty(type=RAGEStudioProperties)
        print("✅ Registered scene properties")
    except Exception as e:
        print(f"❌ Failed to register properties: {e}")

    # Initialize global bridge instance
    if not hasattr(bpy.types.Scene, 'rage_bridge'):
        bpy.types.Scene.rage_bridge = None
        print("✅ Initialized bridge instance")

    # NEW: Initialize game streaming system
    if not hasattr(bpy.types.Scene, 'rage_game_streamer'):
        bpy.types.Scene.rage_game_streamer = None
        print("✅ Initialized game streaming system")

    # NEW: Initialize DLL manager
    if not hasattr(bpy.types.Scene, 'rage_dll_manager'):
        bpy.types.Scene.rage_dll_manager = None
        print("✅ Initialized DLL management system")

    # Register load handler
    bpy.app.handlers.load_post.append(load_handler)

    print(f"🎯 RAGE Studio Suite v2.1.0 successfully loaded!")
    print(" ✅ 100% Binary Exporters Active")
    print(" ✅ Real-time Game Streaming Ready")
    print(" ✅ Multi-Shader DLL System Online")
    print(" ✅ Safe DLL Management Active")
    print(" Use the RAGE panel in 3D Viewport sidebar")
    print("=" * 60)

def unregister():
    print("🔄 Unregistering RAGE Studio Suite v2.1.0...")

    # Remove load handler
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)

    # Clean up bridge connection
    if hasattr(bpy.types.Scene, 'rage_bridge') and bpy.types.Scene.rage_bridge:
        try:
            bpy.types.Scene.rage_bridge.disconnect()
        except:
            pass

    # NEW: Clean up game streaming
    if hasattr(bpy.types.Scene, 'rage_game_streamer') and bpy.types.Scene.rage_game_streamer:
        try:
            bpy.types.Scene.rage_game_streamer.stop_streaming()
        except:
            pass

    # NEW: Clean up DLL manager
    if hasattr(bpy.types.Scene, 'rage_dll_manager') and bpy.types.Scene.rage_dll_manager:
        try:
            bpy.types.Scene.rage_dll_manager.cleanup()
        except:
            pass

    # Unregister classes in reverse order
    unregistered_count = 0
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            unregistered_count += 1
        except Exception as e:
            print(f"❌ Failed to unregister {cls.__name__}: {e}")

    print(f"✅ Unregistered {unregistered_count}/{len(classes)} classes")

    # Clean up properties
    try:
        del bpy.types.Scene.rage_studio
        print("✅ Removed scene properties")
    except:
        pass

    print("✅ RAGE Studio Suite v2.1.0 unregistered successfully")

# Auto-register when running as script
if __name__ == "__main__":
    register()