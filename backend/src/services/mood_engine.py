"""
Mood Engine v5.2 - Production-ready Affective Inference Engine
==============================================================

The Perception Layer: Analyzes individual tracks to compute mood metrics.

This module implements the frozen v5.2 logic for mood prediction based on
Music Information Retrieval (MIR) features. It converts raw audio features
into the VA (Valence-Arousal) space and classifies tracks into mood categories.

v5.2 Frozen Logic Rules (MUST NOT BE MODIFIED):
    1. Context-Aware Acoustic: Orchestral genres get reduced penalty (0.1 vs 0.3)
    2. Kinetic Zero-Floor: dance_safe = max(dance, 25) to prevent zero arousal
    3. VA Rotation: Rotate VA space by 12 degrees for diagonal emotions
    4. Mahalanobis Distance: Use Prototype2D with covariance for mood classification

Architecture:
    Song → MoodEngine.predict() → {valence_score, arousal_score, mood_label, ...}

Dependencies:
    - schema.py: Song dataclass, Mood enum, constants
    - helpers.py: Utility functions (clamp, percentile, softmax, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Iterable, Union
import math

from backend.src.services.schema import (
    Song, SongDict, Mood, MOODS, MOOD_DESCRIPTIONS,
    CAMELOT_VALENCE_BIAS, CAMELOT_MAJOR_BOOST, ORCHESTRAL_GENRES
)
from backend.src.services.helpers import (
    _is_missing, _to_float, clamp, percentile, robust_minmax,
    coerce_0_100, normalize_loudness_to_0_100, softmax, tokenize_genre
)

Number = float


# =============================================================================
# SEMANTIC BUCKETS FOR HUMAN-READABLE OUTPUT
# =============================================================================

AROUSAL_LABELS: Dict[Tuple[int, int], Tuple[str, str]] = {
    (0, 25): ("rất nhẹ nhàng", "very_calm"),
    (25, 40): ("nhẹ nhàng", "calm"),
    (40, 55): ("vừa phải", "moderate"),
    (55, 70): ("sôi động", "energetic"),
    (70, 85): ("mạnh mẽ", "intense"),
    (85, 100): ("bùng nổ", "explosive"),
}

VALENCE_LABELS: Dict[Tuple[int, int], Tuple[str, str]] = {
    (0, 20): ("rất u sầu", "very_melancholic"),
    (20, 35): ("u sầu", "melancholic"),
    (35, 45): ("trầm lắng", "contemplative"),
    (45, 55): ("trung tính", "neutral"),
    (55, 65): ("ấm áp", "warm"),
    (65, 80): ("tươi sáng", "bright"),
    (80, 100): ("rực rỡ", "radiant"),
}


def get_arousal_label(arousal: float) -> Tuple[str, str]:
    """Get human-readable arousal label (vi, en)."""
    for (lo, hi), labels in AROUSAL_LABELS.items():
        if lo <= arousal < hi:
            return labels
    return ("bùng nổ", "explosive")


def get_valence_label(valence: float) -> Tuple[str, str]:
    """Get human-readable valence label (vi, en)."""
    for (lo, hi), labels in VALENCE_LABELS.items():
        if lo <= valence < hi:
            return labels
    return ("rực rỡ", "radiant")


# =============================================================================
# ENGINE CONFIGURATION
# =============================================================================

@dataclass
class EngineConfig:
    """
    MoodEngine v5.2 Configuration - Forensic-level tuned weights.
    
    These weights have been empirically tuned and should NOT be modified
    without extensive A/B testing. They represent the "frozen" v5.2 logic.
    
    Sections:
        - Tempo normalization bounds
        - Loudness dBFS normalization
        - Arousal weights (v5.0 reduced energy to avoid double-counting)
        - Valence weights (v5.0 semantic separation)
        - Halftime/doubletime detection
        - Prototype training parameters
        - VA space rotation angle
        - Angry detection thresholds
    """
    
    # =========================================================================
    # TEMPO NORMALIZATION
    # =========================================================================
    tempo_p_low: Number = 5.0
    tempo_p_high: Number = 95.0
    tempo_abs_low: Number = 50.0
    tempo_abs_high: Number = 200.0

    # =========================================================================
    # LOUDNESS dBFS NORMALIZATION
    # =========================================================================
    loudness_db_floor: Number = -60.0
    loudness_db_ceil: Number = 0.0

    # =========================================================================
    # AROUSAL WEIGHTS v5.0
    # - Reduced energy (was double-counting tempo+loudness)
    # - Added kinetic interaction term: sqrt(tempo * danceability)
    # - Acousticness now scales loudness, not subtract
    # =========================================================================
    w_energy: Number = 0.22
    w_kinetic: Number = 0.18
    w_tempo: Number = 0.10
    w_loudness: Number = 0.16
    w_dance_arousal: Number = 0.08
    w_liveness: Number = 0.06
    w_tension: Number = 0.10
    w_groove: Number = 0.08
    w_energy_buildup: Number = 0.06
    w_rhythmic_complexity: Number = 0.08

    # v5.2: Context-aware acoustic scaling
    # FROZEN LOGIC: orchestral_penalty = 0.1, default_penalty = 0.3
    acoustic_loudness_scale: Number = 0.3
    acoustic_orchestral_scale: Number = 0.1

    # v5.2: Kinetic zero-floor (FROZEN: dance_safe >= 25)
    kinetic_dance_floor: Number = 0.25

    # =========================================================================
    # VALENCE WEIGHTS v5.0
    # - Separated spotify valence vs tunebat happiness
    # - Mode: slope not offset (+8/-4 instead of +50/-20)
    # - Added Camelot/Key bias
    # =========================================================================
    w_valence_core: Number = 0.50
    w_positivity: Number = 0.15
    w_valence_dance: Number = 0.08
    w_valence_mode: Number = 0.06
    w_valence_key: Number = 0.05
    w_valence_brightness: Number = 0.06
    w_valence_nostalgia: Number = 0.04
    w_valence_satisfaction: Number = 0.06

    # Mode adjustment: slope not offset (v5.0 fix)
    mode_major_boost: Number = 8.0
    mode_minor_penalty: Number = -4.0

    # =========================================================================
    # HALFTIME/DOUBLETIME DETECTION
    # =========================================================================
    halftime_tempo_threshold: Number = 90.0
    halftime_energy_threshold: Number = 70.0
    halftime_multiplier: Number = 1.5

    # =========================================================================
    # EMOTIONAL DEPTH & STABILITY
    # =========================================================================
    use_emotional_depth: bool = True
    depth_confidence_boost: Number = 0.12

    use_mood_stability: bool = True
    stability_weight: Number = 0.08

    # =========================================================================
    # ADVANCED FEATURES
    # =========================================================================
    use_advanced_features: bool = True
    harmonic_complexity_weight: Number = 0.04
    atmospheric_weight: Number = 0.03
    volatility_weight: Number = 0.05

    # =========================================================================
    # ENTROPY-BASED CONFIDENCE PENALTY
    # =========================================================================
    use_entropy_penalty: bool = True
    entropy_penalty_factor: Number = 0.4

    # =========================================================================
    # PROTOTYPE TRAINING
    # =========================================================================
    proto_min_std: Number = 8.0
    proto_temperature: Number = 1.0

    # =========================================================================
    # VA SPACE ROTATION (FROZEN: 12 degrees)
    # 
    # WHY ROTATE?
    # In Russell's Circumplex Model, emotions like "sad" and "stress" lie on
    # a diagonal rather than axis-aligned. By rotating the VA space ~12°,
    # we better separate these diagonal emotions for more accurate classification.
    # =========================================================================
    va_rotation_degrees: Number = 12.0

    # =========================================================================
    # WEAK-LABEL ANGRY THRESHOLDS
    # Added rhythmic_complexity for slow-but-angry detection (doom metal)
    # =========================================================================
    angry_loudness_hi: Number = 70.0
    angry_tempo_hi: Number = 65.0
    angry_tension_hi: Number = 65.0
    angry_rhythmic_hi: Number = 60.0

    # =========================================================================
    # GENRE ADAPTATION
    # =========================================================================
    use_genre_tokens: bool = True
    genre_min_count: int = 20
    genre_weight: Number = 0.4

    # =========================================================================
    # INTENSITY THRESHOLDS
    # =========================================================================
    intensity_p_low: Number = 33.0
    intensity_p_high: Number = 66.0


# =============================================================================
# PROTOTYPE2D - MAHALANOBIS-AWARE GAUSSIAN
# =============================================================================

@dataclass
class Prototype2D:
    """
    2D Gaussian prototype with covariance for Mahalanobis distance.
    
    WHY MAHALANOBIS?
    Standard Euclidean distance assumes circular clusters. In VA space,
    emotion clusters are elliptical and correlated (e.g., "sad" songs
    tend to have correlated low V and low A). Mahalanobis distance
    accounts for this elliptical shape and correlation.
    
    Attributes:
        mu_v: Mean valence
        mu_a: Mean arousal
        std_v: Standard deviation of valence
        std_a: Standard deviation of arousal
        cov_va: Covariance between V and A (captures correlation)
    """
    mu_v: Number
    mu_a: Number
    std_v: Number
    std_a: Number
    cov_va: Number = 0.0

    def log_likelihood_diag(self, v: Number, a: Number) -> Number:
        """Diagonal Gaussian log-likelihood (original, assumes no correlation)."""
        sv = max(1e-6, self.std_v)
        sa = max(1e-6, self.std_a)
        zv = (v - self.mu_v) / sv
        za = (a - self.mu_a) / sa
        return -0.5 * (zv * zv + za * za) - math.log(sv) - math.log(sa)

    def log_likelihood_full(self, v: Number, a: Number) -> Number:
        """
        Full 2D Gaussian with covariance (Mahalanobis-aware).
        
        This is the FROZEN v5.2 method for computing likelihood.
        Handles diagonal emotions like sad↔stress properly by
        accounting for the correlation structure.
        """
        sv = max(1e-6, self.std_v)
        sa = max(1e-6, self.std_a)
        rho = clamp(self.cov_va / (sv * sa + 1e-6), -0.99, 0.99)

        dv = v - self.mu_v
        da = a - self.mu_a

        # Mahalanobis distance with correlation
        det_factor = 1 - rho * rho
        if det_factor < 1e-6:
            det_factor = 1e-6

        z = (dv**2 / sv**2 - 2*rho*dv*da/(sv*sa) + da**2/sa**2) / det_factor
        log_det = math.log(sv) + math.log(sa) + 0.5 * math.log(det_factor)

        return -0.5 * z - log_det


# =============================================================================
# MOOD ENGINE v5.2
# =============================================================================

class MoodEngine:
    """
    Mood prediction engine v5.2 with forensic-level fixes.
    
    This is the Perception Layer of the Music Chatbot Backend.
    It analyzes individual tracks and computes mood metrics.
    
    Key Features:
        - Valence/Arousal computation with proper semantic separation
        - Context-aware acoustic penalty (v5.2)
        - Kinetic zero-floor to prevent zero arousal (v5.2)
        - VA space rotation for diagonal emotions
        - Mahalanobis-aware prototype matching
        - Genre-adaptive prototype blending
        - Entropy-based confidence penalty
    
    Usage:
        engine = MoodEngine()
        engine.fit(songs)  # Optional: fit on corpus for better prototypes
        result = engine.predict(song)
    """

    def __init__(self, cfg: Optional[EngineConfig] = None):
        self.cfg = cfg or EngineConfig()

        # Learned bounds
        self._tempo_low: Optional[Number] = None
        self._tempo_high: Optional[Number] = None
        self.valence_mid: Number = 50.0
        self.arousal_mid: Number = 50.0
        self.intensity_low: Number = 33.0
        self.intensity_high: Number = 66.0

        # Precompute rotation matrix for VA space (FROZEN: 12 degrees)
        theta = math.radians(self.cfg.va_rotation_degrees)
        self._cos_theta = math.cos(theta)
        self._sin_theta = math.sin(theta)

        # Prototypes - initialize with defaults
        self.global_protos: Dict[str, Prototype2D] = {m: self._default_proto(m) for m in MOODS}
        self.token_protos: Dict[str, Dict[str, Prototype2D]] = {}
        self.token_counts: Dict[str, int] = {}

    # =========================================================================
    # NORMALIZATION HELPERS
    # =========================================================================

    def tempo_score(self, tempo: Optional[Number]) -> Number:
        """Normalize tempo to 0-100."""
        t = _to_float(tempo)
        if t is None or t <= 0:
            t = (self.cfg.tempo_abs_low + self.cfg.tempo_abs_high) / 2.0
        if self._tempo_low is not None and self._tempo_high is not None:
            return robust_minmax(t, self._tempo_low, self._tempo_high)
        return robust_minmax(t, self.cfg.tempo_abs_low, self.cfg.tempo_abs_high)

    def loudness_score(self, loudness: Optional[Number]) -> Number:
        """
        Normalize loudness dBFS to 0-100.
        
        This produces normalized_loudness which should be used throughout
        the pipeline instead of raw dB values.
        """
        return normalize_loudness_to_0_100(
            _to_float(loudness),
            db_floor=self.cfg.loudness_db_floor,
            db_ceil=self.cfg.loudness_db_ceil,
        )

    def _detect_halftime(self, tempo: Number, energy: Number) -> Number:
        """
        Detect halftime feel (low BPM but high energy).
        
        Trap, metal halftime songs have slow BPM but high perceived energy.
        This adjusts the effective tempo for arousal calculation.
        """
        if (tempo < self.cfg.halftime_tempo_threshold and
            energy > self.cfg.halftime_energy_threshold):
            return tempo * self.cfg.halftime_multiplier
        return tempo

    def _get_key_bias(self, key: Optional[Number], mode: Optional[Number]) -> Number:
        """
        Get Camelot/Key emotional bias based on music theory.
        
        Minor keys tend darker, major keys brighter.
        Returns valence adjustment (-8 to +8).
        """
        if key is None:
            return 0.0

        key_int = int(key) % 12
        base_bias = CAMELOT_VALENCE_BIAS.get(key_int, 0)

        if mode == 1:  # Major mode adds extra brightness
            major_boost = CAMELOT_MAJOR_BOOST.get(key_int, 0)
            return clamp(base_bias + major_boost, -8, 8)

        return clamp(base_bias, -8, 8)

    def _rotate_va(self, v: Number, a: Number) -> Tuple[Number, Number]:
        """
        Rotate VA space to handle diagonal emotions.
        
        WHY ROTATE?
        In Russell's Circumplex Model, emotions like sad and stress are
        positioned on a diagonal, not axis-aligned. By rotating ~12°,
        we better separate these emotions for classification.
        
        The rotation is centered at (50, 50) - the neutral point.
        """
        v_c = v - 50
        a_c = a - 50
        v_rot = v_c * self._cos_theta - a_c * self._sin_theta
        a_rot = v_c * self._sin_theta + a_c * self._cos_theta
        return v_rot + 50, a_rot + 50

    def _get_acoustic_penalty(self, genre: Optional[str]) -> Number:
        """
        v5.2 FROZEN LOGIC: Context-aware acoustic penalty.
        
        Orchestral/classical genres get REDUCED penalty (0.1) because
        they can be acoustic but still high-energy (epic film scores).
        Other genres get standard penalty (0.3).
        """
        if genre is None:
            return self.cfg.acoustic_loudness_scale
        
        genre_lower = genre.lower()
        for orch_genre in ORCHESTRAL_GENRES:
            if orch_genre in genre_lower:
                return self.cfg.acoustic_orchestral_scale
        
        return self.cfg.acoustic_loudness_scale

    # =========================================================================
    # VALENCE SCORE v5.0
    # =========================================================================

    def valence_score(self, song: Union[Song, SongDict]) -> Number:
        """
        Calculate valence score with proper semantic separation.
        
        v5.0 Fixes:
        - Spotify valence (emotional) vs TuneBat happiness (affective) separated
        - Mode: +8/-4 slope, not +50/-20 offset (prevents mode dominance)
        - Camelot/Key adds harmonic emotion bias
        """
        # Handle both Song dataclass and dict
        if isinstance(song, Song):
            song_dict = song.to_legacy_dict()
        else:
            song_dict = song

        # === CORE EMOTIONAL VALENCE (Spotify) ===
        spotify_valence = _to_float(song_dict.get("valence"))
        tunebat_happiness = _to_float(song_dict.get("happiness"))

        if spotify_valence is not None:
            emotional_valence = coerce_0_100(spotify_valence, default=50.0)
        elif tunebat_happiness is not None:
            emotional_valence = coerce_0_100(tunebat_happiness, default=50.0)
        else:
            emotional_valence = 50.0

        # === AFFECTIVE POSITIVITY (TuneBat happiness) ===
        if tunebat_happiness is not None:
            affective_positivity = coerce_0_100(tunebat_happiness, default=50.0)
        else:
            affective_positivity = emotional_valence

        # === DANCEABILITY ===
        dance = coerce_0_100(_to_float(song_dict.get("danceability")), default=50.0)

        # === MODE: SLOPE NOT OFFSET ===
        mode = _to_float(song_dict.get("mode"))
        mode_contrib = 0.0
        if mode is not None:
            mode_contrib = self.cfg.mode_major_boost if mode == 1 else self.cfg.mode_minor_penalty

        # === CAMELOT/KEY HARMONIC BIAS ===
        key = _to_float(song_dict.get("key"))
        key_bias = self._get_key_bias(key, mode)

        # v5.1: Clamp combined harmonic bias to ±10
        harmonic_bias = clamp(mode_contrib + key_bias, -10, 10)

        # === MELODIC BRIGHTNESS ===
        brightness = coerce_0_100(_to_float(song_dict.get("melodic_brightness")), default=50.0)
        brightness_contrib = (brightness - 50.0) * 0.5

        # === NOSTALGIA (bittersweet) ===
        nostalgia = coerce_0_100(_to_float(song_dict.get("nostalgia_factor")), default=40.0)
        nostalgia_contrib = (45.0 - nostalgia) * 0.2

        # === RELEASE SATISFACTION ===
        satisfaction = coerce_0_100(_to_float(song_dict.get("release_satisfaction")), default=50.0)
        satisfaction_contrib = (satisfaction - 50.0) * 0.4

        # === COMBINE ===
        v = (
            self.cfg.w_valence_core * emotional_valence
            + self.cfg.w_positivity * affective_positivity
            + self.cfg.w_valence_dance * dance
            + (self.cfg.w_valence_mode + self.cfg.w_valence_key) * harmonic_bias
            + self.cfg.w_valence_brightness * brightness_contrib
            + self.cfg.w_valence_nostalgia * nostalgia_contrib
            + self.cfg.w_valence_satisfaction * satisfaction_contrib
        )

        return clamp(v, 0.0, 100.0)

    # =========================================================================
    # AROUSAL SCORE v5.2
    # =========================================================================

    def arousal_score(self, song: Union[Song, SongDict]) -> Number:
        """
        Calculate arousal score with interaction terms.
        
        v5.2 FROZEN LOGIC:
        1. Context-aware acoustic penalty (orchestral = 0.1, others = 0.3)
        2. Kinetic zero-floor: dance_safe = max(dance, 25)
        """
        if isinstance(song, Song):
            song_dict = song.to_legacy_dict()
        else:
            song_dict = song

        energy = coerce_0_100(_to_float(song_dict.get("energy")), default=50.0)
        raw_tempo = _to_float(song_dict.get("tempo")) or 120
        dance = coerce_0_100(_to_float(song_dict.get("danceability")), default=50.0)
        acoustic = coerce_0_100(_to_float(song_dict.get("acousticness")), default=50.0)
        liveness = coerce_0_100(_to_float(song_dict.get("liveness")), default=10.0)

        # === HALFTIME DETECTION ===
        adjusted_tempo = self._detect_halftime(raw_tempo, energy)
        tempo = self.tempo_score(adjusted_tempo)

        # === LOUDNESS with CONTEXT-AWARE ACOUSTIC SCALING (v5.2 FROZEN) ===
        raw_loudness = self.loudness_score(_to_float(song_dict.get("loudness")))
        acoustic_penalty = self._get_acoustic_penalty(song_dict.get("genre"))
        acoustic_factor = 1 - acoustic_penalty * (acoustic / 100.0)
        effective_loudness = raw_loudness * acoustic_factor

        # === KINETIC INTERACTION TERM (v5.2 FROZEN: zero-floor at 25) ===
        # High tempo + low dance should still have some kinetic energy
        dance_safe = max(dance, self.cfg.kinetic_dance_floor * 100)  # At least 25
        kinetic = math.sqrt(tempo * dance_safe) / 10.0

        # === TENSION ===
        tension = coerce_0_100(_to_float(song_dict.get("tension_level")), default=50.0)

        # === GROOVE (modulates effective dance) ===
        groove = coerce_0_100(_to_float(song_dict.get("groove_factor")), default=50.0)
        groove_multiplier = 0.7 + (groove / 200.0)
        effective_dance = dance * groove_multiplier

        # === ENERGY BUILDUP ===
        buildup = coerce_0_100(_to_float(song_dict.get("energy_buildup")), default=50.0)

        # === RHYTHMIC COMPLEXITY ===
        rhythmic = coerce_0_100(_to_float(song_dict.get("rhythmic_complexity")), default=50.0)

        # === COMBINE ===
        a = (
            self.cfg.w_energy * energy
            + self.cfg.w_kinetic * kinetic
            + self.cfg.w_tempo * tempo
            + self.cfg.w_loudness * effective_loudness
            + self.cfg.w_dance_arousal * effective_dance
            + self.cfg.w_liveness * liveness
            + self.cfg.w_tension * tension
            + self.cfg.w_energy_buildup * buildup
            + self.cfg.w_rhythmic_complexity * rhythmic
        )

        return clamp(a, 0.0, 100.0)

    # =========================================================================
    # EFFECTIVE DANCEABILITY (Kinetic-aware)
    # =========================================================================

    def effective_danceability(self, song: Union[Song, SongDict]) -> Number:
        """
        Calculate kinetic-aware danceability.
        
        Combines raw danceability with groove factor for a more
        accurate measure of "danceability in context".
        """
        if isinstance(song, Song):
            song_dict = song.to_legacy_dict()
        else:
            song_dict = song

        dance = coerce_0_100(_to_float(song_dict.get("danceability")), default=50.0)
        groove = coerce_0_100(_to_float(song_dict.get("groove_factor")), default=50.0)
        
        # v5.2 FROZEN: zero-floor
        dance_safe = max(dance, self.cfg.kinetic_dance_floor * 100)
        
        # Groove modulation
        groove_multiplier = 0.7 + (groove / 200.0)
        return clamp(dance_safe * groove_multiplier, 0.0, 100.0)

    # =========================================================================
    # WEAK LABELING v5.0
    # =========================================================================

    def _weak_label(self, song: Union[Song, SongDict], v: Number, a: Number) -> str:
        """
        Bootstrap weak labels based on VA position.
        
        v5.0: 
        - VA rotation for better diagonal emotion separation
        - Rhythmic complexity for metal slow-but-angry detection
        """
        if isinstance(song, Song):
            song_dict = song.to_legacy_dict()
        else:
            song_dict = song

        # Rotate VA space for better diagonal emotion separation
        v_rot, a_rot = self._rotate_va(v, a)

        v_hi = v_rot >= self.valence_mid
        a_hi = a_rot >= self.arousal_mid

        if v_hi and a_hi:
            return "energetic"
        if v_hi and not a_hi:
            return "happy"
        if (not v_hi) and (not a_hi):
            return "sad"

        # (-V, +A): stress vs angry
        loud = self.loudness_score(_to_float(song_dict.get("loudness")))
        tempo = self.tempo_score(_to_float(song_dict.get("tempo")))
        tension = coerce_0_100(_to_float(song_dict.get("tension_level")), default=50.0)
        rhythmic = coerce_0_100(_to_float(song_dict.get("rhythmic_complexity")), default=50.0)
        
        # Angry detection with rhythmic complexity (for slow doom metal)
        angry_score = 0.0
        if tension >= self.cfg.angry_tension_hi:
            angry_score += 1.5
        if rhythmic >= self.cfg.angry_rhythmic_hi:
            angry_score += 1.5
        if loud >= self.cfg.angry_loudness_hi:
            angry_score += 1.0
        if tempo >= self.cfg.angry_tempo_hi:
            angry_score += 1.0

        if angry_score >= 3.0:
            return "angry"

        # Slow doom metal fallback
        if tension >= 70 and rhythmic >= 60:
            return "angry"

        return "stress"

    # =========================================================================
    # PROTOTYPE FITTING
    # =========================================================================

    def _default_proto(self, mood: str) -> Prototype2D:
        """Default Gaussian prototype centers with covariance."""
        centers = {
            "energetic": (70.0, 75.0, 0.3),
            "happy": (70.0, 35.0, -0.1),
            "sad": (30.0, 30.0, 0.4),
            "stress": (30.0, 70.0, -0.3),
            "angry": (20.0, 85.0, 0.2),
        }
        mu_v, mu_a, corr = centers.get(mood, (50.0, 50.0, 0.0))
        s = self.cfg.proto_min_std
        cov = corr * s * s
        return Prototype2D(mu_v, mu_a, s, s, cov)

    def _fit_protos(self, points_by_mood: Dict[str, List[Tuple[Number, Number]]]) -> Dict[str, Prototype2D]:
        """Fit Gaussian prototypes with covariance for Mahalanobis distance."""
        protos: Dict[str, Prototype2D] = {}
        for mood in MOODS:
            pts = points_by_mood.get(mood, [])
            if len(pts) < 5:
                protos[mood] = self._default_proto(mood)
                continue

            vs = [p[0] for p in pts]
            as_ = [p[1] for p in pts]
            n = len(pts)

            mu_v = sum(vs) / n
            mu_a = sum(as_) / n

            var_v = sum((x - mu_v) ** 2 for x in vs) / max(1, n - 1)
            var_a = sum((x - mu_a) ** 2 for x in as_) / max(1, n - 1)
            cov_va = sum((vs[i] - mu_v) * (as_[i] - mu_a) for i in range(n)) / max(1, n - 1)

            std_v = max(self.cfg.proto_min_std, math.sqrt(var_v))
            std_a = max(self.cfg.proto_min_std, math.sqrt(var_a))

            protos[mood] = Prototype2D(mu_v, mu_a, std_v, std_a, cov_va)

        return protos

    def fit(self, songs: Iterable[Union[Song, SongDict]]) -> "MoodEngine":
        """
        Fit engine on song corpus to learn better prototypes.
        
        Args:
            songs: Iterable of Song objects or dicts
        
        Returns:
            self for chaining
        """
        songs_list = list(songs)
        if not songs_list:
            self.global_protos = {m: self._default_proto(m) for m in MOODS}
            self.token_protos = {}
            self.token_counts = {}
            return self

        # 1) Tempo bounds
        tempos = []
        for s in songs_list:
            if isinstance(s, Song):
                t = s.tempo
            else:
                t = _to_float(s.get("tempo"))
            if t is not None and t > 0:
                tempos.append(t)
        
        if tempos:
            lo = percentile(tempos, self.cfg.tempo_p_low)
            hi = percentile(tempos, self.cfg.tempo_p_high)
            lo = clamp(lo, 1.0, 300.0)
            hi = clamp(hi, 1.0, 300.0)
            if hi > lo:
                self._tempo_low, self._tempo_high = lo, hi

        # 2) Learn mids + intensity cutoffs
        Vs: List[Number] = []
        As: List[Number] = []
        for s in songs_list:
            Vs.append(self.valence_score(s))
            As.append(self.arousal_score(s))
        
        if Vs:
            self.valence_mid = percentile(Vs, 50.0)
        if As:
            self.arousal_mid = percentile(As, 50.0)
            self.intensity_low = percentile(As, self.cfg.intensity_p_low)
            self.intensity_high = percentile(As, self.cfg.intensity_p_high)

        # 3) Bootstrap labels, then fit global + token prototypes
        global_points: Dict[str, List[Tuple[Number, Number]]] = {m: [] for m in MOODS}
        token_points: Dict[str, Dict[str, List[Tuple[Number, Number]]]] = {}
        token_counts: Dict[str, int] = {}

        for s in songs_list:
            v = self.valence_score(s)
            a = self.arousal_score(s)
            y = self._weak_label(s, v, a)
            global_points[y].append((v, a))

            if self.cfg.use_genre_tokens:
                genre = s.genre if isinstance(s, Song) else s.get("genre")
                for tok in tokenize_genre(genre):
                    token_counts[tok] = token_counts.get(tok, 0) + 1
                    if tok not in token_points:
                        token_points[tok] = {m: [] for m in MOODS}
                    token_points[tok][y].append((v, a))

        self.global_protos = self._fit_protos(global_points)
        self.token_counts = token_counts
        self.token_protos = {}

        if self.cfg.use_genre_tokens:
            for tok, pts_by_mood in token_points.items():
                if token_counts.get(tok, 0) >= int(self.cfg.genre_min_count):
                    self.token_protos[tok] = self._fit_protos(pts_by_mood)

        return self

    # =========================================================================
    # INFERENCE
    # =========================================================================

    def infer_intensity_int(self, arousal: Number) -> int:
        """Map arousal to intensity level 1-3."""
        if arousal >= self.intensity_high:
            return 3
        if arousal >= self.intensity_low:
            return 2
        return 1

    def _entropy(self, probs: Dict[str, Number]) -> Number:
        """Compute entropy of probability distribution."""
        entropy = 0.0
        for p in probs.values():
            if p > 1e-10:
                entropy -= p * math.log(p)
        return entropy

    def _probs_from_protos(self, protos: Dict[str, Prototype2D], v: Number, a: Number) -> Dict[str, Number]:
        """Compute mood probabilities using full likelihood with covariance."""
        logits = {m: protos[m].log_likelihood_full(v, a) for m in MOODS}
        return softmax(logits, temperature=self.cfg.proto_temperature)

    def mood_probabilities(self, song: Union[Song, SongDict], v: Number, a: Number) -> Dict[str, Number]:
        """Get mood probabilities with genre blending."""
        global_probs = self._probs_from_protos(self.global_protos, v, a)

        if not self.cfg.use_genre_tokens:
            return global_probs

        genre = song.genre if isinstance(song, Song) else song.get("genre")
        tokens = tokenize_genre(genre)
        token_probs_list: List[Dict[str, Number]] = []
        
        for tok in tokens:
            if tok in self.token_protos and self.token_counts.get(tok, 0) >= int(self.cfg.genre_min_count):
                token_probs_list.append(self._probs_from_protos(self.token_protos[tok], v, a))

        if not token_probs_list:
            return global_probs

        # Average token probs
        avg_token_probs: Dict[str, Number] = {m: 0.0 for m in MOODS}
        for p in token_probs_list:
            for m in MOODS:
                avg_token_probs[m] += p[m]
        n = float(len(token_probs_list))
        for m in MOODS:
            avg_token_probs[m] /= n

        # Scale genre weight by entropy
        token_entropy = self._entropy(avg_token_probs)
        max_entropy = math.log(len(MOODS))
        entropy_ratio = token_entropy / max_entropy if max_entropy > 0 else 1.0
        adjusted_weight = self.cfg.genre_weight * (0.5 + 0.5 * entropy_ratio)
        
        w = clamp(float(adjusted_weight), 0.0, 1.0)
        blended = {m: (1.0 - w) * global_probs[m] + w * avg_token_probs[m] for m in MOODS}
        s = sum(blended.values()) or 1.0
        return {m: blended[m] / s for m in MOODS}

    def predict(self, song: Union[Song, SongDict]) -> Dict[str, object]:
        """
        Full mood prediction with all v5.2 enhancements.
        
        Returns:
            Dict containing:
            - Core metrics: valence_score, arousal_score, mood, confidence, intensity
            - Human-readable labels (semantic buckets)
            - Mood probabilities for all moods
            - Advanced metrics
            - normalized_loudness, effective_danceability (computed metrics)
        """
        if isinstance(song, Song):
            song_dict = song.to_legacy_dict()
        else:
            song_dict = song

        v = self.valence_score(song_dict)
        a = self.arousal_score(song_dict)

        probs = self.mood_probabilities(song_dict, v, a)
        mood = max(probs, key=probs.get)
        conf = float(probs[mood])

        # === ENTROPY-BASED CONFIDENCE PENALTY ===
        if self.cfg.use_entropy_penalty:
            entropy = self._entropy(probs)
            max_entropy = math.log(len(MOODS))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            conf *= (1 - self.cfg.entropy_penalty_factor * normalized_entropy)

        # === EMOTIONAL DEPTH BOOST ===
        emotional_depth = _to_float(song_dict.get("emotional_depth"))
        if self.cfg.use_emotional_depth and emotional_depth is not None:
            depth_factor = (emotional_depth - 50) / 100.0
            conf = clamp(conf + depth_factor * self.cfg.depth_confidence_boost, 0.0, 1.0)

        # === MOOD STABILITY ADJUSTMENT ===
        mood_stability = _to_float(song_dict.get("mood_stability"))
        if self.cfg.use_mood_stability and mood_stability is not None:
            if mood_stability > 75 and mood in ("stress", "angry"):
                alt_probs = {m: p for m, p in probs.items() if m not in ("stress", "angry")}
                if alt_probs:
                    alt_mood = max(alt_probs, key=alt_probs.get)
                    if probs[alt_mood] > conf * 0.65:
                        mood = alt_mood
                        conf = float(probs[mood])

        # === ADVANCED FEATURES FINE-TUNING ===
        if self.cfg.use_advanced_features:
            harmonic_comp = _to_float(song_dict.get("harmonic_complexity"))
            if harmonic_comp is not None and harmonic_comp > 60:
                if mood in ("stress", "sad"):
                    conf = clamp(conf + 0.02, 0.0, 1.0)

            volatility = _to_float(song_dict.get("emotional_volatility"))
            if volatility is not None and volatility > 70:
                conf = clamp(conf - 0.015, 0.0, 1.0)

            atmospheric = _to_float(song_dict.get("atmospheric_depth"))
            if atmospheric is not None and atmospheric > 70 and mood == "stress":
                if probs.get("sad", 0) > conf * 0.55:
                    mood = "sad"
                    conf = float(probs[mood])

        intensity_int = self.infer_intensity_int(a)
        mood_score = (v + a) / 2.0

        # === HUMAN-READABLE LABELS ===
        arousal_label_vi, arousal_label_en = get_arousal_label(a)
        valence_label_vi, valence_label_en = get_valence_label(v)
        mood_description = MOOD_DESCRIPTIONS.get(mood, "")

        # === COMPUTED METRICS ===
        normalized_loud = self.loudness_score(_to_float(song_dict.get("loudness")))
        eff_dance = self.effective_danceability(song_dict)

        return {
            # Core metrics
            "valence_score": round(v, 2),
            "arousal_score": round(a, 2),
            "mood": mood,
            "mood_confidence": round(conf, 4),
            "intensity": intensity_int,
            "mood_score": round(mood_score, 2),

            # Computed metrics (for downstream use)
            "normalized_loudness": round(normalized_loud, 2),
            "effective_danceability": round(eff_dance, 2),

            # Human-readable labels
            "arousal_label": arousal_label_vi,
            "valence_label": valence_label_vi,
            "arousal_label_en": arousal_label_en,
            "valence_label_en": valence_label_en,
            "mood_description": mood_description,

            # Probabilities
            "mood_probabilities": {m: round(p, 4) for m, p in probs.items()},

            # Advanced metrics pass-through
            "emotional_depth": emotional_depth,
            "mood_stability": mood_stability,
            "tension_level": _to_float(song_dict.get("tension_level")),
            "groove_factor": _to_float(song_dict.get("groove_factor")),
            "harmonic_complexity": _to_float(song_dict.get("harmonic_complexity")),
            "rhythmic_complexity": _to_float(song_dict.get("rhythmic_complexity")),

            # Context scores
            "morning_score": _to_float(song_dict.get("morning_score")),
            "evening_score": _to_float(song_dict.get("evening_score")),
            "workout_score": _to_float(song_dict.get("workout_score")),
            "focus_score": _to_float(song_dict.get("focus_score")),
            "relax_score": _to_float(song_dict.get("relax_score")),
            "party_score": _to_float(song_dict.get("party_score")),
        }

    def predict_song(self, song: Song) -> Song:
        """
        Predict and update a Song object with computed metrics.
        
        This is the preferred method for the Phase 2 pipeline.
        Returns a new Song with all computed fields populated.
        """
        result = self.predict(song)
        
        # Update Song with computed metrics
        song.valence_score = result["valence_score"]
        song.arousal_score = result["arousal_score"]
        song.mood_label = result["mood"]
        song.mood_confidence = result["mood_confidence"]
        song.intensity = result["intensity"]
        song.normalized_loudness = result["normalized_loudness"]
        song.effective_danceability = result["effective_danceability"]
        
        return song
