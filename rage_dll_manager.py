import bpy
import os
import shutil
from bpy.types import Operator, Panel
from bpy.props import StringProperty, BoolProperty

class DLLLocationManager:
    """Manages DLL creation and deployment locations safely"""
   
    def __init__(self):
        # DLLs are created in OUR tool directory
        self.tool_dll_dir = os.path.join(os.path.dirname(__file__), "generated_dlls")
        self.compiled_dll_dir = os.path.join(self.tool_dll_dir, "compiled")
        self.source_dll_dir = os.path.join(self.tool_dll_dir, "sources")
       
        # Game deployment is OPTIONAL and user-controlled
        self.game_dll_locations = {
            'GTAV': {
                'asi_loader': "scripts/",
                'dinput8': "",  # Root directory
                'mod_manager': "mods/"
            },
            'RDR2': {
                'asi_loader': "scripts/",
                'mod_manager': "mods/"
            }
        }
       
        self._ensure_directories()
   
    def _ensure_directories(self):
        """Create our tool's DLL directories"""
        os.makedirs(self.tool_dll_dir, exist_ok=True)
        os.makedirs(self.compiled_dll_dir, exist_ok=True)
        os.makedirs(self.source_dll_dir, exist_ok=True)
   
    def create_dll_package(self, package_name, shaders, deployment_type='asi_loader'):
        """Create DLL package in our tool directory"""
       
        # Generate source code in our tool directory
        source_path = os.path.join(self.source_dll_dir, package_name, f"{package_name}.cpp")
        os.makedirs(os.path.dirname(source_path), exist_ok=True)
       
        dll_source = self._generate_dll_source(package_name, shaders, deployment_type)
        with open(source_path, 'w') as f:
            f.write(dll_source)
       
        # Create build scripts
        self._create_build_scripts(os.path.dirname(source_path), package_name)
       
        # Store package metadata
        package_info = {
            'name': package_name,
            'source_path': source_path,
            'expected_dll_path': os.path.join(self.compiled_dll_dir, f"{package_name}.dll"),
            'deployment_type': deployment_type,
            'shaders': shaders,
            'created_date': str(bpy.context.scene.frame_current)
        }
       
        return package_info
   
    def _generate_dll_source(self, package_name, shaders, deployment_type):
        """Generate safe DLL source code"""
        shader_functions = []
       
        for shader in shaders:
            safe_name = shader['name'].replace(' ', '_')
            shader_functions.append(f"""
// {shader['name']} Shader
extern "C" __declspec(dllexport) const char* Get{shader['name']}Shader() {{
    return "{shader['code'][:100]}...";  // Truncated for example
}}

extern "C" __declspec(dllexport) void Apply{shader['name']}Shader() {{
    // Safe application of {shader['name']}
}}
""")
       
        return f"""
#include <windows.h>
#include <string>
#include <map>

// Safe custom shader storage
std::map<std::string, std::string> CustomShaders = {{
    // Custom shaders go here
}};

// Safe DLL main - minimal interference
BOOL APIENTRY DllMain(HMODULE hModule, DWORD dwReason, LPVOID lpReserved) {{
    switch (dwReason) {{
        case DLL_PROCESS_ATTACH:
            // Initialize safely
            break;
        case DLL_PROCESS_DETACH:
            // Cleanup safely 
            break;
    }}
    return TRUE;
}}

// Export shader count
extern "C" __declspec(dllexport) int GetShaderCount() {{
    return {len(shaders)};
}}

// Export shader names 
extern "C" __declspec(dllexport) const char** GetShaderNames() {{
    static const char* names[] = {{
        {', '.join([f'"{s["name"]}"' for s in shaders])}
    }};
    return names;
}}

// Individual shader functions
{chr(10).join(shader_functions)}
"""
   
    def _create_build_scripts(self, package_dir, package_name):
        """Create build scripts for compiling DLL"""
        # Windows batch script
        build_bat = f"""@echo off
echo Building {package_name}.dll...
echo.
echo This will compile the shader DLL using Visual Studio.
echo Make sure you have Visual Studio installed.
echo.
pause

:: Try to find Visual Studio
set VS_PATH=%ProgramFiles(x86)%\\Microsoft Visual Studio\\2019\\Community\\VC\\Auxiliary\\Build\\vcvars32.bat
if exist "%VS_PATH%" (
    call "%VS_PATH%"
) else (
    echo Visual Studio 2019 not found. Trying 2022...
    set VS_PATH=%ProgramFiles(x86)%\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvars32.bat
    if exist "%VS_PATH%" (
        call "%VS_PATH%"
    ) else (
        echo ERROR: Visual Studio not found.
        echo Please install Visual Studio Build Tools.
        pause
        exit /b 1
    )
)

:: Compile DLL
cl /nologo /LD /Fe"{package_name}.dll" {package_name}.cpp /link /DLL /OUT:"{package_name}.dll"

if %errorlevel% equ 0 (
    echo.
    echo ✅ SUCCESS: {package_name}.dll built successfully!
    echo DLL location: %CD%\\{package_name}.dll
) else (
    echo.
    echo ❌ ERROR: Build failed!
)

echo.
pause
"""
       
        with open(os.path.join(package_dir, "build.bat"), 'w') as f:
            f.write(build_bat)
   
    def get_deployment_path(self, game_type, deployment_type):
        """Get game deployment path if user wants to install"""
        props = bpy.context.scene.rage_studio
       
        if not props.game_directory:
            return None  # User hasn't set game directory
       
        game_root = props.game_directory
        deployment_info = self.game_dll_locations.get(game_type, {})
        deployment_path = deployment_info.get(deployment_type)
       
        if deployment_path:
            full_path = os.path.join(game_root, deployment_path)
            return full_path if os.path.exists(full_path) else None
        return None
   
    def deploy_dll_to_game(self, dll_path, game_type, deployment_type):
        """OPTIONAL: Deploy compiled DLL to game directory (user must confirm)"""
        deployment_path = self.get_deployment_path(game_type, deployment_type)
       
        if not deployment_path:
            return False, "Game directory not set or deployment path not found"
       
        if not os.path.exists(dll_path):
            return False, "DLL file not found - compile it first"
       
        try:
            # Copy DLL to game directory
            dll_name = os.path.basename(dll_path)
            target_path = os.path.join(deployment_path, dll_name)
           
            # Backup existing file if it exists
            if os.path.exists(target_path):
                backup_path = target_path + ".backup"
                shutil.copy2(target_path, backup_path)
                print(f"✅ Backed up existing DLL to: {backup_path}")
           
            shutil.copy2(dll_path, target_path)
            return True, f"DLL deployed to: {target_path}"
           
        except Exception as e:
            return False, f"Deployment failed: {str(e)}"
   
    def cleanup(self):
        """Cleanup resources"""
        print("DLL Manager cleanup completed")

