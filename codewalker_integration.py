import bpy
import bmesh
import mathutils
import math
import random
import os
import subprocess
import xml.etree.ElementTree as ET
import json
import time
import shutil
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Euler
from bpy.types import Operator, Panel
from bpy.props import (StringProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty, PointerProperty)
from bpy_extras.io_utils import ImportHelper, ExportHelper

# Ensure the script runs as an add-on
bl_info = {
    "name": "RAGE Studio Integrated Suite",
    "author": "Gemini",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > RAGE",
    "description": "Tools for heightmap import, terrain splitting, and RAGE game engine map export.",
    "category": "Development",
}

# ============================= CORE HELPER SYSTEMS =============================
class RAGE_CollisionSystem:
    def __init__(self):
        self.collision_types = {'DEFAULT':0,'CONCRETE':1,'DIRT':2,'WATER':3,'WOOD':4,'METAL':5,'GLASS':6,'GRASS':7,'SAND':8,'ROCK':9}

    def generate_collision_mesh(self, obj, collision_type='DEFAULT', simplify=True):
        if not obj or obj.type != 'MESH':
            return None
   
        # Check if a collision object already exists for this mesh
        if bpy.data.objects.get(f"{obj.name}_collision"):
            # Optionally remove or update the existing one
            pass

        mesh = obj.data
        collision_obj = obj.copy()
        collision_obj.data = mesh.copy()
        collision_obj.name = f"{obj.name}_collision"
        bpy.context.collection.objects.link(collision_obj)
        collision_obj.display_type = 'WIRE' # Make collision mesh visually distinct
   
        if simplify:
            # Need to temporarily set active object to apply modifier
            # Ensure the object is in the visible layer collection
            if collision_obj.users_collection:
                bpy.context.view_layer.active_layer_collection.collection.objects.link(collision_obj)
               
            bpy.context.view_layer.objects.active = collision_obj
            # Ensure object is selected for the operator to work
            bpy.ops.object.select_all(action='DESELECT')
            collision_obj.select_set(True)

            # Apply scale/rotation before decimation for predictable results
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

            bpy.ops.object.modifier_add(type='DECIMATE')
            collision_obj.modifiers["Decimate"].ratio = 0.3
            # Apply the modifier
            try:
                bpy.ops.object.modifier_apply(modifier="Decimate")
            except RuntimeError as e:
                print(f"Warning: Could not apply Decimate modifier to {collision_obj.name}. Error: {e}")
           
            # Deselect the collision object for cleanup
            collision_obj.select_set(False)

        collision_obj["rage_collision_type"] = collision_type
        return collision_obj

class RAGE_StreamingSectors:
    def __init__(self):
        self.sector_size = 400.0
        self.sectors = {}

    def auto_partition_world(self, context, sector_size=400.0):
        self.sector_size = sector_size
        self.sectors = {}
        objects = [obj for obj in context.scene.objects if obj.type in {'MESH', 'EMPTY'} and obj.get("rage_sector")]
   
        for obj in objects:
            # Use the sector keys stored during the split operation
            sector_x = obj.get("sector_x", 0)
            sector_y = obj.get("sector_y", 0)
            sector_key = f"{sector_x}_{sector_y}"
       
            if sector_key not in self.sectors:
                self.sectors[sector_key] = []
            self.sectors[sector_key].append(obj)
        return self.sectors

    def export_ipl_files(self, context, export_path):
        # This will only export sectors that have been split using the RAGE_OT_split_terrain_grid operator
        if not self.sectors:
             self.auto_partition_world(context)

        path = Path(export_path)
        path.mkdir(parents=True, exist_ok=True)
       
        exported_count = 0
        for sector_key, objects in self.sectors.items():
            ipl_path = path / f"{sector_key}.ipl"
            with open(ipl_path, 'w') as f:
                f.write("inst\n")
                for obj in objects:
                    if obj.type == 'MESH' and obj.get("rage_sector"):
                        loc = obj.location
                        rot = obj.rotation_euler
                        scale = obj.scale
                        # Use the sector's base name (without "_Sector_x_y") as the model name in the IPL
                        base_name = "_".join(obj.name.split('_')[:-3])
                        f.write(f"{obj.name}, {base_name}.ydr, {loc.x}, {loc.y}, {loc.z}, {rot.x}, {rot.y}, {rot.z}, {scale.x}, {scale.y}, {scale.z}, -1, -1\n")
                        exported_count += 1
                f.write("end\n")
        return exported_count > 0

