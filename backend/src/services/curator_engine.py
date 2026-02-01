"""
Curator Engine v2.0 - Dynamic DJ Brain
=======================================

The Narrative Layer: Generates playlists with smooth transitions and energy flow.

This module implements the weighted scoring system for playlist generation,
handling harmonic mixing (Camelot wheel), texture transitions, and dynamic
re-routing on skip events.

Scoring Formula (FROZEN):
    Score = w_flow * Harmonic + w_energy * Fit + w_texture * Consistency + w_narrative * Bonus
    
    Default weights: 0.30 + 0.40 + 0.20 + 0.10 = 1.0

Harmonic Mixing Logic:
    - Exact match (0 distance): 1.0
    - ±1 step on Camelot wheel: 0.8
    - +2 steps (Energy Boost): 0.5
    - 3+ steps (Clash): 0.3 (fallback to energy match)

Texture Transition Logic:
    - Same texture: 1.0
    - Compatible textures: 0.7-0.8
    - Clashing textures: 0.2-0.3 (UNLESS energy jump > 30)

Edge Case Handling:
    - Empty candidate pool: Return current playlist
    - Key clash with no alternatives: Fallback to pure energy match
    - All candidates recently skipped: Reduce penalties, try anyway

Architecture:
    Pool of Songs → CuratorEngine.generate_playlist() → Ordered Playlist
    Skip Event → CuratorEngine.handle_skip() → Re-routed Playlist
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
import math
import random

from backend.src.services.schema import (
    Song, TextureType, 
    camelot_distance, is_harmonic_compatible, texture_transition_score
)


# =============================================================================
# CURATOR CONFIG
# =============================================================================

@dataclass
class CuratorConfig:
    """
    Configuration for the Curator Engine.
    
    FROZEN SCORING WEIGHTS:
    These weights sum to 1.0 for normalized scoring.
    Changing these will affect playlist quality.
    """
    
    # === SCORING WEIGHTS (FROZEN) ===
    w_energy_fit: float = 0.40       # How close to target energy
    w_harmonic_flow: float = 0.30    # Camelot wheel compatibility  
    w_texture_smooth: float = 0.20   # Texture transition smoothness
    w_narrative_bonus: float = 0.10  # Build-up potential for climax
    
    # === ENERGY MATCHING ===
    energy_tolerance: float = 15.0
    energy_strict_tolerance: float = 8.0
    
    # === BREATHER LOGIC ===
    high_energy_threshold: float = 70.0
    max_consecutive_high: int = 3
    breather_energy_drop: float = 20.0
    
    # === HARMONIC MIXING (FROZEN) ===
    # Exact match = 1.0, ±1 step = 0.8, +2 steps = 0.5
    allow_energy_boost_mix: bool = True
    key_clash_penalty: float = 0.3
    
    # === RE-ROUTING ===
    skip_penalty_weight: float = 0.5
    min_candidates: int = 3
    
    # === VARIETY ===
    same_artist_penalty: float = 0.2
    recently_played_penalty: float = 0.3
    
    # === SELECTION ===
    top_k_candidates: int = 5
    randomness_factor: float = 2.0  # Score exponent for weighted random


# =============================================================================
# PLAYLIST STATE (for Dynamic Re-routing)
# =============================================================================

@dataclass
class PlaylistState:
    """
    Dynamic state for re-routing decisions.
    Tracks user behavior within a session.
    """
    tracks: List[Song] = field(default_factory=list)
    current_index: int = 0
    
    # User preference signals
    texture_preferences: Dict[TextureType, float] = field(default_factory=dict)
    recent_skips: List[int] = field(default_factory=list)
    recent_plays: List[int] = field(default_factory=list)
    
    # Target curve
    energy_curve: List[float] = field(default_factory=list)
    target_mood: str = "happy"
    
    def __post_init__(self):
        if not self.texture_preferences:
            for t in TextureType:
                self.texture_preferences[t] = 1.0
    
    def record_skip(self, track: Song) -> None:
        """Record a skip event - user doesn't want this."""
        self.recent_skips.append(track.song_id)
        
        current_pref = self.texture_preferences.get(track.texture_type, 1.0)
        self.texture_preferences[track.texture_type] = max(0.3, current_pref - 0.2)
        
        self.recent_skips = self.recent_skips[-10:]
    
    def record_play(self, track: Song) -> None:
        """Record a full play - user liked this."""
        self.recent_plays.append(track.song_id)
        
        current_pref = self.texture_preferences.get(track.texture_type, 1.0)
        self.texture_preferences[track.texture_type] = min(1.5, current_pref + 0.1)
        
        self.recent_plays = self.recent_plays[-20:]
    
    def get_texture_multiplier(self, texture: TextureType) -> float:
        """Get preference multiplier for a texture type."""
        return self.texture_preferences.get(texture, 1.0)
    
    @property
    def current_track(self) -> Optional[Song]:
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None
    
    @property
    def remaining_curve(self) -> List[float]:
        if self.current_index < len(self.energy_curve):
            return self.energy_curve[self.current_index:]
        return []


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def _energy_fit_score(candidate_energy: float, target_energy: float, 
                      tolerance: float = 15.0) -> float:
    """
    Score how well candidate energy matches target.
    
    Uses Gaussian falloff for smooth scoring:
    - Within tolerance: 0.7 to 1.0
    - Outside tolerance: Exponential decay to 0.1
    """
    diff = abs(candidate_energy - target_energy)
    if diff <= tolerance:
        return 1.0 - (diff / tolerance) * 0.3
    else:
        return max(0.1, 0.7 * math.exp(-(diff - tolerance) / 20.0))


