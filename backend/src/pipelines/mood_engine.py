"""
Mood Engine v5.2 - Production-ready affective inference engine
Based on MIR (Music Information Retrieval) best practices.

v5.0 Fixes:
1. Valence ≠ Happiness semantic separation
2. Mode handling: slope not offset (+8/-4 instead of +50/-20)
3. Acousticness: scales loudness, not subtract arousal
4. Camelot/Key bias for harmonic emotion
5. Energy de-coupled, interaction terms added (kinetic)
6. Halftime/doubletime BPM detection
7. Groove modulates danceability
8. Rhythmic complexity for angry detection
9. Human-readable semantic buckets
10. Entropy-based confidence penalty
11. Mahalanobis-aware prototype distance with covariance
12. VA space rotation for diagonal emotions (sad↔stress)

v5.1 Tweaks:
13. Kinetic term scaled down (/10) to avoid dominance
14. Harmonic bias (mode+key) clamped to ±10
15. Angry detection: tension+rhythmic weighted 1.5x (slow doom metal fix)
16. Genre token weight scaled by prototype entropy

v5.2 Production:
17. Context-aware acousticness (orchestral/classical penalty reduced)
18. Kinetic zero-floor (dance_safe >= 0.25 to avoid zero arousal)
19. NarrativeAdapter for human-readable explanations
20. Explanation tags for chatbot integration
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Iterable
import math

from backend.src.services.helpers import (
    _is_missing, _to_float, clamp, percentile, robust_minmax,
    coerce_0_100, normalize_loudness_to_0_100, softmax, tokenize_genre
)
from backend.src.services.constants import Song, MOODS

Number = float

# =============================================================================
# CAMELOT KEY EMOTIONAL BIAS
# Minor keys (A) tend darker, Major keys (B) tend brighter
# Values: valence adjustment (-8 to +8)
# =============================================================================
CAMELOT_VALENCE_BIAS = {
    0: -4,   # C minor (5A) - neutral minor
    1: -2,   # C# minor (12A)
    2: -3,   # D minor (7A)
    3: -5,   # D# minor (2A) - darker
    4: +2,   # E minor (9A) - brighter minor
    5: -1,   # F minor (4A)
    6: -6,   # F# minor (11A) - very dark
    7: +3,   # G minor (6A) - emotional but not dark
    8: -4,   # G# minor (1A) - dark
    9: +4,   # A minor (8A) - common, bright minor
    10: -3,  # A# minor (3A)
    11: +1,  # B minor (10A)
}

CAMELOT_MAJOR_BOOST = {
    0: +6,   # C major (8B) - very bright
    1: +4,   # C# major (3B)
    2: +5,   # D major (10B) - bright
    3: +3,   # D# major (5B)
    4: +7,   # E major (12B) - very bright
    5: +4,   # F major (7B)
    6: +2,   # F# major (2B)
    7: +8,   # G major (9B) - extremely bright
    8: +3,   # G# major (4B)
    9: +5,   # A major (11B) - bright
    10: +4,  # A# major (6B)
    11: +6,  # B major (1B)
}

# =============================================================================
# SEMANTIC BUCKETS FOR HUMAN-READABLE OUTPUT
# =============================================================================
AROUSAL_LABELS = {
    (0, 25): ("rất nhẹ nhàng", "very_calm"),
    (25, 40): ("nhẹ nhàng", "calm"),
    (40, 55): ("vừa phải", "moderate"),
    (55, 70): ("sôi động", "energetic"),
    (70, 85): ("mạnh mẽ", "intense"),
    (85, 100): ("bùng nổ", "explosive"),
}

VALENCE_LABELS = {
    (0, 20): ("rất u sầu", "very_melancholic"),
    (20, 35): ("u sầu", "melancholic"),
    (35, 45): ("trầm lắng", "contemplative"),
    (45, 55): ("trung tính", "neutral"),
    (55, 65): ("ấm áp", "warm"),
    (65, 80): ("tươi sáng", "bright"),
    (80, 100): ("rực rỡ", "radiant"),
}

MOOD_DESCRIPTIONS = {
    "energetic": "đầy năng lượng, sôi động",
    "happy": "vui vẻ, tích cực",
    "sad": "buồn, trầm lắng",
    "stress": "căng thẳng, lo lắng",
    "angry": "mạnh mẽ, dữ dội",
}

# v5.2: Genres where acousticness should have reduced penalty
# These genres are naturally acoustic but can be high-energy
ORCHESTRAL_GENRES = {
    "classical", "soundtrack", "orchestral", "opera", "symphony",
    "film score", "cinematic", "epic", "trailer", "game soundtrack",
    "neo-classical", "chamber", "baroque", "romantic", "contemporary classical",
    "flamenco", "acoustic rock", "unplugged", "live"
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


@dataclass
class EngineConfig:
    """v5.0 Configuration - Forensic-level tuned weights."""
    
    # Tempo normalization
    tempo_p_low: Number = 5.0
    tempo_p_high: Number = 95.0
    tempo_abs_low: Number = 50.0
    tempo_abs_high: Number = 200.0

    # Loudness dBFS normalization
    loudness_db_floor: Number = -60.0
    loudness_db_ceil: Number = 0.0

    # =========================================================================
    # AROUSAL WEIGHTS v5.0
    # - Reduced energy (was double-counting tempo+loudness)
    # - Added kinetic interaction term: sqrt(tempo * danceability)
    # - Acousticness now scales loudness, not subtract
    # =========================================================================
    w_energy: Number = 0.22          # Reduced from 0.32 (avoid double-count)
    w_kinetic: Number = 0.18         # v5.1: increased (kinetic now /10 scaled)
    w_tempo: Number = 0.10           # Reduced, tempo already in energy
    w_loudness: Number = 0.16
    w_dance_arousal: Number = 0.08
    w_liveness: Number = 0.06
    w_tension: Number = 0.10
    w_groove: Number = 0.08          # Increased, modulates dance
    w_energy_buildup: Number = 0.06
    w_rhythmic_complexity: Number = 0.08  # NEW: for angry detection

    # Acoustic loudness scaling (NOT subtract from arousal)
    acoustic_loudness_scale: Number = 0.3  # effective_loud = loud * (1 - 0.3*acoustic)
    acoustic_orchestral_scale: Number = 0.1  # v5.2: Reduced penalty for orchestral genres

    # v5.2: Kinetic zero-floor to prevent zero arousal
    kinetic_dance_floor: Number = 0.25  # min(dance, 0.25) for kinetic calc

    # =========================================================================
    # VALENCE WEIGHTS v5.0
    # - Separated spotify valence vs tunebat happiness
    # - Mode: slope not offset (+8/-4 instead of +50/-20)
    # - Added Camelot/Key bias
    # =========================================================================
    w_valence_core: Number = 0.50    # Spotify valence (emotional valence)
    w_positivity: Number = 0.15      # Tunebat happiness (affective positivity)
    w_valence_dance: Number = 0.08
    w_valence_mode: Number = 0.06    # Reduced, slope not offset
    w_valence_key: Number = 0.05     # NEW: Camelot key bias
    w_valence_brightness: Number = 0.06
    w_valence_nostalgia: Number = 0.04
    w_valence_satisfaction: Number = 0.06

    # Mode adjustment: slope not offset
    mode_major_boost: Number = 8.0     # Was +50, now +8
    mode_minor_penalty: Number = -4.0  # Was -20, now -4

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
    depth_confidence_boost: Number = 0.12  # Reduced from 0.15

    use_mood_stability: bool = True
    stability_weight: Number = 0.08

    # =========================================================================
    # ADVANCED FEATURES v5.0
    # =========================================================================
    use_advanced_features: bool = True
    harmonic_complexity_weight: Number = 0.04
    atmospheric_weight: Number = 0.03
    volatility_weight: Number = 0.05

    # =========================================================================
    # ENTROPY-BASED CONFIDENCE PENALTY
    # Reduces confidence for ambiguous predictions
    # =========================================================================
    use_entropy_penalty: bool = True
    entropy_penalty_factor: Number = 0.4  # conf *= (1 - factor * normalized_entropy)

    # =========================================================================
    # PROTOTYPE TRAINING
    # =========================================================================
    proto_min_std: Number = 8.0
    proto_temperature: Number = 1.0

    # VA space rotation for diagonal emotions (sad↔stress)
    va_rotation_degrees: Number = 12.0  # Rotate VA space ~12°

    # =========================================================================
    # WEAK-LABEL ANGRY THRESHOLDS
    # Added rhythmic_complexity for slow but angry detection
    # =========================================================================
    angry_loudness_hi: Number = 70.0
    angry_tempo_hi: Number = 65.0
    angry_tension_hi: Number = 65.0
    angry_rhythmic_hi: Number = 60.0  # NEW: for metal slow but angry

    # Genre adaptation
    use_genre_tokens: bool = True
    genre_min_count: int = 20
    genre_weight: Number = 0.4

    # Intensity thresholds
    intensity_p_low: Number = 33.0
    intensity_p_high: Number = 66.0


@dataclass
class Prototype2D:
    """2D Gaussian prototype with covariance for Mahalanobis distance."""
    mu_v: Number
    mu_a: Number
    std_v: Number
    std_a: Number
    cov_va: Number = 0.0  # Covariance between V and A

    def log_likelihood_diag(self, v: Number, a: Number) -> Number:
        """Diagonal Gaussian log-likelihood (original)."""
        sv = max(1e-6, self.std_v)
        sa = max(1e-6, self.std_a)
        zv = (v - self.mu_v) / sv
        za = (a - self.mu_a) / sa
        return -0.5 * (zv * zv + za * za) - math.log(sv) - math.log(sa)

    def log_likelihood_full(self, v: Number, a: Number) -> Number:
        """
        Full 2D Gaussian with covariance (Mahalanobis-aware).
        Handles diagonal emotions like sad↔stress properly.
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