# Initialize Systems
collision_system = RAGE_CollisionSystem()
streaming_system = RAGE_StreamingSectors()

# ============================= PROPERTY GROUPS =============================
class RAGE_GameMode(bpy.types.PropertyGroup):
    game: bpy.props.EnumProperty(name="Game", items=[('GTAV',"GTA V / FiveM",""),('RDR2',"Red Dead 2",""),('RDR1',"Red Dead 1","")], default='GTAV')

class RAGE_Settings(bpy.types.PropertyGroup):
    fivem_resource_name: bpy.props.StringProperty(name="Resource Name", default="rage_map")
    # This is the master sector size used for splitting and visualization
    sector_size: bpy.props.FloatProperty(
        name="Sector Size",
        default=400.0,
        min=10.0,
        max=2000.0,
        description="Size of map chunks in meters. Triggers grid visualization update."
    )
    show_grid_preview: bpy.props.BoolProperty(
        name="Preview Grid",
        default=False,
        description="Show visual overlay of split sectors",
        update=lambda s, c: bpy.ops.rage.toggle_grid_preview('EXEC')
    )
    # New property for export format selection
    export_format: bpy.props.EnumProperty(
        name="Export Format",
        items=[
            ('OBJ', "Wavefront OBJ (.obj)", "Standard format"),
            ('FBX', "Filmbox (.fbx)", "Industry standard format"),
            ('GLTF', "glTF (.gltf/.glb)", "Modern 3D file format")
        ],
        default='OBJ'
    )

# ============================= TERRAIN OPERATORS =============================

class RAGE_OT_toggle_grid_preview(bpy.types.Operator):
    bl_idname = "rage.toggle_grid_preview"
    bl_label = "Update Grid Preview"
    bl_description = "Creates or removes the visual grid overlay based on Sector Size"

    # Only used for the update function call from the BoolProperty
    def execute(self, context):
        terrain_obj = context.active_object
       
        # 1. Always attempt to remove existing preview
        prev_preview = bpy.data.objects.get("RAGE_Sector_Preview")
        if prev_preview:
            # Need to move object into scene collection to remove it if it was linked elsewhere
            for collection in bpy.data.collections:
                if prev_preview.name in collection.objects:
                    collection.objects.unlink(prev_preview)

            bpy.data.objects.remove(prev_preview)
           
        # 2. Check the settings property to decide if we need to redraw
        if context.scene.rage_settings.show_grid_preview and terrain_obj and terrain_obj.type == 'MESH':
            self.create_grid_visual(context, terrain_obj)
            return {'FINISHED'}
        elif context.scene.rage_settings.show_grid_preview and (not terrain_obj or terrain_obj.type != 'MESH'):
            # If the user toggles it on without a mesh selected, warn them but keep the setting.
            self.report({'WARNING'}, "Select a terrain mesh object to show the grid.")
            return {'CANCELLED'}
       
        return {'FINISHED'} # Successfully toggled/removed the grid

    def create_grid_visual(self, context, terrain_obj):
        sector_size = context.scene.rage_settings.sector_size
      
        # Calculate bounds in world space
        # Use calc_scene_render_bounds for more accurate world-space bounding box
        bbox_corners = [terrain_obj.matrix_world @ Vector(corner) for corner in terrain_obj.bound_box]
        min_x = min(v.x for v in bbox_corners)
        max_x = max(v.x for v in bbox_corners)
        min_y = min(v.y for v in bbox_corners)
        max_y = max(v.y for v in bbox_corners)
        min_z = min(v.z for v in bbox_corners)
        max_z = max(v.z for v in bbox_corners)

        width = max_x - min_x
        height = max_y - min_y
      
        # Calculate the number of splits required
        cols = math.ceil(width / sector_size)
        rows = math.ceil(height / sector_size)

        bm = bmesh.new()
       
        # Determine the height for the grid lines
        grid_height = max_z + 1.0 # Place grid 1 unit above the highest point

        # Create grid lines
        # Vertical lines (X-axis)
        for i in range(cols + 1):
            x = min_x + (i * sector_size)
            # Ensure the last line doesn't overshoot if the size is an exact multiple
            if i == cols: x = max_x
           
            # Create a line slightly above the terrain
            v1 = bm.verts.new((x, min_y, grid_height))
            v2 = bm.verts.new((x, max_y, grid_height))
            bm.edges.new((v1, v2))
          
        # Horizontal lines (Y-axis)
        for i in range(rows + 1):
            y = min_y + (i * sector_size)
            # Ensure the last line doesn't overshoot if the size is an exact multiple
            if i == rows: y = max_y

            v1 = bm.verts.new((min_x, y, grid_height))
            v2 = bm.verts.new((max_x, y, grid_height))
            bm.edges.new((v1, v2))

        mesh = bpy.data.meshes.new("RAGE_Sector_Preview_Data")
        bm.to_mesh(mesh)
        bm.free()

        grid_obj = bpy.data.objects.new("RAGE_Sector_Preview", mesh)
        context.collection.objects.link(grid_obj)
      
        # Visual settings: make it visible over the terrain
        grid_obj.display_type = 'WIRE'
        grid_obj.show_in_front = True # Always visible, even behind objects
        grid_obj.color = (1.0, 0.5, 0.0, 1.0) # Orange
        grid_obj.location = (0, 0, 0) # Location is handled by the world-space coordinates of the grid lines
       
        # Link to the scene collection (and the active layer)
        if not grid_obj.users_collection:
             context.collection.objects.link(grid_obj)


