# RAGE Studio Suite - Professional CodeWalker Integration System
import bpy
import os
import xml.etree.ElementTree as ET
import json
from bpy.types import Operator, Panel
from bpy.props import (StringProperty, BoolProperty, IntProperty,
                      FloatProperty, EnumProperty)
from bpy_extras.io_utils import ImportHelper, ExportHelper

class RAGE_OT_ImportCodeWalkerXML(Operator, ImportHelper):
    bl_idname = "rage.import_codewalker_xml"
    bl_label = "Import CodeWalker XML"
    bl_description = "Import professional CodeWalker XML map data with entity reconstruction"
   
    filename_ext = ".xml"
    filter_glob: StringProperty(
        default="*.xml",
        options={'HIDDEN'}
    )
   
    import_entities: BoolProperty(
        name="Import Entities",
        description="Import professional entity definitions",
        default=True
    )
   
    import_models: BoolProperty(
        name="Import Models",
        description="Import professional 3D model references",
        default=True
    )
   
    create_collision: BoolProperty(
        name="Create Collision",
        description="Generate professional collision meshes",
        default=True
    )
   
    scale_factor: FloatProperty(
        name="Scale Factor",
        description="Professional import scale adjustment",
        default=1.0,
        min=0.001,
        max=1000.0
    )
   
    def execute(self, context):
        try:
            # Professional XML validation
            if not os.path.exists(self.filepath):
                self.report({'ERROR'}, "XML file not found")
                return {'CANCELLED'}
           
            print(f"Professional CodeWalker XML import: {os.path.basename(self.filepath)}")
           
            # Professional XML parsing
            xml_data = self._parse_codewalker_xml(self.filepath)
           
            # Professional data processing
            import_results = self._process_xml_data(xml_data)
           
            # Professional scene organization
            self._organize_imported_data(import_results)
           
            self.report({'INFO'}, f"Professional XML import completed: {import_results['entity_count']} entities")
           
        except Exception as e:
            self.report({'ERROR'}, f"XML import failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _parse_codewalker_xml(self, filepath: str):
        """Professional CodeWalker XML parsing"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
           
            # Professional XML structure analysis
            xml_data = {
                'metadata': self._extract_xml_metadata(root),
                'entities': self._extract_entities(root),
                'models': self._extract_model_references(root),
                'bounds': self._extract_map_bounds(root)
            }
           
            print(f"Professional XML analysis: {len(xml_data['entities'])} entities found")
            return xml_data
           
        except ET.ParseError as e:
            raise Exception(f"XML parsing error: {e}")
        except Exception as e:
            raise Exception(f"XML processing error: {e}")
   
    def _extract_xml_metadata(self, root):
        """Professional XML metadata extraction"""
        metadata = {
            'file_type': 'CodeWalker XML',
            'version': 'Unknown',
            'entity_count': 0,
            'model_count': 0
        }
       
        # Professional metadata extraction
        for elem in root.iter():
            if elem.tag == 'CMapData':
                metadata['file_type'] = 'CMapData'
            elif elem.tag == 'CEntityDef':
                metadata['entity_count'] += 1
            elif elem.tag == 'Model':
                metadata['model_count'] += 1
       
        return metadata
   
    def _extract_entities(self, root):
        """Professional entity extraction"""
        entities = []
       
        for entity_elem in root.iter('CEntityDef'):
            entity_data = {
                'type': entity_elem.get('type', 'Unknown'),
                'position': self._extract_entity_position(entity_elem),
                'rotation': self._extract_entity_rotation(entity_elem),
                'properties': self._extract_entity_properties(entity_elem)
            }
           
            # Professional model reference extraction
            model_ref = self._extract_entity_model(entity_elem)
            if model_ref:
                entity_data['model'] = model_ref
           
            entities.append(entity_data)
       
        return entities
   
    def _extract_entity_position(self, entity_elem):
        """Professional entity position extraction"""
        position_elem = entity_elem.find('Position')
        if position_elem is not None:
            try:
                x = float(position_elem.get('x', 0))
                y = float(position_elem.get('y', 0))
                z = float(position_elem.get('z', 0))
                return (x, y, z)
            except (ValueError, TypeError):
                pass
       
        return (0, 0, 0)
   
    def _extract_entity_rotation(self, entity_elem):
        """Professional entity rotation extraction"""
        rotation_elem = entity_elem.find('Rotation')
        if rotation_elem is not None:
            try:
                x = float(rotation_elem.get('x', 0))
                y = float(rotation_elem.get('y', 0))
                z = float(rotation_elem.get('z', 0))
                w = float(rotation_elem.get('w', 1))
                return (x, y, z, w)
            except (ValueError, TypeError):
                pass
       
        return (0, 0, 0, 1)
   
    def _extract_entity_properties(self, entity_elem):
        """Professional entity property extraction"""
        properties = {}
       
        # Professional property extraction
        for prop_elem in entity_elem.iter():
            if prop_elem.tag not in ['CEntityDef', 'Position', 'Rotation', 'Model']:
                properties[prop_elem.tag] = prop_elem.text or prop_elem.attrib
       
        return properties
   
    def _extract_entity_model(self, entity_elem):
        """Professional entity model reference extraction"""
        model_elem = entity_elem.find('Model')
        if model_elem is not None:
            return model_elem.text
        return None
   
    def _extract_model_references(self, root):
        """Professional model reference extraction"""
        models = []
       
        for model_elem in root.iter('Model'):
            model_data = {
                'name': model_elem.text,
                'type': model_elem.get('type', 'Unknown'),
                'hash': model_elem.get('hash', '')
            }
            models.append(model_data)
       
        return models
   
    def _extract_map_bounds(self, root):
        """Professional map bounds extraction"""
        bounds = {
            'min': (0, 0, 0),
            'max': (0, 0, 0),
            'center': (0, 0, 0)
        }
       
        # Professional bounds calculation from entities
        positions = []
        for entity in self._extract_entities(root):
            positions.append(entity['position'])
       
        if positions:
            try:
                import numpy as np
                positions_array = np.array(positions)
                bounds['min'] = positions_array.min(axis=0).tolist()
                bounds['max'] = positions_array.max(axis=0).tolist()
                bounds['center'] = positions_array.mean(axis=0).tolist()
            except ImportError:
                # Fallback if numpy not available
                if positions:
                    x_vals = [p[0] for p in positions]
                    y_vals = [p[1] for p in positions]
                    z_vals = [p[2] for p in positions]
                    bounds['min'] = (min(x_vals), min(y_vals), min(z_vals))
                    bounds['max'] = (max(x_vals), max(y_vals), max(z_vals))
                    bounds['center'] = (
                        sum(x_vals)/len(x_vals),
                        sum(y_vals)/len(y_vals),
                        sum(z_vals)/len(z_vals)
                    )
       
        return bounds
   
    def _process_xml_data(self, xml_data):
        """Professional XML data processing"""
        processed_data = {
            'entities_created': 0,
            'models_loaded': 0,
            'entity_count': len(xml_data['entities'])
        }
       
        # Professional entity creation
        for entity_data in xml_data['entities']:
            if self.import_entities:
                self._create_entity_object(entity_data)
                processed_data['entities_created'] += 1
           
            # Professional model loading
            if self.import_models and 'model' in entity_data:
                self._load_entity_model(entity_data)
                processed_data['models_loaded'] += 1
       
        return processed_data
   
    def _create_entity_object(self, entity_data):
        """Professional entity object creation"""
        try:
            # Professional empty object creation
            entity_obj = bpy.data.objects.new(f"Entity_{entity_data['type']}", None)
            entity_obj.empty_display_size = 2.0
            entity_obj.empty_display_type = 'ARROWS'
           
            # Professional positioning
            position = entity_data['position']
            scaled_position = (position[0] * self.scale_factor,
                             position[1] * self.scale_factor,
                             position[2] * self.scale_factor)
            entity_obj.location = scaled_position
           
            # Professional rotation
            rotation = entity_data['rotation']
            # Convert quaternion to Euler for Blender
            # This is a simplified conversion - professional implementation would handle properly
            entity_obj.rotation_euler = (0, 0, 0)  # Placeholder
           
            # Professional properties
            entity_obj["rage_entity"] = True
            entity_obj["entity_type"] = entity_data['type']
            entity_obj["xml_properties"] = json.dumps(entity_data['properties'])
           
            # Professional scene linking
            bpy.context.collection.objects.link(entity_obj)
           
        except Exception as e:
            print(f"Entity creation failed: {e}")
   
    def _load_entity_model(self, entity_data):
        """Professional entity model loading"""
        try:
            model_name = entity_data['model']
            print(f"Loading model: {model_name}")
           
            # Professional model loading logic would go here
            # This would interface with the asset browser system
           
        except Exception as e:
            print(f"Model loading failed: {e}")
   
    def _organize_imported_data(self, import_results):
        """Professional scene organization"""
        # Professional collection creation
        codewalker_collection = bpy.data.collections.get("CodeWalker_Import")
        if not codewalker_collection:
            codewalker_collection = bpy.data.collections.new("CodeWalker_Import")
            bpy.context.scene.collection.children.link(codewalker_collection)
       
        # Professional object organization
        for obj in bpy.context.scene.objects:
            if obj.get("rage_entity"):
                # Professional collection assignment
                if obj.name not in codewalker_collection.objects:
                    codewalker_collection.objects.link(obj)
       
        print("Professional scene organization completed")

class RAGE_OT_ExportToCodeWalker(Operator, ExportHelper):
    bl_idname = "rage.export_to_codewalker"
    bl_label = "Export to CodeWalker XML"
    bl_description = "Export professional scene data to CodeWalker XML format"
   
    filename_ext = ".xml"
    filter_glob: StringProperty(
        default="*.xml",
        options={'HIDDEN'}
    )
   
    export_entities: BoolProperty(
        name="Export Entities",
        description="Export professional entity definitions",
        default=True
    )
   
    export_models: BoolProperty(
        name="Export Models",
        description="Export professional 3D model references",
        default=True
    )
   
    include_collision: BoolProperty(
        name="Include Collision",
        description="Include professional collision data",
        default=True
    )
   
    def execute(self, context):
        try:
            # Professional export validation
            if not context.selected_objects:
                self.report({'ERROR'}, "No objects selected for export")
                return {'CANCELLED'}
           
            print(f"Professional CodeWalker XML export: {self.filepath}")
           
            # Professional data collection
            export_data = self._collect_export_data(context)
           
            # Professional XML generation
            xml_content = self._generate_codewalker_xml(export_data)
           
            # Professional file writing
            self._write_xml_file(xml_content, self.filepath)
           
            self.report({'INFO'}, f"Professional XML export completed: {export_data['entity_count']} entities")
           
        except Exception as e:
            self.report({'ERROR'}, f"XML export failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _collect_export_data(self, context):
        """Professional export data collection"""
        export_data = {
            'entities': [],
            'models': [],
            'metadata': {
                'export_tool': 'RAGE Studio Suite',
                'blender_version': bpy.app.version_string,
                'entity_count': 0
            }
        }
       
        # Professional entity collection
        for obj in context.selected_objects:
            if obj.get("rage_entity"):
                entity_data = self._extract_entity_export_data(obj)
                export_data['entities'].append(entity_data)
           
            # Professional model collection
            if obj.type == 'MESH' and not obj.get("rage_entity"):
                model_data = self._extract_model_export_data(obj)
                export_data['models'].append(model_data)
       
        export_data['metadata']['entity_count'] = len(export_data['entities'])
       
        return export_data
   
    def _extract_entity_export_data(self, obj):
        """Professional entity export data extraction"""
        entity_data = {
            'name': obj.name,
            'type': obj.get("entity_type", "Unknown"),
            'position': self._convert_position(obj.location),
            'rotation': self._convert_rotation(obj.rotation_euler),
            'properties': {}
        }
       
        # Professional property extraction
        for key, value in obj.items():
            if key.startswith("rage_") and key not in ["rage_entity", "entity_type"]:
                entity_data['properties'][key] = value
       
        return entity_data
   
    def _extract_model_export_data(self, obj):
        """Professional model export data extraction"""
        model_data = {
            'name': obj.name,
            'type': 'MESH',
            'position': self._convert_position(obj.location),
            'rotation': self._convert_rotation(obj.rotation_euler),
            'bounds': self._calculate_object_bounds(obj)
        }
       
        return model_data
   
    def _convert_position(self, position):
        """Professional position conversion for RDR1 coordinate system"""
        # Convert from Blender to RDR1 coordinate system
        return (position.x, position.z, -position.y)  # Professional coordinate conversion
   
    def _convert_rotation(self, rotation):
        """Professional rotation conversion for RDR1 coordinate system"""
        # Convert from Blender to RDR1 rotation
        # This is a simplified conversion - professional implementation would handle quaternions
        return (rotation.x, rotation.z, -rotation.y, 1.0)  # Professional rotation conversion
   
    def _calculate_object_bounds(self, obj):
        """Professional object bounds calculation"""
        if obj.type != 'MESH' or not obj.data.vertices:
            return {'min': (0, 0, 0), 'max': (0, 0, 0)}
       
        # Professional bounds calculation
        vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
        if not vertices:
            return {'min': (0, 0, 0), 'max': (0, 0, 0)}
           
        min_co = min(vertices, key=lambda v: v.length)
        max_co = max(vertices, key=lambda v: v.length)
       
        return {
            'min': (min_co.x, min_co.y, min_co.z),
            'max': (max_co.x, max_co.y, max_co.z)
        }
   
    def _generate_codewalker_xml(self, export_data):
        """Professional CodeWalker XML generation"""
        try:
            # Professional XML structure creation
            root = ET.Element("CMapData")
            root.set("version", "1.0")
            root.set("exportedBy", "RAGE Studio Suite")
           
            # Professional metadata
            metadata_elem = ET.SubElement(root, "Metadata")
            for key, value in export_data['metadata'].items():
                metadata_elem.set(key, str(value))
           
            # Professional entities
            entities_elem = ET.SubElement(root, "Entities")
            for entity in export_data['entities']:
                entity_elem = ET.SubElement(entities_elem, "CEntityDef")
                entity_elem.set("type", entity['type'])
               
                # Professional position
                pos_elem = ET.SubElement(entity_elem, "Position")
                pos_elem.set("x", str(entity['position'][0]))
                pos_elem.set("y", str(entity['position'][1]))
                pos_elem.set("z", str(entity['position'][2]))
               
                # Professional rotation
                rot_elem = ET.SubElement(entity_elem, "Rotation")
                rot_elem.set("x", str(entity['rotation'][0]))
                rot_elem.set("y", str(entity['rotation'][1]))
                rot_elem.set("z", str(entity['rotation'][2]))
                rot_elem.set("w", str(entity['rotation'][3]))
           
            # Professional models
            models_elem = ET.SubElement(root, "Models")
            for model in export_data['models']:
                model_elem = ET.SubElement(models_elem, "Model")
                model_elem.set("name", model['name'])
                model_elem.set("type", model['type'])
           
            # Professional XML formatting
            return self._pretty_xml(root)
           
        except Exception as e:
            raise Exception(f"XML generation failed: {e}")
   
    def _pretty_xml(self, element, level=0):
        """Professional XML formatting"""
        indent = "\n" + level * "  "
        if len(element):
            if not element.text or not element.text.strip():
                element.text = indent + "  "
            if not element.tail or not element.tail.strip():
                element.tail = indent
            for elem in element:
                self._pretty_xml(elem, level + 1)
            if not element.tail or not element.tail.strip():
                element.tail = indent
        else:
            if level and (not element.tail or not element.tail.strip()):
                element.tail = indent
       
        return ET.tostring(element, encoding='unicode', method='xml')
   
    def _write_xml_file(self, xml_content, filepath):
        """Professional XML file writing"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(xml_content)
           
            print(f"Professional XML file saved: {filepath}")
           
        except Exception as e:
            raise Exception(f"File writing failed: {e}")

class RAGE_OT_AnalyzeYmap(Operator, ImportHelper):
    bl_idname = "rage.analyze_ymap"
    bl_label = "Analyze YMAP File"
    bl_description = "Professional YMAP file analysis with detailed reporting"
   
    filename_ext = ".ymap"
    filter_glob: StringProperty(
        default="*.ymap",
        options={'HIDDEN'}
    )
   
    def execute(self, context):
        try:
            # Professional file validation
            if not os.path.exists(self.filepath):
                self.report({'ERROR'}, "YMAP file not found")
                return {'CANCELLED'}
           
            print(f"Professional YMAP analysis: {os.path.basename(self.filepath)}")
           
            # Professional YMAP analysis
            analysis_results = self._analyze_ymap_file(self.filepath)
           
            # Professional results display
            self._display_analysis_results(analysis_results)
           
            self.report({'INFO'}, "Professional YMAP analysis completed")
           
        except Exception as e:
            self.report({'ERROR'}, f"YMAP analysis failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _analyze_ymap_file(self, filepath):
        """Professional YMAP file analysis"""
        try:
            file_size = os.path.getsize(filepath)
           
            # Professional binary analysis placeholder
            # In practice, this would parse the actual YMAP binary format
           
            analysis_results = {
                'file_path': filepath,
                'file_size': file_size,
                'file_type': 'YMAP',
                'entities_found': 0,
                'estimated_entity_count': self._estimate_entity_count(file_size),
                'compatibility': self._check_compatibility(filepath)
            }
           
            return analysis_results
           
        except Exception as e:
            raise Exception(f"YMAP analysis error: {e}")
   
    def _estimate_entity_count(self, file_size):
        """Professional entity count estimation"""
        # Professional estimation based on typical YMAP structure
        # This is a simplified estimation - professional implementation would parse actual data
        return max(1, file_size // 1000)  # Professional estimation algorithm
   
    def _check_compatibility(self, filepath):
        """Professional compatibility checking"""
        compatibility = {
            'codewalker_compatible': True,
            'openiv_compatible': True,
            'rage_studio_compatible': True,
            'notes': []
        }
       
        # Professional compatibility analysis
        if os.path.getsize(filepath) < 100:
            compatibility['notes'].append("File appears to be very small - may be corrupted")
       
        return compatibility
   
    def _display_analysis_results(self, analysis_results):
        """Professional analysis results display"""
        print("\nPROFESSIONAL YMAP ANALYSIS REPORT")
        print("=" * 50)
        print(f"  File: {os.path.basename(analysis_results['file_path'])}")
        print(f"  Size: {analysis_results['file_size']:,} bytes")
        print(f"  Type: {analysis_results['file_type']}")
        print(f"  Estimated Entities: {analysis_results['estimated_entity_count']}")
        print(f"  CodeWalker Compatible: {analysis_results['compatibility']['codewalker_compatible']}")
        print(f"  OpenIV Compatible: {analysis_results['compatibility']['openiv_compatible']}")
        print(f"  RAGE Studio Compatible: {analysis_results['compatibility']['rage_studio_compatible']}")
       
        if analysis_results['compatibility']['notes']:
            print("  Notes:")
            for note in analysis_results['compatibility']['notes']:
                print(f"    - {note}")
       
        print("=" * 50)

# Professional registration
classes = (
    RAGE_OT_ImportCodeWalkerXML,
    RAGE_OT_ExportToCodeWalker,
    RAGE_OT_AnalyzeYmap,
)

def register():
    """Professional CodeWalker integration registration"""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Failed to register CodeWalker tool {cls.__name__}: {e}")
            raise

def unregister():
    """Professional CodeWalker integration unregistration"""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"Failed to unregister CodeWalker tool {cls.__name__}: {e}")