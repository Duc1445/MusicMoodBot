"""
Narrative Adapter v2.0 - DJ Voice Layer
========================================

The UX Layer: Generates human-readable explanations for moods and playlists.

This module is the "personality" layer of the chatbot, separated from core logic
to maintain clean architecture. It converts engine predictions and curator
decisions into empathetic, conversational Vietnamese narratives.

Key Features:
    - Single-track mood explanations (from MoodEngine predictions)
    - Playlist theme detection and intro generation
    - Real-time transition commentary
    - Skip handling with empathetic responses
    - Context-based listening recommendations

FROZEN LOGIC UPDATES (v2.0):
    1. Uses normalized_loudness (0-100) instead of raw dB values
    2. "Ambient Guard": Lower dance threshold for atmospheric tracks (40 vs 70)
    3. Improved factor extraction with texture awareness

Architecture:
    MoodEngine prediction → NarrativeAdapter → Human-readable explanation
    Playlist → NarrativeGenerator → DJ-style script
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Union
import random

from backend.src.services.schema import (
    Song, TextureType, Mood, MOODS, MOOD_DESCRIPTIONS,
    camelot_distance
)
from backend.src.services.helpers import _to_float


# =============================================================================
# FACTOR TEMPLATES (Vietnamese)
# =============================================================================

FACTOR_TEMPLATES: Dict[str, str] = {
    "tempo_slow": "tempo chậm",
    "tempo_fast": "tempo nhanh",
    "tempo_moderate": "tempo vừa phải",
    "energy_low": "năng lượng thấp",
    "energy_high": "năng lượng cao",
    "energy_moderate": "năng lượng vừa",
    "mode_minor": "giọng thứ (minor)",
    "mode_major": "giọng trưởng (major)",
    "valence_low": "giai điệu u sầu",
    "valence_high": "giai điệu tươi sáng",
    "acoustic": "âm thanh acoustic ấm áp",
    "loud": "âm thanh mạnh mẽ",
    "soft": "âm thanh nhẹ nhàng",
    "danceable": "nhịp điệu dễ nhảy",
    "groove_high": "groove cuốn hút",
    "tension_high": "căng thẳng cao",
    "complex_rhythm": "nhịp điệu phức tạp",
    "atmospheric": "không khí sâu lắng",
    "emotional_depth": "chiều sâu cảm xúc",
    # v2.0: Texture-aware factors
    "texture_organic": "âm thanh acoustic/live",
    "texture_synthetic": "âm thanh điện tử",
    "texture_distorted": "âm thanh rock/metal",
    "texture_atmospheric": "không khí ambient",
}

# =============================================================================
# MOOD NARRATIVE TEMPLATES
# =============================================================================

MOOD_NARRATIVES: Dict[str, List[str]] = {
    "energetic": [
        "Bài hát này tràn đầy năng lượng với {factors}.",
        "Một bản nhạc sôi động, đặc trưng bởi {factors}.",
        "Cảm xúc phấn khích từ {factors}.",
    ],
    "happy": [
        "Bài hát mang lại cảm giác vui vẻ với {factors}.",
        "Giai điệu tích cực, được tạo nên từ {factors}.",
        "Một bản nhạc tươi sáng nhờ {factors}.",
    ],
    "sad": [
        "Bài hát này mang cảm xúc buồn với {factors}.",
        "Giai điệu trầm lắng, đặc trưng bởi {factors}.",
        "Cảm giác u sầu được tạo nên từ {factors}.",
    ],
    "stress": [
        "Bài hát tạo cảm giác căng thẳng với {factors}.",
        "Không khí lo lắng từ {factors}.",
        "Cảm xúc bất an được thể hiện qua {factors}.",
    ],
    "angry": [
        "Bài hát này mạnh mẽ và dữ dội với {factors}.",
        "Năng lượng bùng nổ từ {factors}.",
        "Cảm xúc mãnh liệt được thể hiện qua {factors}.",
    ],
}

# =============================================================================
# PLAYLIST THEME DETECTION
# =============================================================================

class PlaylistTheme:
    """Detected theme/arc of a playlist."""
    HEALING_JOURNEY = "healing_journey"
    DEEP_EMPATHY = "deep_empathy"
    CELEBRATION = "celebration"
    NIGHT_WIND_DOWN = "night_wind_down"
    FOCUS_FLOW = "focus_flow"
    EMOTIONAL_ROLLERCOASTER = "rollercoaster"
    CATHARSIS = "catharsis"


THEME_INTROS: Dict[str, List[str]] = {
    PlaylistTheme.HEALING_JOURNEY: [
        "Mình đã tạo một hành trình chữa lành cho bạn. Bắt đầu từ những giai điệu trầm lắng, ta sẽ dần tìm thấy ánh sáng.",
        "Đây là playlist đưa bạn từ u sầu đến tươi sáng. Hãy để nhạc dẫn lối nhé.",
        "Một hành trình cảm xúc từ buồn đến vui. Đôi khi ta cần đi qua bóng tối để thấy ánh bình minh.",
    ],
    PlaylistTheme.DEEP_EMPATHY: [
        "Đôi khi ta chỉ cần được ở lại với cảm xúc của mình. Playlist này sẽ đồng hành cùng bạn.",
        "Không phải lúc nào cũng cần vui lên. Mình sẽ ở đây, nghe cùng bạn.",
        "Những giai điệu này hiểu bạn. Hãy để cảm xúc được chảy tự nhiên.",
    ],
    PlaylistTheme.CELEBRATION: [
        "Năng lượng đầy ắp! Playlist này sẽ giữ bạn sôi động từ đầu đến cuối.",
        "Party mode: ON! Cứ để nhạc cuốn bạn đi nhé.",
        "Chuẩn bị tinh thần nào - playlist này không có chỗ cho buồn!",
    ],
    PlaylistTheme.NIGHT_WIND_DOWN: [
        "Một buổi tối thư giãn đang chờ bạn. Ta sẽ hạ dần năng lượng để kết thúc ngày.",
        "Wind-down mode. Từ sôi động đến bình yên, chuẩn bị cho giấc ngủ ngon.",
        "Playlist này như một ly trà ấm cuối ngày. Thư thái nhé.",
    ],
    PlaylistTheme.FOCUS_FLOW: [
        "Nhạc nền hoàn hảo để tập trung. Không quá mạnh, không quá nhẹ.",
        "Flow state incoming. Playlist này giữ bạn trong trạng thái làm việc tốt nhất.",
        "Đều đặn và dễ chịu. Để nhạc làm nền, bạn làm việc của mình nhé.",
    ],
    PlaylistTheme.EMOTIONAL_ROLLERCOASTER: [
        "Một chuyến đi cảm xúc đầy màu sắc. Có lúc lên, lúc xuống - như cuộc sống vậy.",
        "Prepare for a ride! Playlist này có đủ mọi cung bậc cảm xúc.",
        "Đa dạng và bất ngờ. Mỗi bài là một trải nghiệm mới.",
    ],
    PlaylistTheme.CATHARSIS: [
        "Ta sẽ xây dựng dần dần đến đỉnh cao, rồi thả lỏng. Cảm giác giải thoát đang chờ.",
        "Build-up → Release. Như một bộ phim có cao trào hoàn hảo.",
        "Playlist này biết cách tạo khoảnh khắc. Chờ đến đỉnh nhé!",
    ],
}

TRANSITION_COMMENTS: Dict[str, List[str]] = {
    "harmonic_perfect": [
        "Chuyển cảnh mượt mà.",
        "Key hoàn hảo.",
        "Nghe như một bài duy nhất.",
    ],
    "harmonic_good": [
        "Chuyển key tự nhiên.",
        "Flow mượt.",
    ],
    "harmonic_boost": [
        "Đẩy năng lượng lên!",
        "Nâng tông đẹp.",
        "Energy boost!",
    ],
    "texture_same": [
        "Giữ nguyên vibe.",
        "Cùng chất nhạc.",
    ],
    "texture_bridge": [
        "Chuyển vibe nhẹ.",
        "Đổi không khí một chút.",
    ],
    "buildup_coming": [
        "Bài này sẽ bùng nổ ở cuối!",
        "Wait for the drop...",
        "Chờ đoạn cao trào nhé.",
    ],
    "lyrical_contrast": [
        "Lời bài này đáng suy ngẫm - không vui như giai điệu đâu.",
        "Để ý kỹ lời nhé, nó ẩn chứa nhiều điều.",
        "Giai điệu vui nhưng lời khá sâu.",
    ],
    "breather": [
        "Nghỉ ngơi một chút trước khi tiếp tục.",
        "Hít thở sâu...",
        "Một khoảng lặng cần thiết.",
    ],
}


# =============================================================================
# NARRATIVE ADAPTER (Single-Track Explanations)
# =============================================================================

class NarrativeAdapter:
    """
    Converts MoodEngine predictions to human-readable narratives.
    
    FROZEN LOGIC v2.0:
    1. Uses normalized_loudness (0-100) instead of raw dB
    2. "Ambient Guard": Lower dance threshold (40) for atmospheric tracks
    """
    
    @staticmethod
    def extract_factors(song: Union[Song, Dict[str, Any]], 
                        prediction: Dict[str, Any]) -> List[str]:
        """
        Extract key contributing factors from song and prediction.
        
        v2.0 UPDATES:
        - Uses normalized_loudness from Engine (0-100), not raw dB
        - "Ambient Guard": Lower dance threshold for atmospheric tracks
        """
        factors = []
        
        # Handle both Song dataclass and dict
        if isinstance(song, Song):
            tempo = song.tempo
            energy = song.energy
            mode = song.mode
            acoustic = song.acousticness
            dance = song.danceability
            texture = song.texture_type
            groove = song.groove_factor
            tension = song.tension_level
            rhythmic = song.rhythmic_complexity
            atmospheric = song.atmospheric_depth
            depth = song.emotional_depth
        else:
            tempo = _to_float(song.get("tempo")) or 120
            energy = _to_float(song.get("energy")) or 50
            mode = _to_float(song.get("mode"))
            acoustic = _to_float(song.get("acousticness")) or 50
            dance = _to_float(song.get("danceability")) or 50
            texture_raw = song.get("texture_type")
            texture = TextureType.HYBRID
            if isinstance(texture_raw, TextureType):
                texture = texture_raw
            elif isinstance(texture_raw, str):
                try:
                    texture = TextureType(texture_raw.lower())
                except ValueError:
                    pass
            groove = _to_float(song.get("groove_factor"))
            tension = _to_float(song.get("tension_level"))
            rhythmic = _to_float(song.get("rhythmic_complexity"))
            atmospheric = _to_float(song.get("atmospheric_depth"))
            depth = _to_float(song.get("emotional_depth"))
        
        # === TEMPO ===
        if tempo < 80:
            factors.append(FACTOR_TEMPLATES["tempo_slow"])
        elif tempo > 130:
            factors.append(FACTOR_TEMPLATES["tempo_fast"])
        
        # === ENERGY ===
        if energy < 35:
            factors.append(FACTOR_TEMPLATES["energy_low"])
        elif energy > 70:
            factors.append(FACTOR_TEMPLATES["energy_high"])
        
        # === MODE ===
        if mode == 0:
            factors.append(FACTOR_TEMPLATES["mode_minor"])
        elif mode == 1:
            factors.append(FACTOR_TEMPLATES["mode_major"])
        
        # === VALENCE ===
        valence = prediction.get("valence_score", 50)
        if valence < 35:
            factors.append(FACTOR_TEMPLATES["valence_low"])
        elif valence > 65:
            factors.append(FACTOR_TEMPLATES["valence_high"])
        
        # === ACOUSTIC ===
        if acoustic > 70:
            factors.append(FACTOR_TEMPLATES["acoustic"])
        
        # === LOUDNESS (v2.0 FROZEN: use normalized_loudness) ===
        normalized_loud = prediction.get("normalized_loudness")
        if normalized_loud is not None:
            if normalized_loud > 75:
                factors.append(FACTOR_TEMPLATES["loud"])
            elif normalized_loud < 40:
                factors.append(FACTOR_TEMPLATES["soft"])
        
        # === DANCEABILITY with AMBIENT GUARD (v2.0 FROZEN) ===
        # Lower threshold for atmospheric tracks
        dance_threshold = 40 if texture == TextureType.ATMOSPHERIC else 70
        if dance > dance_threshold:
            factors.append(FACTOR_TEMPLATES["danceable"])
        
        # === GROOVE ===
        if groove is not None and groove > 65:
            factors.append(FACTOR_TEMPLATES["groove_high"])
        
        # === TENSION ===
        if tension is not None and tension > 65:
            factors.append(FACTOR_TEMPLATES["tension_high"])
        
        # === RHYTHMIC ===
        if rhythmic is not None and rhythmic > 65:
            factors.append(FACTOR_TEMPLATES["complex_rhythm"])
        
        # === ATMOSPHERIC ===
        if atmospheric is not None and atmospheric > 65:
            factors.append(FACTOR_TEMPLATES["atmospheric"])
        
        # === EMOTIONAL DEPTH ===
        if depth is not None and depth > 65:
            factors.append(FACTOR_TEMPLATES["emotional_depth"])
        
        # === TEXTURE (v2.0) ===
        if texture == TextureType.ORGANIC and "acoustic" not in " ".join(factors):
            factors.append(FACTOR_TEMPLATES["texture_organic"])
        elif texture == TextureType.SYNTHETIC:
            factors.append(FACTOR_TEMPLATES["texture_synthetic"])
        elif texture == TextureType.DISTORTED:
            factors.append(FACTOR_TEMPLATES["texture_distorted"])
        
        # Ensure at least 2 factors
        if len(factors) < 2:
            arousal = prediction.get("arousal_score", 50)
            if arousal > 55:
                factors.append(FACTOR_TEMPLATES["energy_moderate"])
            else:
                factors.append(FACTOR_TEMPLATES["tempo_moderate"])
        
        return factors[:4]
    
    @staticmethod
    def generate_explanation(song: Union[Song, Dict[str, Any]], 
                             prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate human-readable explanation for mood prediction.
        
        Returns:
            narrative: Full sentence explanation
            factors: List of contributing factors
            confidence_note: Note about prediction confidence
            short_description: Brief valence/arousal description
        """
        mood = prediction.get("mood", "happy")
        conf = prediction.get("mood_confidence", 0.5)
        
        factors = NarrativeAdapter.extract_factors(song, prediction)
        factors_text = ", ".join(factors[:3])
        if len(factors) > 3:
            factors_text += f" và {factors[3]}"
        
        templates = MOOD_NARRATIVES.get(mood, MOOD_NARRATIVES["happy"])
        template = random.choice(templates)
        narrative = template.format(factors=factors_text)
        
        # Confidence note
        if conf >= 0.8:
            conf_note = "Dự đoán có độ tin cậy cao."
        elif conf >= 0.5:
            conf_note = "Dự đoán có độ tin cậy trung bình."
        else:
            conf_note = "Bài hát có cảm xúc phức tạp, khó phân loại rõ ràng."
        
        return {
            "narrative": narrative,
            "factors": factors,
            "confidence_note": conf_note,
            "short_description": f"{prediction.get('valence_label', 'trung tính')}, {prediction.get('arousal_label', 'vừa phải')}",
        }
    
    @staticmethod
    def get_context_recommendation(prediction: Dict[str, Any]) -> str:
        """Get context-based recommendation (when to listen)."""
        morning = prediction.get("morning_score") or 50
        evening = prediction.get("evening_score") or 50
        workout = prediction.get("workout_score") or 50
        focus = prediction.get("focus_score") or 50
        relax = prediction.get("relax_score") or 50
        party = prediction.get("party_score") or 50
        
        scores = {
            "buổi sáng": morning,
            "buổi tối": evening,
            "tập gym": workout,
            "làm việc tập trung": focus,
            "thư giãn": relax,
            "tiệc tùng": party,
        }
        
        best_context = max(scores, key=scores.get)
        best_score = scores[best_context]
        
        if best_score >= 70:
            return f"Phù hợp nhất để nghe khi {best_context}."
        elif best_score >= 50:
            return f"Có thể nghe khi {best_context}."
        else:
            return "Phù hợp cho nhiều hoàn cảnh khác nhau."


