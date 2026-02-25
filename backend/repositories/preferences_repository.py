"""
User Preferences Repository
===========================
Data access for user_preferences table (learned preference weights).
"""

from typing import List, Dict, Optional
from datetime import datetime
from .base import BaseRepository


class UserPreferencesRepository(BaseRepository):
    """Repository for learned user preferences."""
    
    TABLE = "user_preferences"
    PRIMARY_KEY = "preference_id"
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Dict[str, float]]:
        """
        Get all preferences for a user, grouped by type.
        
        Returns:
            {
                "mood": {"happy": 1.5, "sad": 1.2, ...},
                "genre": {"V-Pop": 1.8, "Ballad": 1.3, ...},
                "artist": {"Sơn Tùng": 1.5, ...}
            }
        """
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT preference_type, preference_value, weight
                FROM user_preferences
                WHERE user_id = ?
            """, (user_id,))
            
            preferences = {
                "mood": {},
                "genre": {},
                "artist": {},
                "tempo": {},
                "energy": {}
            }
            
            for row in cursor.fetchall():
                pref_type = row['preference_type']
                if pref_type in preferences:
                    preferences[pref_type][row['preference_value']] = row['weight']
            
            return preferences
    
    def get_preference_weight(self, user_id: int, pref_type: str, 
                              pref_value: str) -> float:
        """Get specific preference weight. Returns 1.0 if not found."""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT weight FROM user_preferences
                WHERE user_id = ? AND preference_type = ? AND preference_value = ?
            """, (user_id, pref_type, pref_value))
            row = cursor.fetchone()
            return row['weight'] if row else 1.0
    
    def update_preference(self, user_id: int, pref_type: str, 
                          pref_value: str, delta: float) -> float:
        """
        Update preference weight by delta.
        
        Args:
            user_id: User ID
            pref_type: 'mood', 'genre', 'artist', 'tempo', 'energy'
            pref_value: The preference value (e.g., 'happy', 'V-Pop')
            delta: Weight change (+/-)
            
        Returns:
            New weight value
        """
        valid_types = ('mood', 'genre', 'artist', 'tempo', 'energy')
        if pref_type not in valid_types:
            raise ValueError(f"Invalid preference_type: {pref_type}")
        
        with self.connection() as conn:
            # Try to get existing
            cursor = conn.execute("""
                SELECT weight, interaction_count FROM user_preferences
                WHERE user_id = ? AND preference_type = ? AND preference_value = ?
            """, (user_id, pref_type, pref_value))
            row = cursor.fetchone()
            
            if row:
                # Update existing - clamp weight between 0.1 and 3.0
                new_weight = max(0.1, min(3.0, row['weight'] + delta))
                new_count = row['interaction_count'] + 1
                conn.execute("""
                    UPDATE user_preferences
                    SET weight = ?, interaction_count = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND preference_type = ? AND preference_value = ?
                """, (new_weight, new_count, user_id, pref_type, pref_value))
            else:
                # Insert new
                new_weight = max(0.1, min(3.0, 1.0 + delta))
                conn.execute("""
                    INSERT INTO user_preferences 
                    (user_id, preference_type, preference_value, weight, interaction_count)
                    VALUES (?, ?, ?, ?, 1)
                """, (user_id, pref_type, pref_value, new_weight))
            
            conn.commit()
            return new_weight
    
    def set_preference(self, user_id: int, pref_type: str, 
                       pref_value: str, weight: float) -> bool:
        """Set preference weight directly (for manual preference setting)."""
        valid_types = ('mood', 'genre', 'artist', 'tempo', 'energy')
        if pref_type not in valid_types:
            raise ValueError(f"Invalid preference_type: {pref_type}")
        
        weight = max(0.1, min(3.0, weight))  # Clamp
        
        with self.connection() as conn:
            cursor = conn.execute("""
                INSERT INTO user_preferences (user_id, preference_type, preference_value, weight)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, preference_type, preference_value)
                DO UPDATE SET weight = ?, updated_at = CURRENT_TIMESTAMP
            """, (user_id, pref_type, pref_value, weight, weight))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_top_preferences(self, user_id: int, pref_type: str, 
                            limit: int = 5) -> List[Dict]:
        """Get top N preferences of a type by weight."""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT preference_value, weight, interaction_count
                FROM user_preferences
                WHERE user_id = ? AND preference_type = ?
                ORDER BY weight DESC
                LIMIT ?
            """, (user_id, pref_type, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def bulk_update_from_feedback(self, user_id: int, song: Dict, 
                                  feedback_type: str) -> None:
        """
        Update multiple preferences from a single feedback event.
        
        Args:
            user_id: User ID
            song: Song dict with mood, genre, artist fields
            feedback_type: 'like', 'dislike', or 'skip'
        """
        # Determine weight deltas
        deltas = {
            "like": {"mood": 0.15, "genre": 0.12, "artist": 0.10},
            "dislike": {"mood": -0.20, "genre": -0.15, "artist": -0.10},
            "skip": {"mood": -0.05, "genre": -0.03, "artist": -0.02}
        }
        
        delta_map = deltas.get(feedback_type, deltas["skip"])
        
        # Update mood preference
        if song.get("mood"):
            self.update_preference(user_id, "mood", song["mood"], delta_map["mood"])
        
        # Update genre preference
        if song.get("genre"):
            self.update_preference(user_id, "genre", song["genre"], delta_map["genre"])
        
        # Update artist preference
        if song.get("artist"):
            self.update_preference(user_id, "artist", song["artist"], delta_map["artist"])
    
    def reset_user_preferences(self, user_id: int) -> int:
        """Reset all preferences for a user. Returns count of deleted preferences."""
        with self.connection() as conn:
            cursor = conn.execute(
                "DELETE FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount
    
    def get_preference_summary(self, user_id: int) -> Dict:
        """Get summary of user's preferences for profile display."""
        prefs = self.get_user_preferences(user_id)
        
        def top_n(pref_dict: Dict, n: int = 3) -> List[str]:
            sorted_items = sorted(pref_dict.items(), key=lambda x: x[1], reverse=True)
            return [item[0] for item in sorted_items[:n]]
        
        return {
            "favorite_moods": top_n(prefs["mood"]),
            "favorite_genres": top_n(prefs["genre"]),
            "favorite_artists": top_n(prefs["artist"], 5),
            "mood_weights": prefs["mood"],
            "genre_weights": prefs["genre"]
        }
