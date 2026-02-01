"""
Export and Import service for music data.

Features:
- Export songs to JSON/CSV
- Import songs from files
- Backup/restore database
- Data migration utilities
"""

from __future__ import annotations

import json
import csv
import os
import shutil
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from backend.src.services.constants import TABLE_SONGS

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    file_path: Optional[str] = None
    record_count: int = 0
    format: str = ""
    size_bytes: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ImportResult:
    """Result of an import operation."""
    success: bool
    imported_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DataExportService:
    """
    Service for exporting and importing music data.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.export_dir = os.path.join(
            os.path.dirname(db_path), "exports"
        )
        os.makedirs(self.export_dir, exist_ok=True)
    
    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con
    
    def _get_all_songs(self) -> List[Dict]:
        """Fetch all songs from database."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(f"SELECT * FROM {TABLE_SONGS}")
            return [dict(row) for row in cur.fetchall()]
    
    # ==================== EXPORT FUNCTIONS ====================
    
    def export_to_json(
        self,
        file_path: Optional[str] = None,
        pretty: bool = True,
        include_metadata: bool = True
    ) -> ExportResult:
        """
        Export all songs to JSON file.
        
        Args:
            file_path: Output file path (auto-generated if None)
            pretty: Use pretty formatting
            include_metadata: Include export metadata
        """
        try:
            songs = self._get_all_songs()
            
            if file_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(
                    self.export_dir, f"songs_export_{timestamp}.json"
                )
            
            data = {
                "songs": songs
            }
            
            if include_metadata:
                data["metadata"] = {
                    "export_time": datetime.now().isoformat(),
                    "record_count": len(songs),
                    "version": "1.0"
                }
            
            with open(file_path, "w", encoding="utf-8") as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            size = os.path.getsize(file_path)
            
            return ExportResult(
                success=True,
                file_path=file_path,
                record_count=len(songs),
                format="json",
                size_bytes=size
            )
            
        except Exception as e:
            logger.error(f"Export to JSON failed: {e}")
            return ExportResult(success=False, error=str(e))
    
    def export_to_csv(
        self,
        file_path: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> ExportResult:
        """
        Export songs to CSV file.
        
        Args:
            file_path: Output file path
            columns: Specific columns to export
        """
        try:
            songs = self._get_all_songs()
            
            if not songs:
                return ExportResult(
                    success=True,
                    record_count=0,
                    format="csv"
                )
            
            if file_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(
                    self.export_dir, f"songs_export_{timestamp}.csv"
                )
            
            # Get columns from first song if not specified
            if columns is None:
                columns = list(songs[0].keys())
            
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                
                for song in songs:
                    # Filter to only requested columns
                    row = {k: v for k, v in song.items() if k in columns}
                    writer.writerow(row)
            
            size = os.path.getsize(file_path)
            
            return ExportResult(
                success=True,
                file_path=file_path,
                record_count=len(songs),
                format="csv",
                size_bytes=size
            )
            
        except Exception as e:
            logger.error(f"Export to CSV failed: {e}")
            return ExportResult(success=False, error=str(e))
    
    def export_by_mood(
        self,
        mood: str,
        format: ExportFormat = ExportFormat.JSON
    ) -> ExportResult:
        """Export songs filtered by mood."""
        try:
            with self._connect() as con:
                cur = con.cursor()
                cur.execute(
                    f"SELECT * FROM {TABLE_SONGS} WHERE mood = ?",
                    (mood,)
                )
                songs = [dict(row) for row in cur.fetchall()]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(
                self.export_dir,
                f"songs_{mood}_{timestamp}.{format.value}"
            )
            
            if format == ExportFormat.JSON:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"mood": mood, "songs": songs}, f, indent=2)
            else:
                if songs:
                    columns = list(songs[0].keys())
                    with open(file_path, "w", encoding="utf-8", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=columns)
                        writer.writeheader()
                        writer.writerows(songs)
            
            return ExportResult(
                success=True,
                file_path=file_path,
                record_count=len(songs),
                format=format.value,
                size_bytes=os.path.getsize(file_path)
            )
            
        except Exception as e:
            return ExportResult(success=False, error=str(e))
    
    # ==================== IMPORT FUNCTIONS ====================
    
    def import_from_json(
        self,
        file_path: str,
        update_existing: bool = False,
        validate: bool = True
    ) -> ImportResult:
        """
        Import songs from JSON file.
        
        Args:
            file_path: Path to JSON file
            update_existing: Update existing songs by ID
            validate: Validate data before import
        """
        result = ImportResult(success=False)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Handle both formats
            if isinstance(data, dict) and "songs" in data:
                songs = data["songs"]
            elif isinstance(data, list):
                songs = data
            else:
                result.errors.append("Invalid JSON format")
                return result
            
            return self._import_songs(songs, update_existing, validate)
            
        except json.JSONDecodeError as e:
            result.errors.append(f"JSON parse error: {e}")
            return result
        except FileNotFoundError:
            result.errors.append(f"File not found: {file_path}")
            return result
        except Exception as e:
            result.errors.append(f"Import error: {e}")
            return result
    
    def import_from_csv(
        self,
        file_path: str,
        update_existing: bool = False,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> ImportResult:
        """
        Import songs from CSV file.
        
        Args:
            file_path: Path to CSV file
            update_existing: Update existing songs
            column_mapping: Map CSV columns to database columns
        """
        result = ImportResult(success=False)
        
        try:
            songs = []
            
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Apply column mapping if provided
                    if column_mapping:
                        song = {}
                        for csv_col, db_col in column_mapping.items():
                            if csv_col in row:
                                song[db_col] = row[csv_col]
                    else:
                        song = dict(row)
                    
                    # Convert numeric fields
                    for field in ["song_id", "tempo", "energy", "happiness"]:
                        if field in song and song[field]:
                            try:
                                song[field] = int(song[field])
                            except ValueError:
                                pass
                    
                    songs.append(song)
            
            return self._import_songs(songs, update_existing)
            
        except Exception as e:
            result.errors.append(f"CSV import error: {e}")
            return result
    
    def _import_songs(
        self,
        songs: List[Dict],
        update_existing: bool = False,
        validate: bool = True
    ) -> ImportResult:
        """Internal method to import songs to database."""
        result = ImportResult(success=False)
        
        required_fields = ["song_name"]
        
        with self._connect() as con:
            cur = con.cursor()
            
            for i, song in enumerate(songs):
                try:
                    # Validate required fields
                    if validate:
                        missing = [f for f in required_fields if not song.get(f)]
                        if missing:
                            result.skipped_count += 1
                            result.errors.append(
                                f"Row {i}: Missing fields {missing}"
                            )
                            continue
                    
                    song_id = song.get("song_id")
                    
                    if song_id and update_existing:
                        # Update existing
                        cur.execute(
                            f"SELECT song_id FROM {TABLE_SONGS} WHERE song_id = ?",
                            (song_id,)
                        )
                        
                        if cur.fetchone():
                            # Update
                            cols = [k for k in song.keys() if k != "song_id"]
                            set_clause = ", ".join([f"{c}=?" for c in cols])
                            vals = [song[c] for c in cols] + [song_id]
                            
                            cur.execute(
                                f"UPDATE {TABLE_SONGS} SET {set_clause} WHERE song_id=?",
                                vals
                            )
                            result.imported_count += 1
                            continue
                    
                    # Insert new
                    cols = [k for k in song.keys() if k != "song_id"]
                    placeholders = ", ".join(["?"] * len(cols))
                    col_names = ", ".join(cols)
                    vals = [song[c] for c in cols]
                    
                    cur.execute(
                        f"INSERT INTO {TABLE_SONGS} ({col_names}) VALUES ({placeholders})",
                        vals
                    )
                    result.imported_count += 1
                    
                except Exception as e:
                    result.error_count += 1
                    result.errors.append(f"Row {i}: {e}")
            
            con.commit()
        
        result.success = result.imported_count > 0 or result.skipped_count > 0
        return result
    
    # ==================== BACKUP FUNCTIONS ====================
    
    def create_backup(
        self,
        backup_dir: Optional[str] = None
    ) -> ExportResult:
        """
        Create a database backup.
        
        Args:
            backup_dir: Directory for backup file
        """
        try:
            if backup_dir is None:
                backup_dir = os.path.join(self.export_dir, "backups")
            
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"music_backup_{timestamp}.db")
            
            # Create backup using SQLite backup API
            source = sqlite3.connect(self.db_path)
            dest = sqlite3.connect(backup_path)
            
            source.backup(dest)
            
            source.close()
            dest.close()
            
            size = os.path.getsize(backup_path)
            
            return ExportResult(
                success=True,
                file_path=backup_path,
                format="sqlite",
                size_bytes=size
            )
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return ExportResult(success=False, error=str(e))
    
    def restore_from_backup(
        self,
        backup_path: str
    ) -> ImportResult:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
        """
        result = ImportResult(success=False)
        
        try:
            if not os.path.exists(backup_path):
                result.errors.append(f"Backup file not found: {backup_path}")
                return result
            
            # Create a safety backup first
            self.create_backup()
            
            # Close any existing connections
            source = sqlite3.connect(backup_path)
            dest = sqlite3.connect(self.db_path)
            
            source.backup(dest)
            
            source.close()
            dest.close()
            
            result.success = True
            return result
            
        except Exception as e:
            result.errors.append(f"Restore failed: {e}")
            return result
    
    def list_backups(self) -> List[Dict]:
        """List available backups."""
        backup_dir = os.path.join(self.export_dir, "backups")
        
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for f in os.listdir(backup_dir):
            if f.endswith(".db"):
                path = os.path.join(backup_dir, f)
                stat = os.stat(path)
                backups.append({
                    "filename": f,
                    "path": path,
                    "size_bytes": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)
    
    def list_exports(self) -> List[Dict]:
        """List exported files."""
        exports = []
        
        for f in os.listdir(self.export_dir):
            path = os.path.join(self.export_dir, f)
            if os.path.isfile(path) and (f.endswith(".json") or f.endswith(".csv")):
                stat = os.stat(path)
                exports.append({
                    "filename": f,
                    "path": path,
                    "format": "json" if f.endswith(".json") else "csv",
                    "size_bytes": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return sorted(exports, key=lambda x: x["created"], reverse=True)