# =============================================================================
# PLAYLIST THEME DETECTION
# =============================================================================

def detect_playlist_theme(tracks: List[Song]) -> str:
    """
    Analyze playlist to detect its emotional arc/theme.
    
    Returns theme identifier string.
    """
    if len(tracks) < 2:
        return PlaylistTheme.FOCUS_FLOW
    
    first = tracks[0]
    last = tracks[-1]
    
    first_valence = first.valence_score or first.valence
    last_valence = last.valence_score or last.valence
    first_arousal = first.arousal_score or first.energy
    last_arousal = last.arousal_score or last.energy
    
    valences = [t.valence_score or t.valence for t in tracks]
    arousals = [t.arousal_score or t.energy for t in tracks]
    
    avg_valence = sum(valences) / len(valences)
    avg_arousal = sum(arousals) / len(arousals)
    
    variance_valence = sum((v - avg_valence) ** 2 for v in valences) / len(valences)
    variance_arousal = sum((a - avg_arousal) ** 2 for a in arousals) / len(arousals)
    
    valence_change = last_valence - first_valence
    arousal_change = last_arousal - first_arousal
    
    # High variance = rollercoaster
    if variance_valence > 400 or variance_arousal > 400:
        return PlaylistTheme.EMOTIONAL_ROLLERCOASTER
    
    # Sad start → Happy end = Healing
    if first_valence < 40 and last_valence > 55:
        return PlaylistTheme.HEALING_JOURNEY
    
    # Sad throughout = Deep empathy
    if avg_valence < 40 and abs(valence_change) < 15:
        return PlaylistTheme.DEEP_EMPATHY
    
    # High energy throughout = Celebration
    if avg_arousal > 65 and variance_arousal < 200:
        return PlaylistTheme.CELEBRATION
    
    # High → Low = Wind down
    if first_arousal > 55 and last_arousal < 45:
        return PlaylistTheme.NIGHT_WIND_DOWN
    
    # Build then release = Catharsis
    max_arousal_idx = arousals.index(max(arousals))
    if max_arousal_idx > 0 and max_arousal_idx < len(tracks) - 1:
        if arousals[max_arousal_idx] - first_arousal > 20:
            return PlaylistTheme.CATHARSIS
    
    return PlaylistTheme.FOCUS_FLOW