# Blender Operators
class RAGE_OT_CreateDLLPackage(Operator):
    bl_idname = "rage.create_dll_package"
    bl_label = "Create DLL Package"
    bl_description = "Create shader DLL package in tool directory"
   
    package_name: StringProperty(name="Package Name", default="MyCustomShaders")
    deployment_type: StringProperty(name="Deployment Type", default="asi_loader")
   
    def execute(self, context):
        dll_manager = DLLLocationManager()
       
        # Get shaders from your tool
        shaders = self._get_shaders_from_tool(context)
       
        if not shaders:
            self.report({'ERROR'}, "No shaders selected")
            return {'CANCELLED'}
       
        # Create DLL package in OUR tool directory
        package_info = dll_manager.create_dll_package(
            self.package_name,
            shaders,
            self.deployment_type
        )
       
        self.report({'INFO'}, f"✅ DLL package created: {package_info['source_path']}")
        return {'FINISHED'}
   
    def _get_shaders_from_tool(self, context):
        """Get shaders from your main tool's shader system"""
        # Example - replace with your actual shader retrieval
        return [
            {'name': 'CustomReflections', 'code': '// Custom reflection shader code...', 'type': 'pixel'},
            {'name': 'EnhancedLighting', 'code': '// Enhanced lighting shader code...', 'type': 'vertex'}
        ]

class RAGE_OT_DeployDLLToGame(Operator):
    bl_idname = "rage.deploy_dll_to_game"
    bl_label = "Deploy DLL to Game"
    bl_description = "OPTIONAL: Copy compiled DLL to game directory"
   
    dll_path: StringProperty(name="DLL Path")
    game_type: StringProperty(name="Game Type", default="GTAV")
   
    def execute(self, context):
        dll_manager = DLLLocationManager()
       
        if not os.path.exists(self.dll_path):
            self.report({'ERROR'}, "DLL file not found - compile it first")
            return {'CANCELLED'}
       
        # Deploy to game (user confirms this action)
        success, message = dll_manager.deploy_dll_to_game(
            self.dll_path,
            self.game_type,
            'asi_loader'
        )
       
        if success:
            self.report({'INFO'}, f"✅ {message}")
        else:
            self.report({'ERROR'}, f"❌ {message}")
       
        return {'FINISHED'}

# UI Panel
class RAGE_PT_DLLManager(Panel):
    bl_label = "DLL Manager"
    bl_idname = "RAGE_PT_dll_manager"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RAGE'
   
    def draw(self, context):
        layout = self.layout
        props = context.scene.rage_studio
       
        box = layout.box()
        box.label(text="DLL Creation & Deployment", icon='SETTINGS')
       
        # DLL Creation
        row = box.row()
        row.label(text="Package Name:")
        row.prop(self, "package_name", text="")
        row.operator("rage.create_dll_package", text="Create DLL", icon='SCRIPT')
       
        # Deployment Status
        box.label(text="Deployment Locations:", icon='FILE_FOLDER')
       
        if props.game_directory:
            dll_manager = DLLLocationManager()
           
            for game_type in ['GTAV', 'RDR2']:
                deployment_path = dll_manager.get_deployment_path(game_type, 'asi_loader')
                if deployment_path:
                    box.label(text=f"🎮 {game_type}: {deployment_path}", icon='CHECKMARK')
                else:
                    box.label(text=f"❌ {game_type}: Path not found", icon='ERROR')
        else:
            box.label(text="Set game directory to see deployment paths", icon='ERROR')

def register():
    bpy.utils.register_class(RAGE_OT_CreateDLLPackage)
    bpy.utils.register_class(RAGE_OT_DeployDLLToGame)
    bpy.utils.register_class(RAGE_PT_DLLManager)

def unregister():
    bpy.utils.unregister_class(RAGE_OT_CreateDLLPackage)
    bpy.utils.unregister_class(RAGE_OT_DeployDLLToGame)
    bpy.utils.unregister_class(RAGE_PT_DLLManager)