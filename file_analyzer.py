#!/usr/bin/env python3
# =============================================================================
# RDR1 RAGE Evolutionary Analyzer - COMPLETE EDITION
# Enhanced with GUI, batch processing, AND archive creation
# Now with 100% more wranglin' power!
# =============================================================================

import os
import sys
import json
import struct
import zlib
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime

# Third-party imports for enhanced functionality
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rage_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RAGEAnalyzer")

@dataclass
class RPF6Header:
    """RPF6 Archive Header Structure"""
    magic: int
    toc_size: int
    entry_count: int
    names_length: int
    encryption: int
    special_flag: int
    is_valid_rdr1: bool

@dataclass
class RPF6Entry:
    """RPF6 Archive Entry"""
    index: int
    name_offset: int
    data_size: int
    data_offset: int
    flags: int
    uncompressed_size: int
    name: str = ""
    is_compressed: bool = False
    is_directory: bool = False
    resource_type: int = 0

@dataclass
class RPF6FileData:
    """Container for file data with metadata for writing"""
    name: str
    data: bytes
    is_compressed: bool = False
    is_directory: bool = False
    uncompressed_size: int = 0
   
    def __post_init__(self):
        if self.is_compressed and self.uncompressed_size == 0:
            self.uncompressed_size = len(self.data)

class BigEndianEngine:
    """Big Endian serialization/deserialization engine"""

    @staticmethod
    def read_uint32(data: bytes, offset: int) -> int:
        return struct.unpack('>I', data[offset:offset+4])[0]

    @staticmethod
    def read_uint16(data: bytes, offset: int) -> int:
        return struct.unpack('>H', data[offset:offset+2])[0]

    @staticmethod
    def read_float(data: bytes, offset: int) -> float:
        return struct.unpack('>f', data[offset:offset+4])[0]

    @staticmethod
    def write_uint32(value: int) -> bytes:
        return struct.pack('>I', value)

    @staticmethod
    def write_uint16(value: int) -> bytes:
        return struct.pack('>H', value)

class AdvancedZLibCompressor:
    """Enhanced ZLib compression with game compatibility"""

    @staticmethod
    def compress(data: bytes, compression_level: int = 6) -> bytes:
        """Compress data with RDR1-compatible settings"""
        try:
            if not data:
                return data

            # Use zlib with RDR1-compatible settings
            compress_obj = zlib.compressobj(
                level=compression_level,
                method=zlib.DEFLATED,
                wbits=zlib.MAX_WBITS
            )
            compressed = compress_obj.compress(data) + compress_obj.flush()

            logger.info(f"Compressed {len(data)} -> {len(compressed)} bytes")
            return compressed

        except Exception as e:
            logger.error(f"Compression failed: {e}")
            raise

    @staticmethod
    def decompress(data: bytes, uncompressed_size: int = 0) -> bytes:
        """Decompress data with error handling"""
        try:
            if not data:
                return data

            decompressed = zlib.decompress(data)

            # Handle size validation and padding
            if uncompressed_size > 0:
                if len(decompressed) < uncompressed_size:
                    # Pad with zeros
                    decompressed += b'\x00' * (uncompressed_size - len(decompressed))
                elif len(decompressed) > uncompressed_size:
                    # Truncate
                    decompressed = decompressed[:uncompressed_size]

            logger.info(f"Decompressed {len(data)} -> {len(decompressed)} bytes")
            return decompressed

        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            # Return original data as fallback
            return data

