# RAGE Studio Suite - Professional File Format Analysis
import struct
import os
import socket
import json
import threading
import time
import numpy as np
from typing import Tuple, Dict, Any, List, Optional

class RDR1FileAnalyzer:
    """
    Industry-standard file format analyzer for RDR1 PC
    Based on RAGE engine patterns and community research
    """
   
    def __init__(self):
        # RDR1-specific format signatures
        self.format_signatures = {
            b'\x52\x44\x52': 'RDR Model',
            b'\x52\x47\x45': 'RAGE Container',
            b'\x57\x44\x52': 'WDR Model',
            b'\x57\x44\x44': 'WDD Texture',
            b'\x49\x4D\x47': 'IMG Archive',
            b'\x52\x53\x43': 'RSC Resource',
            b'\x56\x45\x52\x54': 'VERT Data',
            b'\x49\x4E\x44\x58': 'INDX Data',
            b'\x46\x4F\x52\x4D': 'FORM Data',
        }
       
        self.known_extensions = {
            '.wdr': 'RDR1 Drawable',
            '.wdd': 'RDR1 Drawable Dictionary',
            '.wtd': 'RDR1 Texture Dictionary',
            '.wbn': 'RDR1 Bound',
            '.wbd': 'RDR1 Bound Data',
            '.ymap': 'RDR1 Map Data',
            '.ytyp': 'RDR1 Type Data',
            '.yft': 'RDR1 Fragment',
            '.ydd': 'RDR1 Drawable Dictionary',
            '.ytd': 'RDR1 Texture Dictionary',
        }
       
        # RAGE version mapping
        self.rage_versions = {
            0x07: 'RSC7 (GTA V)',
            0x08: 'RSC8 (RDR2)',
            0x06: 'RSC6 (GTA IV)'
        }
   
    def analyze_file(self, filepath: str) -> Tuple[str, bytes]:
        """Comprehensive file analysis with industry-standard detection"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
           
        file_size = os.path.getsize(filepath)
       
        with open(filepath, 'rb') as f:
            header = f.read(128)
           
        # Extension-based detection
        ext = os.path.splitext(filepath)[1].lower()
        if ext in self.known_extensions:
            return self.known_extensions[ext], header
           
        # Magic signature detection
        for sig, format_name in self.format_signatures.items():
            if header.startswith(sig):
                return format_name, header
       
        # Deep structure analysis
        return self._deep_analysis(header, filepath, file_size)
   
    def _deep_analysis(self, header: bytes, filepath: str, file_size: int) -> Tuple[str, bytes]:
        """Advanced structure analysis using industry patterns"""
       
        # RAGE Resource Header
        if len(header) >= 16:
            magic = header[0:4]
           
            # RSC formats
            if magic == b'RSC7' or magic == b'RSC8':
                version = 7 if magic == b'RSC7' else 8
                return f"RAGE_Resource_v{version}", header
           
            # Check for version patterns
            if len(header) >= 32:
                potential_version = struct.unpack('<I', header[4:8])[0]
                if potential_version in self.rage_versions:
                    return f"RAGE_{self.rage_versions[potential_version]}", header
       
        # XML-based formats
        if header.startswith(b'<?xml') or header.startswith(b'<CMapData'):
            return "RAGE_XML_MapData", header
           
        return "Unknown_RAGE_Format", header
   
    def get_format_details(self, filepath: str) -> Dict[str, Any]:
        """Extract detailed format information"""
        format_name, header = self.analyze_file(filepath)
       
        details = {
            'format': format_name,
            'file_size': os.path.getsize(filepath),
            'header_hex': header.hex()[:64] + '...' if len(header) > 64 else header.hex(),
            'codewalker_compatible': False,
            'suggested_tools': []
        }
       
        # Format-specific analysis
        if 'WDR' in format_name:
            details.update(self._analyze_wdr_format(header))
            details['codewalker_compatible'] = True
            details['suggested_tools'].extend(['CodeWalker', 'OpenIV'])
        elif 'RSC' in format_name:
            details.update(self._analyze_rsc_format(header))
            details['codewalker_compatible'] = True
            details['suggested_tools'].append('CodeWalker')
        elif 'YMAP' in format_name or 'YTYP' in format_name:
            details.update(self._analyze_xml_format(filepath))
            details['codewalker_compatible'] = True
            details['suggested_tools'].extend(['CodeWalker', 'MapEditor'])
           
        return details
   
    def _analyze_wdr_format(self, header: bytes) -> Dict[str, Any]:
        """Analyze WDR model format structure"""
        analysis = {'vertices': 0, 'faces': 0, 'materials': 0, 'lod_count': 0}
       
        if len(header) >= 64:
            try:
                # WDR structure analysis
                vertex_block_offset = struct.unpack('<I', header[16:20])[0]
                index_block_offset = struct.unpack('<I', header[20:24])[0]
                material_count = struct.unpack('<H', header[28:30])[0]
                lod_count = struct.unpack('<B', header[31:32])[0]
               
                analysis.update({
                    'vertex_block_offset': vertex_block_offset,
                    'index_block_offset': index_block_offset,
                    'materials': material_count,
                    'lod_count': lod_count,
                })
            except struct.error:
                pass
               
        return analysis
   
    def _analyze_rsc_format(self, header: bytes) -> Dict[str, Any]:
        """Analyze RSC resource container format"""
        analysis = {}
       
        if len(header) >= 64:
            try:
                version = struct.unpack('<I', header[4:8])[0]
                system_flags = struct.unpack('<I', header[8:12])[0]
                graphics_flags = struct.unpack('<I', header[12:16])[0]
               
                analysis.update({
                    'version': version,
                    'version_name': self.rage_versions.get(version, 'Unknown'),
                    'system_flags': hex(system_flags),
                    'graphics_flags': hex(graphics_flags),
                })
            except struct.error:
                pass
               
        return analysis
   
    def _analyze_xml_format(self, filepath: str) -> Dict[str, Any]:
        """Analyze XML-based map files"""
        analysis = {}
       
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)
               
            if '<CMapData' in content:
                analysis['map_type'] = 'CMapData'
            if '<CEntityDef' in content:
                analysis['entity_count'] = content.count('<CEntityDef')
               
        except:
            pass
           
        return analysis

class CSharpBridge:
    """
    Professional IPC bridge between Blender and C# backend
    Implements industry-standard communication patterns
    """
   
    def __init__(self):
        self.socket = None
        self.callbacks = {}
        self.connected = False
        self.host = 'localhost'
        self.port = 29275
        self.listener_thread = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
       
    def connect(self, host: str = 'localhost', port: int = 29275) -> bool:
        """Establish connection with timeout and error handling"""
        self.host = host
        self.port = port
       
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)
           
            self.connected = True
            self.reconnect_attempts = 0
           
            # Start background listener
            self.listener_thread = threading.Thread(target=self._listen_messages, daemon=True)
            self.listener_thread.start()
           
            print(f"✅ Connected to RAGE Studio Bridge at {self.host}:{self.port}")
            return True
           
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
            return False
   
    def disconnect(self):
        """Cleanly disconnect from backend"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
           
        self.callbacks.clear()
        print("✅ Disconnected from RAGE Studio Bridge")
   
    def send_command(self, command: str, data: Any = None, callback: callable = None, timeout: float = 30.0) -> str:
        """Send command with professional error handling"""
        if not self.connected:
            if not self._attempt_reconnect():
                if callback:
                    callback({'success': False, 'error': 'Bridge not connected'})
                return None
           
        message_id = f"msg_{int(time.time() * 1000)}"
        payload = {
            'id': message_id,
            'command': command,
            'data': data,
            'timestamp': time.time()
        }
       
        if callback:
            self.callbacks[message_id] = {
                'callback': callback,
                'timestamp': time.time(),
                'timeout': timeout
            }
           
        try:
            json_data = json.dumps(payload, default=self._json_serializer).encode('utf-8')
            length = len(json_data).to_bytes(4, byteorder='little')
           
            self.socket.send(length + json_data)
            return message_id
           
        except Exception as e:
            print(f"❌ Failed to send command {command}: {e}")
            if message_id in self.callbacks:
                del self.callbacks[message_id]
            return None
   
    def _attempt_reconnect(self) -> bool:
        """Attempt reconnection with exponential backoff"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            return False
           
        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 30)
       
        print(f"🔄 Reconnect attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        time.sleep(wait_time)
       
        return self.connect(self.host, self.port)
   
    def _listen_messages(self):
        """Professional message listener with error handling"""
        buffer = b''
        expected_length = 0
       
        while self.connected:
            try:
                chunk = self.socket.recv(4096)
                if not chunk:
                    print("❌ Bridge connection closed by server")
                    self.connected = False
                    break
                   
                buffer += chunk
               
                while len(buffer) >= 4:
                    if expected_length == 0:
                        expected_length = int.from_bytes(buffer[:4], byteorder='little')
                        buffer = buffer[4:]
                   
                    if expected_length > 0 and len(buffer) >= expected_length:
                        json_data = buffer[:expected_length]
                        buffer = buffer[expected_length:]
                        expected_length = 0
                       
                        self._process_message(json_data)
                       
                # Check for timeouts
                self._check_timeouts()
                       
            except Exception as e:
                if self.connected:
                    print(f"❌ Bridge listener error: {e}")
                break
   
    def _process_message(self, json_data: bytes):
        """Process incoming messages professionally"""
        try:
            response = json.loads(json_data.decode('utf-8'))
            message_id = response.get('id')
           
            if message_id in self.callbacks:
                callback_data = self.callbacks[message_id]
                callback_data['callback'](response.get('data', {}))
                del self.callbacks[message_id]
            else:
                self._handle_unsolicited_message(response)
               
        except Exception as e:
            print(f"❌ Failed to process message: {e}")
   
    def _check_timeouts(self):
        """Handle callback timeouts"""
        current_time = time.time()
        timed_out = []
       
        for msg_id, callback_data in self.callbacks.items():
            if current_time - callback_data['timestamp'] > callback_data['timeout']:
                timed_out.append(msg_id)
                callback_data['callback']({
                    'success': False,
                    'error': f'Request timeout after {callback_data["timeout"]}s'
                })
       
        for msg_id in timed_out:
            del self.callbacks[msg_id]
   
    def _handle_unsolicited_message(self, response: dict):
        """Handle unsolicited messages"""
        message_type = response.get('type', 'notification')
        data = response.get('data', {})
       
        if message_type == 'notification':
            print(f"ℹ️ Bridge: {data.get('message', 'Unknown notification')}")
        elif message_type == 'error':
            print(f"❌ Bridge Error: {data.get('error', 'Unknown error')}")
   
    def _json_serializer(self, obj):
        """Professional JSON serializer"""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, 'to_json'):
            return obj.to_json()
        elif isinstance(obj, (np.ndarray, np.generic)):
            return obj.tolist()
        else:
            return str(obj)
   
    # RDR1-specific commands
    def import_rdr_model(self, filepath: str, settings: dict, callback: callable = None) -> str:
        """Import RDR1 model file"""
        return self.send_command('import_rdr_model', {
            'filepath': filepath,
            'settings': settings
        }, callback)
   
    def export_rdr_model(self, filepath: str, export_data: dict, callback: callable = None) -> str:
        """Export to RDR1 model format"""
        return self.send_command('export_rdr_model', {
            'filepath': filepath,
            'export_data': export_data
        }, callback)
   
    def test_connection(self) -> bool:
        """Test bridge connection"""
        if not self.connected:
            return False
           
        ping_received = False
        def ping_callback(response):
            nonlocal ping_received
            ping_received = True
           
        self.send_command('ping', callback=ping_callback)
       
        timeout = 2.0
        start_time = time.time()
        while not ping_received and (time.time() - start_time) < timeout:
            time.sleep(0.1)
           
        return ping_received
   
    def get_status(self) -> dict:
        """Get bridge status"""
        return {
            'connected': self.connected,
            'host': self.host,
            'port': self.port,
            'pending_callbacks': len(self.callbacks),
            'reconnect_attempts': self.reconnect_attempts
        }