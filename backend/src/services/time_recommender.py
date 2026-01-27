"""
Time-based recommendation service.

Features:
- Recommend music based on time of day
- Activity-based recommendations
- Seasonal/weather-based suggestions
- Personal schedule integration
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
import sqlite3
import logging

from backend.src.services.constants import TABLE_SONGS

logger = logging.getLogger(__name__)


class TimeOfDay(str, Enum):
    EARLY_MORNING = "early_morning"  # 5-7 AM
    MORNING = "morning"              # 7-11 AM
    MIDDAY = "midday"                # 11 AM-2 PM
    AFTERNOON = "afternoon"          # 2-5 PM
    EVENING = "evening"              # 5-8 PM
    NIGHT = "night"                  # 8-11 PM
    LATE_NIGHT = "late_night"        # 11 PM-5 AM


class Activity(str, Enum):
    WAKING_UP = "waking_up"
    COMMUTING = "commuting"
    WORKING = "working"
    STUDYING = "studying"
    EXERCISING = "exercising"
    RELAXING = "relaxing"
    COOKING = "cooking"
    DINING = "dining"
    SOCIALIZING = "socializing"
    SLEEPING = "sleeping"
    MEDITATING = "meditating"


@dataclass
class TimeContext:
    """Context for time-based recommendations."""
    time_of_day: TimeOfDay
    hour: int
    is_weekend: bool
    activity: Optional[Activity] = None
    mood_hint: Optional[str] = None
    
    @classmethod
    def from_datetime(cls, dt: datetime = None) -> "TimeContext":
        if dt is None:
            dt = datetime.now()
        
        hour = dt.hour
        is_weekend = dt.weekday() >= 5
        
        # Determine time of day
        if 5 <= hour < 7:
            time_of_day = TimeOfDay.EARLY_MORNING
        elif 7 <= hour < 11:
            time_of_day = TimeOfDay.MORNING
        elif 11 <= hour < 14:
            time_of_day = TimeOfDay.MIDDAY
        elif 14 <= hour < 17:
            time_of_day = TimeOfDay.AFTERNOON
        elif 17 <= hour < 20:
            time_of_day = TimeOfDay.EVENING
        elif 20 <= hour < 23:
            time_of_day = TimeOfDay.NIGHT
        else:
            time_of_day = TimeOfDay.LATE_NIGHT
        
        return cls(
            time_of_day=time_of_day,
            hour=hour,
            is_weekend=is_weekend
        )


@dataclass
class TimeRecommendation:
    """A time-based recommendation."""
    songs: List[Dict]
    context: TimeContext
    suggested_moods: List[str]
    energy_range: tuple
    reason: str


class TimeBasedRecommender:
    """
    Recommends music based on time context.
    
    Uses psychology-backed patterns:
    - Morning: Upbeat, energizing
    - Work hours: Focus, concentration
    - Evening: Relaxation, unwinding
    - Night: Calm, sleep preparation
    """
    
    # Mood preferences by time of day
    TIME_MOOD_MAPPING = {
        TimeOfDay.EARLY_MORNING: {
            "moods": ["calm", "peaceful"],
            "energy_range": (3, 6),
            "tempo_range": (60, 100),
            "reason": "Nhạc nhẹ nhàng để bắt đầu ngày mới"
        },
        TimeOfDay.MORNING: {
            "moods": ["happy", "energetic"],
            "energy_range": (6, 9),
            "tempo_range": (100, 130),
            "reason": "Năng lượng cao để khởi động ngày"
        },
        TimeOfDay.MIDDAY: {
            "moods": ["happy", "calm"],
            "energy_range": (5, 8),
            "tempo_range": (90, 120),
            "reason": "Duy trì năng lượng giữa ngày"
        },
        TimeOfDay.AFTERNOON: {
            "moods": ["calm", "peaceful", "happy"],
            "energy_range": (4, 7),
            "tempo_range": (80, 110),
            "reason": "Nhạc vừa phải cho buổi chiều"
        },
        TimeOfDay.EVENING: {
            "moods": ["calm", "peaceful", "sad"],
            "energy_range": (3, 6),
            "tempo_range": (70, 100),
            "reason": "Thư giãn sau ngày làm việc"
        },
        TimeOfDay.NIGHT: {
            "moods": ["calm", "sad", "peaceful"],
            "energy_range": (2, 5),
            "tempo_range": (60, 90),
            "reason": "Nhạc dịu nhẹ cho buổi tối"
        },
        TimeOfDay.LATE_NIGHT: {
            "moods": ["calm", "peaceful"],
            "energy_range": (1, 4),
            "tempo_range": (50, 80),
            "reason": "Nhạc ru ngủ, thiền định"
        }
    }
    
    # Activity-based preferences
    ACTIVITY_PREFERENCES = {
        Activity.WAKING_UP: {
            "moods": ["calm", "peaceful"],
            "energy_range": (3, 6),
            "reason": "Nhạc nhẹ để thức dậy từ từ"
        },
        Activity.COMMUTING: {
            "moods": ["happy", "energetic"],
            "energy_range": (6, 9),
            "reason": "Năng lượng cho việc di chuyển"
        },
        Activity.WORKING: {
            "moods": ["calm", "peaceful"],
            "energy_range": (4, 6),
            "reason": "Nhạc giúp tập trung làm việc"
        },
        Activity.STUDYING: {
            "moods": ["calm"],
            "energy_range": (3, 5),
            "reason": "Nhạc không lời, giúp tập trung"
        },
        Activity.EXERCISING: {
            "moods": ["energetic", "angry", "happy"],
            "energy_range": (8, 10),
            "reason": "Nhạc mạnh cho tập luyện"
        },
        Activity.RELAXING: {
            "moods": ["calm", "peaceful", "sad"],
            "energy_range": (2, 5),
            "reason": "Nhạc thư giãn"
        },
        Activity.COOKING: {
            "moods": ["happy", "energetic"],
            "energy_range": (5, 8),
            "reason": "Nhạc vui vẻ khi nấu ăn"
        },
        Activity.DINING: {
            "moods": ["calm", "happy"],
            "energy_range": (4, 6),
            "reason": "Nhạc nền cho bữa ăn"
        },
        Activity.SOCIALIZING: {
            "moods": ["happy", "energetic"],
            "energy_range": (6, 9),
            "reason": "Nhạc cho buổi gặp mặt"
        },
        Activity.SLEEPING: {
            "moods": ["calm", "peaceful"],
            "energy_range": (1, 3),
            "reason": "Nhạc ru ngủ"
        },
        Activity.MEDITATING: {
            "moods": ["calm", "peaceful"],
            "energy_range": (1, 3),
            "reason": "Nhạc thiền định"
        }
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con
    
    def get_current_context(self) -> TimeContext:
        """Get current time context."""
        return TimeContext.from_datetime()
    
    def recommend_for_now(
        self,
        limit: int = 10
    ) -> TimeRecommendation:
        """Get recommendations for current time."""
        context = self.get_current_context()
        return self.recommend_for_context(context, limit)
    
    def recommend_for_context(
        self,
        context: TimeContext,
        limit: int = 10
    ) -> TimeRecommendation:
        """
        Get recommendations based on time context.
        
        Uses activity preferences if provided, 
        otherwise falls back to time-of-day preferences.
        """
        # Get preferences
        if context.activity and context.activity in self.ACTIVITY_PREFERENCES:
            prefs = self.ACTIVITY_PREFERENCES[context.activity]
        else:
            prefs = self.TIME_MOOD_MAPPING.get(
                context.time_of_day,
                self.TIME_MOOD_MAPPING[TimeOfDay.MORNING]
            )
        
        moods = prefs["moods"]
        energy_range = prefs["energy_range"]
        reason = prefs["reason"]
        
        # Override mood if hint provided
        if context.mood_hint:
            moods = [context.mood_hint] + [m for m in moods if m != context.mood_hint]
        
        # Query songs
        songs = self._query_songs(moods, energy_range, limit)
        
        return TimeRecommendation(
            songs=songs,
            context=context,
            suggested_moods=moods,
            energy_range=energy_range,
            reason=reason
        )
    
    def recommend_for_activity(
        self,
        activity: Activity,
        limit: int = 10
    ) -> TimeRecommendation:
        """Get recommendations for specific activity."""
        context = self.get_current_context()
        context.activity = activity
        return self.recommend_for_context(context, limit)
    
    def recommend_for_time(
        self,
        hour: int,
        limit: int = 10
    ) -> TimeRecommendation:
        """Get recommendations for specific hour."""
        # Create fake datetime for that hour
        now = datetime.now()
        target_dt = now.replace(hour=hour, minute=0, second=0)
        context = TimeContext.from_datetime(target_dt)
        return self.recommend_for_context(context, limit)
    
    def _query_songs(
        self,
        moods: List[str],
        energy_range: tuple,
        limit: int
    ) -> List[Dict]:
        """Query songs matching criteria."""
        with self._connect() as con:
            cur = con.cursor()
            
            placeholders = ",".join("?" * len(moods))
            
            cur.execute(f"""
                SELECT * FROM {TABLE_SONGS}
                WHERE mood IN ({placeholders})
                AND energy BETWEEN ? AND ?
                ORDER BY mood_score DESC NULLS LAST
                LIMIT ?
            """, (*moods, energy_range[0], energy_range[1], limit))
            
            songs = [dict(row) for row in cur.fetchall()]
            
            # If not enough songs, relax constraints
            if len(songs) < limit:
                cur.execute(f"""
                    SELECT * FROM {TABLE_SONGS}
                    WHERE mood IN ({placeholders})
                    AND song_id NOT IN ({",".join("?" * len(songs))})
                    ORDER BY mood_score DESC NULLS LAST
                    LIMIT ?
                """, (
                    *moods,
                    *[s["song_id"] for s in songs],
                    limit - len(songs)
                ))
                songs.extend([dict(row) for row in cur.fetchall()])
            
            return songs
    
    def get_day_schedule(
        self,
        activities: List[Dict] = None
    ) -> List[Dict]:
        """
        Get music recommendations for entire day.
        
        Args:
            activities: Optional list of {hour, activity} dicts
        """
        schedule = []
        
        # Default time slots
        time_slots = [
            {"hour": 7, "label": "Sáng sớm", "activity": Activity.WAKING_UP},
            {"hour": 9, "label": "Buổi sáng", "activity": Activity.WORKING},
            {"hour": 12, "label": "Trưa", "activity": Activity.DINING},
            {"hour": 14, "label": "Chiều", "activity": Activity.WORKING},
            {"hour": 18, "label": "Tối", "activity": Activity.RELAXING},
            {"hour": 21, "label": "Đêm", "activity": Activity.RELAXING},
        ]
        
        # Override with user activities
        if activities:
            for act in activities:
                for slot in time_slots:
                    if slot["hour"] == act.get("hour"):
                        slot["activity"] = Activity(act["activity"])
        
        for slot in time_slots:
            now = datetime.now()
            target = now.replace(hour=slot["hour"], minute=0)
            context = TimeContext.from_datetime(target)
            context.activity = slot["activity"]
            
            rec = self.recommend_for_context(context, limit=5)
            
            schedule.append({
                "hour": slot["hour"],
                "label": slot["label"],
                "activity": slot["activity"].value,
                "moods": rec.suggested_moods,
                "reason": rec.reason,
                "songs": rec.songs
            })
        
        return schedule
    
    def get_playlist_for_duration(
        self,
        duration_minutes: int,
        activity: Optional[Activity] = None
    ) -> Dict[str, Any]:
        """
        Generate playlist for specific duration.
        
        Estimates ~3.5 minutes per song on average.
        """
        avg_song_duration = 3.5
        num_songs = int(duration_minutes / avg_song_duration) + 1
        
        context = self.get_current_context()
        if activity:
            context.activity = activity
        
        rec = self.recommend_for_context(context, limit=num_songs)
        
        return {
            "duration_minutes": duration_minutes,
            "estimated_songs": num_songs,
            "context": {
                "time_of_day": context.time_of_day.value,
                "activity": activity.value if activity else None
            },
            "reason": rec.reason,
            "songs": rec.songs
        }


@dataclass
class WeatherContext:
    """Weather-based context for recommendations."""
    condition: str  # sunny, cloudy, rainy, snowy, etc.
    temperature: Optional[int] = None  # Celsius
    humidity: Optional[int] = None


class WeatherBasedRecommender:
    """
    Recommends music based on weather.
    """
    
    WEATHER_MOOD_MAPPING = {
        "sunny": {
            "moods": ["happy", "energetic"],
            "energy_range": (6, 9),
            "reason": "Ngày nắng đẹp - nhạc vui tươi"
        },
        "cloudy": {
            "moods": ["calm", "peaceful"],
            "energy_range": (4, 7),
            "reason": "Trời nhiều mây - nhạc trầm lắng"
        },
        "rainy": {
            "moods": ["sad", "calm", "peaceful"],
            "energy_range": (2, 5),
            "reason": "Trời mưa - nhạc buồn nhẹ nhàng"
        },
        "stormy": {
            "moods": ["angry", "energetic"],
            "energy_range": (7, 10),
            "reason": "Bão tố - nhạc mạnh mẽ"
        },
        "snowy": {
            "moods": ["calm", "peaceful"],
            "energy_range": (2, 5),
            "reason": "Tuyết rơi - nhạc êm dịu"
        },
        "foggy": {
            "moods": ["calm", "sad"],
            "energy_range": (2, 4),
            "reason": "Sương mù - nhạc huyền bí"
        },
        "hot": {
            "moods": ["calm", "peaceful"],
            "energy_range": (3, 6),
            "reason": "Trời nóng - nhạc mát mẻ"
        },
        "cold": {
            "moods": ["calm", "happy"],
            "energy_range": (5, 8),
            "reason": "Trời lạnh - nhạc ấm áp"
        }
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con
    
    def recommend_for_weather(
        self,
        weather: WeatherContext,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get recommendations based on weather."""
        condition = weather.condition.lower()
        
        prefs = self.WEATHER_MOOD_MAPPING.get(
            condition,
            self.WEATHER_MOOD_MAPPING["cloudy"]
        )
        
        moods = prefs["moods"]
        energy_range = prefs["energy_range"]
        
        with self._connect() as con:
            cur = con.cursor()
            placeholders = ",".join("?" * len(moods))
            
            cur.execute(f"""
                SELECT * FROM {TABLE_SONGS}
                WHERE mood IN ({placeholders})
                AND energy BETWEEN ? AND ?
                ORDER BY RANDOM()
                LIMIT ?
            """, (*moods, *energy_range, limit))
            
            songs = [dict(row) for row in cur.fetchall()]
        
        return {
            "weather": weather.condition,
            "temperature": weather.temperature,
            "moods": moods,
            "reason": prefs["reason"],
            "songs": songs
        }