class RAGE_OT_import_heightmap(bpy.types.Operator, ImportHelper):
    bl_idname = "rage.import_heightmap"
    bl_label = "Import Heightmap"
    bl_description = "Import terrain from heightmap image and apply scaling"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.png;*.jpg;*.jpeg;*.tiff;*.tif;*.exr", options={'HIDDEN'})
    # These properties control the X, Y, and Z scaling of the imported map
    size: bpy.props.FloatProperty(name="Terrain XY Scale", default=1000.0, min=1.0, max=10000.0, description="Overall width/length of the terrain mesh (X/Y scale)")
    height: bpy.props.FloatProperty(name="Max Height (Z Scale)", default=100.0, min=1.0, max=1000.0, description="Maximum vertical displacement/height (Z scale)")
    subdivisions: bpy.props.IntProperty(name="Subdivisions", default=256, min=16, max=2048, description="Resolution of the initial mesh grid")

    def execute(self, context):
        try:
            # 1. Create the base grid mesh
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=self.subdivisions, y_subdivisions=self.subdivisions, size=self.size, location=(0, 0, 0))
            terrain_obj = context.active_object
            terrain_obj.name = os.path.splitext(os.path.basename(self.filepath))[0] + "_Terrain" # Use filename for better naming
           
            # 2. Add Displace modifier
            disp_mod = terrain_obj.modifiers.new(name="Heightmap", type='DISPLACE')
           
            # 3. Load image and create texture
            img = bpy.data.images.load(self.filepath)
            tex = bpy.data.textures.new(f"Tex_{terrain_obj.name}", type='IMAGE')
            tex.image = img
          
            # 4. Configure and apply modifier
            disp_mod.texture = tex
            disp_mod.strength = self.height # This controls the Z scale
            disp_mod.texture_coords = 'UV'
          
            # Apply the modifier to bake the displacement into the mesh geometry
            bpy.ops.object.modifier_apply(modifier="Heightmap")
           
            # Set custom property for identification
            terrain_obj["rage_terrain"] = True
          
            self.report({'INFO'}, f"Heightmap imported and scaled: {terrain_obj.name}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import heightmap: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class RAGE_OT_split_terrain_grid(bpy.types.Operator):
    bl_idname = "rage.split_terrain_grid"
    bl_label = "Split Terrain by Sector Size"
    bl_description = "Split terrain into grid chunks based on the Sector Size setting. The original object will be hidden."

    create_collision: bpy.props.BoolProperty(name="Create Collision", default=True, description="Generate simplified collision meshes for each sector")
   
    # Use an Enum for the collision material type, linking to the core system
    collision_type: bpy.props.EnumProperty(
        name="Collision Type",
        items=[(k, k.replace('_', ' ').title(), "") for k in RAGE_CollisionSystem().collision_types.keys()],
        default='DEFAULT'
    )

    def execute(self, context):
        terrain_obj = context.active_object
      
        if not terrain_obj or terrain_obj.type != 'MESH' or not terrain_obj.get("rage_terrain"):
            self.report({'ERROR'}, "Select a terrain mesh that was imported/marked as 'rage_terrain'")
            return {'CANCELLED'}

        # Ensure the preview is off and removed
        preview = bpy.data.objects.get("RAGE_Sector_Preview")
        if preview:
            # Setting the property to False triggers the cleanup in the toggle operator
            context.scene.rage_settings.show_grid_preview = False
       
        # Apply current transformations (rotation/scale) before splitting
        bpy.ops.object.select_all(action='DESELECT')
        terrain_obj.select_set(True)
        context.view_layer.objects.active = terrain_obj
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        terrain_obj.select_set(False)

        sector_size = context.scene.rage_settings.sector_size
        original_location = terrain_obj.location.copy()
        original_name = terrain_obj.name
   
        # Get world-space bounds after applying transformations
        bbox_corners = [terrain_obj.matrix_world @ Vector(corner) for corner in terrain_obj.bound_box]
        min_x = min(v.x for v in bbox_corners)
        max_x = max(v.x for v in bbox_corners)
        min_y = min(v.y for v in bbox_corners)
        max_y = max(v.y for v in bbox_corners)
        min_z = min(v.z for v in bbox_corners)
        max_z = max(v.z for v in bbox_corners)
       
        terrain_z_height = max_z - min_z
        terrain_width = max_x - min_x
        terrain_height = max_y - min_y
   
        # Dynamic calculation based on Sector Size
        grid_cols = math.ceil(terrain_width / sector_size)
        grid_rows = math.ceil(terrain_height / sector_size)
   
        # Collection for the new sectors
        sectors_collection = bpy.data.collections.get(f"{original_name}_Sectors")
        if not sectors_collection:
            sectors_collection = bpy.data.collections.new(f"{original_name}_Sectors")
            context.scene.collection.children.link(sectors_collection)
   
        created_sectors = []
   
        # Loop through the grid pattern to perform the cuts
        for x in range(grid_cols):
            for y in range(grid_rows):
                # Calculate sector bounds
                sector_min_x = min_x + (x * sector_size)
                sector_max_x = sector_min_x + sector_size
                sector_min_y = min_y + (y * sector_size)
                sector_max_y = sector_min_y + sector_size
           
                # Duplicate the original terrain object
                sector_obj = terrain_obj.copy()
                # Create a deep copy of the mesh data
                sector_obj.data = terrain_obj.data.copy()
                sector_obj.name = f"{original_name}_Sector_{x}_{y}"
                sectors_collection.objects.link(sector_obj)
   
                # Create boolean box to cut sector
                bpy.ops.mesh.primitive_cube_add(
                    location=(
                        (sector_min_x + sector_max_x) / 2,
                        (sector_min_y + sector_max_y) / 2,
                        (min_z + max_z) / 2 # Center Z of the cutter
                    ),
                    scale=(1, 1, 1) # Reset scale for correct scaling below
                )
                cutter_obj = context.active_object
                cutter_obj.name = f"Cutter_{x}_{y}"
               
                # Scale cutter to fit sector size, ensuring it covers all Z-height
                cutter_obj.scale = (
                    sector_size / 2,
                    sector_size / 2,
                    (terrain_z_height / 2) + 10.0 # Add buffer height
                )
           
                # Add boolean modifier to the duplicated sector
                bool_mod = sector_obj.modifiers.new(name="SectorCut", type='BOOLEAN')
                bool_mod.operation = 'INTERSECT'
                bool_mod.object = cutter_obj
                bool_mod.solver = 'EXACT' # Ensures clean cut on complex meshes
           
                # Apply the modifier
                context.view_layer.objects.active = sector_obj
                sector_obj.select_set(True)
                bpy.ops.object.modifier_apply(modifier="SectorCut")
                sector_obj.select_set(False)
               
                # Delete the cutter object
                bpy.data.objects.remove(cutter_obj, do_unlink=True)
               
                # If mesh is empty after cut (empty sector), remove it
                if len(sector_obj.data.vertices) == 0:
                    bpy.data.objects.remove(sector_obj, do_unlink=True)
                    continue

                # Generate Collision Mesh if requested
                if self.create_collision:
                    collision_obj = collision_system.generate_collision_mesh(sector_obj, collision_type=self.collision_type, simplify=True)
                    if collision_obj:
                        # Collision mesh is created in the main collection, link to sector collection
                        sectors_collection.objects.link(collision_obj)
                        context.scene.collection.objects.unlink(collision_obj) # Unlink from main scene
           
                # Set custom properties for identification and streaming setup
                sector_obj["rage_sector"] = True
                sector_obj["sector_x"] = x
                sector_obj["sector_y"] = y
                created_sectors.append(sector_obj)
   
        # Hide and disable the original terrain object
        terrain_obj.hide_set(True)
        terrain_obj.hide_render = True
   
        self.report({'INFO'}, f"Successfully created {len(created_sectors)} terrain sectors in collection '{sectors_collection.name}'")
        return {'FINISHED'}

# ============================= EXPORT OPERATORS =============================

class RAGE_OT_export_all_tiles(bpy.types.Operator, ExportHelper):
    bl_idname = "rage.export_all_tiles"
    bl_label = "Export All Split Tiles"
    bl_description = "Exports all visible split sectors and collisions to a selected format, creating a directory based on the original mesh name."

    # Use a directory path instead of a file path since we export multiple files
    filepath: bpy.props.StringProperty(subtype="DIR_PATH")
   
    # Use the format property from RAGE_Settings
    @classmethod
    def poll(cls, context):
        # Poll function to ensure we only run if there are sectors to export
        return any(obj.get("rage_sector") for obj in context.scene.objects)

    def execute(self, context):
        # Determine the base directory for the export
        if not self.filepath:
            self.report({'ERROR'}, "Export path not selected.")
            return {'CANCELLED'}

        # Find the original terrain object name to use for the directory
        original_terrain_name = "Exported_Tiles"
        for obj in context.scene.objects:
            if obj.get("rage_terrain") and obj.name.endswith("_Terrain"):
                original_terrain_name = obj.name
                break
       
        # Create the final export directory
        export_path_base = Path(self.filepath) / original_terrain_name
        export_path_base.mkdir(parents=True, exist_ok=True)
       
        # Get the selected export format
        export_format = context.scene.rage_settings.export_format
       
        # Filter for objects that are part of the splitting process (sectors and collisions)
        objects_to_export = [
            obj for obj in context.scene.objects
            if obj.get("rage_sector") or obj.name.endswith("_collision")
        ]
       
        if not objects_to_export:
            self.report({'ERROR'}, "No split terrain sectors found to export. Run 'Split Active Terrain' first.")
            return {'CANCELLED'}

        # Prepare for export: select only the objects we need
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects_to_export:
            obj.select_set(True)
           
        # Get the file extension
        ext = export_format.lower()
        if ext == 'gltf': ext = 'glb' # Use binary GLTF by default for simplicity

        # Perform the actual export based on the selected format
        try:
            if export_format == 'OBJ':
                bpy.ops.export_scene.obj(
                    filepath=str(export_path_base / f"{original_terrain_name}.obj"),
                    use_selection=True,
                    path_mode='RELATIVE',
                    axis_forward='-Z', # Standard RAGE/Game Engine orientation
                    axis_up='Y'
                )
            elif export_format == 'FBX':
                bpy.ops.export_scene.fbx(
                    filepath=str(export_path_base / f"{original_terrain_name}.fbx"),
                    use_selection=True,
                    object_types={'MESH'},
                    apply_scale_options='FBX_SCALE_UNITS',
                    bake_anim_use_all_actions=False,
                    axis_forward='-Z',
                    axis_up='Y'
                )
            elif export_format == 'GLTF':
                bpy.ops.export_scene.gltf(
                    filepath=str(export_path_base / f"{original_terrain_name}.glb"),
                    export_format='GLB', # Binary GLTF
                    use_selection=True,
                    export_apply=True,
                )
           
            # Deselect everything after export
            bpy.ops.object.select_all(action='DESELECT')
           
            self.report({'INFO'}, f"Successfully exported {len(objects_to_export)} tiles to: {export_path_base.resolve()}")
            return {'FINISHED'}

        except Exception as e:
            bpy.ops.object.select_all(action='DESELECT') # Ensure cleanup on failure
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        context.window_manager.fileselect_add(self) # Need to call twice for directory
        return {'RUNNING_MODAL'}


class RAGE_OT_export_fivem(bpy.types.Operator, ExportHelper):
    bl_idname = "rage.export_fivem"
    bl_label = "Export RAGE Streaming Files (.ipl)"
    bl_description = "Exports RAGE streaming setup files (IPL/IDE) for all existing sectors."
    filename_ext = "" # Directory export
   
    filepath: bpy.props.StringProperty(subtype="DIR_PATH")
   
    def execute(self, context):
        if not self.filepath: return {'CANCELLED'}
       
        # 1. Base folder for the resource
        base_name = context.scene.rage_settings.fivem_resource_name
        base = Path(self.filepath) / base_name
       
        # 2. Setup standard FiveM resource structure
        stream = base / "stream"
        base.mkdir(parents=True, exist_ok=True)
        stream.mkdir(parents=True, exist_ok=True)
       
        # 3. Create fxmanifest.lua
        manifest_path = base / "fxmanifest.lua"
        with open(manifest_path, 'w') as f:
            f.write("fx_version 'cerulean'\n")
            f.write("games { 'gta5' }\n")
            f.write(f"description '{base_name} - Generated by RAGE Studio Integrated Suite'\n")
            f.write("files { 'stream/*.ipl', 'stream/*.ide' }\n")
       
        # 4. Export IPL files using the streaming system
        exported = streaming_system.export_ipl_files(context, str(stream))
       
        if exported:
            self.report({'INFO'}, f"FiveM resource exported to {base.resolve()}")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"No sectors found to export IPL files. Export directory created: {base.resolve()}")
            return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# ============================= CODEWALKER OPERATORS (INTEGRATED) =============================
