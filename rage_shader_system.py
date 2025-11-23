import bpy
import os
import json
import shutil
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, IntProperty

class ShaderDLLManager:
    """Complete DLL integration for RAGE Studio Suite"""
   
    def __init__(self, tool_dir):
        self.tool_dir = tool_dir
        self.dll_dir = os.path.join(tool_dir, "shader_dlls")
        self.config_file = os.path.join(tool_dir, "shader_config.json")
        os.makedirs(self.dll_dir, exist_ok=True)
        self.shader_config = self._load_config()
   
    def _load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {"active_shaders": [], "dll_mappings": {}, "shader_presets": {}}
   
    def create_shader_package(self, package_name, shaders):
        package_dir = os.path.join(self.dll_dir, package_name)
        os.makedirs(package_dir, exist_ok=True)
       
        dll_source = self._generate_dll_source(package_name, shaders)
        with open(os.path.join(package_dir, f"{package_name}.cpp"), 'w') as f:
            f.write(dll_source)
       
        package_data = {
            "package_name": package_name,
            "shaders": shaders,
            "source_dir": package_dir
        }
       
        self.shader_config["shader_presets"][package_name] = package_data
        self._save_config()
        return package_dir
   
    def _generate_dll_source(self, package_name, shaders):
        shader_declarations = []
        shader_definitions = []
       
        for shader in shaders:
            shader_name = shader['name'].replace(' ', '_').upper()
            shader_declarations.append(f"extern \"C\" __declspec(dllexport) const char* Get{shader_name}Shader();")
            shader_declarations.append(f"extern \"C\" __declspec(dllexport) void Apply{shader_name}Shader();")
            shader_definitions.append(f"const char* Get{shader_name}Shader() {{ return \"{shader['name']}_DATA\"; }}")
            shader_definitions.append(f"void Apply{shader_name}Shader() {{ /* Apply {shader['name']} */ }}")
       
        return f"""
#include <windows.h>

class ShaderManager {{
public:
    static ShaderManager& GetInstance() {{
        static ShaderManager instance;
        return instance;
    }}
    void ApplyShader(const char* shaderName) {{ }}
}};

BOOL APIENTRY DllMain(HMODULE hModule, DWORD dwReason, LPVOID lpReserved) {{
    return TRUE;
}}

extern "C" __declspec(dllexport) int GetShaderCount() {{ return {len(shaders)}; }}

extern "C" __declspec(dllexport) const char** GetShaderNames() {{
    static const char* names[] = {{ {', '.join([f'"{s["name"]}"' for s in shaders])} }};
    return names;
}}

{chr(10).join(shader_declarations)}

{chr(10).join(shader_definitions)}
"""
   
    def _save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.shader_config, f, indent=2)
   
    def get_active_shaders(self):
        return self.shader_config.get("active_shaders", [])
   
    def create_build_script(self, package_dir, package_name):
        build_script = f"""
@echo off
echo Building {package_name}.dll...
cl /nologo /LD /Fe"{package_name}.dll" {package_name}.cpp /link /DLL
if %errorlevel% equ 0 (echo ✅ Success!) else (echo ❌ Failed!)
pause
"""
        with open(os.path.join(package_dir, "build.bat"), 'w') as f:
            f.write(build_script)

class RAGE_OT_CreateShaderDLL(Operator):
    bl_idname = "rage.create_shader_dll"
    bl_label = "Create Shader DLL Package"
    bl_description = "Create DLL package with multiple shaders"
   
    package_name: StringProperty(name="Package Name", default="MyShaders")
   
    def execute(self, context):
        shaders = []
        for item in getattr(context.scene, 'rage_shader_list', []):
            if getattr(item, 'selected', False):
                shaders.append({
                    'name': item.name,
                    'code': getattr(item, 'code', ''),
                    'type': getattr(item, 'shader_type', 'pixel')
                })
       
        if not shaders:
            self.report({'ERROR'}, "No shaders selected")
            return {'CANCELLED'}
       
        tool_dir = os.path.dirname(os.path.abspath(__file__))
        dll_manager = ShaderDLLManager(tool_dir)
        package_dir = dll_manager.create_shader_package(self.package_name, shaders)
        dll_manager.create_build_script(package_dir, self.package_name)
       
        self.report({'INFO'}, f"Shader DLL created: {package_dir}")
        return {'FINISHED'}

class RAGE_OT_LoadShaderDLL(Operator):
    bl_idname = "rage.load_shader_dll"
    bl_label = "Load Shader DLL"
    bl_description = "Load and activate shader DLL package"
   
    filepath: StringProperty(subtype='FILE_PATH')
   
    def execute(self, context):
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, "DLL file not found")
            return {'CANCELLED'}
       
        tool_dir = os.path.dirname(os.path.abspath(__file__))
        dll_manager = ShaderDLLManager(tool_dir)
       
        dll_name = os.path.basename(self.filepath)
        if dll_name not in dll_manager.shader_config["active_shaders"]:
            dll_manager.shader_config["active_shaders"].append(dll_name)
            dll_manager.shader_config["dll_mappings"][dll_name] = self.filepath
            dll_manager._save_config()
       
        self.report({'INFO'}, f"Shader DLL loaded: {dll_name}")
        return {'FINISHED'}
   
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(RAGE_OT_CreateShaderDLL)
    bpy.utils.register_class(RAGE_OT_LoadShaderDLL)

def unregister():
    bpy.utils.unregister_class(RAGE_OT_CreateShaderDLL)
    bpy.utils.unregister_class(RAGE_OT_LoadShaderDLL)