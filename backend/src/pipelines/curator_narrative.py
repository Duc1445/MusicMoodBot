"""
Narrative Generator v1.0 - DJ Voice Layer
Phase 2: Human-readable playlist explanations

MODULE 3: UX/Narrative layer that:
- Analyzes playlist arc (theme detection)
- Generates DJ-style scripts (Vietnamese)
- Highlights special moments (lyrical contrast, build-ups)
- Provides transition explanations

This is the "personality" layer - separated from core logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import random

from backend.src.pipelines.curator_types import (
    CuratorTrack, TextureType, camelot_distance
)


# =============================================================================
# PLAYLIST THEME DETECTION
# =============================================================================

class PlaylistTheme:
    """Detected theme/arc of a playlist."""
    
    HEALING_JOURNEY = "healing_journey"      # Sad → Happy
    DEEP_EMPATHY = "deep_empathy"            # Sad → Sad (staying with emotion)
    CELEBRATION = "celebration"              # High energy throughout
    NIGHT_WIND_DOWN = "night_wind_down"      # High → Low
    FOCUS_FLOW = "focus_flow"                # Steady moderate
    EMOTIONAL_ROLLERCOASTER = "rollercoaster"  # High variance
    CATHARSIS = "catharsis"                  # Build → Release


def detect_playlist_theme(tracks: List[CuratorTrack]) -> str:
    """
    Analyze playlist to detect its emotional arc/theme.
    
    Returns theme identifier string.
    """
    if len(tracks) < 2:
        return PlaylistTheme.FOCUS_FLOW
    
    # Get first and last moods/energies
    first = tracks[0]
    last = tracks[-1]
    
    first_valence = first.valence_score
    last_valence = last.valence_score
    first_arousal = first.arousal_score
    last_arousal = last.arousal_score
    
    # Calculate average and variance
    valences = [t.valence_score for t in tracks]
    arousals = [t.arousal_score for t in tracks]
    
    avg_valence = sum(valences) / len(valences)
    avg_arousal = sum(arousals) / len(arousals)
    
    variance_valence = sum((v - avg_valence) ** 2 for v in valences) / len(valences)
    variance_arousal = sum((a - avg_arousal) ** 2 for a in arousals) / len(arousals)
    
    # Detect patterns
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
    
    # Default = Focus flow
    return PlaylistTheme.FOCUS_FLOW


# =============================================================================
# NARRATIVE TEMPLATES (Vietnamese)
# =============================================================================

THEME_INTROS = {
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

TRANSITION_COMMENTS = {
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
# HIGHLIGHT DETECTION
# =============================================================================

@dataclass
class PlaylistHighlight:
    """A notable moment in the playlist."""
    track_index: int
    highlight_type: str
    description: str


def detect_highlights(tracks: List[CuratorTrack]) -> List[PlaylistHighlight]:
    """
    Scan playlist for special moments worth highlighting.
    """
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
            if (track.arousal_score > tracks[i-1].arousal_score + 15 and
                track.arousal_score > tracks[i+1].arousal_score + 10):
                highlights.append(PlaylistHighlight(
                    track_index=i,
                    highlight_type="energy_peak",
                    description=f"Track #{i+1} là đỉnh cao năng lượng của playlist."
                ))
    
    return highlights


def detect_transitions(tracks: List[CuratorTrack]) -> List[Tuple[int, str]]:
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
        elif dist == 2 and next_track.arousal_score > current.arousal_score + 10:
            transitions.append((i, "harmonic_boost"))
        
        # Texture change
        if current.texture_type == next_track.texture_type:
            transitions.append((i, "texture_same"))
        elif next_track.texture_type == TextureType.HYBRID:
            transitions.append((i, "texture_bridge"))
    
    return transitions


# =============================================================================
# NARRATIVE GENERATOR
# =============================================================================

class NarrativeGenerator:
    """
    Generates DJ-style commentary for playlists.
    
    This is the "voice" of the chatbot - empathetic and knowledgeable.
    """
    
    def __init__(self):
        self._used_templates = set()  # Avoid repetition
    
    def _pick_template(self, templates: List[str]) -> str:
        """Pick a template, avoiding recent ones."""
        available = [t for t in templates if t not in self._used_templates]
        if not available:
            self._used_templates.clear()
            available = templates
        
        choice = random.choice(available)
        self._used_templates.add(choice)
        
        # Keep memory limited
        if len(self._used_templates) > 20:
            self._used_templates.pop()
        
        return choice
    
    def generate_intro(self, tracks: List[CuratorTrack]) -> str:
        """Generate playlist intro based on detected theme."""
        theme = detect_playlist_theme(tracks)
        templates = THEME_INTROS.get(theme, THEME_INTROS[PlaylistTheme.FOCUS_FLOW])
        return self._pick_template(templates)
    
    def generate_highlight_comments(self, tracks: List[CuratorTrack]) -> List[str]:
        """Generate comments for playlist highlights."""
        highlights = detect_highlights(tracks)
        comments = []
        
        for h in highlights[:3]:  # Max 3 highlights
            if h.highlight_type == "lyrical_contrast":
                template = self._pick_template(TRANSITION_COMMENTS["lyrical_contrast"])
                comments.append(f"🎵 Track #{h.track_index + 1}: {template}")
            elif h.highlight_type == "buildup":
                template = self._pick_template(TRANSITION_COMMENTS["buildup_coming"])
                comments.append(f"🔥 Track #{h.track_index + 1}: {template}")
            elif h.highlight_type == "energy_peak":
                comments.append(f"⚡ Track #{h.track_index + 1} là đỉnh cao của playlist!")
        
        return comments
    
    def generate_dj_script(self, tracks: List[CuratorTrack]) -> Dict[str, object]:
        """
        Generate complete DJ script for a playlist.
        
        Returns:
        - intro: Opening statement
        - theme: Detected theme
        - highlights: Notable moments
        - track_notes: Per-track notes (selective)
        - outro: Closing statement
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
        
        # Only note interesting transitions
        notable_transitions = [
            (i, t) for i, t in transitions 
            if t in ["harmonic_boost", "texture_bridge"]
        ]
        
        for idx, trans_type in notable_transitions[:3]:
            template = self._pick_template(TRANSITION_COMMENTS[trans_type])
            track_notes[idx + 1] = template  # 1-indexed for display
        
        # Outro based on last track mood
        last_track = tracks[-1]
        if last_track.valence_score > 60:
            outro = "Hy vọng bạn đã có những phút giây tuyệt vời! 🎶"
        elif last_track.arousal_score < 40:
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
                "mood": tracks[0].mood,
            },
            "last_track": {
                "title": tracks[-1].title,
                "artist": tracks[-1].artist,
                "mood": tracks[-1].mood,
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
    
    def comment_on_skip(self, 
                        skipped_track: CuratorTrack,
                        replacement: CuratorTrack) -> str:
        """Generate comment when user skips and we re-route."""
        comments = [
            f"Ok, đổi vibe một chút nhé. Thử '{replacement.title}' xem sao.",
            f"Mình hiểu rồi. '{replacement.title}' có lẽ hợp hơn.",
            f"Chuyển sang '{replacement.title}' - hy vọng bạn thích!",
            f"Không sao, mình có bài khác cho bạn: '{replacement.title}'.",
        ]
        return random.choice(comments)
    
    def comment_on_transition(self,
                              current: CuratorTrack,
                              next_track: CuratorTrack) -> Optional[str]:
        """Generate transition comment (if noteworthy)."""
        dist = camelot_distance(current.camelot_code, next_track.camelot_code)
        energy_jump = next_track.arousal_score - current.arousal_score
        
        # Only comment on notable transitions
        if dist == 0:
            return self._pick_template(TRANSITION_COMMENTS["harmonic_perfect"])
        
        if dist == 2 and energy_jump > 15:
            return self._pick_template(TRANSITION_COMMENTS["harmonic_boost"])
        
        if next_track.build_up_potential > 0.7:
            return self._pick_template(TRANSITION_COMMENTS["buildup_coming"])
        
        if next_track.lyrical_contrast:
            return self._pick_template(TRANSITION_COMMENTS["lyrical_contrast"])
        
        # Most transitions don't need commentary
        return None
    
    def generate_breather_comment(self) -> str:
        """Comment when inserting a breather track."""
        return self._pick_template(TRANSITION_COMMENTS["breather"])


# =============================================================================
# QUICK ACCESS FUNCTIONS
# =============================================================================

def generate_playlist_narrative(tracks: List[CuratorTrack]) -> Dict[str, object]:
    """
    Quick function to generate full narrative for a playlist.
    
    Use this from the API layer.
    """
    generator = NarrativeGenerator()
    return generator.generate_dj_script(tracks)


def explain_playlist_theme(tracks: List[CuratorTrack]) -> str:
    """Get simple theme explanation."""
    theme = detect_playlist_theme(tracks)
    generator = NarrativeGenerator()
    return generator._theme_to_vietnamese(theme)
