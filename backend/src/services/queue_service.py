"""
Smart playback queue management.

Features:
- Auto-queue similar songs
- Shuffle with variety constraints
- Queue history
- Skip behavior learning
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import random
import sqlite3
import logging

from backend.src.services.constants import TABLE_SONGS

logger = logging.getLogger(__name__)


class RepeatMode(str, Enum):
    OFF = "off"
    ONE = "one"
    ALL = "all"


class ShuffleMode(str, Enum):
    OFF = "off"
    ON = "on"
    SMART = "smart"  # Weighted shuffle based on preferences


@dataclass
class QueueItem:
    """Item in playback queue."""
    song_id: int
    song: Dict[str, Any]
    added_at: datetime = field(default_factory=datetime.now)
    added_by: str = "user"  # user, auto, recommendation
    position: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "song_id": self.song_id,
            "song": self.song,
            "added_at": self.added_at.isoformat(),
            "added_by": self.added_by,
            "position": self.position
        }


@dataclass
class PlaybackState:
    """Current playback state."""
    current_song: Optional[Dict] = None
    position_ms: int = 0
    is_playing: bool = False
    repeat_mode: RepeatMode = RepeatMode.OFF
    shuffle_mode: ShuffleMode = ShuffleMode.OFF
    volume: int = 100


class SmartQueue:
    """
    Intelligent music queue with auto-suggestions.
    
    Features:
    - Maintains current queue
    - Auto-fills when queue runs low
    - Learns from skip behavior
    - Smart shuffle with variety
    """
    
    def __init__(self, db_path: str, user_id: Optional[int] = None):
        self.db_path = db_path
        self.user_id = user_id
        
        self._queue: Deque[QueueItem] = deque()
        self._history: Deque[QueueItem] = deque(maxlen=100)
        self._current: Optional[QueueItem] = None
        
        self._state = PlaybackState()
        self._skip_count: Dict[int, int] = {}  # song_id -> skip count
        self._play_count: Dict[int, int] = {}  # song_id -> play count
        
        # Auto-queue settings
        self.auto_queue_enabled = True
        self.auto_queue_threshold = 3  # Add more when queue has < N songs
        self.auto_queue_count = 5  # Number to add
        
        # Variety settings for smart shuffle
        self.variety_artist_distance = 3  # Min songs between same artist
        self.variety_mood_window = 5  # Check mood variety in last N songs
    
    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con
    
    def _get_song(self, song_id: int) -> Optional[Dict]:
        """Get song by ID."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                f"SELECT * FROM {TABLE_SONGS} WHERE song_id = ?",
                (song_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None
    
    # ==================== QUEUE MANAGEMENT ====================
    
    def add_to_queue(
        self,
        song_id: int,
        position: int = -1,
        added_by: str = "user"
    ) -> Optional[QueueItem]:
        """Add song to queue."""
        song = self._get_song(song_id)
        if not song:
            return None
        
        item = QueueItem(
            song_id=song_id,
            song=song,
            added_by=added_by,
            position=len(self._queue) if position < 0 else position
        )
        
        if position < 0 or position >= len(self._queue):
            self._queue.append(item)
        else:
            self._queue.insert(position, item)
        
        self._update_positions()
        return item
    
    def add_songs_to_queue(
        self,
        song_ids: List[int],
        added_by: str = "user"
    ) -> List[QueueItem]:
        """Add multiple songs to queue."""
        items = []
        for song_id in song_ids:
            item = self.add_to_queue(song_id, added_by=added_by)
            if item:
                items.append(item)
        return items
    
    def remove_from_queue(self, position: int) -> Optional[QueueItem]:
        """Remove song at position."""
        if 0 <= position < len(self._queue):
            item = self._queue[position]
            del self._queue[position]
            self._update_positions()
            return item
        return None
    
    def clear_queue(self) -> int:
        """Clear queue. Returns count of removed items."""
        count = len(self._queue)
        self._queue.clear()
        return count
    
    def move_in_queue(self, from_pos: int, to_pos: int) -> bool:
        """Move item in queue."""
        if not (0 <= from_pos < len(self._queue) and 0 <= to_pos < len(self._queue)):
            return False
        
        item = self._queue[from_pos]
        del self._queue[from_pos]
        self._queue.insert(to_pos, item)
        self._update_positions()
        return True
    
    def _update_positions(self) -> None:
        """Update position field of all items."""
        for i, item in enumerate(self._queue):
            item.position = i
    
    def get_queue(self) -> List[Dict]:
        """Get current queue."""
        return [item.to_dict() for item in self._queue]
    
    def get_queue_length(self) -> int:
        """Get queue length."""
        return len(self._queue)
    
    # ==================== PLAYBACK CONTROL ====================
    
    def play(self) -> Optional[Dict]:
        """Start/resume playback."""
        self._state.is_playing = True
        
        if self._current is None and self._queue:
            return self.next()
        
        return self._current.song if self._current else None
    
    def pause(self) -> None:
        """Pause playback."""
        self._state.is_playing = False
    
    def next(self) -> Optional[Dict]:
        """Skip to next song."""
        # Record skip if currently playing
        if self._current:
            self._record_skip(self._current.song_id)
            self._history.append(self._current)
        
        # Get next song
        if self._state.repeat_mode == RepeatMode.ONE and self._current:
            # Repeat current song
            return self._current.song
        
        if self._queue:
            if self._state.shuffle_mode == ShuffleMode.SMART:
                self._current = self._get_smart_shuffle_next()
            elif self._state.shuffle_mode == ShuffleMode.ON:
                idx = random.randint(0, len(self._queue) - 1)
                self._current = self._queue[idx]
                del self._queue[idx]
            else:
                self._current = self._queue.popleft()
            
            self._record_play(self._current.song_id)
            self._update_positions()
            
            # Check if auto-queue needed
            if self.auto_queue_enabled and len(self._queue) < self.auto_queue_threshold:
                self._auto_fill_queue()
            
            return self._current.song
        
        # Queue empty - handle repeat all
        if self._state.repeat_mode == RepeatMode.ALL and self._history:
            self._restore_history_to_queue()
            return self.next()
        
        self._current = None
        self._state.is_playing = False
        return None
    
    def previous(self) -> Optional[Dict]:
        """Go to previous song."""
        if self._history:
            if self._current:
                self._queue.appendleft(self._current)
            
            self._current = self._history.pop()
            self._update_positions()
            return self._current.song
        
        return self._current.song if self._current else None
    
    def _record_skip(self, song_id: int) -> None:
        """Record that a song was skipped."""
        self._skip_count[song_id] = self._skip_count.get(song_id, 0) + 1
    
    def _record_play(self, song_id: int) -> None:
        """Record that a song was played."""
        self._play_count[song_id] = self._play_count.get(song_id, 0) + 1
    
    def _restore_history_to_queue(self) -> None:
        """Restore history to queue for repeat all."""
        for item in self._history:
            item.position = len(self._queue)
            self._queue.append(item)
        self._history.clear()
        self._update_positions()
    
    # ==================== SMART FEATURES ====================
    
    def _get_smart_shuffle_next(self) -> QueueItem:
        """Get next song with smart shuffle (variety constraints)."""
        if not self._queue:
            return None
        
        candidates = list(self._queue)
        
        # Get recent artists
        recent_artists = set()
        recent = list(self._history)[-self.variety_artist_distance:]
        for item in recent:
            if item.song.get("artist"):
                recent_artists.add(item.song["artist"])
        
        # Filter out recently played artists
        preferred = [
            c for c in candidates
            if c.song.get("artist") not in recent_artists
        ]
        
        if preferred:
            candidates = preferred
        
        # Weight by inverse skip count
        weights = []
        for c in candidates:
            skip_penalty = 1.0 / (1 + self._skip_count.get(c.song_id, 0))
            play_bonus = 1 + (self._play_count.get(c.song_id, 0) * 0.1)
            weights.append(skip_penalty * play_bonus)
        
        # Weighted random selection
        total = sum(weights)
        r = random.random() * total
        cumsum = 0
        
        for i, w in enumerate(weights):
            cumsum += w
            if r <= cumsum:
                item = candidates[i]
                self._queue.remove(item)
                return item
        
        # Fallback
        item = candidates[-1]
        self._queue.remove(item)
        return item
    
    def _auto_fill_queue(self) -> None:
        """Automatically fill queue with similar songs."""
        if not self._current:
            return
        
        try:
            # Get similar songs
            from backend.src.pipelines.song_similarity import get_similarity_engine
            
            engine = get_similarity_engine(self.db_path)
            current_song = self._current.song
            
            similar = engine.find_similar_songs(
                self._current.song_id,
                limit=self.auto_queue_count * 2
            )
            
            # Filter out already in queue and history
            in_queue = {item.song_id for item in self._queue}
            in_history = {item.song_id for item in self._history}
            skip_ids = in_queue | in_history | {self._current.song_id}
            
            # Also reduce priority for frequently skipped
            candidates = []
            for s in similar:
                if s["song_id"] not in skip_ids:
                    skip_rate = self._skip_count.get(s["song_id"], 0) / max(
                        self._play_count.get(s["song_id"], 1), 1
                    )
                    if skip_rate < 0.5:  # Not skipped too often
                        candidates.append(s)
            
            # Add to queue
            for song in candidates[:self.auto_queue_count]:
                self.add_to_queue(song["song_id"], added_by="auto")
            
            logger.info(f"Auto-filled {len(candidates[:self.auto_queue_count])} songs")
            
        except Exception as e:
            logger.error(f"Auto-fill error: {e}")
    
    # ==================== STATE MANAGEMENT ====================
    
    def set_repeat_mode(self, mode: RepeatMode) -> None:
        """Set repeat mode."""
        self._state.repeat_mode = mode
    
    def set_shuffle_mode(self, mode: ShuffleMode) -> None:
        """Set shuffle mode."""
        self._state.shuffle_mode = mode
    
    def get_state(self) -> Dict[str, Any]:
        """Get current playback state."""
        return {
            "current_song": self._current.song if self._current else None,
            "is_playing": self._state.is_playing,
            "repeat_mode": self._state.repeat_mode.value,
            "shuffle_mode": self._state.shuffle_mode.value,
            "queue_length": len(self._queue),
            "history_length": len(self._history)
        }
    
    def get_history(self) -> List[Dict]:
        """Get playback history."""
        return [item.to_dict() for item in self._history]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            "queue_length": len(self._queue),
            "history_length": len(self._history),
            "total_plays": sum(self._play_count.values()),
            "total_skips": sum(self._skip_count.values()),
            "most_skipped": sorted(
                self._skip_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "most_played": sorted(
                self._play_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "auto_queue_enabled": self.auto_queue_enabled
        }


# ==================== SINGLETON ====================

_queues: Dict[int, SmartQueue] = {}


def get_queue(db_path: str, user_id: int = 0) -> SmartQueue:
    """Get or create queue for user."""
    if user_id not in _queues:
        _queues[user_id] = SmartQueue(db_path, user_id)
    return _queues[user_id]