# =============================================================================
# HIGHLIGHT DETECTION
# =============================================================================

@dataclass
class PlaylistHighlight:
    """A notable moment in the playlist."""
    track_index: int
    highlight_type: str
    description: str


def detect_highlights(tracks: List[Song]) -> List[PlaylistHighlight]:
    """Scan playlist for special moments worth highlighting."""
    highlights = []
    
    for i, track in enumerate(tracks):
        # Lyrical contrast
        if track.lyrical_contrast:
            highlights.append(PlaylistHighlight(
                track_index=i,
                highlight_type="lyrical_contrast",
                description=f"Track #{i+1} '{track.title}' có sự đối lập thú vị giữa giai điệu và lời."
            ))
        
        # High build-up potential
        if track.build_up_potential > 0.7:
            highlights.append(PlaylistHighlight(
                track_index=i,
                highlight_type="buildup",
                description=f"Track #{i+1} '{track.title}' sẽ có đoạn bùng nổ đáng chờ đợi!"
            ))
        
        # Energy peak
        if i > 0 and i < len(tracks) - 1:
            curr_arousal = track.arousal_score or track.energy
            prev_arousal = tracks[i-1].arousal_score or tracks[i-1].energy
            next_arousal = tracks[i+1].arousal_score or tracks[i+1].energy
            
            if curr_arousal > prev_arousal + 15 and curr_arousal > next_arousal + 10:
                highlights.append(PlaylistHighlight(
                    track_index=i,
                    highlight_type="energy_peak",
                    description=f"Track #{i+1} là đỉnh cao năng lượng của playlist."
                ))
    
    return highlights