def _harmonic_flow_score(current_camelot: str, candidate_camelot: str,
                         allow_boost: bool = True) -> float:
    """
    Score harmonic compatibility using Camelot wheel.
    
    FROZEN LOGIC:
        - Distance 0 (exact/relative): 1.0
        - Distance 1 (adjacent): 0.8  (was 0.9, adjusted per spec)
        - Distance 2 (energy boost): 0.5 if allowed, else 0.4
        - Distance 3+: 0.3 (clash)
    """
    dist = camelot_distance(current_camelot, candidate_camelot)
    
    if dist == 0:
        return 1.0
    elif dist == 1:
        return 0.8  # FROZEN: ±1 step = 0.8
    elif dist == 2:
        return 0.5 if allow_boost else 0.4  # FROZEN: +2 steps = 0.5
    elif dist == 3:
        return 0.4
    else:
        return 0.3  # Clash


def _texture_smooth_score(current_texture: TextureType, 
                          candidate_texture: TextureType,
                          energy_jump: float) -> float:
    """
    Score texture transition smoothness.
    
    FROZEN LOGIC:
    Large energy jumps (>30) can justify jarring texture changes.
    This allows dramatic shifts at climax points.
    """
    base_score = texture_transition_score(current_texture, candidate_texture)
    
    # FROZEN: If energy jump > 30, forgive texture clashes
    if abs(energy_jump) > 30:
        return max(base_score, 0.6)
    
    return base_score


def _narrative_bonus_score(candidate: Song, 
                           target_energy: float,
                           current_energy: float) -> float:
    """
    Bonus for songs with high build-up potential during energy climbs.
    
    This catches:
    - Post-rock songs that explode
    - EDM builds to drop
    - Cinematic crescendos
    """
    energy_jump = target_energy - current_energy
    
    if energy_jump >= 15:
        # Climbing - prefer songs that build
        return candidate.build_up_potential
    elif energy_jump <= -15:
        # Dropping - prefer mellow throughout
        return 1.0 - candidate.build_up_potential
    else:
        # Stable - neutral
        return 0.5


# =============================================================================
# CURATOR ENGINE
# =============================================================================