# ... (CodeWalker operators remain unchanged, but they are included below for completeness) ...
class RAGE_OT_ImportCodeWalkerXML(Operator, ImportHelper):
    bl_idname = "rage.import_codewalker_xml"
    bl_label = "Import CodeWalker XML"
    bl_description = "Import CodeWalker XML map data with entity reconstruction"
    filename_ext = ".xml"
    filter_glob: StringProperty(default="*.xml", options={'HIDDEN'})
    import_entities: BoolProperty(name="Import Entities", default=True)
    import_models: BoolProperty(name="Import Models", default=True)
    scale_factor: FloatProperty(name="Scale Factor", default=1.0)
 
    def execute(self, context):
        try:
            tree = ET.parse(self.filepath)
            root = tree.getroot()
            self.process_entities(root, context)
            self.report({'INFO'}, "XML import completed")
        except Exception as e:
            self.report({'ERROR'}, f"XML import failed: {str(e)}")
            return {'CANCELLED'}
        return {'FINISHED'}

    def process_entities(self, root, context):
        cw_coll = bpy.data.collections.get("CodeWalker_Import")
        if not cw_coll:
            cw_coll = bpy.data.collections.new("CodeWalker_Import")
            context.scene.collection.children.link(cw_coll)

        for entity_elem in root.iter('CEntityDef'):
            if not self.import_entities: break
          
            type_attr = entity_elem.get('type', 'Unknown')
            pos_elem = entity_elem.find('Position')
          
            if pos_elem is not None:
                x = float(pos_elem.get('x', 0)) * self.scale_factor
                y = float(pos_elem.get('y', 0)) * self.scale_factor
                z = float(pos_elem.get('z', 0)) * self.scale_factor
              
                obj = bpy.data.objects.new(f"Entity_{type_attr}", None)
                obj.empty_display_type = 'ARROWS'
                obj.location = (x, y, z)
                obj["rage_entity"] = True
                cw_coll.objects.link(obj)

