"""
Curator Engine v1.0 - Dynamic DJ Brain
Phase 2: Adaptive Playlist Generation

MODULE 2: Core pathfinding algorithm with:
- Weighted scoring function (Energy + Harmonic + Texture + Narrative)
- Dynamic re-routing on skip events
- Breather track insertion for listener fatigue prevention
- Energy curve following with tolerance

Based on the "Adaptive DJ Graph" architecture:
- Node = Song (Mood + Texture + Key)
- Edge = Flow Score (transition smoothness)
- Pathfinding = Maximize total flow while following energy curve
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
import math
import random

from backend.src.pipelines.curator_types import (
    CuratorTrack, PlaylistState, TextureType,
    camelot_distance, is_harmonic_compatible,
    texture_transition_score, detect_texture
)


# =============================================================================
# CURATOR CONFIG
# =============================================================================

@dataclass
class CuratorConfig:
    """Configuration for the Curator Engine."""
    
    # === SCORING WEIGHTS ===
    # These sum to 1.0 for normalized scoring
    w_energy_fit: float = 0.40       # How close to target energy
    w_harmonic_flow: float = 0.30    # Camelot wheel compatibility
    w_texture_smooth: float = 0.20   # Texture transition smoothness
    w_narrative_bonus: float = 0.10  # Build-up potential for climax
    
    # === ENERGY MATCHING ===
    energy_tolerance: float = 15.0   # ±15 points is "close enough"
    energy_strict_tolerance: float = 8.0  # For final selection
    
    # === BREATHER LOGIC ===
    high_energy_threshold: float = 70.0  # What counts as "high energy"
    max_consecutive_high: int = 3        # Max high-energy songs before breather
    breather_energy_drop: float = 20.0   # How much to drop for breather
    
    # === HARMONIC MIXING ===
    allow_energy_boost_mix: bool = True  # Allow +2 Camelot jumps
    key_clash_penalty: float = 0.3       # Penalty for bad key transitions
    
    # === RE-ROUTING ===
    skip_penalty_weight: float = 0.5     # How much to penalize skipped textures
    min_candidates: int = 3              # Minimum candidates before fallback
    
    # === VARIETY ===
    same_artist_penalty: float = 0.2     # Avoid same artist back-to-back
    recently_played_penalty: float = 0.3  # Avoid recently played songs


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def _energy_fit_score(candidate_energy: float, target_energy: float, 
                      tolerance: float = 15.0) -> float:
    """
    Score how well candidate energy matches target.
    
    Returns 1.0 for perfect match, decreases with distance.
    Uses Gaussian falloff.
    """
    diff = abs(candidate_energy - target_energy)
    if diff <= tolerance:
        # Within tolerance = high score
        return 1.0 - (diff / tolerance) * 0.3  # 0.7 to 1.0
    else:
        # Outside tolerance = exponential falloff
        return max(0.1, 0.7 * math.exp(-(diff - tolerance) / 20.0))


def _harmonic_flow_score(current_camelot: str, candidate_camelot: str,
                         allow_boost: bool = True) -> float:
    """
    Score harmonic compatibility using Camelot wheel.
    
    Returns:
    - 1.0: Perfect match or relative major/minor
    - 0.9: Adjacent on wheel (±1)
    - 0.7: Energy boost (+2) - only if allowed
    - 0.3: Clash
    """
    dist = camelot_distance(current_camelot, candidate_camelot)
    
    if dist == 0:
        return 1.0  # Perfect
    elif dist == 1:
        return 0.9  # Adjacent - great
    elif dist == 2:
        return 0.7 if allow_boost else 0.4  # Energy boost or slight clash
    elif dist == 3:
        return 0.4  # Usable in a pinch
    else:
        return 0.3  # Clash - avoid


def _texture_smooth_score(current_texture: TextureType, 
                          candidate_texture: TextureType,
                          energy_jump: float) -> float:
    """
    Score texture transition smoothness.
    
    Large energy jumps can justify jarring texture changes.
    """
    base_score = texture_transition_score(current_texture, candidate_texture)
    
    # If energy jump is huge (>30), we can forgive texture clashes
    if abs(energy_jump) > 30:
        return max(base_score, 0.6)
    
    return base_score


def _narrative_bonus_score(candidate: CuratorTrack, 
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
        # We're climbing - prefer songs that build
        return candidate.build_up_potential
    elif energy_jump <= -15:
        # We're dropping - prefer low build-up (mellow throughout)
        return 1.0 - candidate.build_up_potential
    else:
        # Stable energy - neutral
        return 0.5


# =============================================================================
# CURATOR ENGINE
# =============================================================================

class CuratorEngine:
    """
    Dynamic DJ Brain for playlist generation.
    
    Key features:
    - Energy curve following
    - Harmonic mixing (Camelot)
    - Texture clustering
    - Dynamic re-routing on skip
    - Breather track insertion
    """
    
    def __init__(self, cfg: Optional[CuratorConfig] = None):
        self.cfg = cfg or CuratorConfig()
    
    # =========================================================================
    # CORE SCORING
    # =========================================================================
    
    def _score_candidate(self, 
                         current_track: CuratorTrack,
                         candidate: CuratorTrack,
                         target_energy: float,
                         state: PlaylistState) -> float:
        """
        Calculate total score for a candidate track.
        
        Combines:
        - Energy fit (40%)
        - Harmonic flow (30%)
        - Texture smoothness (20%)
        - Narrative bonus (10%)
        
        Plus penalties for:
        - Same artist
        - Recently played
        - Skipped texture preferences
        """
        # === COMPONENT SCORES ===
        energy_score = _energy_fit_score(
            candidate.arousal_score, 
            target_energy,
            self.cfg.energy_tolerance
        )
        
        harmonic_score = _harmonic_flow_score(
            current_track.camelot_code,
            candidate.camelot_code,
            self.cfg.allow_energy_boost_mix
        )
        
        energy_jump = target_energy - current_track.arousal_score
        texture_score = _texture_smooth_score(
            current_track.texture_type,
            candidate.texture_type,
            energy_jump
        )
        
        narrative_score = _narrative_bonus_score(
            candidate,
            target_energy,
            current_track.arousal_score
        )
        
        # === WEIGHTED COMBINATION ===
        base_score = (
            self.cfg.w_energy_fit * energy_score +
            self.cfg.w_harmonic_flow * harmonic_score +
            self.cfg.w_texture_smooth * texture_score +
            self.cfg.w_narrative_bonus * narrative_score
        )
        
        # === PENALTIES ===
        # Same artist penalty
        if candidate.artist.lower() == current_track.artist.lower():
            base_score *= (1.0 - self.cfg.same_artist_penalty)
        
        # Recently played penalty
        if candidate.song_id in state.recent_plays[-5:]:
            base_score *= (1.0 - self.cfg.recently_played_penalty)
        
        # Skip-based texture preference
        texture_mult = state.get_texture_multiplier(candidate.texture_type)
        base_score *= texture_mult
        
        # Recently skipped penalty
        if candidate.song_id in state.recent_skips:
            base_score *= 0.3
        
        return base_score
    
    # =========================================================================
    # CANDIDATE SELECTION
    # =========================================================================
    
    def _select_next_track(self,
                           current_track: CuratorTrack,
                           pool: List[CuratorTrack],
                           target_energy: float,
                           state: PlaylistState,
                           used_ids: set) -> Optional[CuratorTrack]:
        """
        Select best next track from pool.
        
        Uses weighted scoring + some randomness for variety.
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
        
        # Take top candidates and add some randomness
        top_k = min(5, len(scored))
        top_candidates = scored[:top_k]
        
        if not top_candidates:
            return None
        
        # Weighted random selection from top candidates
        # Squares scores to favor higher scores more
        weights = [s ** 2 for _, s in top_candidates]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return top_candidates[0][0]
        
        # Weighted selection
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
    
    def _needs_breather(self, recent_tracks: List[CuratorTrack]) -> bool:
        """
        Check if we need a breather track.
        
        True if last N tracks were all high-energy.
        """
        if len(recent_tracks) < self.cfg.max_consecutive_high:
            return False
        
        # Check last N tracks
        last_n = recent_tracks[-self.cfg.max_consecutive_high:]
        all_high = all(
            t.arousal_score >= self.cfg.high_energy_threshold 
            for t in last_n
        )
        
        return all_high
    
    def _get_breather_energy(self, current_energy: float) -> float:
        """Get target energy for a breather track."""
        breather = current_energy - self.cfg.breather_energy_drop
        return max(40.0, breather)  # Don't go too low
    
    # =========================================================================
    # MAIN GENERATION
    # =========================================================================
    
    def generate_playlist(self,
                          seed_track: CuratorTrack,
                          energy_curve: List[float],
                          pool: List[CuratorTrack]) -> List[CuratorTrack]:
        """
        Generate a playlist following the energy curve.
        
        Args:
            seed_track: Starting track
            energy_curve: Target energy for each position [e1, e2, e3, ...]
            pool: Available tracks to choose from
        
        Returns:
            Ordered playlist of CuratorTracks
        """
        if not energy_curve or not pool:
            return [seed_track]
        
        # Initialize
        playlist = [seed_track]
        used_ids = {seed_track.song_id}
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
                actual_target = self._get_breather_energy(current.arousal_score)
            
            # Select next track
            next_track = self._select_next_track(
                current, pool, actual_target, state, used_ids
            )
            
            if next_track is None:
                # Pool exhausted
                break
            
            playlist.append(next_track)
            used_ids.add(next_track.song_id)
            current = next_track
            state.current_index = len(playlist) - 1
        
        return playlist
    
    # =========================================================================
    # DYNAMIC RE-ROUTING
    # =========================================================================
    
    def handle_skip(self,
                    state: PlaylistState,
                    pool: List[CuratorTrack]) -> Optional[CuratorTrack]:
        """
        Handle a skip event and re-route.
        
        Called when user skips the current track.
        Returns the replacement track.
        """
        skipped_track = state.current_track
        if skipped_track is None:
            return None
        
        # Record the skip
        state.record_skip(skipped_track)
        
        # Get remaining energy targets
        remaining_curve = state.remaining_curve
        if not remaining_curve:
            return None
        
        # Get the previous track (what we're transitioning from)
        prev_idx = state.current_index - 1
        if prev_idx < 0:
            # Skipped the first track - use seed logic
            prev_track = skipped_track  # Fallback
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
            # Hot-swap in playlist
            state.tracks[state.current_index] = replacement
        
        return replacement
    
    def reroute_upcoming(self,
                         state: PlaylistState,
                         pool: List[CuratorTrack],
                         lookahead: int = 3) -> List[CuratorTrack]:
        """
        Re-route the next N tracks based on current preferences.
        
        Called after a skip to rebuild the upcoming segment.
        """
        if state.current_track is None:
            return []
        
        remaining_curve = state.remaining_curve
        if len(remaining_curve) <= 1:
            return []
        
        # Rebuild next N tracks
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
        
        # Replace upcoming segment in playlist
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
    """Pre-defined energy curve patterns for common use cases."""
    
    @staticmethod
    def healing_journey(length: int = 8, start: float = 30.0, end: float = 70.0) -> List[float]:
        """Sad → Happy arc (healing/catharsis)."""
        if length <= 1:
            return [end]
        
        curve = []
        for i in range(length):
            progress = i / (length - 1)
            # Smooth ease-in-out curve
            ease = 0.5 - 0.5 * math.cos(math.pi * progress)
            energy = start + (end - start) * ease
            curve.append(round(energy, 1))
        
        return curve
    
    @staticmethod
    def deep_dive(length: int = 8, low: float = 25.0) -> List[float]:
        """Stay in melancholic space (deep empathy)."""
        # Slight wave pattern
        curve = []
        for i in range(length):
            wave = math.sin(math.pi * i / length) * 10
            curve.append(round(low + wave, 1))
        return curve
    
    @staticmethod
    def party_build(length: int = 10, start: float = 50.0, peak: float = 85.0) -> List[float]:
        """Build to peak then slight cooldown."""
        if length <= 1:
            return [peak]
        
        curve = []
        peak_pos = int(length * 0.7)  # Peak at 70%
        
        for i in range(length):
            if i < peak_pos:
                # Build up
                progress = i / peak_pos
                energy = start + (peak - start) * progress
            else:
                # Slight cooldown
                progress = (i - peak_pos) / (length - peak_pos)
                energy = peak - (peak - 70) * progress
            curve.append(round(energy, 1))
        
        return curve
    
    @staticmethod
    def focus_steady(length: int = 8, level: float = 45.0) -> List[float]:
        """Steady moderate energy for focus/work."""
        return [level] * length
    
    @staticmethod
    def wind_down(length: int = 6, start: float = 60.0, end: float = 30.0) -> List[float]:
        """Evening relaxation curve."""
        if length <= 1:
            return [end]
        
        curve = []
        for i in range(length):
            progress = i / (length - 1)
            # Smooth descent
            energy = start - (start - end) * progress
            curve.append(round(energy, 1))
        
        return curve
    
    @staticmethod
    def custom(points: List[Tuple[int, float]], length: int) -> List[float]:
        """
        Create custom curve from control points.
        
        Args:
            points: List of (position, energy) tuples
            length: Total curve length
        """
        if not points:
            return [50.0] * length
        
        # Sort by position
        points = sorted(points, key=lambda x: x[0])
        
        curve = []
        for i in range(length):
            # Find surrounding control points
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
                # Interpolate
                t = (i - left[0]) / (right[0] - left[0])
                energy = left[1] + (right[1] - left[1]) * t
                curve.append(round(energy, 1))
        
        return curve
