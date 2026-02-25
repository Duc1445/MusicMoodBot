"""
Chat Orchestrator
=================
The main orchestrator for the chat recommendation pipeline.

Pipeline Flow:
1. Input Classification (text → NLP mood detection, chip → direct mood)
2. Candidate Song Selection (MoodEngine)
3. Personalization Re-ranking (PreferenceModel)
4. Playlist Curation (CuratorEngine)
5. Save & Respond

Author: MusicMoodBot Team
Version: 2.0.0
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Pipeline imports
from backend.src.pipelines.text_mood_detector import TextMoodDetector, MoodScore
from backend.src.pipelines.mood_engine import MoodEngine, EngineConfig
from backend.src.pipelines.curator_engine import CuratorEngine, CuratorConfig
from backend.src.ranking.preference_model import PreferenceModel

# Repository imports
from backend.repositories import (
    SongRepository, 
    HistoryRepository, 
    FeedbackRepository,
    UserPreferencesRepository,
    PlaylistRepository
)

# Constants
from shared.constants import MOODS, MOODS_VI, MOOD_VI_TO_EN, MOOD_EN_TO_VI, MOOD_EMOJI

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MoodResult:
    """Result of mood detection."""
    mood: str  # English mood (for engines)
    mood_vi: str  # Vietnamese mood (for display)
    confidence: float
    intensity: str  # "Nhẹ", "Vừa", "Mạnh"
    keywords_matched: List[str] = field(default_factory=list)
    is_greeting: bool = False
    source: str = "text"  # "text" or "chip"


@dataclass 
class SongRecommendation:
    """A single song recommendation with metadata."""
    song_id: int
    name: str
    artist: str
    genre: str
    mood: str
    mood_match_score: float
    pref_score: float
    final_score: float
    reason: str
    audio_features: Dict[str, float] = field(default_factory=dict)


@dataclass
class ChatResponse:
    """Response from chat orchestrator."""
    success: bool
    detected_mood: Optional[MoodResult] = None
    bot_message: str = ""
    songs: List[SongRecommendation] = field(default_factory=list)
    playlist_id: Optional[int] = None
    session_id: str = ""
    require_mood_selection: bool = False
    error: Optional[str] = None


@dataclass
class FeedbackResponse:
    """Response from feedback processing."""
    success: bool
    message: str
    preference_updated: bool = False


# =============================================================================
# NARRATIVE GENERATOR
# =============================================================================

class NarrativeGenerator:
    """Generate natural language responses for the chatbot."""
    
    MOOD_RESPONSES = {
        "happy": [
            "Tuyệt vời! Tôi thấy bạn đang vui 😊 Đây là những bài hát tràn đầy năng lượng cho bạn:",
            "Thật tuyệt khi bạn đang vui! 🎉 Cùng làm ngày hôm nay thêm tuyệt vời nhé:",
            "Năng lượng tích cực đang lan tỏa! ✨ Đây là playlist cho bạn:"
        ],
        "sad": [
            "Tôi hiểu bạn đang buồn 😢 Đây là những bài hát có thể đồng cảm cùng bạn:",
            "Những lúc buồn, âm nhạc là người bạn tốt nhất 💙 Nghe thử nhé:",
            "Hãy để âm nhạc an ủi bạn nhé 🎵 Đây là những bài tôi chọn:"
        ],
        "energetic": [
            "Năng lượng đang dâng trào! ⚡ Đây là những bài sẽ giúp bạn bùng nổ:",
            "Sẵn sàng cho một ngày đầy năng lượng! 🔥 Nhạc hot đây:",
            "Let's go! 🚀 Những bài này sẽ không làm bạn thất vọng:"
        ],
        "stress": [
            "Tôi hiểu bạn đang suy tư 🧠 Đây là những bài giúp bạn thư giãn:",
            "Hãy thả lỏng và để âm nhạc dẫn lối 🌙 Nghe thử nhé:",
            "Âm nhạc sẽ giúp bạn tĩnh tâm ✨ Đây là playlist cho bạn:"
        ],
        "angry": [
            "Đôi khi cần xả stress! 💪 Đây là những bài có nhịp mạnh cho bạn:",
            "Hãy để âm nhạc giải tỏa cảm xúc 🎸 Check this out:",
            "I got you! 🔊 Những bài này sẽ giúp bạn release:"
        ]
    }
    
    INTENSITY_SUFFIXES = {
        "Nhẹ": " Tôi chọn những bài nhẹ nhàng, mellow cho bạn.",
        "Vừa": " Những bài với intensity vừa phải, balanced.",
        "Mạnh": " Đây toàn bộ là những bài có intensity cao!"
    }
    
    GREETING_RESPONSES = [
        "Xin chào! 👋 Tôi là MusicMoodBot. Bạn đang cảm thấy thế nào hôm nay?",
        "Hello! 🎵 Hãy cho tôi biết tâm trạng của bạn để tôi gợi ý nhạc phù hợp nhé!",
        "Chào bạn! ✨ Hôm nay bạn muốn nghe nhạc phong cách gì?"
    ]
    
    @classmethod
    def generate_response(cls, mood: str, intensity: str = None) -> str:
        """Generate bot response based on mood and intensity."""
        import random
        
        responses = cls.MOOD_RESPONSES.get(mood, cls.MOOD_RESPONSES["happy"])
        message = random.choice(responses)
        
        if intensity and intensity in cls.INTENSITY_SUFFIXES:
            message += cls.INTENSITY_SUFFIXES[intensity]
        
        return message
    
    @classmethod
    def generate_greeting_response(cls) -> str:
        """Generate response for greetings."""
        import random
        return random.choice(cls.GREETING_RESPONSES)
    
    @classmethod
    def generate_song_reason(cls, song: Dict, mood: str, intensity: str) -> str:
        """Generate personalized reason for song recommendation."""
        reasons = []
        
        # Mood-based reason
        if mood == "happy":
            reasons.append("giai điệu tươi vui")
        elif mood == "sad":
            reasons.append("lời ca sâu lắng")
        elif mood == "energetic":
            reasons.append("nhịp điệu sôi động")
        elif mood == "stress":
            reasons.append("âm thanh thư giãn")
        elif mood == "angry":
            reasons.append("beat mạnh mẽ")
        
        # Genre-based reason
        genre = song.get("genre", "")
        if genre:
            if "Ballad" in genre:
                reasons.append("ballad da diết")
            elif "Pop" in genre or "V-Pop" in genre:
                reasons.append("V-Pop cuốn hút")
            elif "R&B" in genre:
                reasons.append("R&B smooth")
            elif "Rock" in genre:
                reasons.append("rock đầy năng lượng")
        
        # Artist mention
        artist = song.get("artist", "")
        if artist:
            reasons.append(f"của nghệ sĩ {artist}")
        
        return "Với " + ", ".join(reasons) if reasons else "Bài hát phù hợp với tâm trạng của bạn"


# =============================================================================
# CHAT ORCHESTRATOR
# =============================================================================

class ChatOrchestrator:
    """
    Main orchestrator for the chat recommendation pipeline.
    
    Coordinates:
    - TextMoodDetector for NLP mood detection
    - MoodEngine for song candidate selection
    - PreferenceModel for personalization
    - CuratorEngine for playlist curation
    """
    
    def __init__(
        self,
        db_path: str = None,
        mood_config: EngineConfig = None,
        curator_config: CuratorConfig = None
    ):
        """
        Initialize orchestrator with all components.
        
        Args:
            db_path: Optional database path override
            mood_config: Optional MoodEngine configuration
            curator_config: Optional CuratorEngine configuration
        """
        # Initialize repositories
        self.song_repo = SongRepository(db_path)
        self.history_repo = HistoryRepository(db_path)
        self.feedback_repo = FeedbackRepository(db_path)
        self.prefs_repo = UserPreferencesRepository(db_path)
        self.playlist_repo = PlaylistRepository(db_path)
        
        # Initialize AI components
        self.text_detector = TextMoodDetector()
        self.mood_engine = MoodEngine(cfg=mood_config or EngineConfig())
        self.curator_engine = CuratorEngine(cfg=curator_config or CuratorConfig())
        
        # User preference models (cached per user)
        self._pref_models: Dict[int, PreferenceModel] = {}
        
        # Fit mood engine with all songs
        self._fit_mood_engine()
    
    def _fit_mood_engine(self):
        """Fit mood engine with all songs from database."""
        try:
            songs = self.song_repo.get_all(limit=10000)
            if songs:
                self.mood_engine.fit(songs)
                logger.info(f"MoodEngine fitted with {len(songs)} songs")
        except Exception as e:
            logger.error(f"Failed to fit MoodEngine: {e}")
    
    def _get_pref_model(self, user_id: int) -> PreferenceModel:
        """Get or create preference model for user."""
        if user_id not in self._pref_models:
            model = PreferenceModel()
            
            # Try to train from user's feedback history
            feedback_data = self.feedback_repo.get_feedback_for_training(user_id)
            if len(feedback_data) >= 5:  # Need minimum samples
                try:
                    songs = [dict(row) for row in feedback_data]
                    labels = [row['label'] for row in feedback_data]
                    model.fit(songs, labels)
                    logger.info(f"Trained preference model for user {user_id} with {len(songs)} samples")
                except Exception as e:
                    logger.warning(f"Could not train preference model: {e}")
            
            self._pref_models[user_id] = model
        
        return self._pref_models[user_id]
    
    # =========================================================================
    # MAIN PIPELINE
    # =========================================================================
    
    def process_message(
        self,
        user_id: int,
        message: str = None,
        mood: str = None,
        intensity: str = None,
        input_type: str = "text",
        session_id: str = None,
        limit: int = 10
    ) -> ChatResponse:
        """
        Process user message and return song recommendations.
        
        This is the main entry point for the chat pipeline.
        
        Args:
            user_id: User ID
            message: Text message (for NLP detection)
            mood: Direct mood selection (for chip input)
            intensity: Intensity level ("Nhẹ", "Vừa", "Mạnh")
            input_type: "text" or "chip"
            session_id: Optional session ID for tracking
            limit: Maximum songs to return
            
        Returns:
            ChatResponse with songs and metadata
        """
        session_id = session_id or str(uuid.uuid4())
        
        try:
            # Step 1: Mood Detection
            mood_result = self._detect_mood(message, mood, intensity, input_type)
            
            # Handle greetings
            if mood_result.is_greeting:
                return ChatResponse(
                    success=True,
                    detected_mood=mood_result,
                    bot_message=NarrativeGenerator.generate_greeting_response(),
                    session_id=session_id,
                    require_mood_selection=True
                )
            
            # Step 2: Get Candidate Songs
            candidates = self._get_candidates(
                mood_result.mood, 
                mood_result.intensity,
                limit=50  # Get more for re-ranking
            )
            
            if not candidates:
                # Fallback to popular songs
                candidates = self.song_repo.get_top_rated(limit=20)
                if not candidates:
                    candidates = self.song_repo.get_random(limit=20)
            
            # Step 3: Personalization Re-ranking
            personalized = self._personalize(candidates, user_id, mood_result)
            
            # Step 4: Playlist Curation
            curated = self._curate_playlist(personalized[:limit * 2], mood_result)
            
            # Take top N
            final_songs = curated[:limit]
            
            # Step 5: Save to history
            history_ids = self._save_to_history(
                user_id, final_songs, mood_result, input_type, message, session_id
            )
            
            # Create auto playlist
            playlist_id = None
            if len(final_songs) >= 3:
                song_ids = [s.song_id for s in final_songs]
                playlist_id = self.playlist_repo.create_auto_playlist(
                    user_id, mood_result.mood_vi, song_ids
                )
            
            # Generate response
            bot_message = NarrativeGenerator.generate_response(
                mood_result.mood, mood_result.intensity
            )
            
            return ChatResponse(
                success=True,
                detected_mood=mood_result,
                bot_message=bot_message,
                songs=final_songs,
                playlist_id=playlist_id,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Chat pipeline error: {e}", exc_info=True)
            return ChatResponse(
                success=False,
                error=f"Có lỗi xảy ra: {str(e)}",
                session_id=session_id
            )
    
    # =========================================================================
    # PIPELINE STEPS
    # =========================================================================
    
    def _detect_mood(
        self,
        message: str = None,
        mood: str = None,
        intensity: str = None,
        input_type: str = "text"
    ) -> MoodResult:
        """
        Step 1: Detect mood from input.
        
        - If input_type == "text": Use NLP text mood detector
        - If input_type == "chip": Use direct mood/intensity values
        """
        if input_type == "chip" and mood:
            # Direct mood from chip selection
            mood_en = MOOD_VI_TO_EN.get(mood, mood.lower())
            mood_vi = mood if mood in MOODS_VI else MOOD_EN_TO_VI.get(mood, mood)
            
            return MoodResult(
                mood=mood_en,
                mood_vi=mood_vi,
                confidence=1.0,
                intensity=intensity or "Vừa",
                source="chip"
            )
        
        # NLP text detection
        if message:
            result = self.text_detector.detect(message)
            
            if result.is_greeting:
                return MoodResult(
                    mood="",
                    mood_vi="",
                    confidence=0.0,
                    intensity="",
                    is_greeting=True,
                    source="text"
                )
            
            mood_en = MOOD_VI_TO_EN.get(result.mood, result.mood.lower())
            mood_vi = result.mood if result.mood in MOODS_VI else MOOD_EN_TO_VI.get(result.mood, result.mood)
            
            return MoodResult(
                mood=mood_en,
                mood_vi=mood_vi,
                confidence=result.confidence,
                intensity=result.intensity,
                keywords_matched=result.keywords_matched,
                source="text"
            )
        
        # Default fallback
        return MoodResult(
            mood="happy",
            mood_vi="Vui",
            confidence=0.5,
            intensity="Vừa",
            source="default"
        )
    
    def _get_candidates(
        self,
        mood: str,
        intensity: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Step 2: Get candidate songs from MoodEngine.
        """
        try:
            # Get all songs for mood engine
            all_songs = self.song_repo.get_all(limit=10000)
            
            # Use mood engine to score and rank
            if self.mood_engine._fitted:
                # Score all songs
                scored = []
                for song in all_songs:
                    try:
                        prediction = self.mood_engine.predict_one(song)
                        song_mood = prediction.get("label", "")
                        
                        # Calculate match score
                        if song_mood.lower() == mood.lower():
                            score = 1.0
                        else:
                            score = 0.5
                        
                        scored.append({
                            **song,
                            "mood_score": score,
                            "predicted_mood": song_mood
                        })
                    except:
                        pass
                
                # Sort by mood score
                scored.sort(key=lambda x: x.get("mood_score", 0), reverse=True)
                return scored[:limit]
            
            # Fallback: filter by mood field
            mood_songs = self.song_repo.get_by_mood(mood, limit=limit)
            if mood_songs:
                return mood_songs
            
            # Last fallback: random songs
            return self.song_repo.get_random(limit=limit)
            
        except Exception as e:
            logger.error(f"Error getting candidates: {e}")
            return self.song_repo.get_random(limit=limit)
    
    def _personalize(
        self,
        candidates: List[Dict],
        user_id: int,
        mood_result: MoodResult
    ) -> List[SongRecommendation]:
        """
        Step 3: Re-rank candidates using preference model.
        
        Final score = 0.6 * mood_score + 0.4 * preference_score
        """
        # Get user preferences
        user_prefs = self.prefs_repo.get_user_preferences(user_id)
        pref_model = self._get_pref_model(user_id)
        
        recommendations = []
        
        for song in candidates:
            mood_score = song.get("mood_score", 0.5)
            
            # Calculate preference score
            pref_score = 1.0
            
            # Boost from learned preferences
            song_mood = song.get("mood") or song.get("predicted_mood", "")
            song_genre = song.get("genre", "")
            song_artist = song.get("artist", "")
            
            if song_mood and song_mood in user_prefs.get("mood", {}):
                pref_score *= user_prefs["mood"][song_mood]
            
            if song_genre and song_genre in user_prefs.get("genre", {}):
                pref_score *= user_prefs["genre"][song_genre]
            
            if song_artist and song_artist in user_prefs.get("artist", {}):
                pref_score *= user_prefs["artist"][song_artist]
            
            # Use ML model if fitted
            if pref_model.is_fitted:
                try:
                    _, like_prob = pref_model.predict_proba(song)
                    pref_score *= (0.5 + like_prob)  # Scale to 0.5-1.5
                except:
                    pass
            
            # Normalize pref_score
            pref_score = min(2.0, pref_score)
            
            # Final score
            final_score = 0.6 * mood_score + 0.4 * pref_score
            
            # Generate reason
            reason = NarrativeGenerator.generate_song_reason(
                song, mood_result.mood, mood_result.intensity
            )
            
            recommendations.append(SongRecommendation(
                song_id=song.get("song_id", 0),
                name=song.get("song_name") or song.get("name", "Unknown"),
                artist=song.get("artist", "Unknown"),
                genre=song.get("genre", ""),
                mood=song_mood,
                mood_match_score=mood_score,
                pref_score=pref_score,
                final_score=final_score,
                reason=reason,
                audio_features={
                    "energy": song.get("energy", 50),
                    "valence": song.get("valence", 50),
                    "tempo": song.get("tempo", 120)
                }
            ))
        
        # Sort by final score
        recommendations.sort(key=lambda x: x.final_score, reverse=True)
        
        return recommendations
    
    def _curate_playlist(
        self,
        songs: List[SongRecommendation],
        mood_result: MoodResult
    ) -> List[SongRecommendation]:
        """
        Step 4: Use CuratorEngine to create smooth playlist.
        
        Optimizes for:
        - Energy flow
        - Harmonic compatibility (Camelot)
        - Texture transitions
        """
        if len(songs) < 3:
            return songs
        
        try:
            # Convert to dict format for curator
            song_dicts = []
            for s in songs:
                song_dicts.append({
                    "song_id": s.song_id,
                    "name": s.name,
                    "artist": s.artist,
                    "energy": s.audio_features.get("energy", 50),
                    "valence": s.audio_features.get("valence", 50),
                    "tempo": s.audio_features.get("tempo", 120),
                    "camelot_key": "8A",  # Default if not available
                    "_recommendation": s
                })
            
            # Create song lookup
            song_lookup = {s["song_id"]: s["_recommendation"] for s in song_dicts}
            
            # For now, apply simple energy-based ordering
            # Full curator integration would use CuratorEngine.curate()
            
            # Sort by energy to create flow
            intensity_map = {"Nhẹ": 0.3, "Vừa": 0.6, "Mạnh": 0.9}
            target_energy = intensity_map.get(mood_result.intensity, 0.6) * 100
            
            # Sort by distance from target energy
            song_dicts.sort(
                key=lambda x: abs(x.get("energy", 50) - target_energy)
            )
            
            # Return reordered songs
            return [song_lookup[s["song_id"]] for s in song_dicts if s["song_id"] in song_lookup]
            
        except Exception as e:
            logger.warning(f"Curation failed, returning original order: {e}")
            return songs
    
    def _save_to_history(
        self,
        user_id: int,
        songs: List[SongRecommendation],
        mood_result: MoodResult,
        input_type: str,
        input_text: str,
        session_id: str
    ) -> List[int]:
        """
        Step 5: Save recommendations to listening history.
        """
        history_ids = []
        
        for song in songs:
            try:
                history_id = self.history_repo.add_chat_entry(
                    user_id=user_id,
                    mood=mood_result.mood_vi,
                    intensity=mood_result.intensity,
                    song_id=song.song_id,
                    reason=song.reason
                )
                if history_id:
                    history_ids.append(history_id)
            except Exception as e:
                logger.warning(f"Failed to save history: {e}")
        
        return history_ids
    
    # =========================================================================
    # ENRICHED REQUEST PROCESSING (Multi-turn Integration)
    # =========================================================================
    
    def process_enriched_request(
        self,
        user_id: int,
        enriched_data: Dict[str, Any],
        session_id: str = None,
        limit: int = 10
    ) -> ChatResponse:
        """
        Process an enriched request from the conversation manager.
        
        This method integrates the multi-turn conversation system with
        the existing recommendation pipeline.
        
        Args:
            user_id: User ID
            enriched_data: Dict containing:
                - final_mood: Final detected mood
                - final_intensity: Intensity (0-1)
                - clarity_score: Confidence in mood detection
                - valence: Emotional valence (-1 to 1)
                - arousal: Energy level (0-1)
                - context: Activity, time_of_day, location, etc.
                - mood_history: List of detected moods
            session_id: Conversation session ID
            limit: Maximum songs to return
            
        Returns:
            ChatResponse with recommendations
        """
        session_id = session_id or str(uuid.uuid4())
        
        try:
            # Extract mood data
            mood_en = enriched_data.get('final_mood', 'happy')
            intensity_raw = enriched_data.get('final_intensity', 0.5)
            clarity = enriched_data.get('clarity_score', 0.5)
            valence = enriched_data.get('valence', 0.0)
            arousal = enriched_data.get('arousal', 0.5)
            context = enriched_data.get('context', {})
            
            # Map intensity to Vietnamese level
            if intensity_raw < 0.4:
                intensity_vi = "Nhẹ"
            elif intensity_raw < 0.7:
                intensity_vi = "Vừa"
            else:
                intensity_vi = "Mạnh"
            
            # Create MoodResult
            mood_vi = MOOD_EN_TO_VI.get(mood_en, mood_en.capitalize())
            mood_result = MoodResult(
                mood=mood_en,
                mood_vi=mood_vi,
                confidence=clarity,
                intensity=intensity_vi,
                source="conversation"
            )
            
            # Get candidates with context-aware adjustments
            candidates = self._get_candidates_enriched(
                mood=mood_en,
                intensity=intensity_vi,
                valence=valence,
                arousal=arousal,
                context=context,
                limit=50
            )
            
            if not candidates:
                candidates = self.song_repo.get_random(limit=20)
            
            # Personalization
            personalized = self._personalize(candidates, user_id, mood_result)
            
            # Curation
            curated = self._curate_playlist(personalized[:limit * 2], mood_result)
            final_songs = curated[:limit]
            
            # Save to history
            self._save_to_history(
                user_id, final_songs, mood_result, 
                "conversation", None, session_id
            )
            
            # Create playlist
            playlist_id = None
            if len(final_songs) >= 3:
                song_ids = [s.song_id for s in final_songs]
                playlist_id = self.playlist_repo.create_auto_playlist(
                    user_id, mood_result.mood_vi, song_ids
                )
            
            # Generate response
            bot_message = NarrativeGenerator.generate_response(
                mood_result.mood, mood_result.intensity
            )
            
            return ChatResponse(
                success=True,
                detected_mood=mood_result,
                bot_message=bot_message,
                songs=final_songs,
                playlist_id=playlist_id,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Enriched request pipeline error: {e}", exc_info=True)
            return ChatResponse(
                success=False,
                error=f"Có lỗi xảy ra: {str(e)}",
                session_id=session_id
            )
    
    def _get_candidates_enriched(
        self,
        mood: str,
        intensity: str,
        valence: float,
        arousal: float,
        context: Dict[str, Any],
        limit: int = 50
    ) -> List[Dict]:
        """
        Get candidate songs with enriched context awareness.
        
        Uses valence/arousal for more precise matching.
        """
        try:
            all_songs = self.song_repo.get_all(limit=10000)
            
            # Score songs based on multiple factors
            scored = []
            for song in all_songs:
                score = 0.0
                
                # Mood match (primary)
                song_mood = (song.get("mood") or "").lower()
                if song_mood == mood.lower():
                    score += 0.5
                
                # Valence match
                song_valence = song.get("valence", 50)
                if isinstance(song_valence, (int, float)):
                    song_valence_norm = (song_valence - 50) / 50  # Normalize to -1 to 1
                    valence_diff = abs(song_valence_norm - valence)
                    score += 0.2 * (1 - min(valence_diff, 1.0))
                
                # Arousal/Energy match
                song_energy = song.get("energy", 50)
                if isinstance(song_energy, (int, float)):
                    song_arousal = song_energy / 100.0
                    arousal_diff = abs(song_arousal - arousal)
                    score += 0.2 * (1 - min(arousal_diff, 1.0))
                
                # Context-based adjustments
                activity = context.get('activity')
                if activity:
                    # Exercise: boost high energy
                    if activity == 'exercising' and song_energy > 70:
                        score += 0.1
                    # Sleeping: boost low energy
                    elif activity == 'sleeping' and song_energy < 40:
                        score += 0.1
                    # Working/Studying: favor instrumental or moderate energy
                    elif activity in ('working', 'studying') and 40 <= song_energy <= 70:
                        score += 0.1
                
                scored.append({
                    **song,
                    "mood_score": score
                })
            
            # Sort by score
            scored.sort(key=lambda x: x.get("mood_score", 0), reverse=True)
            return scored[:limit]
            
        except Exception as e:
            logger.error(f"Error getting enriched candidates: {e}")
            return self.song_repo.get_random(limit=limit)
    
    # =========================================================================
    # FEEDBACK PROCESSING
    # =========================================================================
    
    def process_feedback(
        self,
        user_id: int,
        song_id: int,
        feedback_type: str,
        history_id: int = None,
        listened_duration: int = None
    ) -> FeedbackResponse:
        """
        Process user feedback on a song.
        
        Updates:
        - feedback table
        - user_preferences (weights)
        - listening_history (if history_id provided)
        
        Args:
            user_id: User ID
            song_id: Song ID
            feedback_type: 'like', 'dislike', or 'skip'
            history_id: Optional history entry ID
            listened_duration: Seconds listened before feedback
            
        Returns:
            FeedbackResponse
        """
        if feedback_type not in ('like', 'dislike', 'skip'):
            return FeedbackResponse(
                success=False,
                message="Invalid feedback type"
            )
        
        try:
            # 1. Save feedback
            self.feedback_repo.add(
                user_id=user_id,
                song_id=song_id,
                feedback_type=feedback_type,
                history_id=history_id
            )
            
            # 2. Get song info for preference update
            song = self.song_repo.get_by_id(song_id)
            if song:
                # 3. Update user preferences
                self.prefs_repo.bulk_update_from_feedback(
                    user_id=user_id,
                    song=song,
                    feedback_type=feedback_type
                )
            
            # 4. Update history if provided
            if history_id and listened_duration:
                try:
                    self.history_repo.update(
                        history_id,
                        listened_duration_seconds=listened_duration,
                        completed=(listened_duration > 60)
                    )
                except:
                    pass
            
            # 5. Invalidate cached preference model
            if user_id in self._pref_models:
                del self._pref_models[user_id]
            
            # Generate response message
            messages = {
                "like": "Đã ghi nhận! 👍 Tôi sẽ gợi ý nhiều bài tương tự hơn.",
                "dislike": "Đã hiểu! 👎 Tôi sẽ tránh gợi ý những bài tương tự.",
                "skip": "Đã ghi nhận. ⏭️"
            }
            
            return FeedbackResponse(
                success=True,
                message=messages[feedback_type],
                preference_updated=True
            )
            
        except Exception as e:
            logger.error(f"Feedback processing error: {e}")
            return FeedbackResponse(
                success=False,
                message=f"Lỗi: {str(e)}"
            )


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_orchestrator: Optional[ChatOrchestrator] = None


def get_chat_orchestrator() -> ChatOrchestrator:
    """Get or create singleton ChatOrchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ChatOrchestrator()
    return _orchestrator