class RAGE_OT_ExportToCodeWalker(Operator, ExportHelper):
    bl_idname = "rage.export_to_codewalker"
    bl_label = "Export to CodeWalker XML"
    bl_description = "Export scene data to CodeWalker XML format"
    filename_ext = ".xml"
    filter_glob: StringProperty(default="*.xml", options={'HIDDEN'})
 
    def execute(self, context):
        root = ET.Element("CMapData")
        root.set("version", "1.0")
        root.set("exportedBy", "RAGE Studio Integrated")
      
        entities_elem = ET.SubElement(root, "Entities")
      
        count = 0
        for obj in context.selected_objects:
            if obj.get("rage_entity") or obj.type == 'MESH':
                ent = ET.SubElement(entities_elem, "CEntityDef")
                ent.set("name", obj.name)
              
                pos = ET.SubElement(ent, "Position")
                pos.set("x", str(obj.location.x))
                pos.set("y", str(obj.location.y))
                pos.set("z", str(obj.location.z))
                count += 1

        tree = ET.ElementTree(root)
        tree.write(self.filepath, encoding='utf-8', xml_declaration=True)
        self.report({'INFO'}, f"Exported {count} entities to CodeWalker XML")
        return {'FINISHED'}
# ... (CodeWalker operators end here) ...

