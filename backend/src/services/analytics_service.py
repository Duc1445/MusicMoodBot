"""
Analytics service for music data insights.
Provides statistics, trends, and user behavior analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import Counter
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class TimeRange:
    """Time range for analytics queries."""
    start: datetime
    end: datetime
    
    @classmethod
    def last_7_days(cls) -> "TimeRange":
        end = datetime.now()
        start = end - timedelta(days=7)
        return cls(start, end)
    
    @classmethod
    def last_30_days(cls) -> "TimeRange":
        end = datetime.now()
        start = end - timedelta(days=30)
        return cls(start, end)
    
    @classmethod
    def today(cls) -> "TimeRange":
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return cls(start, now)


class AnalyticsService:
    """
    Service for generating analytics and insights.
    
    Features:
    - Song statistics
    - User behavior analysis
    - Mood trends
    - Listening patterns
    - Recommendation effectiveness
    """
    
    def __init__(self, db_path: str = "music.db"):
        self.db_path = db_path
    
    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    # ==================== SONG ANALYTICS ====================
    
    def get_song_stats(self) -> Dict[str, Any]:
        """Get overall song statistics."""
        con = self._connect()
        cur = con.cursor()
        
        # Total songs
        cur.execute("SELECT COUNT(*) FROM songs")
        total_songs = cur.fetchone()[0]
        
        # Songs by mood
        cur.execute("""
            SELECT mood, COUNT(*) as count 
            FROM songs 
            WHERE mood IS NOT NULL 
            GROUP BY mood 
            ORDER BY count DESC
        """)
        mood_distribution = dict(cur.fetchall())
        
        # Songs by genre
        cur.execute("""
            SELECT genre, COUNT(*) as count 
            FROM songs 
            WHERE genre IS NOT NULL 
            GROUP BY genre 
            ORDER BY count DESC
            LIMIT 10
        """)
        top_genres = dict(cur.fetchall())
        
        # Intensity distribution
        cur.execute("""
            SELECT intensity, COUNT(*) as count 
            FROM songs 
            WHERE intensity IS NOT NULL 
            GROUP BY intensity
        """)
        intensity_distribution = dict(cur.fetchall())
        
        # Average features
        cur.execute("""
            SELECT 
                AVG(energy) as avg_energy,
                AVG(happiness) as avg_happiness,
                AVG(danceability) as avg_danceability,
                AVG(tempo) as avg_tempo,
                AVG(acousticness) as avg_acousticness
            FROM songs
        """)
        row = cur.fetchone()
        avg_features = {
            "energy": round(row[0] or 0, 2),
            "happiness": round(row[1] or 0, 2),
            "danceability": round(row[2] or 0, 2),
            "tempo": round(row[3] or 0, 2),
            "acousticness": round(row[4] or 0, 2)
        }
        
        # Feature ranges
        cur.execute("""
            SELECT 
                MIN(energy), MAX(energy),
                MIN(happiness), MAX(happiness),
                MIN(tempo), MAX(tempo)
            FROM songs
        """)
        row = cur.fetchone()
        feature_ranges = {
            "energy": {"min": row[0], "max": row[1]},
            "happiness": {"min": row[2], "max": row[3]},
            "tempo": {"min": row[4], "max": row[5]}
        }
        
        con.close()
        
        return {
            "total_songs": total_songs,
            "mood_distribution": mood_distribution,
            "top_genres": top_genres,
            "intensity_distribution": intensity_distribution,
            "average_features": avg_features,
            "feature_ranges": feature_ranges
        }
    
    def get_mood_breakdown(self) -> Dict[str, Any]:
        """Detailed mood analysis."""
        con = self._connect()
        cur = con.cursor()
        
        results = {}
        
        for mood in ["energetic", "happy", "sad", "stress", "angry"]:
            cur.execute("""
                SELECT 
                    COUNT(*) as count,
                    AVG(energy) as avg_energy,
                    AVG(happiness) as avg_happiness,
                    AVG(tempo) as avg_tempo,
                    AVG(mood_score) as avg_mood_score,
                    AVG(mood_confidence) as avg_confidence
                FROM songs
                WHERE mood = ?
            """, (mood,))
            
            row = cur.fetchone()
            if row and row[0] > 0:
                results[mood] = {
                    "count": row[0],
                    "avg_energy": round(row[1] or 0, 2),
                    "avg_happiness": round(row[2] or 0, 2),
                    "avg_tempo": round(row[3] or 0, 2),
                    "avg_mood_score": round(row[4] or 0, 2),
                    "avg_confidence": round(row[5] or 0, 3)
                }
        
        con.close()
        return results
    
    # ==================== USER ANALYTICS ====================
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a specific user."""
        con = self._connect()
        cur = con.cursor()
        
        # Total plays
        cur.execute("""
            SELECT 
                COUNT(*) as total_plays,
                COUNT(DISTINCT song_id) as unique_songs,
                SUM(play_count) as total_listens,
                AVG(rating) as avg_rating
            FROM listening_history
            WHERE user_id = ?
        """, (user_id,))
        
        row = cur.fetchone()
        basic_stats = {
            "total_plays": row[0],
            "unique_songs": row[1],
            "total_listens": row[2] or 0,
            "avg_rating": round(row[3] or 0, 2)
        }
        
        # Favorite moods
        cur.execute("""
            SELECT s.mood, COUNT(*) as count
            FROM listening_history lh
            JOIN songs s ON lh.song_id = s.song_id
            WHERE lh.user_id = ?
            GROUP BY s.mood
            ORDER BY count DESC
        """, (user_id,))
        favorite_moods = dict(cur.fetchall())
        
        # Top artists
        cur.execute("""
            SELECT s.artist, COUNT(*) as count
            FROM listening_history lh
            JOIN songs s ON lh.song_id = s.song_id
            WHERE lh.user_id = ?
            GROUP BY s.artist
            ORDER BY count DESC
            LIMIT 5
        """, (user_id,))
        top_artists = dict(cur.fetchall())
        
        # Liked songs count
        cur.execute("""
            SELECT COUNT(*) FROM listening_history
            WHERE user_id = ? AND liked = 1
        """, (user_id,))
        liked_count = cur.fetchone()[0]
        
        # Most played songs
        cur.execute("""
            SELECT s.song_name, s.artist, lh.play_count
            FROM listening_history lh
            JOIN songs s ON lh.song_id = s.song_id
            WHERE lh.user_id = ?
            ORDER BY lh.play_count DESC
            LIMIT 5
        """, (user_id,))
        most_played = [
            {"song_name": r[0], "artist": r[1], "plays": r[2]}
            for r in cur.fetchall()
        ]
        
        con.close()
        
        return {
            **basic_stats,
            "liked_songs": liked_count,
            "favorite_moods": favorite_moods,
            "top_artists": top_artists,
            "most_played": most_played
        }
    
    def get_user_listening_trend(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily listening trend for a user."""
        con = self._connect()
        cur = con.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        cur.execute("""
            SELECT 
                DATE(last_played) as date,
                COUNT(*) as plays,
                SUM(play_count) as listens
            FROM listening_history
            WHERE user_id = ? AND last_played >= ?
            GROUP BY DATE(last_played)
            ORDER BY date
        """, (user_id, start_date))
        
        trend = [
            {"date": r[0], "plays": r[1], "listens": r[2]}
            for r in cur.fetchall()
        ]
        
        con.close()
        return trend
    
    def get_user_mood_history(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Track user's mood preferences over time."""
        con = self._connect()
        cur = con.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        cur.execute("""
            SELECT 
                DATE(lh.last_played) as date,
                s.mood,
                COUNT(*) as count
            FROM listening_history lh
            JOIN songs s ON lh.song_id = s.song_id
            WHERE lh.user_id = ? AND lh.last_played >= ? AND s.mood IS NOT NULL
            GROUP BY DATE(lh.last_played), s.mood
            ORDER BY date, count DESC
        """, (user_id, start_date))
        
        # Organize by date
        mood_history = {}
        for date, mood, count in cur.fetchall():
            if date not in mood_history:
                mood_history[date] = []
            mood_history[date].append({"mood": mood, "count": count})
        
        con.close()
        return mood_history
    
    # ==================== GLOBAL ANALYTICS ====================
    
    def get_trending_songs(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending songs based on recent activity."""
        con = self._connect()
        cur = con.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        cur.execute("""
            SELECT 
                s.song_id, s.song_name, s.artist, s.mood,
                COUNT(DISTINCT lh.user_id) as unique_listeners,
                SUM(lh.play_count) as total_plays,
                AVG(lh.rating) as avg_rating
            FROM songs s
            JOIN listening_history lh ON s.song_id = lh.song_id
            WHERE lh.last_played >= ?
            GROUP BY s.song_id
            ORDER BY unique_listeners DESC, total_plays DESC
            LIMIT ?
        """, (start_date, limit))
        
        trending = [
            {
                "song_id": r[0],
                "song_name": r[1],
                "artist": r[2],
                "mood": r[3],
                "unique_listeners": r[4],
                "total_plays": r[5],
                "avg_rating": round(r[6] or 0, 2)
            }
            for r in cur.fetchall()
        ]
        
        con.close()
        return trending
    
    def get_popular_moods(self, days: int = 7) -> Dict[str, int]:
        """Get most popular moods based on listening activity."""
        con = self._connect()
        cur = con.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        cur.execute("""
            SELECT s.mood, SUM(lh.play_count) as plays
            FROM songs s
            JOIN listening_history lh ON s.song_id = lh.song_id
            WHERE lh.last_played >= ? AND s.mood IS NOT NULL
            GROUP BY s.mood
            ORDER BY plays DESC
        """, (start_date,))
        
        popular_moods = dict(cur.fetchall())
        con.close()
        return popular_moods
    
    def get_hourly_distribution(self, days: int = 30) -> Dict[int, int]:
        """Get listening distribution by hour of day."""
        con = self._connect()
        cur = con.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        cur.execute("""
            SELECT 
                CAST(strftime('%H', last_played) AS INTEGER) as hour,
                SUM(play_count) as plays
            FROM listening_history
            WHERE last_played >= ?
            GROUP BY hour
            ORDER BY hour
        """, (start_date,))
        
        distribution = dict(cur.fetchall())
        con.close()
        
        # Fill missing hours
        return {h: distribution.get(h, 0) for h in range(24)}
    
    # ==================== RECOMMENDATION ANALYTICS ====================
    
    def get_recommendation_effectiveness(self) -> Dict[str, Any]:
        """Analyze how effective recommendations are."""
        con = self._connect()
        cur = con.cursor()
        
        # Calculate based on recommendation_history and listening_history correlation
        cur.execute("""
            SELECT COUNT(*) FROM recommendation_history
        """)
        total_recommendations = cur.fetchone()[0]
        
        # Recommendations that were actually listened to
        cur.execute("""
            SELECT COUNT(DISTINCT rh.song_id)
            FROM recommendation_history rh
            JOIN listening_history lh ON rh.song_id = lh.song_id
            WHERE lh.created_at > rh.recommend_date
        """)
        followed_count = cur.fetchone()[0]
        
        # Recommendations that were liked
        cur.execute("""
            SELECT COUNT(DISTINCT rh.song_id)
            FROM recommendation_history rh
            JOIN listening_history lh ON rh.song_id = lh.song_id
            WHERE lh.liked = 1 AND lh.created_at > rh.recommend_date
        """)
        liked_count = cur.fetchone()[0]
        
        con.close()
        
        follow_rate = followed_count / total_recommendations if total_recommendations > 0 else 0
        like_rate = liked_count / followed_count if followed_count > 0 else 0
        
        return {
            "total_recommendations": total_recommendations,
            "recommendations_followed": followed_count,
            "follow_rate": round(follow_rate, 4),
            "liked_from_recommendations": liked_count,
            "like_rate": round(like_rate, 4)
        }
    
    # ==================== DASHBOARD DATA ====================
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary data for dashboard."""
        return {
            "song_stats": self.get_song_stats(),
            "mood_breakdown": self.get_mood_breakdown(),
            "trending": self.get_trending_songs(days=7, limit=5),
            "popular_moods": self.get_popular_moods(days=7),
            "hourly_distribution": self.get_hourly_distribution(days=30),
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_insights(self) -> List[Dict[str, str]]:
        """Generate actionable insights from data."""
        insights = []
        
        song_stats = self.get_song_stats()
        mood_dist = song_stats.get("mood_distribution", {})
        
        # Mood balance insight
        total = sum(mood_dist.values()) if mood_dist else 0
        if total > 0:
            max_mood = max(mood_dist.items(), key=lambda x: x[1])
            min_mood = min(mood_dist.items(), key=lambda x: x[1])
            
            if max_mood[1] / total > 0.4:
                insights.append({
                    "type": "warning",
                    "title": "Mood imbalance detected",
                    "message": f"'{max_mood[0]}' mood dominates with {max_mood[1]/total:.0%}. Consider adding more diverse songs."
                })
            
            if min_mood[1] / total < 0.1:
                insights.append({
                    "type": "info",
                    "title": "Underrepresented mood",
                    "message": f"'{min_mood[0]}' mood only has {min_mood[1]} songs. Consider adding more."
                })
        
        # Feature insight
        avg_features = song_stats.get("average_features", {})
        if avg_features.get("energy", 0) > 70:
            insights.append({
                "type": "info",
                "title": "High energy library",
                "message": f"Average energy is {avg_features['energy']:.0f}/100. Great for workout playlists!"
            })
        
        if avg_features.get("acousticness", 0) < 30:
            insights.append({
                "type": "info",
                "title": "Mostly electronic",
                "message": f"Low acousticness ({avg_features['acousticness']:.0f}/100). Consider adding acoustic songs for variety."
            })
        
        return insights


# Global instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service(db_path: str = None) -> AnalyticsService:
    """Get or create analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        if db_path is None:
            current_file = os.path.abspath(__file__)
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            db_path = os.path.join(backend_dir, "src", "database", "music.db")
        _analytics_service = AnalyticsService(db_path)
    return _analytics_service