class CuratorEngine:
    """
    Dynamic DJ Brain for playlist generation.
    
    Key Features:
        - Energy curve following
        - Harmonic mixing (Camelot wheel)
        - Texture clustering with penalty for clashes
        - Dynamic re-routing on skip
        - Breather track insertion for fatigue prevention
    
    Usage:
        curator = CuratorEngine()
        playlist = curator.generate_playlist(
            seed_track=first_song,
            energy_curve=[50, 55, 60, 70, 80, 75, 60],
            pool=all_songs
        )
    """
    
    def __init__(self, cfg: Optional[CuratorConfig] = None):
        self.cfg = cfg or CuratorConfig()
    
    # =========================================================================
    # CORE SCORING
    # =========================================================================
    
    def _score_candidate(self, 
                         current_track: Song,
                         candidate: Song,
                         target_energy: float,
                         state: PlaylistState) -> float:
        """
        Calculate total score for a candidate track.
        
        FROZEN FORMULA:
        Score = w_energy * EnergyFit + w_harmonic * HarmonicFlow 
              + w_texture * TextureSmooth + w_narrative * NarrativeBonus
        
        Plus penalties for same artist, recently played, skipped textures.
        """
        # Get arousal scores (use computed or raw energy)
        current_energy = current_track.arousal_score or current_track.energy
        candidate_energy = candidate.arousal_score or candidate.energy
        
        # === COMPONENT SCORES ===
        energy_score = _energy_fit_score(
            candidate_energy, 
            target_energy,
            self.cfg.energy_tolerance
        )
        
        harmonic_score = _harmonic_flow_score(
            current_track.camelot_code,
            candidate.camelot_code,
            self.cfg.allow_energy_boost_mix
        )
        
        energy_jump = target_energy - current_energy
        texture_score = _texture_smooth_score(
            current_track.texture_type,
            candidate.texture_type,
            energy_jump
        )
        
        narrative_score = _narrative_bonus_score(
            candidate,
            target_energy,
            current_energy
        )
        
        # === WEIGHTED COMBINATION (FROZEN) ===
        base_score = (
            self.cfg.w_energy_fit * energy_score +
            self.cfg.w_harmonic_flow * harmonic_score +
            self.cfg.w_texture_smooth * texture_score +
            self.cfg.w_narrative_bonus * narrative_score
        )
        
        # === PENALTIES ===
        # Same artist
        if candidate.artist.lower() == current_track.artist.lower():
            base_score *= (1.0 - self.cfg.same_artist_penalty)
        
        # Recently played
        if candidate.song_id in state.recent_plays[-5:]:
            base_score *= (1.0 - self.cfg.recently_played_penalty)
        
        # Texture preference (learned from skips)
        texture_mult = state.get_texture_multiplier(candidate.texture_type)
        base_score *= texture_mult
        
        # Recently skipped
        if candidate.song_id in state.recent_skips:
            base_score *= 0.3
        
        return base_score
    
    def _score_candidate_energy_only(self, 
                                     candidate: Song,
                                     target_energy: float) -> float:
        """
        Fallback scoring using only energy match.
        
        Used when harmonic matching fails (key clashes).
        """
        candidate_energy = candidate.arousal_score or candidate.energy
        return _energy_fit_score(candidate_energy, target_energy, self.cfg.energy_tolerance)
    
    # =========================================================================
    # CANDIDATE SELECTION
    # =========================================================================
    
    def _select_next_track(self,
                           current_track: Song,
                           pool: List[Song],
                           target_energy: float,
                           state: PlaylistState,
                           used_ids: Set[int]) -> Optional[Song]:
        """
        Select best next track from pool.
        
        Uses weighted scoring + randomness for variety.
        
        EDGE CASE HANDLING:
        - Empty pool after filtering: Return None
        - All harmonically incompatible: Fallback to energy-only scoring
        """
        # Filter out already used songs
        candidates = [t for t in pool if t.song_id not in used_ids]
        
        if not candidates:
            return None
        
        # Score all candidates
        scored = []
        for candidate in candidates:
            score = self._score_candidate(
                current_track, candidate, target_energy, state
            )
            scored.append((candidate, score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Check if top candidates are all key clashes
        top_candidates = scored[:self.cfg.top_k_candidates]
        
        # EDGE CASE: If best harmonic score is below threshold, fallback to energy
        if top_candidates and top_candidates[0][1] < 0.2:
            # Fallback: Score by energy only
            energy_scored = []
            for candidate in candidates:
                score = self._score_candidate_energy_only(candidate, target_energy)
                energy_scored.append((candidate, score))
            energy_scored.sort(key=lambda x: x[1], reverse=True)
            top_candidates = energy_scored[:self.cfg.top_k_candidates]
        
        if not top_candidates:
            return None
        
        # Weighted random selection (squared scores favor higher scores)
        weights = [max(0.01, s ** self.cfg.randomness_factor) for _, s in top_candidates]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return top_candidates[0][0]
        
        r = random.random() * total_weight
        cumulative = 0
        for (track, _), w in zip(top_candidates, weights):
            cumulative += w
            if r <= cumulative:
                return track
        
        return top_candidates[0][0]
    
    # =========================================================================
    # BREATHER TRACK LOGIC
    # =========================================================================
    
    def _needs_breather(self, recent_tracks: List[Song]) -> bool:
        """
        Check if we need a breather track.
        
        True if last N tracks were all high-energy.
        Prevents listener fatigue.
        """
        if len(recent_tracks) < self.cfg.max_consecutive_high:
            return False
        
        last_n = recent_tracks[-self.cfg.max_consecutive_high:]
        all_high = all(
            (t.arousal_score or t.energy) >= self.cfg.high_energy_threshold 
            for t in last_n
        )
        
        return all_high
    
    def _get_breather_energy(self, current_energy: float) -> float:
        """Get target energy for a breather track."""
        breather = current_energy - self.cfg.breather_energy_drop
        return max(40.0, breather)
    
    # =========================================================================
    # MAIN GENERATION
    # =========================================================================
    
    def generate_playlist(self,
                          seed_track: Song,
                          energy_curve: List[float],
                          pool: List[Song]) -> List[Song]:
        """
        Generate a playlist following the energy curve.
        
        Args:
            seed_track: Starting track
            energy_curve: Target energy for each position [e1, e2, e3, ...]
            pool: Available tracks to choose from
        
        Returns:
            Ordered playlist of Songs
        
        EDGE CASES:
        - Empty energy_curve: Return just seed
        - Empty pool: Return just seed
        - Pool exhausted mid-generation: Return partial playlist
        """
        if not energy_curve or not pool:
            return [seed_track]
        
        playlist = [seed_track]
        used_ids: Set[int] = {seed_track.song_id}
        state = PlaylistState(
            tracks=playlist,
            energy_curve=energy_curve,
            current_index=0
        )
        
        current = seed_track
        
        for i, target_energy in enumerate(energy_curve):
            # Check for breather need
            actual_target = target_energy
            if self._needs_breather(playlist):
                actual_target = self._get_breather_energy(
                    current.arousal_score or current.energy
                )
            
            # Select next track
            next_track = self._select_next_track(
                current, pool, actual_target, state, used_ids
            )
            
            if next_track is None:
                break  # Pool exhausted
            
            playlist.append(next_track)
            used_ids.add(next_track.song_id)
            current = next_track
            state.current_index = len(playlist) - 1
        
        return playlist
    
    def generate_playlist_from_mood(self,
                                    seed_track: Song,
                                    target_mood: str,
                                    length: int,
                                    pool: List[Song]) -> List[Song]:
        """
        Generate playlist with auto-computed energy curve based on mood.
        
        Convenience method that creates appropriate energy curve
        for common mood targets.
        """
        # Compute appropriate curve based on mood
        seed_energy = seed_track.arousal_score or seed_track.energy
        
        if target_mood == "energetic":
            curve = EnergyCurveTemplates.party_build(length, start=seed_energy)
        elif target_mood == "happy":
            curve = EnergyCurveTemplates.healing_journey(length, start=seed_energy, end=70.0)
        elif target_mood == "sad":
            curve = EnergyCurveTemplates.deep_dive(length, low=seed_energy)
        elif target_mood == "stress":
            curve = EnergyCurveTemplates.focus_steady(length, level=55.0)
        else:
            curve = [seed_energy] * length
        
        return self.generate_playlist(seed_track, curve, pool)
    
    # =========================================================================
    # DYNAMIC RE-ROUTING
    # =========================================================================
    
    def handle_skip(self,
                    state: PlaylistState,
                    pool: List[Song]) -> Optional[Song]:
        """
        Handle a skip event and re-route.
        
        Called when user skips the current track.
        Returns the replacement track.
        """
        skipped_track = state.current_track
        if skipped_track is None:
            return None
        
        state.record_skip(skipped_track)
        
        remaining_curve = state.remaining_curve
        if not remaining_curve:
            return None
        
        # Get previous track for transition
        prev_idx = state.current_index - 1
        if prev_idx < 0:
            prev_track = skipped_track
        else:
            prev_track = state.tracks[prev_idx]
        
        # Find replacement with updated preferences
        used_ids = {t.song_id for t in state.tracks}
        replacement = self._select_next_track(
            prev_track,
            pool,
            remaining_curve[0],
            state,
            used_ids
        )
        
        if replacement:
            state.tracks[state.current_index] = replacement
        
        return replacement
    
    def reroute_upcoming(self,
                         state: PlaylistState,
                         pool: List[Song],
                         lookahead: int = 3) -> List[Song]:
        """
        Re-route the next N tracks based on current preferences.
        
        Called after a skip to rebuild the upcoming segment.
        """
        if state.current_track is None:
            return []
        
        remaining_curve = state.remaining_curve
        if len(remaining_curve) <= 1:
            return []
        
        current = state.current_track
        used_ids = {t.song_id for t in state.tracks[:state.current_index + 1]}
        
        new_segment = []
        for i in range(min(lookahead, len(remaining_curve) - 1)):
            target = remaining_curve[i + 1] if i + 1 < len(remaining_curve) else remaining_curve[-1]
            
            next_track = self._select_next_track(
                current, pool, target, state, used_ids
            )
            
            if next_track is None:
                break
            
            new_segment.append(next_track)
            used_ids.add(next_track.song_id)
            current = next_track
        
        # Replace upcoming segment
        start_idx = state.current_index + 1
        for i, track in enumerate(new_segment):
            if start_idx + i < len(state.tracks):
                state.tracks[start_idx + i] = track
            else:
                state.tracks.append(track)
        
        return new_segment


# =============================================================================
# ENERGY CURVE TEMPLATES
# =============================================================================

class EnergyCurveTemplates:
    """
    Pre-defined energy curve patterns for common use cases.
    
    These templates are designed based on music psychology research
    and DJ best practices for listener engagement.
    """
    
    @staticmethod
    def healing_journey(length: int = 8, start: float = 30.0, end: float = 70.0) -> List[float]:
        """
        Sad → Happy arc (healing/catharsis).
        
        Smooth ease-in-out curve for emotional progression.
        """
        if length <= 1:
            return [end]
        
        curve = []
        for i in range(length):
            progress = i / (length - 1)
            ease = 0.5 - 0.5 * math.cos(math.pi * progress)
            energy = start + (end - start) * ease
            curve.append(round(energy, 1))
        
        return curve
    
    @staticmethod
    def deep_dive(length: int = 8, low: float = 25.0) -> List[float]:
        """
        Stay in melancholic space (deep empathy).
        
        Slight wave pattern to maintain interest while staying low.
        """
        curve = []
        for i in range(length):
            wave = math.sin(math.pi * i / length) * 10
            curve.append(round(low + wave, 1))
        return curve
    
    @staticmethod
    def party_build(length: int = 10, start: float = 50.0, peak: float = 85.0) -> List[float]:
        """
        Build to peak then slight cooldown.
        
        Peak at 70% of playlist, then gentle descent.
        """
        if length <= 1:
            return [peak]
        
        curve = []
        peak_pos = int(length * 0.7)
        
        for i in range(length):
            if i < peak_pos:
                progress = i / peak_pos
                energy = start + (peak - start) * progress
            else:
                progress = (i - peak_pos) / (length - peak_pos)
                energy = peak - (peak - 70) * progress
            curve.append(round(energy, 1))
        
        return curve
    
    @staticmethod
    def focus_steady(length: int = 8, level: float = 45.0) -> List[float]:
        """
        Steady moderate energy for focus/work.
        
        Flat curve to avoid distraction.
        """
        return [level] * length
    
    @staticmethod
    def wind_down(length: int = 6, start: float = 60.0, end: float = 30.0) -> List[float]:
        """
        Evening relaxation curve.
        
        Smooth descent for sleep preparation.
        """
        if length <= 1:
            return [end]
        
        curve = []
        for i in range(length):
            progress = i / (length - 1)
            energy = start - (start - end) * progress
            curve.append(round(energy, 1))
        
        return curve
    
    @staticmethod
    def workout_intervals(length: int = 10, low: float = 55.0, high: float = 85.0) -> List[float]:
        """
        Interval training pattern.
        
        Alternates between moderate and high intensity.
        """
        curve = []
        for i in range(length):
            if i % 3 == 0:
                curve.append(high)
            else:
                curve.append(low + (high - low) * 0.3)
        return curve
    
    @staticmethod
    def custom(points: List[Tuple[int, float]], length: int) -> List[float]:
        """
        Create custom curve from control points.
        
        Args:
            points: List of (position, energy) tuples
            length: Total curve length
        
        Linear interpolation between control points.
        """
        if not points:
            return [50.0] * length
        
        points = sorted(points, key=lambda x: x[0])
        
        curve = []
        for i in range(length):
            left = None
            right = None
            
            for pos, energy in points:
                if pos <= i:
                    left = (pos, energy)
                if pos >= i and right is None:
                    right = (pos, energy)
            
            if left is None:
                curve.append(points[0][1])
            elif right is None:
                curve.append(points[-1][1])
            elif left[0] == right[0]:
                curve.append(left[1])
            else:
                t = (i - left[0]) / (right[0] - left[0])
                energy = left[1] + (right[1] - left[1]) * t
                curve.append(round(energy, 1))
        
        return curve