# ============================= GENERIC OPERATORS =============================
class RAGE_OT_generate_collision(bpy.types.Operator):
    bl_idname = "rage.generate_collision"
    bl_label = "Generate Collision"
    bl_description = "Generates a simplified collision mesh for all selected objects."
    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                if collision_system.generate_collision_mesh(obj):
                    count += 1
        self.report({'INFO'}, f"Generated collision for {count} objects.")
        return {'FINISHED'}

class RAGE_OT_auto_streaming_setup(bpy.types.Operator):
    bl_idname = "rage.auto_streaming_setup"
    bl_label = "Auto Partition (RAGE Sectors)"
    bl_description = "Partitions split sectors into streaming groups for RAGE export preparation."
    def execute(self, context):
        sectors = streaming_system.auto_partition_world(context, context.scene.rage_settings.sector_size)
        self.report({'INFO'}, f"Partioned objects into {len(sectors)} streaming sectors")
        return {'FINISHED'}

class RAGE_OT_create_mission(bpy.types.Operator):
    bl_idname = "rage.create_mission"
    bl_label = "Create Mission Marker"
    bl_description = "Places an empty object at the cursor location to mark a mission start point."
    def execute(self, context):
        empty = bpy.data.objects.new("Mission_Marker", None)
        empty.location = context.scene.cursor.location
        context.collection.objects.link(empty)
        return {'FINISHED'}

