import bpy
import os
import bmesh
import mathutils
from bpy.types import Operator
from bpy.props import (StringProperty, BoolProperty, IntProperty,
                      FloatProperty, EnumProperty, CollectionProperty)
from bpy_extras.io_utils import ImportHelper, ExportHelper

from .file_analyzer import CSharpBridge, RDR1FileAnalyzer
from .exporter import RAGEUniversalExporter

class RAGE_OT_ConnectBridge(Operator):
    bl_idname = "rage.connect_bridge"
    bl_label = "Connect to Bridge"
    bl_description = "Establish connection to C# backend bridge server"
   
    def execute(self, context):
        props = context.scene.rage_studio
       
        # Initialize bridge if needed
        if not hasattr(bpy.types.Scene, 'rage_bridge') or bpy.types.Scene.rage_bridge is None:
            bpy.types.Scene.rage_bridge = CSharpBridge()
       
        bridge = bpy.types.Scene.rage_bridge
       
        if bridge.connected:
            self.report({'INFO'}, "Bridge already connected")
            return {'FINISHED'}
       
        # Attempt connection with professional error handling
        try:
            if bridge.connect(props.bridge_host, props.bridge_port):
                props.bridge_connected = True
                self.report({'INFO'}, f"✅ Connected to bridge at {props.bridge_host}:{props.bridge_port}")
               
                # Verify connection
                if bridge.test_connection():
                    self.report({'INFO'}, "✅ Bridge connection verified")
                else:
                    self.report({'WARNING'}, "⚠️ Bridge connected but not responding")
            else:
                props.bridge_connected = False
                self.report({'ERROR'}, f"❌ Failed to connect to {props.bridge_host}:{props.bridge_port}")
               
        except Exception as e:
            props.bridge_connected = False
            self.report({'ERROR'}, f"❌ Connection error: {str(e)}")
       
        return {'FINISHED'}

class RAGE_OT_DisconnectBridge(Operator):
    bl_idname = "rage.disconnect_bridge"
    bl_label = "Disconnect Bridge"
    bl_description = "Disconnect from C# backend bridge server"
   
    def execute(self, context):
        props = context.scene.rage_studio
       
        if hasattr(bpy.types.Scene, 'rage_bridge') and bpy.types.Scene.rage_bridge:
            bpy.types.Scene.rage_bridge.disconnect()
       
        props.bridge_connected = False
        self.report({'INFO'}, "✅ Bridge disconnected")
       
        return {'FINISHED'}

class RAGE_OT_SetGameType(Operator):
    bl_idname = "rage.set_game_type"
    bl_label = "Set Game Type"
    bl_description = "Set the current RAGE game type for operations"
   
    game_type: EnumProperty(
        name="Game Type",
        description="Target RAGE game",
        items=[
            ('RDR1', 'Red Dead Redemption 1', 'RDR1 PC modding tools'),
            ('RDR2', 'Red Dead Redemption 2', 'RDR2 PC modding tools'),
            ('GTAV', 'Grand Theft Auto V', 'GTA V PC modding tools')
        ],
        default='GTAV'
    )
   
    def execute(self, context):
        props = context.scene.rage_studio
        props.current_game = self.game_type
        self.report({'INFO'}, f"🎮 Game type set to: {self.game_type}")
        return {'FINISHED'}