class MoodEngine:
    """Mood prediction engine v5.2 with forensic-level fixes."""

    def __init__(self, cfg: Optional[EngineConfig] = None):
        self.cfg = cfg or EngineConfig()

        # learned bounds / thresholds
        self._tempo_low: Optional[Number] = None
        self._tempo_high: Optional[Number] = None
        self.valence_mid: Number = 50.0
        self.arousal_mid: Number = 50.0
        self.intensity_low: Number = 33.0
        self.intensity_high: Number = 66.0

        # Precompute rotation matrix for VA space (diagonal emotions)
        theta = math.radians(self.cfg.va_rotation_degrees)
        self._cos_theta = math.cos(theta)
        self._sin_theta = math.sin(theta)

        # prototypes - initialize with defaults for unfitted usage
        self.global_protos: Dict[str, Prototype2D] = {m: self._default_proto(m) for m in MOODS}
        self.token_protos: Dict[str, Dict[str, Prototype2D]] = {}
        self.token_counts: Dict[str, int] = {}

    # =========================================================================
    # HELPER METHODS
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
        """Normalize loudness dBFS to 0-100."""
        return normalize_loudness_to_0_100(
            _to_float(loudness),
            db_floor=self.cfg.loudness_db_floor,
            db_ceil=self.cfg.loudness_db_ceil,
        )

    def _detect_halftime(self, tempo: Number, energy: Number) -> Number:
        """
        Detect halftime feel (low BPM but high energy).
        Trap, metal halftime → multiply tempo.
        """
        if (tempo < self.cfg.halftime_tempo_threshold and
            energy > self.cfg.halftime_energy_threshold):
            return tempo * self.cfg.halftime_multiplier
        return tempo

    def _get_key_bias(self, key: Optional[Number], mode: Optional[Number]) -> Number:
        """
        Get Camelot/Key emotional bias based on music theory.
        Returns valence adjustment (-8 to +8).
        """
        if key is None:
            return 0.0

        key_int = int(key) % 12
        base_bias = CAMELOT_VALENCE_BIAS.get(key_int, 0)

        # Major mode adds extra brightness
        if mode == 1:
            major_boost = CAMELOT_MAJOR_BOOST.get(key_int, 0)
            return clamp(base_bias + major_boost, -8, 8)

        return clamp(base_bias, -8, 8)

    def _rotate_va(self, v: Number, a: Number) -> Tuple[Number, Number]:
        """
        Rotate VA space to handle diagonal emotions.
        Sad↔Stress are on a diagonal, not axis-aligned.
        """
        v_c = v - 50
        a_c = a - 50
        v_rot = v_c * self._cos_theta - a_c * self._sin_theta
        a_rot = v_c * self._sin_theta + a_c * self._cos_theta
        return v_rot + 50, a_rot + 50

    def _get_acoustic_penalty(self, genre: Optional[str]) -> Number:
        """
        v5.2: Context-aware acoustic penalty.
        Orchestral/classical genres get reduced penalty because
        they can be acoustic but still high-energy.
        """
        if genre is None:
            return self.cfg.acoustic_loudness_scale
        
        # Tokenize and check for orchestral genres
        genre_lower = genre.lower()
        for orch_genre in ORCHESTRAL_GENRES:
            if orch_genre in genre_lower:
                return self.cfg.acoustic_orchestral_scale
        
        return self.cfg.acoustic_loudness_scale

    # =========================================================================
    # VALENCE SCORE v5.0
    # - Spotify valence ≠ Tunebat happiness (semantic separation)
    # - Mode: slope +8/-4, not offset +50/-20
    # - Camelot/Key harmonic emotion bias
    # =========================================================================

    def valence_score(self, song: Song) -> Number:
        """
        Calculate valence score with proper semantic separation.
        
        v5.0 Fixes:
        - Spotify valence (emotional) vs Tunebat happiness (affective) separated
        - Mode: +8/-4 slope, not +50/-20 offset
        - Camelot/Key adds harmonic emotion bias
        """
        # === CORE EMOTIONAL VALENCE (Spotify) ===
        spotify_valence = _to_float(song.get("valence"))
        tunebat_happiness = _to_float(song.get("happiness"))

        # Prefer Spotify valence for emotional valence
        if spotify_valence is not None:
            emotional_valence = coerce_0_100(spotify_valence, default=50.0)
        elif tunebat_happiness is not None:
            emotional_valence = coerce_0_100(tunebat_happiness, default=50.0)
        else:
            emotional_valence = 50.0

        # === AFFECTIVE POSITIVITY (Tunebat happiness) ===
        # Different from emotional valence - this is "perceived pleasantness"
        if tunebat_happiness is not None:
            affective_positivity = coerce_0_100(tunebat_happiness, default=50.0)
        else:
            affective_positivity = emotional_valence

        # === DANCEABILITY ===
        dance = coerce_0_100(_to_float(song.get("danceability")), default=50.0)

        # === MODE: SLOPE NOT OFFSET ===
        mode = _to_float(song.get("mode"))
        mode_contrib = 0.0
        if mode is not None:
            # +8 for major, -4 for minor (slope, not offset!)
            mode_contrib = self.cfg.mode_major_boost if mode == 1 else self.cfg.mode_minor_penalty

        # === CAMELOT/KEY HARMONIC BIAS ===
        key = _to_float(song.get("key"))
        key_bias = self._get_key_bias(key, mode)

        # v5.1: Clamp combined harmonic bias to avoid resonance (G major + major mode)
        harmonic_bias = clamp(mode_contrib + key_bias, -10, 10)

        # === MELODIC BRIGHTNESS ===
        brightness = coerce_0_100(_to_float(song.get("melodic_brightness")), default=50.0)
        brightness_contrib = (brightness - 50.0) * 0.5

        # === NOSTALGIA (bittersweet) ===
        nostalgia = coerce_0_100(_to_float(song.get("nostalgia_factor")), default=40.0)
        nostalgia_contrib = (45.0 - nostalgia) * 0.2

        # === RELEASE SATISFACTION ===
        satisfaction = coerce_0_100(_to_float(song.get("release_satisfaction")), default=50.0)
        satisfaction_contrib = (satisfaction - 50.0) * 0.4

        # === COMBINE ===
        # v5.1: Use combined harmonic_bias instead of separate mode+key
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
    # AROUSAL SCORE v5.0
    # - Energy reduced (avoid double-counting)
    # - Kinetic interaction: sqrt(tempo * dance)
    # - Acousticness scales loudness, not subtract
    # - Halftime detection
    # =========================================================================

    def arousal_score(self, song: Song) -> Number:
        """
        Calculate arousal score with interaction terms.
        
        v5.2 Fixes:
        - Context-aware acoustic penalty (orchestral reduced)
        - Kinetic zero-floor (dance_safe >= 0.25)
        """
        energy = coerce_0_100(_to_float(song.get("energy")), default=50.0)
        raw_tempo = _to_float(song.get("tempo")) or 120
        dance = coerce_0_100(_to_float(song.get("danceability")), default=50.0)
        acoustic = coerce_0_100(_to_float(song.get("acousticness")), default=50.0)
        liveness = coerce_0_100(_to_float(song.get("liveness")), default=10.0)

        # === HALFTIME DETECTION ===
        adjusted_tempo = self._detect_halftime(raw_tempo, energy)
        tempo = self.tempo_score(adjusted_tempo)

        # === LOUDNESS with CONTEXT-AWARE ACOUSTIC SCALING ===
        # v5.2: Orchestral/classical gets reduced penalty
        raw_loudness = self.loudness_score(_to_float(song.get("loudness")))
        acoustic_penalty = self._get_acoustic_penalty(song.get("genre"))
        acoustic_factor = 1 - acoustic_penalty * (acoustic / 100.0)
        effective_loudness = raw_loudness * acoustic_factor

        # === KINETIC INTERACTION TERM ===
        # v5.2: Zero-floor to prevent kinetic = 0 when dance is low
        # High tempo + low dance should still have some kinetic energy
        dance_safe = max(dance, self.cfg.kinetic_dance_floor * 100)  # At least 25
        kinetic = math.sqrt(tempo * dance_safe) / 10.0

        # === TENSION ===
        tension = coerce_0_100(_to_float(song.get("tension_level")), default=50.0)

        # === GROOVE (modulates effective dance) ===
        groove = coerce_0_100(_to_float(song.get("groove_factor")), default=50.0)
        groove_multiplier = 0.7 + (groove / 200.0)  # 0.7 to 1.2
        effective_dance = dance * groove_multiplier

        # === ENERGY BUILDUP ===
        buildup = coerce_0_100(_to_float(song.get("energy_buildup")), default=50.0)

        # === RHYTHMIC COMPLEXITY ===
        rhythmic = coerce_0_100(_to_float(song.get("rhythmic_complexity")), default=50.0)

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
    # WEAK LABELING v5.0
    # - VA rotation for diagonal emotions
    # - Rhythmic complexity for slow-but-angry detection
    # =========================================================================

    def _weak_label(self, song: Song, v: Number, a: Number) -> str:
        """
        Bootstrap weak labels based on VA position.
        
        v5.0: 
        - VA rotation for better diagonal emotion separation
        - Rhythmic complexity for metal slow but angry
        """
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
        loud = self.loudness_score(_to_float(song.get("loudness")))
        tempo = self.tempo_score(_to_float(song.get("tempo")))
        tension = coerce_0_100(_to_float(song.get("tension_level")), default=50.0)
        rhythmic = coerce_0_100(_to_float(song.get("rhythmic_complexity")), default=50.0)
        
        # Angry detection with rhythmic complexity (for metal slow but angry)
        # v5.1: Tension+rhythmic weighted 1.5x (catches slow doom metal)
        angry_score = 0.0
        if tension >= self.cfg.angry_tension_hi:
            angry_score += 1.5  # Tension is key indicator
        if rhythmic >= self.cfg.angry_rhythmic_hi:
            angry_score += 1.5  # Rhythmic catches slow angry
        if loud >= self.cfg.angry_loudness_hi:
            angry_score += 1.0
        if tempo >= self.cfg.angry_tempo_hi:
            angry_score += 1.0

        # Need 3+ weighted points for angry
        if angry_score >= 3.0:
            return "angry"

        # Also angry if extremely high tension + rhythmic (slow doom metal)
        if tension >= 70 and rhythmic >= 60:
            return "angry"

        return "stress"

    # =========================================================================
    # PROTOTYPE FITTING
    # =========================================================================

    def _default_proto(self, mood: str) -> Prototype2D:
        """Default Gaussian prototype centers with covariance."""
        centers = {
            "energetic": (70.0, 75.0, 0.3),   # (mu_v, mu_a, correlation)
            "happy": (70.0, 35.0, -0.1),
            "sad": (30.0, 30.0, 0.4),         # Positive V-A correlation
            "stress": (30.0, 70.0, -0.3),     # Negative correlation
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

            # Variance
            var_v = sum((x - mu_v) ** 2 for x in vs) / max(1, n - 1)
            var_a = sum((x - mu_a) ** 2 for x in as_) / max(1, n - 1)

            # Covariance for Mahalanobis
            cov_va = sum((vs[i] - mu_v) * (as_[i] - mu_a) for i in range(n)) / max(1, n - 1)

            std_v = max(self.cfg.proto_min_std, math.sqrt(var_v))
            std_a = max(self.cfg.proto_min_std, math.sqrt(var_a))

            protos[mood] = Prototype2D(mu_v, mu_a, std_v, std_a, cov_va)

        return protos

    def fit(self, songs: Iterable[Song]) -> "MoodEngine":
        """Fit engine on song corpus."""
        songs_list = list(songs)
        if not songs_list:
            self.global_protos = {m: self._default_proto(m) for m in MOODS}
            self.token_protos = {}
            self.token_counts = {}
            return self

        # 1) Tempo bounds
        tempos = [t for t in (_to_float(s.get("tempo")) for s in songs_list) if t is not None and t > 0]
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

        # 3) bootstrap labels, then fit global + token prototypes
        global_points: Dict[str, List[Tuple[Number, Number]]] = {m: [] for m in MOODS}
        token_points: Dict[str, Dict[str, List[Tuple[Number, Number]]]] = {}
        token_counts: Dict[str, int] = {}

        for s in songs_list:
            v = self.valence_score(s)
            a = self.arousal_score(s)
            y = self._weak_label(s, v, a)
            global_points[y].append((v, a))

            if self.cfg.use_genre_tokens:
                for tok in tokenize_genre(s.get("genre")):
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
    # INFERENCE v5.0
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

    def mood_probabilities(self, song: Song, v: Number, a: Number) -> Dict[str, Number]:
        """Get mood probabilities with genre blending."""
        global_probs = self._probs_from_protos(self.global_protos, v, a)

        if not self.cfg.use_genre_tokens:
            return global_probs

        tokens = tokenize_genre(song.get("genre"))
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

        # v5.1: Scale genre weight by token prototype entropy
        # Tight prototypes (low entropy) should have less influence
        token_entropy = self._entropy(avg_token_probs)
        max_entropy = math.log(len(MOODS))
        entropy_ratio = token_entropy / max_entropy if max_entropy > 0 else 1.0
        # High entropy = more uncertain = reduce genre influence
        adjusted_weight = self.cfg.genre_weight * (0.5 + 0.5 * entropy_ratio)
        
        w = clamp(float(adjusted_weight), 0.0, 1.0)
        blended = {m: (1.0 - w) * global_probs[m] + w * avg_token_probs[m] for m in MOODS}
        s = sum(blended.values()) or 1.0
        return {m: blended[m] / s for m in MOODS}

    def predict(self, song: Song) -> Dict[str, object]:
        """
        Full mood prediction with all v5.0 enhancements.
        
        Returns:
        - Core metrics: valence, arousal, mood, confidence, intensity
        - Human-readable labels (semantic buckets)
        - Mood probabilities for all moods
        - Advanced metrics
        """
        v = self.valence_score(song)
        a = self.arousal_score(song)

        probs = self.mood_probabilities(song, v, a)
        mood = max(probs, key=probs.get)
        conf = float(probs[mood])

        # === ENTROPY-BASED CONFIDENCE PENALTY ===
        # Reduces confidence for ambiguous predictions
        if self.cfg.use_entropy_penalty:
            entropy = self._entropy(probs)
            max_entropy = math.log(len(MOODS))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            conf *= (1 - self.cfg.entropy_penalty_factor * normalized_entropy)

        # === EMOTIONAL DEPTH BOOST ===
        emotional_depth = _to_float(song.get("emotional_depth"))
        if self.cfg.use_emotional_depth and emotional_depth is not None:
            depth_factor = (emotional_depth - 50) / 100.0
            conf = clamp(conf + depth_factor * self.cfg.depth_confidence_boost, 0.0, 1.0)

        # === MOOD STABILITY ADJUSTMENT ===
        mood_stability = _to_float(song.get("mood_stability"))
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
            harmonic_comp = _to_float(song.get("harmonic_complexity"))
            if harmonic_comp is not None and harmonic_comp > 60:
                if mood in ("stress", "sad"):
                    conf = clamp(conf + 0.02, 0.0, 1.0)

            volatility = _to_float(song.get("emotional_volatility"))
            if volatility is not None and volatility > 70:
                conf = clamp(conf - 0.015, 0.0, 1.0)

            atmospheric = _to_float(song.get("atmospheric_depth"))
            if atmospheric is not None and atmospheric > 70 and mood == "stress":
                if probs.get("sad", 0) > conf * 0.55:
                    mood = "sad"
                    conf = float(probs[mood])

        intensity_int = self.infer_intensity_int(a)
        mood_score = (v + a) / 2.0

        # === HUMAN-READABLE LABELS (semantic buckets) ===
        arousal_label_vi, arousal_label_en = get_arousal_label(a)
        valence_label_vi, valence_label_en = get_valence_label(v)
        mood_description = MOOD_DESCRIPTIONS.get(mood, "")

        # === GATHER ALL METRICS ===
        return {
            # Core metrics
            "valence_score": round(v, 2),
            "arousal_score": round(a, 2),
            "mood": mood,
            "mood_confidence": round(conf, 4),
            "intensity": intensity_int,
            "mood_score": round(mood_score, 2),

            # Human-readable labels (NEW v5.0)
            "arousal_label": arousal_label_vi,
            "valence_label": valence_label_vi,
            "mood_description": mood_description,

            # Probabilities for all moods
            "mood_probabilities": {m: round(p, 4) for m, p in probs.items()},

            # Advanced metrics
            "emotional_depth": emotional_depth,
            "mood_stability": mood_stability,
            "tension_level": _to_float(song.get("tension_level")),
            "groove_factor": _to_float(song.get("groove_factor")),
            "harmonic_complexity": _to_float(song.get("harmonic_complexity")),
            "rhythmic_complexity": _to_float(song.get("rhythmic_complexity")),

            # Context scores for chatbot
            "morning_score": _to_float(song.get("morning_score")),
            "evening_score": _to_float(song.get("evening_score")),
            "workout_score": _to_float(song.get("workout_score")),
            "focus_score": _to_float(song.get("focus_score")),
            "relax_score": _to_float(song.get("relax_score")),
            "party_score": _to_float(song.get("party_score")),
        }

    def predict_with_explanation(self, song: Song) -> Dict[str, object]:
        """
        Full mood prediction WITH human-readable explanation (v5.2).
        Use this for chatbot responses where narrative is needed.
        """
        prediction = self.predict(song)
        
        # Generate explanation using NarrativeAdapter
        explanation = NarrativeAdapter.generate_explanation(song, prediction)
        context_rec = NarrativeAdapter.get_context_recommendation(prediction)
        
        prediction["explanation"] = {
            "narrative": explanation["narrative"],
            "factors": explanation["factors"],
            "confidence_note": explanation["confidence_note"],
            "short_description": explanation["short_description"],
            "context_recommendation": context_rec,
        }
        
        return prediction


# =============================================================================
# NARRATIVE ADAPTER v5.2
# Generates human-readable explanations for chatbot integration
# =============================================================================

class NarrativeAdapter:
    """
    Converts MoodEngine predictions to human-readable narratives.
    Separated from core engine to maintain clean architecture.
    """

    # Explanation templates for each contributing factor
    FACTOR_TEMPLATES = {
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
    }

    # Mood narrative templates
    MOOD_NARRATIVES = {
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

    @staticmethod
    def extract_factors(song: Song, prediction: Dict) -> List[str]:
        """
        Extract key contributing factors from song and prediction.
        Returns list of human-readable factor descriptions.
        """
        factors = []
        
        # Tempo factor
        tempo = _to_float(song.get("tempo")) or 120
        if tempo < 80:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["tempo_slow"])
        elif tempo > 130:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["tempo_fast"])
        
        # Energy factor
        energy = _to_float(song.get("energy")) or 50
        if energy < 35:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["energy_low"])
        elif energy > 70:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["energy_high"])
        
        # Mode factor
        mode = _to_float(song.get("mode"))
        if mode == 0:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["mode_minor"])
        elif mode == 1:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["mode_major"])
        
        # Valence factor
        valence = prediction.get("valence_score", 50)
        if valence < 35:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["valence_low"])
        elif valence > 65:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["valence_high"])
        
        # Acoustic factor
        acoustic = _to_float(song.get("acousticness")) or 0
        if acoustic > 70:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["acoustic"])
        
        # Loudness factor
        loudness = _to_float(song.get("loudness")) or -10
        if loudness > -5:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["loud"])
        elif loudness < -15:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["soft"])
        
        # Danceability factor
        dance = _to_float(song.get("danceability")) or 50
        if dance > 70:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["danceable"])
        
        # Groove factor
        groove = _to_float(song.get("groove_factor"))
        if groove is not None and groove > 65:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["groove_high"])
        
        # Tension factor
        tension = _to_float(song.get("tension_level"))
        if tension is not None and tension > 65:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["tension_high"])
        
        # Rhythmic complexity
        rhythmic = _to_float(song.get("rhythmic_complexity"))
        if rhythmic is not None and rhythmic > 65:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["complex_rhythm"])
        
        # Atmospheric depth
        atmospheric = _to_float(song.get("atmospheric_depth"))
        if atmospheric is not None and atmospheric > 65:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["atmospheric"])
        
        # Emotional depth
        depth = _to_float(song.get("emotional_depth"))
        if depth is not None and depth > 65:
            factors.append(NarrativeAdapter.FACTOR_TEMPLATES["emotional_depth"])
        
        # Ensure at least 2 factors
        if len(factors) < 2:
            arousal = prediction.get("arousal_score", 50)
            if arousal > 55:
                factors.append(NarrativeAdapter.FACTOR_TEMPLATES["energy_moderate"])
            else:
                factors.append(NarrativeAdapter.FACTOR_TEMPLATES["tempo_moderate"])
        
        return factors[:4]  # Limit to 4 most relevant factors

    @staticmethod
    def generate_explanation(song: Song, prediction: Dict) -> Dict[str, object]:
        """
        Generate human-readable explanation for mood prediction.
        
        Returns:
        - narrative: Full sentence explanation
        - factors: List of contributing factors
        - confidence_note: Note about prediction confidence
        """
        import random
        
        mood = prediction.get("mood", "happy")
        conf = prediction.get("mood_confidence", 0.5)
        
        # Extract factors
        factors = NarrativeAdapter.extract_factors(song, prediction)
        factors_text = ", ".join(factors[:3])
        if len(factors) > 3:
            factors_text += f" và {factors[3]}"
        
        # Select narrative template
        templates = NarrativeAdapter.MOOD_NARRATIVES.get(mood, NarrativeAdapter.MOOD_NARRATIVES["happy"])
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
    def get_context_recommendation(prediction: Dict) -> str:
        """
        Get context-based recommendation (when to listen).
        """
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

