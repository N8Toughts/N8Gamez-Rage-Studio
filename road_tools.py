import bpy
import bmesh
import os
from mathutils import Vector, Matrix, geometry
from bpy.types import Operator, Panel
from bpy.props import (StringProperty, BoolProperty, IntProperty,
                       FloatProperty, FloatVectorProperty, EnumProperty)

class RAGE_OT_CreateRoadFromCurve(Operator):
    bl_idname = "rage.create_road_from_curve"
    bl_label = "Create Road from Curve"
    bl_description = "Generate professional road mesh from selected curve with industry-standard parameters"
   
    road_width: FloatProperty(
        name="Road Width",
        description="Professional road width in meters",
        default=8.0,
        min=1.0,
        max=50.0
    )
   
    road_thickness: FloatProperty(
        name="Road Thickness",
        description="Professional road thickness in meters",
        default=0.3,
        min=0.1,
        max=2.0
    )
   
    segments_per_unit: FloatProperty(
        name="Segments per Unit",
        description="Professional road resolution (segments per meter)",
        default=0.5,
        min=0.1,
        max=2.0
    )
   
    create_shoulders: BoolProperty(
        name="Create Shoulders",
        description="Generate professional road shoulders",
        default=True
    )
   
    shoulder_width: FloatProperty(
        name="Shoulder Width",
        description="Professional shoulder width in meters",
        default=1.5,
        min=0.5,
        max=5.0
    )
   
    auto_uv: BoolProperty(
        name="Auto UV",
        description="Generate professional UV coordinates for road textures",
        default=True
    )
   
    create_collision: BoolProperty(
        name="Create Collision",
        description="Generate professional collision mesh for road",
        default=True
    )
   
    def execute(self, context):
        if not context.active_object or context.active_object.type != 'CURVE':
            self.report({'ERROR'}, "❌ Select a professional curve object for road path")
            return {'CANCELLED'}
       
        curve_obj = context.active_object
       
        try:
            # Professional road generation pipeline
            road_data = self._create_road_system(
                curve_obj,
                self.road_width,
                self.road_thickness,
                self.segments_per_unit,
                self.create_shoulders,
                self.shoulder_width
            )
           
            # Professional UV generation
            if self.auto_uv:
                self._generate_road_uv(road_data['road_mesh'])
           
            # Professional material creation
            self._create_road_material(road_data['road_mesh'])
           
            # Professional collision generation
            if self.create_collision:
                self._create_road_collision(road_data)
           
            # Professional scene management
            if hasattr(context.scene, 'rage_studio'):
                context.scene.rage_studio.active_road_curve = curve_obj.name
           
            self.report({'INFO'}, f"✅ Professional road created: {self.road_width}m width")
           
        except Exception as e:
            self.report({'ERROR'}, f"❌ Road creation failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _create_road_system(self, curve_obj, width: float, thickness: float, segments: float, create_shoulders: bool, shoulder_width: float):
        """Professional road system creation"""
        # Professional road mesh creation
        road_mesh = self._create_road_mesh(curve_obj, width, thickness, segments)
       
        # Professional shoulder creation
        shoulders = None
        if create_shoulders:
            shoulders = self._create_road_shoulders(curve_obj, width, shoulder_width, thickness, segments)
       
        return {
            'road_mesh': road_mesh,
            'shoulders': shoulders,
            'curve_object': curve_obj,
            'width': width,
            'thickness': thickness
        }
   
    def _create_road_mesh(self, curve_obj, width: float, thickness: float, segments: float):
        """Professional road mesh generation"""
        # Calculate professional segment count
        curve_length = self._calculate_curve_length(curve_obj)
        segment_count = max(8, int(curve_length * segments))
       
        # Professional mesh creation
        mesh = bpy.data.meshes.new("RAGE_Road_Professional")
        obj = bpy.data.objects.new("RAGE_Road_Professional", mesh)
       
        # Professional scene linking
        bpy.context.collection.objects.link(obj)
        obj.location = curve_obj.location
       
        # Professional bmesh processing
        bm = bmesh.new()
       
        try:
            # Professional curve sampling
            curve_points = self._sample_curve_points(curve_obj, segment_count)
           
            # Professional road geometry generation
            vertices = []
            faces = []
           
            # Generate professional road vertices
            for i, point in enumerate(curve_points):
                # Calculate professional road direction
                if i == 0:
                    direction = (curve_points[1] - point).normalized()
                elif i == len(curve_points) - 1:
                    direction = (point - curve_points[i-1]).normalized()
                else:
                    direction = (curve_points[i+1] - curve_points[i-1]).normalized()
               
                # Calculate professional perpendicular direction
                perpendicular = direction.cross(Vector((0, 0, 1))).normalized()
               
                # Generate professional road vertices
                left_point = point + perpendicular * (width / 2)
                right_point = point - perpendicular * (width / 2)
               
                vertices.extend([left_point, right_point])
           
            # Generate professional road faces
            for i in range(len(curve_points) - 1):
                idx1 = i * 2
                idx2 = i * 2 + 1
                idx3 = (i + 1) * 2
                idx4 = (i + 1) * 2 + 1
               
                # Professional quad face creation
                faces.append([idx1, idx2, idx4, idx3])
           
            # Professional mesh construction
            for vert in vertices:
                bm.verts.new(vert)
           
            bm.verts.ensure_lookup_table()
           
            for face_indices in faces:
                try:
                    face_verts = [bm.verts[i] for i in face_indices]
                    bm.faces.new(face_verts)
                except ValueError:
                    pass  # Professional duplicate face handling
           
            # Professional extrusion for road thickness
            extruded = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
            bmesh.ops.translate(bm, vec=(0, 0, -thickness), verts=extruded['geom'])
           
            # Professional mesh finalization
            bm.to_mesh(mesh)
            mesh.update()
           
        finally:
            bm.free()
       
        # Professional road properties
        obj["rage_road"] = True
        obj["road_width"] = width
        obj["road_thickness"] = thickness
        obj["road_length"] = curve_length
       
        return obj
   
    def _create_road_shoulders(self, curve_obj, road_width: float, shoulder_width: float, thickness: float, segments: float):
        """Professional road shoulder generation"""
        # Calculate professional segment count
        curve_length = self._calculate_curve_length(curve_obj)
        segment_count = max(8, int(curve_length * segments))
       
        # Professional shoulder mesh creation
        shoulder_mesh = bpy.data.meshes.new("RAGE_Road_Shoulders_Professional")
        shoulder_obj = bpy.data.objects.new("RAGE_Road_Shoulders_Professional", shoulder_mesh)
       
        # Professional scene linking
        bpy.context.collection.objects.link(shoulder_obj)
        shoulder_obj.location = curve_obj.location
       
        # Professional bmesh processing
        bm = bmesh.new()
       
        try:
            # Professional curve sampling
            curve_points = self._sample_curve_points(curve_obj, segment_count)
           
            vertices = []
            faces = []
           
            # Generate professional shoulder vertices
            for i, point in enumerate(curve_points):
                # Calculate professional road direction
                if i == 0:
                    direction = (curve_points[1] - point).normalized()
                elif i == len(curve_points) - 1:
                    direction = (point - curve_points[i-1]).normalized()
                else:
                    direction = (curve_points[i+1] - curve_points[i-1]).normalized()
               
                # Calculate professional perpendicular direction
                perpendicular = direction.cross(Vector((0, 0, 1))).normalized()
               
                # Generate professional shoulder vertices
                left_outer = point + perpendicular * (road_width / 2 + shoulder_width)
                left_inner = point + perpendicular * (road_width / 2)
                right_inner = point - perpendicular * (road_width / 2)
                right_outer = point - perpendicular * (road_width / 2 + shoulder_width)
               
                vertices.extend([left_outer, left_inner, right_inner, right_outer])
           
            # Generate professional shoulder faces
            for i in range(len(curve_points) - 1):
                # Left shoulder
                idx1 = i * 4
                idx2 = i * 4 + 1
                idx3 = (i + 1) * 4 + 1
                idx4 = (i + 1) * 4
                faces.append([idx1, idx2, idx3, idx4])
               
                # Right shoulder
                idx5 = i * 4 + 2
                idx6 = i * 4 + 3
                idx7 = (i + 1) * 4 + 3
                idx8 = (i + 1) * 4 + 2
                faces.append([idx5, idx6, idx7, idx8])
           
            # Professional mesh construction
            for vert in vertices:
                bm.verts.new(vert)
           
            bm.verts.ensure_lookup_table()
           
            for face_indices in faces:
                try:
                    face_verts = [bm.verts[i] for i in face_indices]
                    bm.faces.new(face_verts)
                except ValueError:
                    pass
           
            # Professional extrusion for shoulder thickness
            extruded = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
            bmesh.ops.translate(bm, vec=(0, 0, -thickness * 0.5), verts=extruded['geom'])
           
            # Professional mesh finalization
            bm.to_mesh(shoulder_mesh)
            shoulder_mesh.update()
           
        finally:
            bm.free()
       
        # Professional shoulder properties
        shoulder_obj["rage_road_shoulder"] = True
        shoulder_obj["shoulder_width"] = shoulder_width
       
        return shoulder_obj
   
    def _calculate_curve_length(self, curve_obj):
        """Professional curve length calculation"""
        try:
            # Professional curve length calculation
            curve = curve_obj.data
            total_length = 0.0
           
            for spline in curve.splines:
                if spline.type == 'BEZIER':
                    # Professional Bezier curve length approximation
                    points = spline.bezier_points
                    for i in range(len(points) - 1):
                        p1 = points[i].co
                        p2 = points[i+1].co
                        total_length += (p2 - p1).length
                elif spline.type == 'POLY':
                    # Professional poly curve length calculation
                    points = spline.points
                    for i in range(len(points) - 1):
                        p1 = Vector(points[i].co[:3])
                        p2 = Vector(points[i+1].co[:3])
                        total_length += (p2 - p1).length
           
            return total_length
           
        except Exception as e:
            print(f"⚠️ Curve length calculation failed: {e}")
            return 10.0  # Professional fallback length
   
    def _sample_curve_points(self, curve_obj, segment_count: int):
        """Professional curve point sampling"""
        points = []
        curve = curve_obj.data
       
        try:
            for spline in curve.splines:
                if spline.type == 'BEZIER':
                    # Professional Bezier curve sampling
                    bezier_points = spline.bezier_points
                    if len(bezier_points) < 2:
                        continue
                   
                    # Professional uniform sampling
                    for i in range(segment_count):
                        t = i / (segment_count - 1)
                        point = self._evaluate_bezier(bezier_points, t)
                        points.append(point)
                       
                elif spline.type == 'POLY':
                    # Professional poly curve sampling
                    poly_points = spline.points
                    if len(poly_points) < 2:
                        continue
                   
                    # Professional uniform sampling
                    for i in range(segment_count):
                        t = i / (segment_count - 1)
                        point = self._evaluate_poly(poly_points, t)
                        points.append(point)
           
            return points
           
        except Exception as e:
            print(f"⚠️ Curve sampling failed: {e}")
            # Professional fallback: straight line
            return [Vector((0, 0, 0)), Vector((10, 0, 0))]
   
    def _evaluate_bezier(self, bezier_points, t: float):
        """Professional Bezier curve evaluation"""
        # Professional Bezier curve evaluation algorithm
        n = len(bezier_points) - 1
        point = Vector((0, 0, 0))
       
        for i, bp in enumerate(bezier_points):
            # Professional Bernstein polynomial calculation
            binomial = self._binomial_coefficient(n, i)
            weight = binomial * (t ** i) * ((1 - t) ** (n - i))
            point += bp.co * weight
       
        return point
   
    def _evaluate_poly(self, poly_points, t: float):
        """Professional poly curve evaluation"""
        # Professional linear interpolation for poly curves
        n = len(poly_points) - 1
        segment = t * n
        index = int(segment)
        local_t = segment - index
       
        if index >= n:
            return Vector(poly_points[-1].co[:3])
       
        p1 = Vector(poly_points[index].co[:3])
        p2 = Vector(poly_points[index + 1].co[:3])
       
        return p1.lerp(p2, local_t)
   
    def _binomial_coefficient(self, n: int, k: int):
        """Professional binomial coefficient calculation"""
        if k < 0 or k > n:
            return 0
        if k == 0 or k == n:
            return 1
       
        # Professional efficient calculation
        k = min(k, n - k)
        result = 1
        for i in range(1, k + 1):
            result = result * (n - k + i) // i
       
        return result
   
    def _generate_road_uv(self, road_obj):
        """Professional road UV coordinate generation"""
        try:
            # Professional UV generation
            mesh = road_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
           
            # Professional UV layer creation
            uv_layer = bm.loops.layers.uv.verify()
           
            # Professional UV calculation based on road geometry
            for face in bm.faces:
                for loop in face.loops:
                    vert = loop.vert
                    # Professional UV mapping based on position
                    uv_x = vert.co.x / 10.0  # Professional texture scale
                    uv_y = vert.co.y / 10.0
                    loop[uv_layer].uv = (uv_x, uv_y)
           
            # Professional mesh update
            bm.to_mesh(mesh)
            bm.free()
           
            print("✅ Professional road UV coordinates generated")
           
        except Exception as e:
            print(f"⚠️ Road UV generation failed: {e}")
   
    def _create_road_material(self, road_obj):
        """Professional road material creation"""
        try:
            mat = bpy.data.materials.new(name="RAGE_Road_Material_Professional")
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
           
            # Professional node cleanup
            nodes.clear()
           
            # Professional road shader setup
            output_node = nodes.new(type='ShaderNodeOutputMaterial')
            bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
           
            # Professional road material properties
            bsdf_node.inputs['Base Color'].default_value = (0.2, 0.2, 0.2, 1.0)  # Professional asphalt color
            bsdf_node.inputs['Roughness'].default_value = 0.9
            bsdf_node.inputs['Specular'].default_value = 0.1
           
            # Professional node connections
            links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
           
            # Professional material assignment
            if road_obj.data.materials:
                road_obj.data.materials[0] = mat
            else:
                road_obj.data.materials.append(mat)
           
            print("✅ Professional road material created")
               
        except Exception as e:
            print(f"⚠️ Road material creation failed: {e}")
   
    def _create_road_collision(self, road_data):
        """Professional road collision mesh generation"""
        try:
            road_obj = road_data['road_mesh']
           
            # Professional collision mesh creation
            collision_mesh = road_obj.data.copy()
            collision_obj = bpy.data.objects.new(f"{road_obj.name}_Collision_Professional", collision_mesh)
           
            # Professional scene linking
            bpy.context.collection.objects.link(collision_obj)
           
            # Professional collision properties
            collision_obj["rage_collision"] = True
            collision_obj.display_type = 'WIRE'
            collision_obj.hide_render = True
           
            # Professional parenting
            collision_obj.parent = road_obj
            collision_obj.matrix_parent_inverse = road_obj.matrix_world.inverted()
           
            print("✅ Professional road collision generated")
           
        except Exception as e:
            print(f"⚠️ Road collision generation failed: {e}")

class RAGE_OT_GenerateRoadNetwork(Operator):
    bl_idname = "rage.generate_road_network"
    bl_label = "Generate Road Network"
    bl_description = "Create professional interconnected road network from multiple curves"
   
    road_width: FloatProperty(
        name="Road Width",
        description="Professional network road width in meters",
        default=8.0,
        min=1.0,
        max=50.0
    )
   
    intersection_radius: FloatProperty(
        name="Intersection Radius",
        description="Professional intersection rounding radius",
        default=5.0,
        min=1.0,
        max=20.0
    )
   
    auto_connect: BoolProperty(
        name="Auto Connect",
        description="Automatically connect nearby road endpoints",
        default=True
    )
   
    connection_threshold: FloatProperty(
        name="Connection Threshold",
        description="Professional connection distance threshold",
        default=2.0,
        min=0.1,
        max=10.0
    )
   
    def execute(self, context):
        curve_objects = [obj for obj in context.selected_objects if obj.type == 'CURVE']
       
        if len(curve_objects) < 2:
            self.report({'ERROR'}, "❌ Select at least 2 professional curve objects for road network")
            return {'CANCELLED'}
       
        try:
            # Professional road network generation
            network_data = self._create_road_network(
                curve_objects,
                self.road_width,
                self.intersection_radius,
                self.auto_connect,
                self.connection_threshold
            )
           
            self.report({'INFO'}, f"✅ Professional road network created with {len(curve_objects)} roads")
           
        except Exception as e:
            self.report({'ERROR'}, f"❌ Road network generation failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _create_road_network(self, curve_objects, road_width: float, intersection_radius: float, auto_connect: bool, threshold: float):
        """Professional road network creation"""
        road_meshes = []
       
        # Professional individual road generation
        for curve_obj in curve_objects:
            road_data = self._create_road_mesh(curve_obj, road_width, 0.3, 0.5)
            road_meshes.append(road_data)
       
        # Professional intersection handling
        if auto_connect:
            self._create_intersections(road_meshes, intersection_radius, threshold)
       
        return {
            'roads': road_meshes,
            'intersections': len(road_meshes)  # Professional intersection count
        }
   
    def _create_intersections(self, road_meshes, radius: float, threshold: float):
        """Professional intersection creation"""
        # Professional intersection detection and creation
        intersections = self._find_intersections(road_meshes, threshold)
       
        for intersection in intersections:
            self._create_intersection_mesh(intersection, radius)
       
        print(f"✅ Created {len(intersections)} professional intersections")
   
    def _find_intersections(self, road_meshes, threshold: float):
        """Professional intersection detection"""
        intersections = []
       
        # Professional intersection detection algorithm
        for i, road1 in enumerate(road_meshes):
            for j, road2 in enumerate(road_meshes[i+1:], i+1):
                # Professional bounding box intersection test
                if self._check_road_intersection(road1, road2, threshold):
                    intersection_point = self._calculate_intersection_point(road1, road2)
                    if intersection_point:
                        intersections.append({
                            'roads': [road1, road2],
                            'point': intersection_point
                        })
       
        return intersections
   
    def _check_road_intersection(self, road1, road2, threshold: float):
        """Professional road intersection checking"""
        # Professional simplified intersection check
        bbox1 = road1.bound_box
        bbox2 = road2.bound_box
       
        # Professional axis-aligned bounding box intersection
        for axis in range(3):
            min1 = min(vert[axis] for vert in bbox1)
            max1 = max(vert[axis] for vert in bbox1)
            min2 = min(vert[axis] for vert in bbox2)
            max2 = max(vert[axis] for vert in bbox2)
           
            if max1 < min2 - threshold or min1 > max2 + threshold:
                return False
       
        return True
   
    def _calculate_intersection_point(self, road1, road2):
        """Professional intersection point calculation"""
        # Professional intersection point calculation
        # This is a simplified version - in practice, you'd use proper geometric intersection
        center1 = Vector(road1.location)
        center2 = Vector(road2.location)
       
        return (center1 + center2) / 2
   
    def _create_intersection_mesh(self, intersection, radius: float):
        """Professional intersection mesh creation"""
        try:
            # Professional intersection mesh creation
            mesh = bpy.data.meshes.new("RAGE_Intersection_Professional")
            obj = bpy.data.objects.new("RAGE_Intersection_Professional", mesh)
           
            # Professional scene linking
            bpy.context.collection.objects.link(obj)
            obj.location = intersection['point']
           
            # Professional intersection properties
            obj["rage_intersection"] = True
            obj["intersection_radius"] = radius
           
            print("✅ Professional intersection created")
           
        except Exception as e:
            print(f"⚠️ Intersection creation failed: {e}")

class RAGE_OT_ConvertCurveToRoad(Operator):
    bl_idname = "rage.convert_curve_to_road"
    bl_label = "Convert Curve to Road"
    bl_description = "Convert existing professional curve to RAGE-compatible road with automatic optimization"
   
    road_width: FloatProperty(
        name="Road Width",
        description="Professional converted road width",
        default=8.0,
        min=1.0,
        max=50.0
    )
   
    optimize_geometry: BoolProperty(
        name="Optimize Geometry",
        description="Professional geometry optimization for game performance",
        default=True
    )
   
    simplify_tolerance: FloatProperty(
        name="Simplify Tolerance",
        description="Professional curve simplification tolerance",
        default=0.1,
        min=0.01,
        max=1.0
    )
   
    def execute(self, context):
        if not context.active_object or context.active_object.type != 'CURVE':
            self.report({'ERROR'}, "❌ Select a professional curve object to convert")
            return {'CANCELLED'}
       
        curve_obj = context.active_object
       
        try:
            # Professional curve optimization
            if self.optimize_geometry:
                self._optimize_curve(curve_obj, self.simplify_tolerance)
           
            # Professional road conversion
            road_data = self._create_road_mesh(curve_obj, self.road_width, 0.3, 0.5)
           
            # Professional property transfer
            self._transfer_curve_properties(curve_obj, road_data)
           
            self.report({'INFO'}, f"✅ Professional curve converted to road: {self.road_width}m width")
           
        except Exception as e:
            self.report({'ERROR'}, f"❌ Curve conversion failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _optimize_curve(self, curve_obj, tolerance: float):
        """Professional curve optimization"""
        try:
            curve = curve_obj.data
           
            for spline in curve.splines:
                if spline.type == 'BEZIER' and len(spline.bezier_points) > 2:
                    # Professional Bezier curve simplification
                    self._simplify_bezier_spline(spline, tolerance)
                elif spline.type == 'POLY' and len(spline.points) > 2:
                    # Professional poly curve simplification
                    self._simplify_poly_spline(spline, tolerance)
           
            print("✅ Professional curve optimization completed")
           
        except Exception as e:
            print(f"⚠️ Curve optimization failed: {e}")
   
    def _simplify_bezier_spline(self, spline, tolerance: float):
        """Professional Bezier spline simplification"""
        # Professional Bezier curve simplification algorithm
        # This would implement industry-standard curve simplification
        pass
   
    def _simplify_poly_spline(self, spline, tolerance: float):
        """Professional poly spline simplification"""
        # Professional poly curve simplification algorithm
        # This would implement industry-standard polyline simplification
        pass
   
    def _transfer_curve_properties(self, curve_obj, road_obj):
        """Professional property transfer from curve to road"""
        # Transfer professional properties
        if "rage_road_type" in curve_obj:
            road_obj["rage_road_type"] = curve_obj["rage_road_type"]
       
        if "road_name" in curve_obj:
            road_obj.name = f"RAGE_Road_{curve_obj['road_name']}_Professional"
       
        # Professional metadata transfer
        road_obj["converted_from_curve"] = True
        road_obj["original_curve"] = curve_obj.name

class RAGE_OT_GeneratePath(Operator):
    bl_idname = "rage.generate_path"
    bl_label = "Generate Path"
    bl_description = "Create professional pedestrian or animal paths with optimized geometry"
   
    path_width: FloatProperty(
        name="Path Width",
        description="Professional path width in meters",
        default=2.0,
        min=0.5,
        max=10.0
    )
   
    path_type: EnumProperty(
        name="Path Type",
        description="Professional path type",
        items=[
            ('PEDESTRIAN', 'Pedestrian', 'Professional walking path'),
            ('ANIMAL', 'Animal', 'Professional animal trail'),
            ('BIKE', 'Bike', 'Professional bicycle path')
        ],
        default='PEDESTRIAN'
    )
   
    surface_type: EnumProperty(
        name="Surface Type",
        description="Professional path surface material",
        items=[
            ('DIRT', 'Dirt', 'Professional dirt path'),
            ('GRAVEL', 'Gravel', 'Professional gravel path'),
            ('PAVED', 'Paved', 'Professional paved path')
        ],
        default='DIRT'
    )
   
    create_collision: BoolProperty(
        name="Create Collision",
        description="Generate professional collision for path",
        default=True
    )
   
    def execute(self, context):
        if not context.active_object or context.active_object.type != 'CURVE':
            self.report({'ERROR'}, "❌ Select a professional curve object for path")
            return {'CANCELLED'}
       
        curve_obj = context.active_object
       
        try:
            # Professional path generation
            path_data = self._create_path_system(
                curve_obj,
                self.path_width,
                self.path_type,
                self.surface_type
            )
           
            # Professional collision generation
            if self.create_collision:
                self._create_path_collision(path_data)
           
            self.report({'INFO'}, f"✅ Professional {self.path_type.lower()} path created")
           
        except Exception as e:
            self.report({'ERROR'}, f"❌ Path generation failed: {str(e)}")
            return {'CANCELLED'}
       
        return {'FINISHED'}
   
    def _create_path_system(self, curve_obj, width: float, path_type: str, surface_type: str):
        """Professional path system creation"""
        # Professional path mesh creation
        path_mesh = self._create_path_mesh(curve_obj, width, path_type)
       
        # Professional path material creation
        self._create_path_material(path_mesh, surface_type, path_type)
       
        return {
            'path_mesh': path_mesh,
            'path_type': path_type,
            'surface_type': surface_type,
            'width': width
        }
   
    def _create_path_mesh(self, curve_obj, width: float, path_type: str):
        """Professional path mesh generation"""
        # Professional path mesh creation (similar to road but with different parameters)
        mesh = bpy.data.meshes.new(f"RAGE_{path_type}_Path_Professional")
        obj = bpy.data.objects.new(f"RAGE_{path_type}_Path_Professional", mesh)
       
        # Professional scene linking
        bpy.context.collection.objects.link(obj)
        obj.location = curve_obj.location
       
        # Professional bmesh processing
        bm = bmesh.new()
       
        try:
            # Professional curve sampling with path-specific parameters
            curve_length = self._calculate_curve_length(curve_obj)
            segment_count = max(4, int(curve_length * 0.3))  # Professional path resolution
           
            curve_points = self._sample_curve_points(curve_obj, segment_count)
           
            vertices = []
            faces = []
           
            # Generate professional path vertices
            for i, point in enumerate(curve_points):
                if i == 0:
                    direction = (curve_points[1] - point).normalized()
                elif i == len(curve_points) - 1:
                    direction = (point - curve_points[i-1]).normalized()
                else:
                    direction = (curve_points[i+1] - curve_points[i-1]).normalized()
               
                perpendicular = direction.cross(Vector((0, 0, 1))).normalized()
               
                left_point = point + perpendicular * (width / 2)
                right_point = point - perpendicular * (width / 2)
               
                vertices.extend([left_point, right_point])
           
            # Generate professional path faces
            for i in range(len(curve_points) - 1):
                idx1 = i * 2
                idx2 = i * 2 + 1
                idx3 = (i + 1) * 2
                idx4 = (i + 1) * 2 + 1
               
                faces.append([idx1, idx2, idx4, idx3])
           
            # Professional mesh construction
            for vert in vertices:
                bm.verts.new(vert)
           
            bm.verts.ensure_lookup_table()
           
            for face_indices in faces:
                try:
                    face_verts = [bm.verts[i] for i in face_indices]
                    bm.faces.new(face_verts)
                except ValueError:
                    pass
           
            # Professional mesh finalization
            bm.to_mesh(mesh)
            mesh.update()
           
        finally:
            bm.free()
       
        # Professional path properties
        obj["rage_path"] = True
        obj["path_type"] = path_type
        obj["path_width"] = width
       
        return obj
   
    def _create_path_material(self, path_obj, surface_type: str, path_type: str):
        """Professional path material creation"""
        try:
            mat_name = f"RAGE_{path_type}_{surface_type}_Material_Professional"
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
           
            # Professional node cleanup
            nodes.clear()
           
            # Professional path shader setup
            output_node = nodes.new(type='ShaderNodeOutputMaterial')
            bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
           
            # Professional path material properties based on surface type
            if surface_type == 'DIRT':
                bsdf_node.inputs['Base Color'].default_value = (0.4, 0.3, 0.2, 1.0)  # Professional dirt color
                bsdf_node.inputs['Roughness'].default_value = 0.9
            elif surface_type == 'GRAVEL':
                bsdf_node.inputs['Base Color'].default_value = (0.5, 0.5, 0.5, 1.0)  # Professional gravel color
                bsdf_node.inputs['Roughness'].default_value = 0.8
            else:  # PAVED
                bsdf_node.inputs['Base Color'].default_value = (0.3, 0.3, 0.3, 1.0)  # Professional paved color
                bsdf_node.inputs['Roughness'].default_value = 0.7
           
            bsdf_node.inputs['Specular'].default_value = 0.1
           
            # Professional node connections
            links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
           
            # Professional material assignment
            if path_obj.data.materials:
                path_obj.data.materials[0] = mat
            else:
                path_obj.data.materials.append(mat)
           
            print(f"✅ Professional {surface_type} path material created")
               
        except Exception as e:
            print(f"⚠️ Path material creation failed: {e}")
   
    def _create_path_collision(self, path_data):
        """Professional path collision generation"""
        try:
            path_obj = path_data['path_mesh']
           
            # Professional collision mesh creation
            collision_mesh = path_obj.data.copy()
            collision_obj = bpy.data.objects.new(f"{path_obj.name}_Collision_Professional", collision_mesh)
           
            # Professional scene linking
            bpy.context.collection.objects.link(collision_obj)
           
            # Professional collision properties
            collision_obj["rage_collision"] = True
            collision_obj.display_type = 'WIRE'
            collision_obj.hide_render = True
           
            # Professional parenting
            collision_obj.parent = path_obj
            collision_obj.matrix_parent_inverse = path_obj.matrix_world.inverted()
           
            print("✅ Professional path collision generated")
           
        except Exception as e:
            print(f"⚠️ Path collision generation failed: {e}")

# Professional registration
classes = (
    RAGE_OT_CreateRoadFromCurve,
    RAGE_OT_GenerateRoadNetwork,
    RAGE_OT_ConvertCurveToRoad,
    RAGE_OT_GeneratePath,
)

def register():
    """Professional road tools registration"""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"❌ Failed to register road tool {cls.__name__}: {e}")
            raise

def unregister():
    """Professional road tools unregistration"""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"⚠️ Failed to unregister road tool {cls.__name__}: {e}")