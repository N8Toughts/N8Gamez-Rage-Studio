import bpy
import threading
import time
import socket
import json
from bpy.types import Operator, Panel
from bpy.props import BoolProperty, StringProperty, IntProperty

class GameDataStreamer:
    """Real-time game data streaming for GTA V and RDR2"""
   
    def __init__(self):
        self.host = 'localhost'
        self.port = 29291
        self.clients = []
        self.running = False
        self.server_thread = None
        self.last_coords = None
       
    def start_streaming(self):
        """Start socket server for real-time data streaming"""
        if self.running:
            return  # Already running
           
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
       
        # Start coordinate polling
        self._start_coordinate_polling()
       
        print(f"🎮 Game streaming started on {self.host}:{self.port}")
       
    def stop_streaming(self):
        """Stop all streaming activities"""
        self.running = False
        self.clients.clear()
        print("🛑 Game streaming stopped")
       
    def _run_server(self):
        """Run TCP server for game data streaming"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
       
        try:
            sock.bind((self.host, self.port))
            sock.listen(5)
           
            while self.running:
                try:
                    sock.settimeout(1.0)  # Non-blocking accept
                    client, addr = sock.accept()
                    self.clients.append(client)
                    print(f"🎯 Game client connected: {addr}")
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:  # Only log if we're supposed to be running
                        print(f"⚠️ Client connection error: {e}")
                   
        except Exception as e:
            print(f"❌ Streaming server error: {e}")
        finally:
            sock.close()
           
    def _start_coordinate_polling(self):
        """Start polling for game coordinates"""
        def poll_coordinates():
            while self.running:
                try:
                    # Simulate coordinate updates - replace with real game data
                    coords = self._get_simulated_coordinates()
                    if coords:
                        self.send_coordinates(*coords)
                    time.sleep(0.1)  # 10Hz polling
                except Exception as e:
                    print(f"⚠️ Coordinate polling error: {e}")
                    time.sleep(1.0)
                   
        poll_thread = threading.Thread(target=poll_coordinates, daemon=True)
        poll_thread.start()
       
    def _get_simulated_coordinates(self):
        """Simulate game coordinates - replace with real game integration"""
        # This would connect to GTA V/RDR2 memory and read actual coordinates
        # For now, we simulate movement in a circle
        import math
        t = time.time()
        radius = 10.0
        x = math.cos(t) * radius
        y = math.sin(t) * radius 
        z = 5.0
       
        return (x, y, z)
       
    def send_coordinates(self, x, y, z, rotation=None):
        """Send coordinates to connected clients"""
        data = {
            'type': 'coordinates',
            'x': x,
            'y': y,
            'z': z,
            'rotation': rotation or {'x': 0, 'y': 0, 'z': 0},
            'timestamp': time.time()
        }
       
        self._broadcast_data(data)
       
    def _broadcast_data(self, data):
        """Broadcast data to all connected clients"""
        json_data = json.dumps(data) + '\n'
        disconnected_clients = []
       
        for client in self.clients:
            try:
                client.send(json_data.encode('utf-8'))
            except:
                disconnected_clients.append(client)
               
        # Remove disconnected clients
        for client in disconnected_clients:
            self.clients.remove(client)

class RAGE_OT_StartGameStreaming(Operator):
    bl_idname = "rage.start_game_streaming"
    bl_label = "Start Game Streaming"
    bl_description = "Start real-time game data streaming"
   
    def execute(self, context):
        if not hasattr(bpy.types.Scene, 'rage_game_streamer'):
            bpy.types.Scene.rage_game_streamer = GameDataStreamer()
           
        streamer = bpy.types.Scene.rage_game_streamer
        streamer.start_streaming()
       
        self.report({'INFO'}, "✅ Game streaming started")
        return {'FINISHED'}

class RAGE_OT_StopGameStreaming(Operator):
    bl_idname = "rage.stop_game_streaming"
    bl_label = "Stop Game Streaming"
    bl_description = "Stop real-time game data streaming"
   
    def execute(self, context):
        if hasattr(bpy.types.Scene, 'rage_game_streamer') and bpy.types.Scene.rage_game_streamer:
            bpy.types.Scene.rage_game_streamer.stop_streaming()
            self.report({'INFO'}, "🛑 Game streaming stopped")
        else:
            self.report({'WARNING'}, "⚠️ Game streaming not active")
           
        return {'FINISHED'}

class RAGE_OT_ConnectToGame(Operator):
    bl_idname = "rage.connect_to_game"
    bl_label = "Connect to Game"
    bl_description = "Connect to running GTA V or RDR2 instance"
   
    def execute(self, context):
        # This would implement actual game process connection
        # For now, we start the streaming server
        bpy.ops.rage.start_game_streaming()
        self.report({'INFO'}, "🎮 Connected to game simulation")
        return {'FINISHED'}

class RAGE_PT_GameIntegration(Panel):
    bl_label = "Game Integration"
    bl_idname = "RAGE_PT_game_integration"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RAGE'
   
    def draw(self, context):
        layout = self.layout
       
        box = layout.box()
        box.label(text="Real-time Game Integration", icon='WORLD')
       
        # Streaming controls
        row = box.row()
        row.operator("rage.connect_to_game", icon='LINKED')
        row.operator("rage.start_game_streaming", icon='PLAY')
        row.operator("rage.stop_game_streaming", icon='PAUSE')
       
        # Status
        streamer_active = hasattr(bpy.types.Scene, 'rage_game_streamer') and \
                         bpy.types.Scene.rage_game_streamer and \
                         bpy.types.Scene.rage_game_streamer.running
       
        if streamer_active:
            box.label(text="🟢 Streaming Active", icon='CHECKMARK')
            if bpy.types.Scene.rage_game_streamer.last_coords:
                coords = bpy.types.Scene.rage_game_streamer.last_coords
                box.label(text=f"Coordinates: {coords}")
        else:
            box.label(text="🔴 Streaming Inactive", icon='CANCEL')
       
        # Instructions
        box.label(text="Streams real-time coordinates to Blender", icon='INFO')

def register():
    bpy.utils.register_class(RAGE_OT_StartGameStreaming)
    bpy.utils.register_class(RAGE_OT_StopGameStreaming)
    bpy.utils.register_class(RAGE_OT_ConnectToGame)
    bpy.utils.register_class(RAGE_PT_GameIntegration)

def unregister():
    bpy.utils.unregister_class(RAGE_OT_StartGameStreaming)
    bpy.utils.unregister_class(RAGE_OT_StopGameStreaming)
    bpy.utils.unregister_class(RAGE_OT_ConnectToGame)
    bpy.utils.unregister_class(RAGE_PT_GameIntegration)