def detect_transitions(tracks: List[Song]) -> List[Tuple[int, str]]:
    """
    Detect notable transitions between tracks.
    
    Returns list of (track_index, transition_type).
    """
    transitions = []
    
    for i in range(len(tracks) - 1):
        current = tracks[i]
        next_track = tracks[i + 1]
        
        # Harmonic quality
        dist = camelot_distance(current.camelot_code, next_track.camelot_code)
        if dist == 0:
            transitions.append((i, "harmonic_perfect"))
        elif dist == 1:
            transitions.append((i, "harmonic_good"))
        elif dist == 2:
            next_arousal = next_track.arousal_score or next_track.energy
            curr_arousal = current.arousal_score or current.energy
            if next_arousal > curr_arousal + 10:
                transitions.append((i, "harmonic_boost"))
        
        # Texture change
        if current.texture_type == next_track.texture_type:
            transitions.append((i, "texture_same"))
        elif next_track.texture_type == TextureType.HYBRID:
            transitions.append((i, "texture_bridge"))
    
    return transitions


# =============================================================================
# NARRATIVE GENERATOR (Playlist-Level)
# =============================================================================

class NarrativeGenerator:
    """
    Generates DJ-style commentary for playlists.
    
    This is the "voice" of the chatbot - empathetic and knowledgeable.
    """
    
    def __init__(self):
        self._used_templates: set = set()
    
    def _pick_template(self, templates: List[str]) -> str:
        """Pick a template, avoiding recent ones."""
        available = [t for t in templates if t not in self._used_templates]
        if not available:
            self._used_templates.clear()
            available = templates
        
        choice = random.choice(available)
        self._used_templates.add(choice)
        
        if len(self._used_templates) > 20:
            self._used_templates.pop()
        
        return choice
    
    def generate_intro(self, tracks: List[Song]) -> str:
        """Generate playlist intro based on detected theme."""
        theme = detect_playlist_theme(tracks)
        templates = THEME_INTROS.get(theme, THEME_INTROS[PlaylistTheme.FOCUS_FLOW])
        return self._pick_template(templates)
    
    def generate_highlight_comments(self, tracks: List[Song]) -> List[str]:
        """Generate comments for playlist highlights."""
        highlights = detect_highlights(tracks)
        comments = []
        
        for h in highlights[:3]:
            if h.highlight_type == "lyrical_contrast":
                template = self._pick_template(TRANSITION_COMMENTS["lyrical_contrast"])
                comments.append(f"🎵 Track #{h.track_index + 1}: {template}")
            elif h.highlight_type == "buildup":
                template = self._pick_template(TRANSITION_COMMENTS["buildup_coming"])
                comments.append(f"🔥 Track #{h.track_index + 1}: {template}")
            elif h.highlight_type == "energy_peak":
                comments.append(f"⚡ Track #{h.track_index + 1} là đỉnh cao của playlist!")
        
        return comments
    
    def generate_dj_script(self, tracks: List[Song]) -> Dict[str, Any]:
        """
        Generate complete DJ script for a playlist.
        
        Returns:
            intro: Opening statement
            theme: Detected theme
            highlights: Notable moments
            track_notes: Per-track notes (selective)
            outro: Closing statement
        """
        if not tracks:
            return {
                "intro": "Hmm, chưa có bài nào trong playlist.",
                "theme": "empty",
                "highlights": [],
                "track_notes": {},
                "outro": "",
            }
        
        theme = detect_playlist_theme(tracks)
        intro = self.generate_intro(tracks)
        highlights = self.generate_highlight_comments(tracks)
        
        # Generate selective track notes
        track_notes = {}
        transitions = detect_transitions(tracks)
        
        notable_transitions = [
            (i, t) for i, t in transitions 
            if t in ["harmonic_boost", "texture_bridge"]
        ]
        
        for idx, trans_type in notable_transitions[:3]:
            template = self._pick_template(TRANSITION_COMMENTS[trans_type])
            track_notes[idx + 1] = template
        
        # Outro based on last track mood
        last_track = tracks[-1]
        last_valence = last_track.valence_score or last_track.valence
        last_arousal = last_track.arousal_score or last_track.energy
        
        if last_valence > 60:
            outro = "Hy vọng bạn đã có những phút giây tuyệt vời! 🎶"
        elif last_arousal < 40:
            outro = "Chúc bạn một đêm bình yên. 🌙"
        else:
            outro = "Cảm ơn bạn đã nghe cùng mình! 💜"
        
        return {
            "intro": intro,
            "theme": theme,
            "theme_vi": self._theme_to_vietnamese(theme),
            "highlights": highlights,
            "track_notes": track_notes,
            "outro": outro,
            "track_count": len(tracks),
            "first_track": {
                "title": tracks[0].title,
                "artist": tracks[0].artist,
                "mood": tracks[0].mood_label or "unknown",
            },
            "last_track": {
                "title": tracks[-1].title,
                "artist": tracks[-1].artist,
                "mood": tracks[-1].mood_label or "unknown",
            },
        }
    
    def _theme_to_vietnamese(self, theme: str) -> str:
        """Convert theme identifier to Vietnamese display name."""
        mapping = {
            PlaylistTheme.HEALING_JOURNEY: "Hành trình chữa lành",
            PlaylistTheme.DEEP_EMPATHY: "Đồng cảm sâu sắc",
            PlaylistTheme.CELEBRATION: "Bùng nổ năng lượng",
            PlaylistTheme.NIGHT_WIND_DOWN: "Thư giãn cuối ngày",
            PlaylistTheme.FOCUS_FLOW: "Tập trung làm việc",
            PlaylistTheme.EMOTIONAL_ROLLERCOASTER: "Cung bậc cảm xúc",
            PlaylistTheme.CATHARSIS: "Cao trào giải thoát",
        }
        return mapping.get(theme, "Playlist của bạn")
    
    # =========================================================================
    # REAL-TIME COMMENTARY
    # =========================================================================
    
    def comment_on_skip(self, skipped_track: Song, replacement: Song) -> str:
        """Generate comment when user skips and we re-route."""
        comments = [
            f"Ok, đổi vibe một chút nhé. Thử '{replacement.title}' xem sao.",
            f"Mình hiểu rồi. '{replacement.title}' có lẽ hợp hơn.",
            f"Chuyển sang '{replacement.title}' - hy vọng bạn thích!",
            f"Không sao, mình có bài khác cho bạn: '{replacement.title}'.",
        ]
        return random.choice(comments)
    
    def comment_on_transition(self, current: Song, next_track: Song) -> Optional[str]:
        """Generate transition comment (if noteworthy)."""
        dist = camelot_distance(current.camelot_code, next_track.camelot_code)
        
        curr_arousal = current.arousal_score or current.energy
        next_arousal = next_track.arousal_score or next_track.energy
        energy_jump = next_arousal - curr_arousal
        
        if dist == 0:
            return self._pick_template(TRANSITION_COMMENTS["harmonic_perfect"])
        
        if dist == 2 and energy_jump > 15:
            return self._pick_template(TRANSITION_COMMENTS["harmonic_boost"])
        
        if next_track.build_up_potential > 0.7:
            return self._pick_template(TRANSITION_COMMENTS["buildup_coming"])
        
        if next_track.lyrical_contrast:
            return self._pick_template(TRANSITION_COMMENTS["lyrical_contrast"])
        
        return None
    
    def generate_breather_comment(self) -> str:
        """Comment when inserting a breather track."""
        return self._pick_template(TRANSITION_COMMENTS["breather"])


# =============================================================================
# QUICK ACCESS FUNCTIONS
# =============================================================================

def generate_playlist_narrative(tracks: List[Song]) -> Dict[str, Any]:
    """
    Quick function to generate full narrative for a playlist.
    
    Use this from the API layer.
    """
    generator = NarrativeGenerator()
    return generator.generate_dj_script(tracks)


def explain_playlist_theme(tracks: List[Song]) -> str:
    """Get simple theme explanation."""
    theme = detect_playlist_theme(tracks)
    generator = NarrativeGenerator()
    return generator._theme_to_vietnamese(theme)


def generate_song_explanation(song: Union[Song, Dict[str, Any]], 
                              prediction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Quick function to generate explanation for a single song.
    
    Use this from the API layer after MoodEngine.predict().
    """
    explanation = NarrativeAdapter.generate_explanation(song, prediction)
    context_rec = NarrativeAdapter.get_context_recommendation(prediction)
    
    return {
        **explanation,
        "context_recommendation": context_rec,
    }