# ============================= UI PANELS =============================
class RAGE_PT_main_panel(bpy.types.Panel):
    bl_label = "RAGE Studio"
    bl_idname = "RAGE_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Game Environment Settings", icon='PREFERENCES')
        layout.prop(context.scene.rage_game_mode, "game", text="Game")

class RAGE_PT_terrain_tools(bpy.types.Panel):
    bl_label = "Terrain & Splitting"
    bl_idname = "RAGE_PT_terrain_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.rage_settings
       
        # --- Heightmap Import ---
        layout.label(text="Heightmap Import (Scaling)", icon='IMAGE_DATA')
        layout.operator("rage.import_heightmap", text="Import Heightmap", icon='IMPORT')
       
        layout.separator()
        layout.label(text="Grid Splitter", icon='MOD_GRID')
       
        # --- Grid Splitter Settings ---
        box = layout.box()
        box.prop(settings, "sector_size")
       
        # Grid Preview Toggle (uses the property's update function to call the operator)
        row = box.row()
        icon = 'HIDE_OFF' if settings.show_grid_preview else 'HIDE_ON'
        row.prop(settings, "show_grid_preview", text="Grid Preview Overlay", icon=icon)
       
        # --- Split Operator ---
        split_op = box.operator("rage.split_terrain_grid", text="Split Active Terrain", icon='SCULPTMODE_HLT')
        split_op.create_collision = True # Default to creating collision
        split_op.collision_type = 'GRASS' # Default collision type