class RAGE_OT_AnalyzeFile(Operator, ImportHelper):
    bl_idname = "rage.analyze_file"
    bl_label = "Analyze RAGE File"
    bl_description = "Analyze RAGE file format and structure with detailed reporting"
   
    filename_ext = ".*"
    filter_glob: StringProperty(
        default="*.*",
        options={'HIDDEN'}
    )
   
    def execute(self, context):
        props = context.scene.rage_studio
       
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, f"❌ File not found: {self.filepath}")
            return {'CANCELLED'}
       
        analyzer = RDR1FileAnalyzer()
       
        try:
            format_name, header = analyzer.analyze_file(self.filepath)
            details = analyzer.get_format_details(self.filepath)
           
            props.last_analyzed_file = self.filepath
           
            # Professional reporting
            self.report({'INFO'}, f"📄 File type: {format_name}")
           
            if props.debug_mode:
                print(f"\n🔍 RAGE File Analysis Report")
                print(f"   File: {self.filepath}")
                print(f"   Format: {format_name}")
                print(f"   Size: {details['file_size']:,} bytes")
                print(f"   Header: {details['header_hex']}")
               
                # Print detailed analysis
                for key, value in details.items():
                    if key not in ['format', 'file_size', 'header_hex']:
                        print(f"   {key}: {value}")
           
        except Exception as e:
            self.report({'ERROR'}, f"❌ Analysis failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}

class RAGE_OT_ExportSelected(Operator, ExportHelper):
    bl_idname = "rage.export_selected"
    bl_label = "Export Selected to RAGE"
    bl_description = "Export selected objects to RAGE format with professional processing"
   
    filename_ext = ".ydr"
    filter_glob: StringProperty(
        default="*.ydr;*.ydd;*.ytd;*.ybn;*.wdr;*.wdd;*.wtd;*.wbn",
        options={'HIDDEN'}
    )
   
    # Professional export options
    export_collision: BoolProperty(
        name="Export Collision",
        description="Export collision data with optimized meshes",
        default=True
    )
   
    export_lods: BoolProperty(
        name="Export LODs",
        description="Export Level of Detail meshes for performance",
        default=True
    )
   
    def execute(self, context):
        props = context.scene.rage_studio
       
        # Professional validation
        if not props.bridge_connected:
            self.report({'ERROR'}, "❌ Bridge not connected. Please connect first.")
            return {'CANCELLED'}
       
        if not context.selected_objects:
            self.report({'ERROR'}, "❌ No objects selected for export")
            return {'CANCELLED'}
       
        bridge = bpy.types.Scene.rage_bridge
        exporter = RAGEUniversalExporter(bridge)
       
        try:
            # Professional export settings
            settings = {
                'export_collision': self.export_collision,
                'export_lods': self.export_lods,
                'scale_factor': props.export_settings.scale_factor,
                'apply_modifiers': props.export_settings.apply_modifiers,
                'optimize_mesh': props.export_settings.optimize_mesh,
                'split_large_meshes': props.export_settings.split_large_meshes,
                'mesh_split_threshold': props.export_settings.mesh_split_threshold
            }
           
            # Start professional export
            message_id = exporter.export_selected(self.filepath, settings, props.current_game)
           
            if message_id:
                self.report({'INFO'}, f"🚀 Export started: {message_id}")
               
                # Professional callback handling
                def export_callback(response):
                    if response.get('success'):
                        self.report({'INFO'}, f"✅ Export completed: {self.filepath}")
                    else:
                        error_msg = response.get('error', 'Unknown error')
                        self.report({'ERROR'}, f"❌ Export failed: {error_msg}")
               
                bridge.callbacks[message_id] = export_callback
               
            else:
                self.report({'ERROR'}, "❌ Failed to start export process")
                return {'CANCELLED'}
               
        except Exception as e:
            self.report({'ERROR'}, f"❌ Export error: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def draw(self, context):
        """Professional export options UI"""
        layout = self.layout
        props = context.scene.rage_studio
       
        # Export options
        box = layout.box()
        box.label(text="Export Options", icon='EXPORT')
        box.prop(self, "export_collision")
        box.prop(self, "export_lods")
       
        # Current settings
        box = layout.box()
        box.label(text="Current Settings", icon='SETTINGS')
        box.prop(props.export_settings, "scale_factor")
        box.prop(props.export_settings, "apply_modifiers")
        box.prop(props.export_settings, "optimize_mesh")

class RAGE_OT_ImportRAGEModel(Operator, ImportHelper):
    bl_idname = "rage.import_rage_model"
    bl_label = "Import RAGE Model"
    bl_description = "Import RAGE model file with professional material and mesh processing"
   
    filename_ext = ".ydr"
    filter_glob: StringProperty(
        default="*.ydr;*.ydd;*.ytd;*.ybn;*.wdr;*.wdd;*.wtd;*.wbn",
        options={'HIDDEN'}
    )
   
    def execute(self, context):
        props = context.scene.rage_studio
       
        if not props.bridge_connected:
            self.report({'ERROR'}, "❌ Bridge not connected. Please connect first.")
            return {'CANCELLED'}
       
        bridge = bpy.types.Scene.rage_bridge
       
        try:
            # Professional import callback
            def import_callback(response):
                if response.get('success'):
                    mesh_data = response.get('mesh_data', {})
                    self._create_blender_mesh(mesh_data)
                    self.report({'INFO'}, f"✅ Import completed: {self.filepath}")
                else:
                    error_msg = response.get('error', 'Unknown error')
                    self.report({'ERROR'}, f"❌ Import failed: {error_msg}")
           
            # Send professional import command
            bridge.send_command(
                'import_model',
                {
                    'filepath': self.filepath,
                    'settings': {
                        'auto_scale': props.import_settings.auto_scale,
                        'import_textures': props.import_settings.import_textures,
                        'create_materials': props.import_settings.create_materials,
                        'import_lods': props.import_settings.import_lods,
                        'import_collision': props.import_settings.import_collision,
                        'merge_vertices': props.import_settings.merge_vertices
                    }
                },
                callback=import_callback
            )
           
            self.report({'INFO'}, f"🚀 Import started: {self.filepath}")
           
        except Exception as e:
            self.report({'ERROR'}, f"❌ Import error: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _create_blender_mesh(self, mesh_data):
        """Professional mesh creation from imported data"""
        try:
            import bmesh
            from mathutils import Vector
           
            mesh_name = mesh_data.get('name', 'RAGE_Model')
            vertices = mesh_data.get('vertices', [])
            faces = mesh_data.get('faces', [])
            normals = mesh_data.get('normals', [])
           
            # Create professional mesh object
            mesh = bpy.data.meshes.new(mesh_name)
            obj = bpy.data.objects.new(mesh_name, mesh)
           
            # Link to scene
            bpy.context.collection.objects.link(obj)
           
            # Professional bmesh processing
            bm = bmesh.new()
           
            # Add vertices professionally
            for v_data in vertices:
                if len(v_data) >= 3:
                    bm.verts.new((v_data[0], v_data[1], v_data[2]))
           
            bm.verts.ensure_lookup_table()
           
            # Add faces with error handling
            for f_data in faces:
                if len(f_data) >= 3:
                    try:
                        face_verts = [bm.verts[i] for i in f_data if i < len(bm.verts)]
                        if len(face_verts) >= 3:
                            bm.faces.new(face_verts)
                    except Exception as e:
                        print(f"⚠️ Failed to create face: {e}")
           
            # Professional mesh finalization
            bm.to_mesh(mesh)
            bm.free()
           
            # Set as active object
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
           
            # Apply normals if provided
            if normals and len(normals) == len(mesh.vertices):
                mesh.normals_split_custom_set([(n[0], n[1], n[2]) for n in normals])
                mesh.use_auto_smooth = True
           
            print(f"✅ Created mesh: {mesh_name} with {len(vertices)} vertices, {len(faces)} faces")
           
        except Exception as e:
            print(f"❌ Mesh creation error: {e}")
            raise

class RAGE_OT_SplitMeshForCollision(Operator):
    bl_idname = "rage.split_mesh_for_collision"
    bl_label = "Split Mesh for Collision"
    bl_description = "Split selected mesh into collision-friendly chunks using professional algorithms"
   
    def execute(self, context):
        if not context.active_object or context.active_object.type != 'MESH':
            self.report({'ERROR'}, "❌ Select a mesh object")
            return {'CANCELLED'}
       
        obj = context.active_object
        mesh = obj.data
       
        try:
            # Professional mesh splitting workflow
            bpy.ops.object.mode_set(mode='EDIT')
           
            # Select all faces
            bpy.ops.mesh.select_all(action='SELECT')
           
            # Professional separation by loose parts
            bpy.ops.mesh.separate(type='LOOSE')
           
            # Return to object mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            # Professional chunk naming and setup
            chunks = [obj for obj in context.selected_objects if obj != context.active_object]
            for i, chunk in enumerate(chunks):
                chunk.name = f"{obj.name}_collision_{i:02d}"
                # Professional collision properties
                chunk["rage_collision"] = True
                chunk.display_type = 'WIRE'
                chunk.hide_render = True
           
            self.report({'INFO'}, f"✅ Split mesh into {len(chunks)} collision chunks")
           
        except Exception as e:
            self.report({'ERROR'}, f"❌ Mesh split failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}

class RAGE_OT_ExportCollisionMesh(Operator, ExportHelper):
    bl_idname = "rage.export_collision_mesh"
    bl_label = "Export Collision Mesh"
    bl_description = "Export selected mesh as optimized RAGE collision data"
   
    filename_ext = ".ybn"
    filter_glob: StringProperty(
        default="*.ybn;*.wbn",
        options={'HIDDEN'}
    )
   
    def execute(self, context):
        props = context.scene.rage_studio
       
        if not props.bridge_connected:
            self.report({'ERROR'}, "❌ Bridge not connected")
            return {'CANCELLED'}
       
        # Professional collision object detection
        collision_objects = [obj for obj in context.selected_objects
                           if obj.type == 'MESH' and obj.get('rage_collision')]
       
        if not collision_objects:
            self.report({'ERROR'}, "❌ No collision meshes selected")
            return {'CANCELLED'}
       
        bridge = bpy.types.Scene.rage_bridge
       
        try:
            def export_callback(response):
                if response.get('success'):
                    self.report({'INFO'}, f"✅ Collision export completed: {self.filepath}")
                else:
                    error_msg = response.get('error', 'Unknown error')
                    self.report({'ERROR'}, f"❌ Collision export failed: {error_msg}")
           
            # Professional collision data preparation
            collision_data = {
                'objects': [],
                'export_path': self.filepath
            }
           
            for obj in collision_objects:
                mesh_data = self._extract_collision_mesh(obj)
                collision_data['objects'].append(mesh_data)
           
            bridge.send_command('export_collision', collision_data, callback=export_callback)
            self.report({'INFO'}, f"🚀 Exporting {len(collision_objects)} collision objects")
           
        except Exception as e:
            self.report({'ERROR'}, f"❌ Collision export error: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _extract_collision_mesh(self, obj):
        """Professional collision mesh extraction"""
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
       
        # Professional collision optimization
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.001)
       
        vertices = []
        for vert in bm.verts:
            vertices.append([vert.co.x, vert.co.y, vert.co.z])
       
        faces = []
        for face in bm.faces:
            if len(face.verts) == 3:
                faces.append([v.index for v in face.verts])
       
        bm.free()
       
        return {
            'name': obj.name,
            'vertices': vertices,
            'faces': faces,
            'location': list(obj.location),
            'rotation': list(obj.rotation_euler),
            'scale': list(obj.scale)
        }

class RAGE_OT_GenerateRiver(Operator):
    bl_idname = "rage.generate_river"
    bl_label = "Generate River"
    bl_description = "Generate professional river mesh from selected curve with realistic flow"
   
    river_width: FloatProperty(
        name="River Width",
        description="Width of the river in meters",
        default=10.0,
        min=1.0,
        max=100.0
    )
   
    river_depth: FloatProperty(
        name="River Depth",
        description="Depth of the river in meters",
        default=2.0,
        min=0.1,
        max=20.0
    )
   
    def execute(self, context):
        if not context.active_object or context.active_object.type != 'CURVE':
            self.report({'ERROR'}, "❌ Select a curve object for river path")
            return {'CANCELLED'}
       
        curve_obj = context.active_object
       
        try:
            # Professional river generation
            river_mesh = self._create_river_from_curve(curve_obj, self.river_width, self.river_depth)
            river_obj = bpy.data.objects.new(f"River_{curve_obj.name}", river_mesh)
           
            # Professional scene integration
            bpy.context.collection.objects.link(river_obj)
            river_obj.location = curve_obj.location
           
            # Professional river properties
            river_obj["rage_river"] = True
            river_obj["river_width"] = self.river_width
            river_obj["river_depth"] = self.river_depth
           
            # Professional material setup
            self._create_river_material(river_obj)
           
            self.report({'INFO'}, f"✅ River generated from {curve_obj.name}")
           
        except Exception as e:
            self.report({'ERROR'}, f"❌ River generation failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _create_river_from_curve(self, curve_obj, width, depth):
        """Professional river mesh creation"""
        # Create professional mesh data
        mesh = bpy.data.meshes.new("RiverMesh")
       
        # Convert curve to mesh professionally
        temp_mesh = curve_obj.to_mesh()
       
        # Professional bmesh processing
        bm = bmesh.new()
        bm.from_mesh(temp_mesh)
       
        # Extrude for river width professionally
        extruded = bmesh.ops.extrude_edge_only(bm, edges=bm.edges)
       
        # Professional scaling
        bmesh.ops.scale(bm, vec=(width, width, width), verts=extruded['geom'])
       
        # Professional face creation
        bmesh.ops.contextual_create(bm, geom=bm.edges)
       
        # Finalize mesh professionally
        bm.to_mesh(mesh)
        bm.free()
       
        # Cleanup
        bpy.data.meshes.remove(temp_mesh)
       
        return mesh
   
    def _create_river_material(self, river_obj):
        """Professional river material creation"""
        try:
            mat = bpy.data.materials.new(name="River_Material")
            mat.use_nodes = True
           
            # Professional water shader setup would go here
            # This is a placeholder for advanced water material
           
            if river_obj.data.materials:
                river_obj.data.materials[0] = mat
            else:
                river_obj.data.materials.append(mat)
               
        except Exception as e:
            print(f"⚠️ River material creation failed: {e}")

class RAGE_OT_ScanGameAssets(Operator):
    bl_idname = "rage.scan_game_assets"
    bl_label = "Scan Game Assets"
    bl_description = "Scan RAGE game directory for assets with professional database building"
   
    def execute(self, context):
        props = context.scene.rage_studio
       
        if not props.game_directory or not os.path.exists(props.game_directory):
            self.report({'ERROR'}, "❌ Game directory not set or invalid")
            return {'CANCELLED'}
       
        try:
            # Professional asset scanning
            asset_dirs = self._find_asset_directories(props.game_directory)
           
            if not asset_dirs:
                self.report({'WARNING'}, "⚠️ No RAGE asset directories found")
                return {'CANCELLED'}
           
            # Professional database building
            asset_count = self._build_asset_database(asset_dirs)
           
            self.report({'INFO'}, f"✅ Found {asset_count} assets in {len(asset_dirs)} directories")
           
        except Exception as e:
            self.report({'ERROR'}, f"❌ Asset scan failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _find_asset_directories(self, game_dir):
        """Professional asset directory discovery"""
        asset_dirs = []
       
        # Professional directory patterns for RAGE games
        potential_dirs = [
            'models',
            'textures',
            'maps',
            'levels',
            'x64',
            'dlcpacks',
            'stream',
            'x64e',
            'dlc_patch'
        ]
       
        for dir_name in potential_dirs:
            dir_path = os.path.join(game_dir, dir_name)
            if os.path.exists(dir_path):
                asset_dirs.append(dir_path)
       
        return asset_dirs
   
    def _build_asset_database(self, asset_dirs):
        """Professional asset database building"""
        asset_count = 0
       
        for asset_dir in asset_dirs:
            for root, dirs, files in os.walk(asset_dir):
                for file in files:
                    # Professional file type detection for all RAGE games
                    if any(file.lower().endswith(ext) for ext in ['.wdr', '.wdd', '.wtd', '.ymap', '.ytyp', '.ydr', '.ydd', '.ytd', '.ybn']):
                        asset_count += 1
       
        return asset_count

class RAGE_OT_ReloadScripts(Operator):
    bl_idname = "rage.reload_scripts"
    bl_label = "Reload Scripts"
    bl_description = "Reload RAGE Studio Suite scripts for professional development workflow"
   
    def execute(self, context):
        try:
            # Professional module reloading
            import importlib
            import sys
           
            # Find and reload our modules professionally
            modules_to_reload = []
            for module_name in list(sys.modules.keys()):
                if module_name.startswith('rage_studio_suite'):
                    modules_to_reload.append(module_name)
           
            for module_name in modules_to_reload:
                importlib.reload(sys.modules[module_name])
           
            self.report({'INFO'}, f"✅ Reloaded {len(modules_to_reload)} modules")
        except Exception as e:
            self.report({'ERROR'}, f"❌ Reload failed: {str(e)}")
       
        return {'FINISHED'}

# Professional operator registration
classes = (
    RAGE_OT_ConnectBridge,
    RAGE_OT_DisconnectBridge,
    RAGE_OT_SetGameType,
    RAGE_OT_AnalyzeFile,
    RAGE_OT_ExportSelected,
    RAGE_OT_ImportRAGEModel,
    RAGE_OT_SplitMeshForCollision,
    RAGE_OT_ExportCollisionMesh,
    RAGE_OT_GenerateRiver,
    RAGE_OT_ScanGameAssets,
    RAGE_OT_ReloadScripts,
)

def register():
    """Professional operator registration"""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"❌ Failed to register operator {cls.__name__}: {e}")
            raise

def unregister():
    """Professional operator unregistration"""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"⚠️ Failed to unregister operator {cls.__name__}: {e}")