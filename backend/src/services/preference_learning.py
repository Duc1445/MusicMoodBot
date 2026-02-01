"""
User preference learning and personalization service.

Features:
- Learn from user interactions
- Build preference profiles
- Personalized recommendations
- Feedback processing
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter
import sqlite3
import json
import logging
import math

from backend.src.services.constants import TABLE_SONGS

logger = logging.getLogger(__name__)


@dataclass
class UserPreference:
    """User preference profile."""
    user_id: int
    favorite_moods: Dict[str, float] = field(default_factory=dict)
    favorite_genres: Dict[str, float] = field(default_factory=dict)
    favorite_artists: Dict[str, float] = field(default_factory=dict)
    energy_preference: float = 5.0  # 1-10
    tempo_preference: float = 100.0  # BPM
    listening_history: List[int] = field(default_factory=list)
    liked_songs: List[int] = field(default_factory=list)
    disliked_songs: List[int] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class InteractionEvent:
    """User interaction event."""
    user_id: int
    song_id: int
    event_type: str  # play, like, dislike, skip, complete
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: Optional[int] = None
    context: Optional[Dict] = None


class UserPreferenceLearner:
    """
    Learns and manages user preferences from interactions.
    
    Uses collaborative filtering and content-based methods.
    """
    
    # Weights for different interaction types
    INTERACTION_WEIGHTS = {
        "play": 1.0,
        "complete": 2.0,
        "like": 3.0,
        "dislike": -2.0,
        "skip": -0.5,
        "add_to_playlist": 2.5,
        "share": 3.0
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._preferences_cache: Dict[int, UserPreference] = {}
        self._init_tables()
    
    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con
    
    def _init_tables(self) -> None:
        """Initialize preference tables."""
        with self._connect() as con:
            cur = con.cursor()
            
            # User preferences table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY,
                    favorite_moods TEXT,
                    favorite_genres TEXT,
                    favorite_artists TEXT,
                    energy_preference REAL DEFAULT 5.0,
                    tempo_preference REAL DEFAULT 100.0,
                    listening_history TEXT,
                    liked_songs TEXT,
                    disliked_songs TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Interactions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    song_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    duration_seconds INTEGER,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (song_id) REFERENCES songs(song_id)
                )
            """)
            
            # Index for fast lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_user 
                ON user_interactions(user_id, created_at)
            """)
            
            con.commit()
    
    def record_interaction(self, event: InteractionEvent) -> None:
        """Record a user interaction."""
        with self._connect() as con:
            cur = con.cursor()
            
            context_json = json.dumps(event.context) if event.context else None
            
            cur.execute("""
                INSERT INTO user_interactions 
                (user_id, song_id, event_type, duration_seconds, context)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event.user_id,
                event.song_id,
                event.event_type,
                event.duration_seconds,
                context_json
            ))
            
            con.commit()
        
        # Update cached preferences
        self._update_preferences_from_event(event)
    
    def _update_preferences_from_event(self, event: InteractionEvent) -> None:
        """Update preference cache from new event."""
        prefs = self.get_preferences(event.user_id)
        
        # Get song details
        song = self._get_song(event.song_id)
        if not song:
            return
        
        weight = self.INTERACTION_WEIGHTS.get(event.event_type, 1.0)
        
        # Update mood preference
        if song.get("mood"):
            mood = song["mood"]
            current = prefs.favorite_moods.get(mood, 0.0)
            prefs.favorite_moods[mood] = current + weight
        
        # Update genre preference
        if song.get("genre"):
            genre = song["genre"]
            current = prefs.favorite_genres.get(genre, 0.0)
            prefs.favorite_genres[genre] = current + weight
        
        # Update artist preference
        if song.get("artist"):
            artist = song["artist"]
            current = prefs.favorite_artists.get(artist, 0.0)
            prefs.favorite_artists[artist] = current + weight
        
        # Update energy/tempo preferences (moving average)
        if song.get("energy"):
            prefs.energy_preference = (
                prefs.energy_preference * 0.9 + song["energy"] * 0.1
            )
        
        if song.get("tempo"):
            prefs.tempo_preference = (
                prefs.tempo_preference * 0.9 + song["tempo"] * 0.1
            )
        
        # Update history
        if event.event_type == "play":
            prefs.listening_history.append(event.song_id)
            # Keep last 100
            prefs.listening_history = prefs.listening_history[-100:]
        
        if event.event_type == "like":
            if event.song_id not in prefs.liked_songs:
                prefs.liked_songs.append(event.song_id)
            if event.song_id in prefs.disliked_songs:
                prefs.disliked_songs.remove(event.song_id)
        
        if event.event_type == "dislike":
            if event.song_id not in prefs.disliked_songs:
                prefs.disliked_songs.append(event.song_id)
            if event.song_id in prefs.liked_songs:
                prefs.liked_songs.remove(event.song_id)
        
        prefs.last_updated = datetime.now()
        self._preferences_cache[event.user_id] = prefs
        
        # Save to database periodically
        self._save_preferences(prefs)
    
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
    
    def get_preferences(self, user_id: int) -> UserPreference:
        """Get user preferences (from cache or database)."""
        if user_id in self._preferences_cache:
            return self._preferences_cache[user_id]
        
        prefs = self._load_preferences(user_id)
        self._preferences_cache[user_id] = prefs
        return prefs
    
    def _load_preferences(self, user_id: int) -> UserPreference:
        """Load preferences from database."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            row = cur.fetchone()
            
            if row:
                row_dict = dict(row)
                return UserPreference(
                    user_id=user_id,
                    favorite_moods=json.loads(row_dict.get("favorite_moods") or "{}"),
                    favorite_genres=json.loads(row_dict.get("favorite_genres") or "{}"),
                    favorite_artists=json.loads(row_dict.get("favorite_artists") or "{}"),
                    energy_preference=row_dict.get("energy_preference", 5.0),
                    tempo_preference=row_dict.get("tempo_preference", 100.0),
                    listening_history=json.loads(row_dict.get("listening_history") or "[]"),
                    liked_songs=json.loads(row_dict.get("liked_songs") or "[]"),
                    disliked_songs=json.loads(row_dict.get("disliked_songs") or "[]")
                )
            
            return UserPreference(user_id=user_id)
    
    def _save_preferences(self, prefs: UserPreference) -> None:
        """Save preferences to database."""
        with self._connect() as con:
            cur = con.cursor()
            
            cur.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (user_id, favorite_moods, favorite_genres, favorite_artists,
                 energy_preference, tempo_preference, listening_history,
                 liked_songs, disliked_songs, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                prefs.user_id,
                json.dumps(prefs.favorite_moods),
                json.dumps(prefs.favorite_genres),
                json.dumps(prefs.favorite_artists),
                prefs.energy_preference,
                prefs.tempo_preference,
                json.dumps(prefs.listening_history),
                json.dumps(prefs.liked_songs),
                json.dumps(prefs.disliked_songs)
            ))
            
            con.commit()
    
    def get_personalized_recommendations(
        self,
        user_id: int,
        limit: int = 10,
        mood_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Get personalized song recommendations.
        
        Combines:
        - User's mood preferences
        - Liked similar songs
        - Energy/tempo preferences
        - Excludes disliked and recently played
        """
        prefs = self.get_preferences(user_id)
        
        # Get all songs
        with self._connect() as con:
            cur = con.cursor()
            
            if mood_filter:
                cur.execute(
                    f"SELECT * FROM {TABLE_SONGS} WHERE mood = ?",
                    (mood_filter,)
                )
            else:
                cur.execute(f"SELECT * FROM {TABLE_SONGS}")
            
            songs = [dict(row) for row in cur.fetchall()]
        
        # Score each song
        scored_songs = []
        
        for song in songs:
            song_id = song["song_id"]
            
            # Skip disliked songs
            if song_id in prefs.disliked_songs:
                continue
            
            # Calculate personalization score
            score = self._calculate_song_score(song, prefs)
            
            # Boost liked songs slightly
            if song_id in prefs.liked_songs:
                score *= 1.2
            
            # Penalize recently played
            if song_id in prefs.listening_history[-20:]:
                score *= 0.5
            
            scored_songs.append((song, score))
        
        # Sort by score and return top N
        scored_songs.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {**song, "personalization_score": round(score, 2)}
            for song, score in scored_songs[:limit]
        ]
    
    def _calculate_song_score(
        self,
        song: Dict,
        prefs: UserPreference
    ) -> float:
        """Calculate personalization score for a song."""
        score = 0.0
        
        # Mood match
        mood = song.get("mood")
        if mood and mood in prefs.favorite_moods:
            mood_weight = prefs.favorite_moods[mood]
            max_mood_weight = max(prefs.favorite_moods.values()) if prefs.favorite_moods else 1
            score += (mood_weight / max_mood_weight) * 30
        
        # Genre match
        genre = song.get("genre")
        if genre and genre in prefs.favorite_genres:
            genre_weight = prefs.favorite_genres[genre]
            max_genre_weight = max(prefs.favorite_genres.values()) if prefs.favorite_genres else 1
            score += (genre_weight / max_genre_weight) * 25
        
        # Artist match
        artist = song.get("artist")
        if artist and artist in prefs.favorite_artists:
            artist_weight = prefs.favorite_artists[artist]
            max_artist_weight = max(prefs.favorite_artists.values()) if prefs.favorite_artists else 1
            score += (artist_weight / max_artist_weight) * 20
        
        # Energy similarity
        if song.get("energy"):
            energy_diff = abs(song["energy"] - prefs.energy_preference)
            energy_score = max(0, 10 - energy_diff * 2)
            score += energy_score
        
        # Tempo similarity
        if song.get("tempo"):
            tempo_diff = abs(song["tempo"] - prefs.tempo_preference)
            tempo_score = max(0, 10 - tempo_diff / 10)
            score += tempo_score
        
        # Base score from mood_score
        if song.get("mood_score"):
            score += song["mood_score"] * 5
        
        return score
    
    def get_similar_users(
        self,
        user_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """Find users with similar preferences."""
        prefs = self.get_preferences(user_id)
        
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT user_id FROM user_preferences WHERE user_id != ?",
                (user_id,)
            )
            other_users = [row["user_id"] for row in cur.fetchall()]
        
        similarities = []
        
        for other_id in other_users:
            other_prefs = self.get_preferences(other_id)
            similarity = self._calculate_preference_similarity(prefs, other_prefs)
            similarities.append({
                "user_id": other_id,
                "similarity": round(similarity, 2)
            })
        
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:limit]
    
    def _calculate_preference_similarity(
        self,
        prefs1: UserPreference,
        prefs2: UserPreference
    ) -> float:
        """Calculate similarity between two user preferences."""
        # Cosine similarity for mood preferences
        mood_sim = self._dict_cosine_similarity(
            prefs1.favorite_moods,
            prefs2.favorite_moods
        )
        
        # Genre similarity
        genre_sim = self._dict_cosine_similarity(
            prefs1.favorite_genres,
            prefs2.favorite_genres
        )
        
        # Liked songs overlap (Jaccard)
        liked_overlap = len(
            set(prefs1.liked_songs) & set(prefs2.liked_songs)
        ) / max(
            len(set(prefs1.liked_songs) | set(prefs2.liked_songs)),
            1
        )
        
        # Weighted combination
        return mood_sim * 0.4 + genre_sim * 0.3 + liked_overlap * 0.3
    
    def _dict_cosine_similarity(
        self,
        dict1: Dict[str, float],
        dict2: Dict[str, float]
    ) -> float:
        """Calculate cosine similarity between two dictionaries."""
        if not dict1 or not dict2:
            return 0.0
        
        all_keys = set(dict1.keys()) | set(dict2.keys())
        
        dot_product = sum(
            dict1.get(k, 0) * dict2.get(k, 0)
            for k in all_keys
        )
        
        norm1 = math.sqrt(sum(v ** 2 for v in dict1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in dict2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user listening statistics."""
        prefs = self.get_preferences(user_id)
        
        with self._connect() as con:
            cur = con.cursor()
            
            # Get interaction counts
            cur.execute("""
                SELECT event_type, COUNT(*) as count
                FROM user_interactions
                WHERE user_id = ?
                GROUP BY event_type
            """, (user_id,))
            
            interactions = {
                row["event_type"]: row["count"]
                for row in cur.fetchall()
            }
            
            # Get recent plays
            cur.execute("""
                SELECT song_id, COUNT(*) as play_count
                FROM user_interactions
                WHERE user_id = ? AND event_type = 'play'
                GROUP BY song_id
                ORDER BY play_count DESC
                LIMIT 5
            """, (user_id,))
            
            top_played = [dict(row) for row in cur.fetchall()]
        
        # Get top moods
        top_moods = sorted(
            prefs.favorite_moods.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Get top genres
        top_genres = sorted(
            prefs.favorite_genres.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "user_id": user_id,
            "total_interactions": sum(interactions.values()),
            "interactions_by_type": interactions,
            "liked_songs_count": len(prefs.liked_songs),
            "disliked_songs_count": len(prefs.disliked_songs),
            "top_moods": [{"mood": m, "score": s} for m, s in top_moods],
            "top_genres": [{"genre": g, "score": s} for g, s in top_genres],
            "top_played_songs": top_played,
            "energy_preference": round(prefs.energy_preference, 1),
            "tempo_preference": round(prefs.tempo_preference, 0)
        }
    
    def clear_preferences(self, user_id: int) -> bool:
        """Clear user preferences (for testing or reset)."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "DELETE FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            cur.execute(
                "DELETE FROM user_interactions WHERE user_id = ?",
                (user_id,)
            )
            con.commit()
        
        if user_id in self._preferences_cache:
            del self._preferences_cache[user_id]
        
        return True