class RAGE_PT_codewalker_tools(bpy.types.Panel):
    bl_label = "CodeWalker Integration"
    bl_idname = "RAGE_PT_codewalker_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        layout.label(text="XML Tools", icon='FILE_SCRIPT')
        box = layout.box()
        box.operator("rage.import_codewalker_xml", text="Import CW XML")
        box.operator("rage.export_to_codewalker", text="Export CW XML")

class RAGE_PT_collision_tools(bpy.types.Panel):
    bl_label = "Collision Tools"
    bl_idname = "RAGE_PT_collision_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        layout.operator("rage.generate_collision", text="Generate Collision")

class RAGE_PT_streaming_tools(bpy.types.Panel):
    bl_label = "Streaming & Export"
    bl_idname = "RAGE_PT_streaming_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RAGE"
    bl_parent_id = "RAGE_PT_main_panel"

    def draw(self, context):
        layout = self.layout
       
        # --- RAGE Streaming (IPL) Export ---
        box_rage = layout.box()
        box_rage.label(text="RAGE/FiveM Export", icon='EXPORT')
        box_rage.prop(context.scene.rage_settings, "fivem_resource_name")
        box_rage.operator("rage.auto_streaming_setup", text="1. Auto Partition (Check Sectors)")
        box_rage.operator("rage.export_fivem", text="2. Export RAGE Streaming Files (.ipl)")

        layout.separator()
       
        # --- Generic All Tiles Export ---
        box_generic = layout.box()
        box_generic.label(text="Generic Tiles Export", icon='EXPORT')
        row = box_generic.row(align=True)
        row.label(text="Format:")
        row.prop(context.scene.rage_settings, "export_format", text="")
        box_generic.operator("rage.export_all_tiles", text="Export All Tiles (Meshes/Collisions)", icon='FILE_FOLDER')

# ============================= REGISTRATION =============================
classes = (
    RAGE_GameMode,
    RAGE_Settings,
    RAGE_OT_import_heightmap,
    RAGE_OT_toggle_grid_preview,
    RAGE_OT_split_terrain_grid,
    RAGE_OT_export_all_tiles, # New Export Operator
    RAGE_OT_ImportCodeWalkerXML,
    RAGE_OT_ExportToCodeWalker,
    RAGE_OT_export_fivem,
    RAGE_OT_generate_collision,
    RAGE_OT_auto_streaming_setup,
    RAGE_OT_create_mission,
    RAGE_PT_main_panel,
    RAGE_PT_terrain_tools,
    RAGE_PT_codewalker_tools,
    RAGE_PT_collision_tools,
    RAGE_PT_streaming_tools,
)

def register():
    # Attempt to unregister first in case of a hot-reload
    try: unregister()
    except: pass
   
    for cls in classes:
        bpy.utils.register_class(cls)
  
    # Register property groups on the scene
    bpy.types.Scene.rage_game_mode = bpy.props.PointerProperty(type=RAGE_GameMode)
    bpy.types.Scene.rage_settings = bpy.props.PointerProperty(type=RAGE_Settings)
    print("✅ RAGE Studio Integrated Suite registered successfully")

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
  
    # Delete property groups from the scene
    if hasattr(bpy.types.Scene, 'rage_game_mode'): del bpy.types.Scene.rage_game_mode
    if hasattr(bpy.types.Scene, 'rage_settings'): del bpy.types.Scene.rage_settings
    print("❌ RAGE Studio Integrated Suite unregistered")

if __name__ == "__main__":
    register()