class RPF6Editor:
    """Enhanced RPF6 Archive Editor with GUI support"""

    def __init__(self, file_path: str, read_only: bool = True):
        self.file_path = file_path
        self.read_only = read_only
        self.header: Optional[RPF6Header] = None
        self.entries: List[RPF6Entry] = []
        self.name_table: bytes = b""
        self.alignment = 2048
        self.file_handle = None
        self.endianness = "big"

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        self._open_file()
        self.parse_rpf6_structure()

    def _open_file(self):
        """Open file with appropriate mode"""
        mode = 'rb' if self.read_only else 'r+b'
        self.file_handle = open(self.file_path, mode)

    def parse_rpf6_structure(self):
        """Parse RPF6 archive structure"""
        logger.info(f"Parsing RPF6 structure: {self.file_path}")

        try:
            self.file_handle.seek(0)
            header_bytes = self.file_handle.read(24)

            if len(header_bytes) < 24:
                raise ValueError("File too small for RPF6 header")

            # Parse header
            self.header = RPF6Header(
                magic=BigEndianEngine.read_uint32(header_bytes, 0),
                toc_size=BigEndianEngine.read_uint32(header_bytes, 4),
                entry_count=BigEndianEngine.read_uint32(header_bytes, 8),
                names_length=BigEndianEngine.read_uint32(header_bytes, 12),
                encryption=BigEndianEngine.read_uint32(header_bytes, 16),
                special_flag=BigEndianEngine.read_uint32(header_bytes, 20),
                is_valid_rdr1=header_bytes[20:24] == b'\x52\x53\x44\x0A'
            )

            # Validate magic number
            if self.header.magic != 0x52504636: # 'RPF6'
                raise ValueError(f"Invalid RPF6 magic: 0x{self.header.magic:08X}")

            # Parse entries
            self._parse_entries()

            # Parse name table
            self._parse_name_table()

            logger.info(f"RPF6 structure parsed: {len(self.entries)} entries")

        except Exception as e:
            logger.error(f"Failed to parse RPF6 structure: {e}")
            raise

    def _parse_entries(self):
        """Parse TOC entries"""
        self.entries = []

        for i in range(self.header.entry_count):
            entry_offset = 24 + (i * 16)
            self.file_handle.seek(entry_offset)
            entry_bytes = self.file_handle.read(16)

            if len(entry_bytes) < 16:
                break

            entry = RPF6Entry(
                index=i,
                name_offset=BigEndianEngine.read_uint32(entry_bytes, 0),
                data_size=BigEndianEngine.read_uint32(entry_bytes, 4),
                data_offset=struct.unpack('>I', b'\x00' + entry_bytes[8:11])[0], # 3-byte offset
                flags=entry_bytes[11],
                uncompressed_size=BigEndianEngine.read_uint32(entry_bytes, 12)
            )

            # Parse flags
            entry.is_compressed = (entry.flags & 0x80) != 0
            entry.is_directory = (entry.flags & 0x40) != 0
            entry.resource_type = entry.flags & 0x3F

            self.entries.append(entry)

    def _parse_name_table(self):
        """Parse name table and resolve entry names"""
        name_table_start = 24 + (self.header.entry_count * 16)
        self.file_handle.seek(name_table_start)
        self.name_table = self.file_handle.read(self.header.names_length)

        # Resolve entry names
        for entry in self.entries:
            name_bytes = bytearray()
            offset = entry.name_offset

            while offset < len(self.name_table) and self.name_table[offset] != 0:
                name_bytes.append(self.name_table[offset])
                offset += 1

            if name_bytes:
                entry.name = name_bytes.decode('ascii', errors='replace')
            else:
                entry.name = f'[Unnamed_{entry.index}]'

    def extract_file(self, file_name: str) -> bytes:
        """Extract file from archive"""
        entry = next((e for e in self.entries if e.name == file_name and not e.is_directory), None)

        if not entry:
            raise ValueError(f"File not found in archive: {file_name}")

        logger.info(f"Extracting: {file_name} ({entry.data_size} bytes)")

        # Calculate actual data offset
        actual_data_offset = entry.data_offset * self.alignment

        if actual_data_offset >= os.path.getsize(self.file_path):
            raise ValueError(f"Data offset beyond file size: {actual_data_offset}")

        # Read file data
        self.file_handle.seek(actual_data_offset)
        file_data = self.file_handle.read(entry.data_size)

        # Handle compression
        if entry.is_compressed:
            logger.info(f"Decompressing: {file_name}")
            try:
                file_data = AdvancedZLibCompressor.decompress(file_data, entry.uncompressed_size)
            except Exception as e:
                logger.warning(f"Decompression failed for {file_name}: {e}")
                # Return compressed data as fallback

        return file_data

    def get_archive_info(self) -> Dict[str, Any]:
        """Get comprehensive archive information"""
        compressed_files = sum(1 for e in self.entries if e.is_compressed)
        directories = sum(1 for e in self.entries if e.is_directory)
        total_uncompressed = sum(e.uncompressed_size for e in self.entries if e.is_compressed)

        return {
            'total_entries': self.header.entry_count,
            'compressed_files': compressed_files,
            'directories': directories,
            'name_table_size': self.header.names_length,
            'estimated_uncompressed_size': total_uncompressed,
            'is_rdr1_archive': self.header.is_valid_rdr1,
            'archive_size': os.path.getsize(self.file_path)
        }

    def close(self):
        """Close file handle"""
        if self.file_handle:
            self.file_handle.close()
        self.file_handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class RPF6Writer:
    """Complete RPF6 Archive Writer - Wrangler of File Structures"""
   
    def __init__(self):
        self.entries: List[RPF6Entry] = []
        self.name_table = b""
        self.alignment = 2048
        self.encryption = 0
        self.special_flag = 0x5253440A # RDR1 PC signature
       
    def create_new_archive(self):
        """Create a new empty RPF6 archive - Fresh start, partner!"""
        logger.info("Creating new RPF6 archive - fresh territory!")
        self.entries = []
        self.name_table = b""
        return True
       
    def add_file(self, file_path: Union[str, Path], archive_path: str, compress: bool = False, compression_level: int = 6) -> bool:
        """Add a file to the archive - Load 'er up!"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False
               
            with open(file_path, 'rb') as f:
                file_data = f.read()
               
            return self.add_file_data(file_data, archive_path, compress, compression_level)
               
        except Exception as e:
            logger.error(f"Failed to add file {file_path}: {e}")
            return False
           
    def add_file_data(self, file_data: bytes, archive_path: str, compress: bool = False, compression_level: int = 6) -> bool:
        """Add file data directly to archive"""
        try:
            uncompressed_size = len(file_data)
            data_size = uncompressed_size
           
            # Handle compression if requested
            compressed_data = None
            if compress:
                logger.info(f"Compressing: {archive_path}")
                compressed_data = AdvancedZLibCompressor.compress(file_data, compression_level)
                data_size = len(compressed_data)
               
            # Create entry
            entry = RPF6Entry(
                index=len(self.entries),
                name_offset=0, # Will be set during build
                data_size=data_size,
                data_offset=0, # Will be calculated during build
                flags=0,
                uncompressed_size=uncompressed_size,
                name=archive_path,
                is_compressed=compress,
                is_directory=False,
                resource_type=0
            )
           
            # Store the actual data
            entry._file_data = compressed_data if compress else file_data
           
            self.entries.append(entry)
            logger.info(f"Added file: {archive_path} ({data_size} bytes)")
            return True
           
        except Exception as e:
            logger.error(f"Failed to add file data for {archive_path}: {e}")
            return False
           
    def add_directory(self, dir_path: str) -> bool:
        """Add a directory entry - Marking our territory!"""
        try:
            # Ensure directory path ends with /
            if not dir_path.endswith('/'):
                dir_path += '/'
               
            entry = RPF6Entry(
                index=len(self.entries),
                name_offset=0,
                data_size=0,
                data_offset=0,
                flags=0x40, # Directory flag
                uncompressed_size=0,
                name=dir_path,
                is_compressed=False,
                is_directory=True,
                resource_type=0
            )
           
            self.entries.append(entry)
            logger.info(f"Added directory: {dir_path}")
            return True
           
        except Exception as e:
            logger.error(f"Failed to add directory {dir_path}: {e}")
            return False
           
    def add_directory_recursive(self, local_directory: Union[str, Path], archive_base_path: str = "") -> bool:
        """Add a directory and all its contents recursively - Roundup time!"""
        try:
            local_path = Path(local_directory)
           
            if not local_path.exists():
                logger.error(f"Directory not found: {local_path}")
                return False
               
            # Add the directory itself
            if archive_base_path:
                self.add_directory(archive_base_path)
               
            # Add all files and subdirectories
            for item in local_path.rglob('*'):
                relative_path = item.relative_to(local_path)
                archive_path = str(Path(archive_base_path) / relative_path) if archive_base_path else str(relative_path)
               
                if item.is_file():
                    # Convert Windows paths to RPF format
                    archive_path = archive_path.replace('\\', '/')
                    self.add_file(item, archive_path)
                elif item.is_dir():
                    archive_path = archive_path.replace('\\', '/') + '/'
                    self.add_directory(archive_path)
                   
            logger.info(f"Added directory recursively: {local_path} -> {archive_base_path}")
            return True
           
        except Exception as e:
            logger.error(f"Failed to add directory recursively {local_directory}: {e}")
            return False
           
    def remove_entry(self, archive_path: str) -> bool:
        """Remove an entry from the archive - Cleaning house!"""
        initial_count = len(self.entries)
        self.entries = [e for e in self.entries if e.name != archive_path]
       
        removed = len(self.entries) < initial_count
        if removed:
            logger.info(f"Removed entry: {archive_path}")
        else:
            logger.warning(f"Entry not found for removal: {archive_path}")
           
        return removed
       
    def _build_name_table(self) -> Dict[str, int]:
        """Build the name table and return name offsets - Making our mark!"""
        logger.info("Building name table...")
       
        # Sort entries by name for consistent ordering
        sorted_entries = sorted(self.entries, key=lambda x: x.name)
       
        self.name_table = b""
        name_offsets = {}
       
        for entry in sorted_entries:
            if entry.name not in name_offsets:
                name_offsets[entry.name] = len(self.name_table)
                encoded_name = entry.name.encode('ascii', errors='replace')
                self.name_table += encoded_name + b'\x00' # Null-terminated
               
        logger.info(f"Name table built: {len(self.name_table)} bytes, {len(name_offsets)} unique names")
        return name_offsets
       
    def _calculate_data_offsets(self) -> List[int]:
        """Calculate data offsets for all entries - Planning the trail!"""
        logger.info("Calculating data offsets...")
       
        # Calculate sizes
        header_size = 24
        toc_size = len(self.entries) * 16
        names_size = len(self.name_table)
       
        # Start of data section (aligned)
        data_start = header_size + toc_size + names_size
        data_start = ((data_start + self.alignment - 1) // self.alignment) * self.alignment
       
        offsets = []
        current_offset = data_start
       
        for entry in self.entries:
            if entry.is_directory:
                # Directories don't have data
                offsets.append(0)
            else:
                offsets.append(current_offset)
                # Move to next aligned position
                current_offset += ((entry.data_size + self.alignment - 1) // self.alignment) * self.alignment
               
        logger.info(f"Data offsets calculated. Total archive size: ~{current_offset} bytes")
        return offsets
       
    def get_archive_info(self) -> Dict[str, Any]:
        """Get information about the current archive state - Taking stock!"""
        compressed_files = sum(1 for e in self.entries if e.is_compressed)
        directories = sum(1 for e in self.entries if e.is_directory)
        total_compressed_size = sum(e.data_size for e in self.entries if e.is_compressed and not e.is_directory)
        total_uncompressed_size = sum(e.uncompressed_size for e in self.entries if not e.is_directory)
       
        return {
            'total_entries': len(self.entries),
            'file_entries': len(self.entries) - directories,
            'compressed_files': compressed_files,
            'directories': directories,
            'name_table_size': len(self.name_table),
            'total_compressed_size': total_compressed_size,
            'total_uncompressed_size': total_uncompressed_size,
            'compression_ratio': total_compressed_size / total_uncompressed_size if total_uncompressed_size > 0 else 0,
            'estimated_archive_size': self._estimate_archive_size(),
            'is_rdr1_format': True
        }
       
    def _estimate_archive_size(self) -> int:
        """Estimate the final archive size - Scoutin' ahead!"""
        header_size = 24
        toc_size = len(self.entries) * 16
        names_size = len(self.name_table)
       
        data_size = sum(
            ((e.data_size + self.alignment - 1) // self.alignment) * self.alignment
            for e in self.entries if not e.is_directory
        )
       
        total_size = header_size + toc_size + names_size + data_size
        return total_size
       
    def write_archive(self, output_path: Union[str, Path], progress_callback=None) -> bool:
        """Write the complete RPF6 archive to disk - Headin' for the sunset!"""
        try:
            output_path = Path(output_path)
            logger.info(f"Writing RPF6 archive to: {output_path}")
           
            # Build name table and get offsets
            name_offsets = self._build_name_table()
           
            # Calculate data offsets
            data_offsets = self._calculate_data_offsets()
           
            # Update entries with calculated offsets
            for i, entry in enumerate(self.entries):
                entry.name_offset = name_offsets[entry.name]
                entry.data_offset = data_offsets[i] // self.alignment # Convert to 2048-block units
               
                # Build flags
                entry.flags = 0
                if entry.is_compressed:
                    entry.flags |= 0x80
                if entry.is_directory:
                    entry.flags |= 0x40
                entry.flags |= (entry.resource_type & 0x3F)
               
            # Create directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
           
            with open(output_path, 'wb') as f:
                # Write header
                header = struct.pack('>IIIIII',
                    0x52504636, # magic 'RPF6'
                    len(self.entries) * 16, # toc_size
                    len(self.entries), # entry_count
                    len(self.name_table), # names_length
                    self.encryption,
                    self.special_flag # RDR1 PC signature
                )
                f.write(header)
               
                if progress_callback:
                    progress_callback(10, "Writing table of contents...")
               
                # Write TOC entries
                for i, entry in enumerate(self.entries):
                    # Pack entry data
                    entry_bytes = struct.pack('>II',
                        entry.name_offset,
                        entry.data_size
                    )
                   
                    # 3-byte data offset (big endian)
                    data_offset_3byte = struct.pack('>I', entry.data_offset)[1:4]
                    entry_bytes += data_offset_3byte
                   
                    # Flags and uncompressed size
                    entry_bytes += bytes([entry.flags])
                    entry_bytes += struct.pack('>I', entry.uncompressed_size)
                   
                    f.write(entry_bytes)
                   
                if progress_callback:
                    progress_callback(30, "Writing name table...")
               
                # Write name table
                f.write(self.name_table)
               
                # Pad to alignment
                current_pos = f.tell()
                next_aligned = ((current_pos + self.alignment - 1) // self.alignment) * self.alignment
                pad_size = next_aligned - current_pos
                if pad_size > 0:
                    f.write(b'\x00' * pad_size)
                   
                if progress_callback:
                    progress_callback(50, "Writing file data...")
               
                # Write file data
                for i, entry in enumerate(self.entries):
                    if not entry.is_directory and hasattr(entry, '_file_data'):
                        f.write(entry._file_data)
                       
                        # Pad to alignment
                        current_pos = f.tell()
                        next_aligned = ((current_pos + self.alignment - 1) // self.alignment) * self.alignment
                        pad_size = next_aligned - current_pos
                        if pad_size > 0:
                            f.write(b'\x00' * pad_size)
                           
                    if progress_callback and i % 10 == 0:
                        progress = 50 + (i / len(self.entries)) * 45
                        progress_callback(int(progress), f"Writing files... ({i}/{len(self.entries)})")
                       
            logger.info(f"Successfully wrote RPF6 archive: {output_path}")
           
            if progress_callback:
                progress_callback(100, "Archive complete!")
               
            return True
           
        except Exception as e:
            logger.error(f"Failed to write RPF6 archive: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {e}")
            return False
           
    def list_entries(self) -> List[Dict[str, Any]]:
        """List all entries in the archive - Taking roll call!"""
        return [{
            'name': entry.name,
            'size': entry.data_size,
            'uncompressed_size': entry.uncompressed_size,
            'is_directory': entry.is_directory,
            'is_compressed': entry.is_compressed,
            'resource_type': entry.resource_type
        } for entry in self.entries]

class RPF6Modifier(RPF6Writer):
    """Enhanced writer that can modify existing archives - Like a trusty steed that knows the trails!"""
   
    def __init__(self, source_archive_path: str = None):
        super().__init__()
        self.source_editor = None
        self.modified_entries = {}
        self.original_entries = {}
       
        if source_archive_path and os.path.exists(source_archive_path):
            self.load_existing_archive(source_archive_path)
   
    def load_existing_archive(self, archive_path: str) -> bool:
        """Load an existing archive as the base for modifications"""
        try:
            logger.info(f"Loading existing archive for modification: {archive_path}")
            self.source_editor = RPF6Editor(archive_path)
           
            # Copy all original entries to our writer
            for entry in self.source_editor.entries:
                # Store original entry data
                self.original_entries[entry.name] = {
                    'data_size': entry.data_size,
                    'uncompressed_size': entry.uncompressed_size,
                    'is_compressed': entry.is_compressed,
                    'is_directory': entry.is_directory,
                    'data_offset': entry.data_offset
                }
               
                # Add to writer entries (we'll extract data on-demand)
                new_entry = RPF6Entry(
                    index=len(self.entries),
                    name_offset=0,
                    data_size=entry.data_size,
                    data_offset=0,
                    flags=entry.flags,
                    uncompressed_size=entry.uncompressed_size,
                    name=entry.name,
                    is_compressed=entry.is_compressed,
                    is_directory=entry.is_directory,
                    resource_type=entry.resource_type
                )
               
                # Mark that this entry comes from original archive
                new_entry._from_original = True
                new_entry._original_path = archive_path
               
                self.entries.append(new_entry)
               
            logger.info(f"Loaded {len(self.entries)} entries from original archive")
            return True
           
        except Exception as e:
            logger.error(f"Failed to load existing archive: {e}")
            return False
   
    def replace_file(self, archive_path: str, new_file_path: str, compress: bool = None) -> bool:
        """Replace a file in the archive with a new version"""
        try:
            # Remove existing entry if it exists
            self.remove_entry(archive_path)
           
            # Add new file
            if compress is None:
                # Auto-detect compression based on file type
                compress = self._should_compress_file(archive_path)
               
            success = self.add_file(new_file_path, archive_path, compress)
            if success:
                self.modified_entries[archive_path] = 'replaced'
            return success
           
        except Exception as e:
            logger.error(f"Failed to replace file {archive_path}: {e}")
            return False
   
    def replace_file_data(self, archive_path: str, new_data: bytes, compress: bool = None) -> bool:
        """Replace file content with new data"""
        try:
            # Remove existing entry
            self.remove_entry(archive_path)
           
            if compress is None:
                compress = self._should_compress_file(archive_path)
               
            success = self.add_file_data(new_data, archive_path, compress)
            if success:
                self.modified_entries[archive_path] = 'replaced'
            return success
           
        except Exception as e:
            logger.error(f"Failed to replace file data for {archive_path}: {e}")
            return False
   
    def _should_compress_file(self, file_path: str) -> bool:
        """Determine if a file should be compressed based on its type"""
        compress_extensions = {'.wtd', '.wdr', '.wft', '.wvd', '.dds', '.xml', '.txt'}
        file_ext = Path(file_path).suffix.lower()
        return file_ext in compress_extensions
   
    def extract_original_file(self, archive_path: str) -> Optional[bytes]:
        """Extract a file from the original archive"""
        if not self.source_editor:
            return None
           
        try:
            return self.source_editor.extract_file(archive_path)
        except Exception as e:
            logger.warning(f"Failed to extract original file {archive_path}: {e}")
            return None
   
    def get_modification_summary(self) -> Dict[str, Any]:
        """Get summary of modifications made"""
        added_files = [e for e in self.entries if not hasattr(e, '_from_original') and not e.is_directory]
        modified_files = [name for name in self.modified_entries]
        removed_files = [name for name in self.original_entries if name not in [e.name for e in self.entries]]
       
        return {
            'original_files': len(self.original_entries),
            'current_files': len([e for e in self.entries if not e.is_directory]),
            'added_files': len(added_files),
            'modified_files': len(modified_files),
            'removed_files': len(removed_files),
            'added_file_list': [e.name for e in added_files],
            'modified_file_list': modified_files,
            'removed_file_list': removed_files
        }

class RDR1ModBuilder:
    """Specialized tool for creating clean RDR1 mod archives - Fresh trails for new adventures!"""
   
    def __init__(self):
        self.writer = RPF6Writer()
        self.mod_metadata = {
            'mod_name': 'Unnamed_Mod',
            'author': 'Unknown',
            'version': '1.0.0',
            'description': 'RDR1 PC Modification',
            'game_version': '1491.50' # RDR1 PC version
        }
   
    def set_mod_metadata(self, name: str, author: str = "", version: str = "1.0.0", description: str = ""):
        """Set mod metadata"""
        self.mod_metadata = {
            'mod_name': name,
            'author': author,
            'version': version,
            'description': description,
            'game_version': '1491.50',
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
   
    def create_mod_structure(self, mod_type: str = "generic"):
        """Create standard directory structure for different mod types"""
        base_dirs = [
            "textures/",
            "models/",
            "audio/",
            "scripts/",
            "data/",
            "ui/",
            "maps/"
        ]
       
        # Type-specific structures
        structures = {
            "texture": ["textures/characters/", "textures/weapons/", "textures/environments/"],
            "model": ["models/characters/", "models/vehicles/", "models/weapons/"],
            "script": ["scripts/", "data/config/"],
            "audio": ["audio/music/", "audio/sfx/", "audio/voices/"],
            "ui": ["ui/textures/", "ui/menus/", "ui/hud/"],
            "map": ["maps/", "data/placement/", "data/zones/"]
        }
       
        # Add base directories
        for directory in base_dirs:
            self.writer.add_directory(directory)
       
        # Add type-specific directories
        if mod_type in structures:
            for directory in structures[mod_type]:
                self.writer.add_directory(directory)
       
        # Add mod info file
        mod_info = json.dumps(self.mod_metadata, indent=2)
        self.writer.add_file_data(mod_info.encode('utf-8'), "mod_info.json")
       
        logger.info(f"Created mod structure for {mod_type} mod: {self.mod_metadata['mod_name']}")
   
    def create_mod_archive(self, output_path: str, include_readme: bool = True) -> bool:
        """Create a complete mod archive with all standard components"""
       
        # Add readme file if requested
        if include_readme:
            readme_content = self._generate_readme()
            self.writer.add_file_data(readme_content.encode('utf-8'), "README.txt")
       
        # Build the archive
        success = self.writer.write_archive(output_path)
       
        if success:
            logger.info(f"Mod archive created successfully: {output_path}")
            self._log_mod_summary()
       
        return success
   
    def _generate_readme(self) -> str:
        """Generate a mod readme file"""
        return f"""RDR1 PC Mod: {self.mod_metadata['mod_name']}
Version: {self.mod_metadata['version']}
Author: {self.mod_metadata['author']}
Description: {self.mod_metadata['description']}

Created with RDR1 RPF Wrangler Tool
Creation Date: {self.mod_metadata['created_date']}

INSTALLATION:
1. Backup your original RPF files
2. Replace the corresponding RPF file with this one
3. Launch Red Dead Redemption PC

NOTE: Use at your own risk. Always backup original files.
"""

    def _log_mod_summary(self):
        """Log mod creation summary"""
        info = self.writer.get_archive_info()
        logger.info(f"Mod '{self.mod_metadata['mod_name']}' created successfully!")
        logger.info(f" - Files: {info['file_entries']}")
        logger.info(f" - Directories: {info['directories']}")
        logger.info(f" - Estimated Size: {info['estimated_archive_size']} bytes")

class AdvancedTextureAnalyzer:
    """Enhanced texture analysis with DDS support"""

    # Texture format mapping
    FORMAT_MAP = {
        0x31545844: "DXT1", # 'DXT1'
        0x33545844: "DXT3", # 'DXT3'
        0x35545844: "DXT5", # 'DXT5'
        0x30315844: "DX10", # 'DX10'
        0x15: "ABR8GBB8",
        0x10: "R8G8B8",
        0x00: "DXT1a"
    }

    @staticmethod
    def analyze_wtd_texture(wtd_data: bytes) -> Dict[str, Any]:
        """Analyze WTD texture file"""
        analysis = {
            'success': False,
            'texture_count': 0,
            'textures': [],
            'platform': 'Unknown',
            'errors': [],
            'warnings': []
        }

        try:
            if len(wtd_data) < 64:
                analysis['errors'].append("WTD file too small (min 64 bytes)")
                return analysis

            # Check magic number
            magic = BigEndianEngine.read_uint32(wtd_data, 0)
            if magic != 0x57444400: # 'WTD\0'
                analysis['errors'].append(f"Invalid WTD magic: 0x{magic:08X}")
                return analysis

            # Parse header
            analysis['platform'] = "PC" if wtd_data[16] == 0x09 else "Console"
            analysis['texture_count'] = BigEndianEngine.read_uint16(wtd_data, 8)
            analysis['total_size'] = BigEndianEngine.read_uint32(wtd_data, 12)

            logger.info(f"WTD Analysis: {analysis['texture_count']} textures, Platform: {analysis['platform']}")

            # Parse texture entries
            texture_entry_offset = 64

            for i in range(analysis['texture_count']):
                if texture_entry_offset + 32 > len(wtd_data):
                    analysis['warnings'].append(f"Incomplete texture entry at index {i}")
                    break

                texture = {
                    'index': i,
                    'name_offset': BigEndianEngine.read_uint32(wtd_data, texture_entry_offset),
                    'width': BigEndianEngine.read_uint16(wtd_data, texture_entry_offset + 4),
                    'height': BigEndianEngine.read_uint16(wtd_data, texture_entry_offset + 6),
                    'format': BigEndianEngine.read_uint32(wtd_data, texture_entry_offset + 8),
                    'data_offset': BigEndianEngine.read_uint32(wtd_data, texture_entry_offset + 12),
                    'data_size': BigEndianEngine.read_uint32(wtd_data, texture_entry_offset + 16)
                }

                # Get texture name and format
                texture['name'] = AdvancedTextureAnalyzer._extract_texture_name(wtd_data, texture['name_offset'])
                texture['format_name'] = AdvancedTextureAnalyzer._get_format_name(texture['format'])
                texture['estimated_vram'] = AdvancedTextureAnalyzer._estimate_vram_usage(
                    texture['width'], texture['height'], texture['format_name']
                )

                analysis['textures'].append(texture)
                texture_entry_offset += 32

            analysis['success'] = True

        except Exception as e:
            analysis['errors'].append(f"Analysis failed: {e}")

        return analysis

    @staticmethod
    def _extract_texture_name(wtd_data: bytes, name_offset: int) -> str:
        """Extract texture name from WTD data"""
        if name_offset >= len(wtd_data):
            return "Unknown"

        name_bytes = bytearray()
        offset = name_offset

        while offset < len(wtd_data) and wtd_data[offset] != 0:
            name_bytes.append(wtd_data[offset])
            offset += 1

        return name_bytes.decode('ascii', errors='replace') if name_bytes else f"Texture_{name_offset}"

    @staticmethod
    def _get_format_name(format_code: int) -> str:
        """Get texture format name from code"""
        return AdvancedTextureAnalyzer.FORMAT_MAP.get(format_code, f"Unknown_0x{format_code:08X}")

    @staticmethod
    def _estimate_vram_usage(width: int, height: int, format_name: str) -> int:
        """Estimate VRAM usage for texture"""
        block_sizes = {
            "DXT1": 8, "DXT3": 16, "DXT5": 16, "DXT1a": 8,
            "ABR8GBB8": 4, "R8G8B8": 3
        }

        block_size = block_sizes.get(format_name, 4)

        if format_name.startswith("DXT"):
            # DXT formats work in 4x4 blocks
            blocks_wide = (width + 3) // 4
            blocks_high = (height + 3) // 4
            return blocks_wide * blocks_high * block_size
        else:
            # Regular formats
            return width * height * block_size

class BatchProcessor:
    """Batch processing engine for multiple files"""

    def __init__(self):
        self.results = []
        self.progress_callback = None

    def set_progress_callback(self, callback):
        """Set progress update callback"""
        self.progress_callback = callback

    def process_directory(self, directory: str, file_pattern: str = "*") -> List[Dict]:
        """Process all files in directory matching pattern"""
        self.results = []
        path = Path(directory)

        files = list(path.rglob(file_pattern))
        total_files = len(files)

        for i, file_path in enumerate(files):
            if self.progress_callback:
                self.progress_callback(i, total_files, f"Processing {file_path.name}")

            try:
                result = self.analyze_file(str(file_path))
                self.results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                self.results.append({
                    'file_path': str(file_path),
                    'error': str(e),
                    'success': False
                })

        return self.results

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze single file"""
        result = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path),
            'analysis_time': datetime.now().isoformat(),
            'success': False
        }

        try:
            # Detect file format
            format_info = self.detect_file_format(file_path)
            result['format'] = format_info

            # Format-specific analysis
            if format_info['detected_format'] == 'RPF6_Archive':
                archive = RPF6Editor(file_path)
                result['archive_info'] = archive.get_archive_info()
                result['entries'] = [{'name': e.name, 'size': e.data_size} for e in archive.entries[:10]] # Sample
                archive.close()

            elif format_info['detected_format'] == 'WTD_TextureDictionary':
                with open(file_path, 'rb') as f:
                    texture_data = f.read()
                    texture_analysis = AdvancedTextureAnalyzer.analyze_wtd_texture(texture_data)
                    result['texture_analysis'] = texture_analysis

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    @staticmethod
    def detect_file_format(file_path: str) -> Dict[str, Any]:
        """Detect file format using magic numbers and extensions"""
        detection = {
            'file_path': file_path,
            'detected_format': 'Unknown',
            'confidence': 0,
            'details': {},
            'recommended_action': 'Manual analysis required'
        }

        try:
            extension = Path(file_path).suffix.lower()

            # Extension-based detection
            extension_map = {
                '.rpf': 'RPF6_Archive',
                '.wtd': 'WTD_TextureDictionary',
                '.wdr': 'WDR_StaticModel',
                '.wft': 'WFT_VehicleModel',
                '.wvd': 'WVD_ModelTextures',
                '.ide': 'IDE_itemDefinitions',
                '.ipl': 'IPL_Placement',
                '.wpl': 'WPL_WorldPlacement',
                '.sc': 'SC_Script',
                '.xml': 'XML_Configuration'
            }

            if extension in extension_map:
                detection['detected_format'] = extension_map[extension]
                detection['confidence'] = 70
                detection['details']['extension_match'] = True

            # Magic number verification
            with open(file_path, 'rb') as f:
                magic_bytes = f.read(4)
                if len(magic_bytes) == 4:
                    magic = struct.unpack('>I', magic_bytes)[0]

                    magic_map = {
                        0x52504636: 'RPF6_Archive', # RPF6
                        0x57444400: 'WTD_TextureDictionary', # WTD
                        0x57445200: 'WDR_Drawable', # WDR
                        0x57465400: 'WFT_Fragment', # WFT
                        0x52534307: 'RSC_Resource' # RSC
                    }

                    if magic in magic_map:
                        detection['detected_format'] = magic_map[magic]
                        detection['confidence'] = 95
                        detection['details']['magic_match'] = True
                        detection['details']['magic_value'] = f"0x{magic:08X}"

            # Set recommended actions
            action_map = {
                'RPF6_Archive': "Use RPF6 editor to explore contents",
                'WTD_TextureDictionary': "Use texture analyzer to extract textures",
                'WDR_StaticModel': "Ready for Blender import (static geometry)",
                'WFT_VehicleModel': "Ready for Blender import (vehicle with hierarchy)",
                'SC_Script': "Use script analyzer for bytecode analysis"
            }

            detection['recommended_action'] = action_map.get(
                detection['detected_format'],
                "Use comprehensive analyzer for detailed analysis"
            )

        except Exception as e:
            detection['details']['error'] = str(e)
            detection['confidence'] = 0

        return detection

class RAGEAnalyzerGUI:
    """Modern GUI for RAGE Evolutionary Analyzer - NOW WITH ARCHIVE CREATION!"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RAGE Evolutionary Analyzer - Python Edition 🤠")
        self.root.geometry("1400x900")

        # Initialize components
        self.batch_processor = BatchProcessor()
        self.current_archive = None
        self.rpf_writer = RPF6Writer() # 🆕 NEW WRITER!
        self.rpf_modifier = None # 🆕 For archive modifications

        self.setup_gui()

    def setup_gui(self):
        """Setup the GUI interface"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # File Analysis Tab
        self.setup_file_analysis_tab(notebook)

        # Batch Processing Tab
        self.setup_batch_processing_tab(notebook)

        # Archive Explorer Tab
        self.setup_archive_explorer_tab(notebook)

        # 🆕 ARCHIVE CREATOR TAB
        self.setup_archive_creator_tab(notebook)

        # 🆕 ARCHIVE MODIFIER TAB
        self.setup_archive_modifier_tab(notebook)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to wrangle them RPF files! 🤠")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief='sunken')
        status_bar.pack(side='bottom', fill='x')

    def setup_file_analysis_tab(self, notebook):
        """Setup file analysis tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="File Analysis")

        # File selection
        ttk.Label(frame, text="Select File:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.file_path_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.file_path_var, width=80).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5, pady=5)

        # Analyze button
        ttk.Button(frame, text="Analyze File", command=self.analyze_single_file).grid(row=1, column=0, columnspan=3, pady=10)

        # Results area
        self.results_text = tk.Text(frame, height=20, width=100)
        scrollbar = ttk.Scrollbar(frame, command=self.results_text.yview)
        self.results_text.config(yscrollcommand=scrollbar.set)
        self.results_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')
        scrollbar.grid(row=2, column=2, sticky='ns', pady=5)

        # Configure grid weights
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def setup_batch_processing_tab(self, notebook):
        """Setup batch processing tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Batch Processing")

        # Directory selection
        ttk.Label(frame, text="Select Directory:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.dir_path_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.dir_path_var, width=80).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_directory).grid(row=0, column=2, padx=5, pady=5)

        # File pattern
        ttk.Label(frame, text="File Pattern:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.pattern_var = tk.StringVar(value='*')
        ttk.Entry(frame, textvariable=self.pattern_var, width=80).grid(row=1, column=1, padx=5, pady=5)

        # Process button
        ttk.Button(frame, text="Start Batch Processing", command=self.start_batch_processing).grid(row=2, column=0, columnspan=3, pady=10)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=3, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

        # Progress label
        self.progress_label = ttk.Label(frame, text="Ready")
        self.progress_label.grid(row=4, column=0, columnspan=3)

        # Results preview
        columns = ('File', 'Format', 'Size', 'Status')
        self.batch_tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            self.batch_tree.heading(col, text=col)
        self.batch_tree.grid(row=5, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

        # Configure grid weights
        frame.grid_rowconfigure(5, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def setup_archive_explorer_tab(self, notebook):
        """Setup archive explorer tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Archive Explorer")

        # Archive selection
        ttk.Label(frame, text="Select RPF6 Archive:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.archive_path_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.archive_path_var, width=80).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_archive).grid(row=0, column=2, padx=5, pady=5)

        # Open archive button
        ttk.Button(frame, text="Open Archive", command=self.open_archive).grid(row=1, column=0, columnspan=3, pady=10)

        # Archive info
        self.archive_info_text = tk.Text(frame, height=5, width=100)
        self.archive_info_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

        # Contents treeview
        columns = ('Name', 'Size', 'Compressed', 'Type')
        self.archive_tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            self.archive_tree.heading(col, text=col)
        self.archive_tree.grid(row=3, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

        # Extract button
        ttk.Button(frame, text="Extract Selected", command=self.extract_selected).grid(row=4, column=0, pady=5)
        ttk.Button(frame, text="Extract All", command=self.extract_all).grid(row=4, column=1, pady=5)

        # Configure grid weights
        frame.grid_rowconfigure(3, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def setup_archive_creator_tab(self, notebook):
        """🆕 Setup archive creation tab - Building new territories!"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🤠 Archive Creator")
       
        # Archive creation section
        ttk.Label(frame, text="🤠 RDR1 RPF Archive Creator", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=3, pady=10)
       
        # Create new archive button
        ttk.Button(frame, text="🆕 Create New Archive", command=self.create_new_archive).grid(row=1, column=0, padx=5, pady=5)
       
        # Add files section
        ttk.Label(frame, text="Add Files:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Button(frame, text="📁 Add Single File", command=self.add_single_file).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(frame, text="📂 Add Directory Tree", command=self.add_directory_tree).grid(row=2, column=2, padx=5, pady=5)
       
        # Archive contents
        ttk.Label(frame, text="Archive Contents:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
       
        # Contents treeview
        columns = ('Name', 'Size', 'Compressed', 'Type')
        self.creator_tree = ttk.Treeview(frame, columns=columns, show='headings', height=12)
        for col in columns:
            self.creator_tree.heading(col, text=col)
        self.creator_tree.grid(row=4, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)
       
        # Entry management
        ttk.Button(frame, text="🗑️ Remove Selected", command=self.remove_creator_entry).grid(row=5, column=0, padx=5, pady=5)
        ttk.Button(frame, text="🧹 Clear All", command=self.clear_creator_entries).grid(row=5, column=1, padx=5, pady=5)
       
        # Archive info
        self.creator_info_text = tk.Text(frame, height=4, width=80)
        self.creator_info_text.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky='ew')
       
        # Build archive section
        ttk.Label(frame, text="Output Path:").grid(row=7, column=0, sticky='w', padx=5, pady=5)
        self.output_path_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.output_path_var, width=50).grid(row=7, column=1, padx=5, pady=5)
        ttk.Button(frame, text="📁 Browse Output", command=self.browse_output_path).grid(row=7, column=2, padx=5, pady=5)
       
        # Progress bar for building
        self.creator_progress_var = tk.DoubleVar()
        self.creator_progress_bar = ttk.Progressbar(frame, variable=self.creator_progress_var, maximum=100)
        self.creator_progress_bar.grid(row=8, column=0, columnspan=3, sticky='ew', padx=5, pady=5)
       
        self.creator_progress_label = ttk.Label(frame, text="Ready to build")
        self.creator_progress_label.grid(row=9, column=0, columnspan=3)
       
        # Build button
        ttk.Button(frame, text="🏗️ Build Archive", command=self.build_archive).grid(row=10, column=0, columnspan=3, pady=10)
       
        # Configure grid weights
        frame.grid_rowconfigure(4, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def setup_archive_modifier_tab(self, notebook):
        """🆕 Setup archive modification tab - For editing existing archives!"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🔧 Archive Modifier")
       
        # Archive selection for modification
        ttk.Label(frame, text="Select Archive to Modify:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.modify_source_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.modify_source_var, width=80).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Browse", command=self.browse_modify_source).grid(row=0, column=2, padx=5, pady=5)
       
        # Load archive for modification
        ttk.Button(frame, text="📂 Load Archive for Modification", command=self.load_archive_for_modification).grid(row=1, column=0, columnspan=3, pady=10)
       
        # Modification controls
        ttk.Label(frame, text="Modification Actions:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Button(frame, text="📝 Replace File", command=self.modifier_replace_file).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(frame, text="➕ Add File", command=self.modifier_add_file).grid(row=2, column=2, padx=5, pady=5)
       
        # Modification contents
        ttk.Label(frame, text="Modified Archive Contents:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
       
        # Contents treeview
        columns = ('Name', 'Size', 'Status', 'Type')
        self.modifier_tree = ttk.Treeview(frame, columns=columns, show='headings', height=12)
        for col in columns:
            self.modifier_tree.heading(col, text=col)
        self.modifier_tree.grid(row=4, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)
       
        # Modification info
        self.modifier_info_text = tk.Text(frame, height=4, width=80)
        self.modifier_info_text.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky='ew')
       
        # Build modified archive section
        ttk.Label(frame, text="Modified Output Path:").grid(row=6, column=0, sticky='w', padx=5, pady=5)
        self.modify_output_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.modify_output_var, width=50).grid(row=6, column=1, padx=5, pady=5)
        ttk.Button(frame, text="📁 Browse Output", command=self.browse_modify_output).grid(row=6, column=2, padx=5, pady=5)
       
        # Progress bar for building modified archive
        self.modifier_progress_var = tk.DoubleVar()
        self.modifier_progress_bar = ttk.Progressbar(frame, variable=self.modifier_progress_var, maximum=100)
        self.modifier_progress_bar.grid(row=7, column=0, columnspan=3, sticky='ew', padx=5, pady=5)
       
        self.modifier_progress_label = ttk.Label(frame, text="Ready to build modified archive")
        self.modifier_progress_label.grid(row=8, column=0, columnspan=3)
       
        # Build modified archive button
        ttk.Button(frame, text="🔨 Build Modified Archive", command=self.build_modified_archive).grid(row=9, column=0, columnspan=3, pady=10)
       
        # Configure grid weights
        frame.grid_rowconfigure(4, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    # =========================================================================
    # EXISTING GUI METHODS
    # =========================================================================

    def browse_file(self):
        """Browse for single file"""
        file_path = filedialog.askopenfilename(
            title="Select RDR1 File",
            filetypes=[
                ("All RDR1 Files", "*.rpf *.wtd *.wdr *.wft *.wvd *.ide *.ipl *.wpl *.sc *.xml"),
                ("RPF6 Archives", "*.rpf"),
                ("Texture Files", "*.wtd *.wvd"),
                ("Model Files", "*.wdr *.wft"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)

    def browse_directory(self):
        """Browse for directory"""
        dir_path = filedialog.askdirectory(title="Select Directory for Batch Processing")
        if dir_path:
            self.dir_path_var.set(dir_path)

    def browse_archive(self):
        """Browse for RPF6 archive"""
        file_path = filedialog.askopenfilename(
            title="Select RPF6 Archive",
            filetypes=[("RPF6 Archives", "*.rpf"), ("All Files", "*.*")]
        )
        if file_path:
            self.archive_path_var.set(file_path)

    def analyze_single_file(self):
        """Analyze single file"""
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "Please select a valid file")
            return

        def analyze_thread():
            self.status_var.set("Analyzing file...")
            try:
                result = self.batch_processor.analyze_file(file_path)
                self.display_analysis_result(result)
                self.status_var.set("Analysis complete")
            except Exception as e:
                self.status_var.set(f"Analysis failed: {e}")
                messagebox.showerror("Error", f"Analysis failed: {e}")

        threading.Thread(target=analyze_thread, daemon=True).start()

    def display_analysis_result(self, result: Dict):
        """Display analysis results in GUI"""
        self.results_text.delete(1.0, tk.END)

        if result.get('success', False):
            self.results_text.insert(tk.END, f"=== FILE ANALYSIS REPORT ===\n\n")
            self.results_text.insert(tk.END, f"File: {result['file_name']}\n")
            self.results_text.insert(tk.END, f"Size: {result['file_size']} bytes\n")
            self.results_text.insert(tk.END, f"Format: {result['format']['detected_format']} "
                                           f"(Confidence: {result['format']['confidence']}%)\n")
            self.results_text.insert(tk.END, f"Recommended: {result['format']['recommended_action']}\n\n")

            if 'archive_info' in result:
                self.results_text.insert(tk.END, "=== ARCHIVE INFO ===\n")
                for key, value in result['archive_info'].items():
                    self.results_text.insert(tk.END, f"  {key}: {value}\n")

            if 'texture_analysis' in result:
                tex_analysis = result['texture_analysis']
                self.results_text.insert(tk.END, f"\n=== TEXTURE ANALYSIS ===\n")
                self.results_text.insert(tk.END, f"Textures: {tex_analysis['texture_count']}\n")
                self.results_text.insert(tk.END, f"Platform: {tex_analysis['platform']}\n")

                for texture in tex_analysis['textures'][:5]: # Show first 5
                    self.results_text.insert(tk.END, f"\n  {texture['name']}: "
                                                   f"{texture['width']}x{texture['height']} "
                                                   f"[{texture['format_name']}]\n")
        else:
            self.results_text.insert(tk.END, f"Analysis failed: {result.get('error', 'Unknown error')}")

    def start_batch_processing(self):
        """Start batch processing"""
        dir_path = self.dir_path_var.get()
        if not dir_path or not os.path.exists(dir_path):
            messagebox.showerror("Error", "Please select a valid directory")
            return

        pattern = self.pattern_var.get()

        def progress_callback(current, total, message):
            progress = (current / total) * 100
            self.progress_var.set(progress)
            self.progress_label.config(text=message)
            self.root.update_idletasks()

        def batch_thread():
            self.batch_tree.delete(*self.batch_tree.get_children())
            self.batch_processor.set_progress_callback(progress_callback)

            try:
                results = self.batch_processor.process_directory(dir_path, pattern)

                for result in results:
                    status = "Success" if result.get('success', False) else "Failed"
                    format_name = result.get('format', {}).get('detected_format', 'Unknown')

                    self.batch_tree.insert("", 'end', values=(
                        result['file_name'],
                        format_name,
                        result['file_size'],
                        status
                    ))

                self.progress_label.config(text=f"Batch processing complete: {len(results)} files processed")
                self.status_var.set("Batch processing complete")

            except Exception as e:
                self.status_var.set(f"Batch processing failed: {e}")
                messagebox.showerror("Error", f"Batch processing failed: {e}")

        threading.Thread(target=batch_thread, daemon=True).start()

    def open_archive(self):
        """Open RPF6 archive for exploration"""
        archive_path = self.archive_path_var.get()
        if not archive_path or not os.path.exists(archive_path):
            messagebox.showerror("Error", "Please select a valid RPF6 archive")
            return

        try:
            if self.current_archive:
                self.current_archive.close()

            self.current_archive = RPF6Editor(archive_path)
            info = self.current_archive.get_archive_info()

            # Display archive info
            self.archive_info_text.delete(1.0, tk.END)
            self.archive_info_text.insert(tk.END, f"== ARCHIVE INFORMATION ==\n\n")
            for key, value in info.items():
                self.archive_info_text.insert(tk.END, f"{key}: {value}\n")

            # Populate contents tree
            self.archive_tree.delete(*self.archive_tree.get_children())
            for entry in self.current_archive.entries:
                entry_type = "Directory" if entry.is_directory else "File"
                compressed = "Yes" if entry.is_compressed else "No"

                self.archive_tree.insert("", 'end', values=(
                    entry.name,
                    entry.data_size,
                    compressed,
                    entry_type
                ))

            self.status_var.set(f"Archive opened: {len(self.current_archive.entries)} entries")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open archive: {e}")
            self.status_var.set(f"Failed to open archive: {e}")

    def extract_selected(self):
        """Extract selected files from archive"""
        if not self.current_archive:
            messagebox.showerror("Error", "No archive open")
            return

        selection = self.archive_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select files to extract")
            return

        extract_dir = filedialog.askdirectory(title="Select extraction directory")
        if not extract_dir:
            return

        def extract_thread():
            for item in selection:
                values = self.archive_tree.item(item)['values']
                file_name = values[0]

                if values[3] == "File": # Only extract files, not directories
                    try:
                        file_data = self.current_archive.extract_file(file_name)
                        extract_path = os.path.join(extract_dir, file_name)

                        # Create directories if needed
                        os.makedirs(os.path.dirname(extract_path), exist_ok=True)

                        with open(extract_path, 'wb') as f:
                            f.write(file_data)

                        logger.info(f"Extracted: {file_name} -> {extract_path}")

                    except Exception as e:
                        logger.error(f"Failed to extract {file_name}: {e}")

            self.status_var.set("Extraction complete")
            messagebox.showinfo("Success", "Selected files extracted successfully")

        threading.Thread(target=extract_thread, daemon=True).start()

    def extract_all(self):
        """Extract all files from archive"""
        if not self.current_archive:
            messagebox.showerror("Error", "No archive open")
            return

        extract_dir = filedialog.askdirectory(title="Select extraction directory")
        if not extract_dir:
            return

        def extract_thread():
            for entry in self.current_archive.entries:
                if not entry.is_directory: # Only extract files
                    try:
                        file_data = self.current_archive.extract_file(entry.name)
                        extract_path = os.path.join(extract_dir, entry.name)

                        # Create directories if needed
                        os.makedirs(os.path.dirname(extract_path), exist_ok=True)

                        with open(extract_path, 'wb') as f:
                            f.write(file_data)

                    except Exception as e:
                        logger.error(f"Failed to extract {entry.name}: {e}")

            self.status_var.set("Extraction complete")
            messagebox.showinfo("Success", "All files extracted successfully")

        threading.Thread(target=extract_thread, daemon=True).start()

    # =========================================================================
    # 🆕 NEW ARCHIVE CREATOR METHODS
    # =========================================================================

    def create_new_archive(self):
        """Create a new empty archive"""
        self.rpf_writer.create_new_archive()
        self.update_creator_display()
        self.status_var.set("New archive created - ready to add files! 🤠")

    def add_single_file(self):
        """Add a single file to the archive"""
        files = filedialog.askopenfilenames(title="Select files to add to archive")
        for file_path in files:
            archive_path = os.path.basename(file_path)
            # Ask about compression for this file
            compress = messagebox.askyesno("Compression", f"Compress '{archive_path}'?")
            self.rpf_writer.add_file(file_path, archive_path, compress=compress)
           
        self.update_creator_display()

    def add_directory_tree(self):
        """Add a directory tree to the archive"""
        dir_path = filedialog.askdirectory(title="Select directory to add recursively")
        if dir_path:
            archive_base = filedialog.askstring("Base Path", "Enter base path in archive (optional):")
            self.rpf_writer.add_directory_recursive(dir_path, archive_base)
            self.update_creator_display()

    def remove_creator_entry(self):
        """Remove selected entry from creator"""
        selection = self.creator_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select an entry to remove")
            return
       
        for item in selection:
            values = self.creator_tree.item(item)['values']
            entry_name = values[0]
            self.rpf_writer.remove_entry(entry_name)
       
        self.update_creator_display()

    def clear_creator_entries(self):
        """Clear all entries from creator"""
        if messagebox.askyesno("Confirm", "Clear all entries from archive?"):
            self.rpf_writer.entries.clear()
            self.update_creator_display()

    def browse_output_path(self):
        """Browse for output path"""
        output_path = filedialog.asksaveasfilename(
            title="Save RPF Archive As",
            defaultextension=".rpf",
            filetypes=[("RPF6 Archives", "*.rpf"), ("All Files", "*.*")]
        )
        if output_path:
            self.output_path_var.set(output_path)

    def build_archive(self):
        """Build the final archive"""
        output_path = self.output_path_var.get()
        if not output_path:
            messagebox.showerror("Error", "Please select an output path")
            return

        if len(self.rpf_writer.entries) == 0:
            messagebox.showerror("Error", "No files added to archive")
            return

        def progress_callback(progress, message):
            self.creator_progress_var.set(progress)
            self.creator_progress_label.config(text=message)
            self.root.update_idletasks()

        def build_thread():
            try:
                success = self.rpf_writer.write_archive(output_path, progress_callback)
                if success:
                    self.status_var.set(f"Archive built successfully: {output_path} 🤠")
                    messagebox.showinfo("Success", f"Archive built successfully!\n\n{output_path}")
                else:
                    self.status_var.set("Archive build failed")
                    messagebox.showerror("Error", "Failed to build archive")
            except Exception as e:
                self.status_var.set(f"Build error: {e}")
                messagebox.showerror("Error", f"Build failed: {e}")

        threading.Thread(target=build_thread, daemon=True).start()

    def update_creator_display(self):
        """Update the creator tab display"""
        # Clear tree
        self.creator_tree.delete(*self.creator_tree.get_children())
       
        # Add entries
        for entry in self.rpf_writer.list_entries():
            comp_flag = "Yes" if entry['is_compressed'] else "No"
            entry_type = "Directory" if entry['is_directory'] else "File"
            size = entry['size'] if not entry['is_directory'] else 0
           
            self.creator_tree.insert("", 'end', values=(
                entry['name'],
                size,
                comp_flag,
                entry_type
            ))
       
        # Update info
        info = self.rpf_writer.get_archive_info()
        self.creator_info_text.delete(1.0, tk.END)
        self.creator_info_text.insert(tk.END, "=== ARCHIVE INFO ===\n\n")
        for key, value in info.items():
            self.creator_info_text.insert(tk.END, f"{key}: {value}\n")

    # =========================================================================
    # 🆕 NEW ARCHIVE MODIFIER METHODS
    # =========================================================================

    def browse_modify_source(self):
        """Browse for source archive to modify"""
        file_path = filedialog.askopenfilename(
            title="Select RPF6 Archive to Modify",
            filetypes=[("RPF6 Archives", "*.rpf"), ("All Files", "*.*")]
        )
        if file_path:
            self.modify_source_var.set(file_path)

    def browse_modify_output(self):
        """Browse for modified archive output path"""
        output_path = filedialog.asksaveasfilename(
            title="Save Modified RPF Archive As",
            defaultextension=".rpf",
            filetypes=[("RPF6 Archives", "*.rpf"), ("All Files", "*.*")]
        )
        if output_path:
            self.modify_output_var.set(output_path)

    def load_archive_for_modification(self):
        """Load an existing archive for modification"""
        source_path = self.modify_source_var.get()
        if not source_path or not os.path.exists(source_path):
            messagebox.showerror("Error", "Please select a valid source archive")
            return

        try:
            self.rpf_modifier = RPF6Modifier(source_path)
            self.update_modifier_display()
            self.status_var.set(f"Archive loaded for modification: {len(self.rpf_modifier.entries)} entries")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load archive for modification: {e}")

    def modifier_replace_file(self):
        """Replace a file in the modified archive"""
        if not self.rpf_modifier:
            messagebox.showerror("Error", "No archive loaded for modification")
            return

        # Select file to replace
        selection = self.modifier_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a file to replace")
            return

        file_to_replace = self.modifier_tree.item(selection[0])['values'][0]
       
        # Select replacement file
        new_file = filedialog.askopenfilename(title=f"Select replacement for {file_to_replace}")
        if new_file:
            success = self.rpf_modifier.replace_file(file_to_replace, new_file)
            if success:
                self.update_modifier_display()
                self.status_var.set(f"Replaced file: {file_to_replace}")
            else:
                messagebox.showerror("Error", f"Failed to replace {file_to_replace}")

    def modifier_add_file(self):
        """Add a file to the modified archive"""
        if not self.rpf_modifier:
            messagebox.showerror("Error", "No archive loaded for modification")
            return

        files = filedialog.askopenfilenames(title="Select files to add to modified archive")
        for file_path in files:
            archive_path = os.path.basename(file_path)
            compress = messagebox.askyesno("Compression", f"Compress '{archive_path}'?")
            self.rpf_modifier.add_file(file_path, archive_path, compress=compress)
       
        self.update_modifier_display()

    def build_modified_archive(self):
        """Build the modified archive"""
        if not self.rpf_modifier:
            messagebox.showerror("Error", "No archive loaded for modification")
            return

        output_path = self.modify_output_var.get()
        if not output_path:
            messagebox.showerror("Error", "Please select an output path")
            return

        def progress_callback(progress, message):
            self.modifier_progress_var.set(progress)
            self.modifier_progress_label.config(text=message)
            self.root.update_idletasks()

        def build_thread():
            try:
                success = self.rpf_modifier.write_archive(output_path, progress_callback)
                if success:
                    summary = self.rpf_modifier.get_modification_summary()
                    self.status_var.set(f"Modified archive built: {output_path}")
                   
                    # Show modification summary
                    summary_text = f"Modifications Summary:\n"
                    summary_text += f"• Original files: {summary['original_files']}\n"
                    summary_text += f"• Added files: {summary['added_files']}\n"
                    summary_text += f"• Modified files: {summary['modified_files']}\n"
                    summary_text += f"• Removed files: {summary['removed_files']}\n"
                   
                    messagebox.showinfo("Success", f"Modified archive built successfully!\n\n{output_path}\n\n{summary_text}")
                else:
                    self.status_var.set("Modified archive build failed")
                    messagebox.showerror("Error", "Failed to build modified archive")
            except Exception as e:
                self.status_var.set(f"Build error: {e}")
                messagebox.showerror("Error", f"Build failed: {e}")

        threading.Thread(target=build_thread, daemon=True).start()

    def update_modifier_display(self):
        """Update the modifier tab display"""
        if not self.rpf_modifier:
            return

        # Clear tree
        self.modifier_tree.delete(*self.modifier_tree.get_children())
       
        # Add entries with status indicators
        for entry in self.rpf_modifier.list_entries():
            status = "Original"
            if hasattr(entry, '_from_original') and not entry['_from_original']:
                status = "Added"
            elif entry['name'] in self.rpf_modifier.modified_entries:
                status = "Modified"
           
            entry_type = "Directory" if entry['is_directory'] else "File"
            size = entry['size'] if not entry['is_directory'] else 0
           
            self.modifier_tree.insert("", 'end', values=(
                entry['name'],
                size,
                status,
                entry_type
            ))
       
        # Update info
        if hasattr(self.rpf_modifier, 'get_modification_summary'):
            summary = self.rpf_modifier.get_modification_summary()
            info = self.rpf_modifier.get_archive_info()
           
            self.modifier_info_text.delete(1.0, tk.END)
            self.modifier_info_text.insert(tk.END, "=== MODIFICATION SUMMARY ===\n\n")
            self.modifier_info_text.insert(tk.END, f"Original files: {summary['original_files']}\n")
            self.modifier_info_text.insert(tk.END, f"Current files: {summary['current_files']}\n")
            self.modifier_info_text.insert(tk.END, f"Added files: {summary['added_files']}\n")
            self.modifier_info_text.insert(tk.END, f"Modified files: {summary['modified_files']}\n")
            self.modifier_info_text.insert(tk.END, f"Removed files: {summary['removed_files']}\n\n")
           
            self.modifier_info_text.insert(tk.END, "=== ARCHIVE INFO ===\n")
            for key, value in info.items():
                self.modifier_info_text.insert(tk.END, f"{key}: {value}\n")

    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    print("🤠 RAGE Evolutionary Analyzer - Python Edition")
    print("Enhanced with GUI, batch processing, AND archive creation!")
    print("Now with 100% more wranglin' power! 🐎")
    print("=" * 60)

    # Check for optional dependencies
    if not HAS_NUMPY:
        print("⚠️ numpy not installed - some advanced features disabled")
    if not HAS_PIL:
        print("⚠️ PIL/Pillow not installed - texture preview disabled")

    # Launch GUI
    app = RAGEAnalyzerGUI()
    app.run()

# =============================================================================
# DEMONSTRATION AND TESTING FUNCTIONS
# =============================================================================

def demonstrate_rpf_writer():
    """Demonstrate the RPF writer capabilities - Showin' off our new gear!"""
    print("🤠 RDR1 RPF Writer Demonstration - Taming the Wild West of File Formats!")
    print("=" * 70)
   
    writer = RPF6Writer()
   
    # Create a new archive
    writer.create_new_archive()
   
    # Add some directories
    writer.add_directory("textures/")
    writer.add_directory("models/")
    writer.add_directory("audio/")
   
    # Create some dummy files to add
    test_files = {
        "textures/character.dds": b"FAKE_DDS_TEXTURE_DATA" * 100,
        "models/sheriff.wdr": b"FAKE_MODEL_DATA" * 200,
        "audio/revolver.wav": b"FAKE_AUDIO_DATA" * 50,
        "readme.txt": b"This archive was created by the RDR1 RPF Wrangler!"
    }
   
    # Add files with mixed compression
    for name, data in test_files.items():
        compress = name.endswith(('.dds', '.wdr')) # Compress textures and models
        writer.add_file_data(data, name, compress=compress)
   
    # Show archive info
    info = writer.get_archive_info()
    print("\n📊 Archive Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")
   
    # List entries
    print(f"\n📁 Archive Contents ({len(writer.entries)} entries):")
    for entry in writer.list_entries():
        comp_flag = " [C]" if entry['is_compressed'] else ""
        dir_flag = " [D]" if entry['is_directory'] else ""
        print(f"  {entry['name']}{comp_flag}{dir_flag} - {entry['size']} bytes")
   
    # Write test archive
    test_output = "test_archive.rpf"
    success = writer.write_archive(test_output)
   
    if success:
        file_size = os.path.getsize(test_output)
        print(f"\n✅ Successfully created test archive: {test_output} ({file_size} bytes)")
        print("🤠 Saddle up! We're ready to wrangle some RPF files!")
    else:
        print(f"\n❌ Failed to create test archive")
   
    return success

def demonstrate_mod_builder():
    """Demonstrate the mod builder capabilities"""
    print("\n🛠️ RDR1 Mod Builder Demonstration")
    print("=" * 50)
   
    builder = RDR1ModBuilder()
    builder.set_mod_metadata(
        name="Test Mod Pack",
        author="RDR1 Wrangler",
        version="1.0.0",
        description="A test mod for Red Dead Redemption PC"
    )
   
    # Create a texture mod structure
    builder.create_mod_structure("texture")
   
    # Show what we built
    info = builder.writer.get_archive_info()
    print(f"📦 Mod Archive Info:")
    print(f"  Files: {info['file_entries']}")
    print(f"  Directories: {info['directories']}")
    print(f"  Estimated Size: {info['estimated_archive_size']} bytes")
   
    # List the structure
    print(f"\n📁 Mod Structure:")
    for entry in builder.writer.list_entries():
        if entry['is_directory']:
            print(f"  📁 {entry['name']}")
        else:
            print(f"  📄 {entry['name']}")
   
    # Create the mod archive
    test_output = "test_mod.rpf"
    success = builder.create_mod_archive(test_output)
   
    if success:
        print(f"\n✅ Successfully created mod archive: {test_output}")
        print("🎮 Ready for RDR1 PC modding!")
    else:
        print(f"\n❌ Failed to create mod archive")
   
    return success

def demonstrate_archive_modification():
    """Demonstrate modifying an existing archive"""
    print("\n🔧 Archive Modification Demonstration")
    print("=" * 50)
   
    # First create a test archive to modify
    writer = RPF6Writer()
    writer.create_new_archive()
   
    # Add some test files
    test_files = {
        "original_texture.dds": b"ORIGINAL_TEXTURE_DATA",
        "original_model.wdr": b"ORIGINAL_MODEL_DATA",
        "config.xml": b"<config>original</config>"
    }
   
    for name, data in test_files.items():
        writer.add_file_data(data, name, compress=True)
   
    # Create the original archive
    original_path = "original_archive.rpf"
    writer.write_archive(original_path)
    print(f"📁 Created original archive: {original_path}")
   
    # Now modify it
    modifier = RPF6Modifier(original_path)
   
    # Replace a file
    new_texture_data = b"MODIFIED_TEXTURE_DATA_NEW_VERSION"
    modifier.replace_file_data("original_texture.dds", new_texture_data)
   
    # Add a new file
    modifier.add_file_data(b"BRAND_NEW_FILE_CONTENT", "new_file.txt")
   
    # Show modification summary
    summary = modifier.get_modification_summary()
    print(f"\n📊 Modification Summary:")
    print(f"  Original files: {summary['original_files']}")
    print(f"  Added files: {summary['added_files']}")
    print(f"  Modified files: {summary['modified_files']}")
    print(f"  Removed files: {summary['removed_files']}")
   
    # Create modified archive
    modified_path = "modified_archive.rpf"
    success = modifier.write_archive(modified_path)
   
    if success:
        print(f"\n✅ Successfully created modified archive: {modified_path}")
        print("🔄 Archive modification complete!")
       
        # Clean up test files
        try:
            os.remove(original_path)
            os.remove(modified_path)
            print("🧹 Cleaned up test files")
        except:
            pass
    else:
        print(f"\n❌ Failed to create modified archive")
   
    return success

if __name__ == "__main__":
    # Check if we should run demonstrations
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("🚀 Running RDR1 RPF Toolkit Demonstrations...")
       
        # Run demonstrations
        demo1 = demonstrate_rpf_writer()
        demo2 = demonstrate_mod_builder()
        demo3 = demonstrate_archive_modification()
       
        print(f"\n🎯 Demonstration Results:")
        print(f"  RPF Writer: {'✅' if demo1 else '❌'}")
        print(f"  Mod Builder: {'✅' if demo2 else '❌'}")
        print(f"  Archive Modifier: {'✅' if demo3 else '❌'}")
       
        if demo1 and demo2 and demo3:
            print("\n🎉 All demonstrations completed successfully!")
            print("🤠 Your RDR1 RPF toolkit is ready for action!")
        else:
            print("\n⚠️ Some demonstrations failed. Check the logs for details.")
    else:
        # Run the main GUI application
        main()