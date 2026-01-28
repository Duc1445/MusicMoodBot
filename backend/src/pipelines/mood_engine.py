"""Mood engine model with VA (Valence-Arousal) + probabilistic prototypes."""

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

@dataclass
class EngineConfig:
    # tempo normalization bounds learned by fit() via percentiles
    tempo_p_low: Number = 5.0
    tempo_p_high: Number = 95.0
    tempo_abs_low: Number = 50.0
    tempo_abs_high: Number = 200.0

    # loudness dBFS normalization
    loudness_db_floor: Number = -60.0
    loudness_db_ceil: Number = 0.0

    # arousal weights (v4.0 - advanced features)
    w_energy: Number = 0.32
    w_tempo: Number = 0.14
    w_loudness: Number = 0.14
    w_dance_arousal: Number = 0.08
    w_acoustic_penalty: Number = 0.05
    w_liveness: Number = 0.06
    w_tension: Number = 0.08  # NEW v4.0: tension level
    w_groove: Number = 0.06  # NEW v4.0: groove factor
    w_energy_buildup: Number = 0.07  # NEW v4.0: energy buildup

    # valence weights (v4.0 - advanced features)
    w_valence_happiness: Number = 0.58
    w_valence_dance: Number = 0.10
    w_valence_mode: Number = 0.07
    w_valence_instrumental: Number = 0.04
    w_valence_brightness: Number = 0.08  # NEW v4.0: melodic brightness
    w_valence_nostalgia: Number = 0.06  # NEW v4.0: nostalgia factor
    w_valence_satisfaction: Number = 0.07  # NEW v4.0: release satisfaction

    # emotional depth weights (v3.1)
    use_emotional_depth: bool = True
    depth_confidence_boost: Number = 0.15

    # mood stability weights (v3.1)
    use_mood_stability: bool = True
    stability_weight: Number = 0.10

    # NEW v4.0: Advanced feature weights
    use_advanced_features: bool = True
    harmonic_complexity_weight: Number = 0.05
    rhythmic_complexity_weight: Number = 0.05
    atmospheric_weight: Number = 0.04
    volatility_weight: Number = 0.06

    # prototype training
    proto_min_std: Number = 8.0
    proto_temperature: Number = 1.0

    # weak-label angry proxy thresholds
    angry_loudness_hi: Number = 75.0
    angry_tempo_hi: Number = 70.0
    angry_tension_hi: Number = 70.0  # NEW v4.0

    # genre adaptation (tokens, safe for "ballad+rock")
    use_genre_tokens: bool = True
    genre_min_count: int = 25
    genre_weight: Number = 0.5

    # intensity thresholds learned by fit (percentiles of arousal)
    intensity_p_low: Number = 33.0
    intensity_p_high: Number = 66.0


@dataclass
class Prototype2D:
    mu_v: Number
    mu_a: Number
    std_v: Number
    std_a: Number

    def log_likelihood_diag(self, v: Number, a: Number) -> Number:
        sv = max(1e-6, self.std_v)
        sa = max(1e-6, self.std_a)
        zv = (v - self.mu_v) / sv
        za = (a - self.mu_a) / sa
        # log N up to constant term:
        return -0.5 * (zv * zv + za * za) - math.log(sv) - math.log(sa)


class MoodEngine:
    def __init__(self, cfg: Optional[EngineConfig] = None):
        self.cfg = cfg or EngineConfig()

        # learned bounds / thresholds
        self._tempo_low: Optional[Number] = None
        self._tempo_high: Optional[Number] = None
        self.valence_mid: Number = 50.0
        self.arousal_mid: Number = 50.0
        self.intensity_low: Number = 33.0
        self.intensity_high: Number = 66.0

        # prototypes
        self.global_protos: Dict[str, Prototype2D] = {}
        self.token_protos: Dict[str, Dict[str, Prototype2D]] = {}
        self.token_counts: Dict[str, int] = {}

    # --- normalization helpers
    def tempo_score(self, tempo: Optional[Number]) -> Number:
        t = _to_float(tempo)
        if t is None or t <= 0:
            t = (self.cfg.tempo_abs_low + self.cfg.tempo_abs_high) / 2.0
        if self._tempo_low is not None and self._tempo_high is not None:
            return robust_minmax(t, self._tempo_low, self._tempo_high)
        return robust_minmax(t, self.cfg.tempo_abs_low, self.cfg.tempo_abs_high)

    def loudness_score(self, loudness: Optional[Number]) -> Number:
        return normalize_loudness_to_0_100(
            _to_float(loudness),
            db_floor=self.cfg.loudness_db_floor,
            db_ceil=self.cfg.loudness_db_ceil,
        )

    def valence_score(self, song: Song) -> Number:
        """
        Tính valence score (độ tích cực/vui vẻ) từ các thuộc tính.
        v4.0: Thêm melodic_brightness, nostalgia, release_satisfaction.
        """
        # Support both 'happiness' (TuneBat) and 'valence' (Spotify) fields
        happiness = _to_float(song.get("happiness"))
        valence = _to_float(song.get("valence"))
        
        # Use whichever is available, prefer 'valence' if both exist
        if valence is not None:
            happiness_val = coerce_0_100(valence, default=50.0)
        elif happiness is not None:
            happiness_val = coerce_0_100(happiness, default=50.0)
        else:
            happiness_val = 50.0
            
        dance = coerce_0_100(_to_float(song.get("danceability")), default=50.0)
        
        # Mode (major=1 adds happiness, minor=0 neutral/sad)
        mode = _to_float(song.get("mode"))
        mode_bonus = 0.0
        if mode is not None:
            mode_bonus = 50.0 if mode == 1 else -20.0
        
        # Instrumentalness (pure instrumental tends to be more neutral)
        instrumental = coerce_0_100(_to_float(song.get("instrumentalness")), default=0.0)
        instrumental_pull = (50.0 - happiness_val) * (instrumental / 100.0)
        
        # NEW v4.0: Melodic brightness (higher pitch = brighter = happier)
        brightness = coerce_0_100(_to_float(song.get("melodic_brightness")), default=50.0)
        brightness_contrib = (brightness - 50.0)  # -50 to +50
        
        # NEW v4.0: Nostalgia factor (can be bittersweet, slight negative)
        nostalgia = coerce_0_100(_to_float(song.get("nostalgia_factor")), default=40.0)
        nostalgia_contrib = (50.0 - nostalgia) * 0.3  # High nostalgia = slightly less happy
        
        # NEW v4.0: Release satisfaction (cathartic = happier)
        satisfaction = coerce_0_100(_to_float(song.get("release_satisfaction")), default=50.0)
        satisfaction_contrib = (satisfaction - 50.0)  # -50 to +50
        
        v = (
            self.cfg.w_valence_happiness * happiness_val 
            + self.cfg.w_valence_dance * dance
            + self.cfg.w_valence_mode * mode_bonus
            + self.cfg.w_valence_instrumental * instrumental_pull
            + self.cfg.w_valence_brightness * brightness_contrib
            + self.cfg.w_valence_nostalgia * nostalgia_contrib
            + self.cfg.w_valence_satisfaction * satisfaction_contrib
        )
        return clamp(v, 0.0, 100.0)

    def arousal_score(self, song: Song) -> Number:
        """
        Tính arousal score (mức năng lượng/kích thích) từ các thuộc tính.
        v4.0: Thêm tension, groove, energy_buildup.
        """
        energy = coerce_0_100(_to_float(song.get("energy")), default=50.0)
        tempo = self.tempo_score(_to_float(song.get("tempo")))
        loud = self.loudness_score(_to_float(song.get("loudness")))
        dance = coerce_0_100(_to_float(song.get("danceability")), default=50.0)
        acoustic = coerce_0_100(_to_float(song.get("acousticness")), default=50.0)
        liveness = coerce_0_100(_to_float(song.get("liveness")), default=10.0)
        
        # NEW v4.0: Tension level (dissonance = higher arousal)
        tension = coerce_0_100(_to_float(song.get("tension_level")), default=50.0)
        
        # NEW v4.0: Groove factor (good groove = moderate arousal boost)
        groove = coerce_0_100(_to_float(song.get("groove_factor")), default=50.0)
        groove_contrib = (groove - 50.0) * 0.5  # Less impact than energy
        
        # NEW v4.0: Energy buildup (crescendo = higher perceived arousal)
        buildup = coerce_0_100(_to_float(song.get("energy_buildup")), default=50.0)

        a = (
            self.cfg.w_energy * energy
            + self.cfg.w_tempo * tempo
            + self.cfg.w_loudness * loud
            + self.cfg.w_dance_arousal * dance
            - self.cfg.w_acoustic_penalty * acoustic
            + self.cfg.w_liveness * liveness
            + self.cfg.w_tension * tension
            + self.cfg.w_groove * groove_contrib
            + self.cfg.w_energy_buildup * buildup
        )
        return clamp(a, 0.0, 100.0)

    # --- bootstrap weak labels (no human labels needed)
    def _weak_label(self, song: Song, v: Number, a: Number) -> str:
        """
        Gán nhãn yếu dựa trên valence/arousal.
        v4.0: Sử dụng tension_level và harmonic_complexity để phân biệt stress/angry.
        """
        v_hi = v >= self.valence_mid
        a_hi = a >= self.arousal_mid

        if v_hi and a_hi:
            return "energetic"
        if v_hi and not a_hi:
            return "happy"
        if (not v_hi) and (not a_hi):
            return "sad"

        # (-V, +A): stress vs angry proxy
        loud = self.loudness_score(_to_float(song.get("loudness")))
        tempo = self.tempo_score(_to_float(song.get("tempo")))
        
        # NEW v4.0: Use tension_level for better stress/angry distinction
        tension = coerce_0_100(_to_float(song.get("tension_level")), default=50.0)
        harmonic_comp = coerce_0_100(_to_float(song.get("harmonic_complexity")), default=50.0)
        
        # Angry: high tension + loud + fast + complex harmony
        if (tension >= self.cfg.angry_tension_hi and 
            loud >= self.cfg.angry_loudness_hi and 
            tempo >= self.cfg.angry_tempo_hi):
            return "angry"
        
        # Also angry if extremely high tension with moderate loudness
        if tension >= 80 and loud >= 60:
            return "angry"
            
        return "stress"

    def _default_proto(self, mood: str) -> Prototype2D:
        centers = {
            "energetic": (70.0, 75.0),
            "happy": (70.0, 35.0),
            "sad": (30.0, 30.0),
            "stress": (30.0, 70.0),
            "angry": (20.0, 85.0),
        }
        mu_v, mu_a = centers.get(mood, (50.0, 50.0))
        s = self.cfg.proto_min_std
        return Prototype2D(mu_v, mu_a, s, s)

    def _fit_protos(self, points_by_mood: Dict[str, List[Tuple[Number, Number]]]) -> Dict[str, Prototype2D]:
        protos: Dict[str, Prototype2D] = {}
        for mood in MOODS:
            pts = points_by_mood.get(mood, [])
            if len(pts) < 5:
                protos[mood] = self._default_proto(mood)
                continue
            vs = [p[0] for p in pts]
            as_ = [p[1] for p in pts]
            mu_v = sum(vs) / len(vs)
            mu_a = sum(as_) / len(as_)
            std_v = math.sqrt(sum((x - mu_v) ** 2 for x in vs) / max(1, len(vs) - 1))
            std_a = math.sqrt(sum((x - mu_a) ** 2 for x in as_) / max(1, len(as_) - 1))
            std_v = max(self.cfg.proto_min_std, std_v)
            std_a = max(self.cfg.proto_min_std, std_a)
            protos[mood] = Prototype2D(mu_v, mu_a, std_v, std_a)
        return protos

    def fit(self, songs: Iterable[Song]) -> "MoodEngine":
        songs_list = list(songs)
        if not songs_list:
            self.global_protos = {m: self._default_proto(m) for m in MOODS}
            self.token_protos = {}
            self.token_counts = {}
            return self

        # 1) tempo bounds
        tempos = [t for t in (_to_float(s.get("tempo")) for s in songs_list) if t is not None and t > 0]
        if tempos:
            lo = percentile(tempos, self.cfg.tempo_p_low)
            hi = percentile(tempos, self.cfg.tempo_p_high)
            lo = clamp(lo, 1.0, 300.0)
            hi = clamp(hi, 1.0, 300.0)
            if hi > lo:
                self._tempo_low, self._tempo_high = lo, hi

        # 2) learn mids + intensity cutoffs from VA
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

    # --- inference
    def infer_intensity_int(self, arousal: Number) -> int:
        if arousal >= self.intensity_high:
            return 3
        if arousal >= self.intensity_low:
            return 2
        return 1

    def _probs_from_protos(self, protos: Dict[str, Prototype2D], v: Number, a: Number) -> Dict[str, Number]:
        logits = {m: protos[m].log_likelihood_diag(v, a) for m in MOODS}
        return softmax(logits, temperature=self.cfg.proto_temperature)

    def mood_probabilities(self, song: Song, v: Number, a: Number) -> Dict[str, Number]:
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

        # average token probs
        avg_token_probs: Dict[str, Number] = {m: 0.0 for m in MOODS}
        for p in token_probs_list:
            for m in MOODS:
                avg_token_probs[m] += p[m]
        n = float(len(token_probs_list))
        for m in MOODS:
            avg_token_probs[m] /= n

        w = clamp(float(self.cfg.genre_weight), 0.0, 1.0)
        blended = {m: (1.0 - w) * global_probs[m] + w * avg_token_probs[m] for m in MOODS}
        s = sum(blended.values()) or 1.0
        return {m: blended[m] / s for m in MOODS}

    def predict(self, song: Song) -> Dict[str, object]:
        """
        Dự đoán mood cho một bài hát.
        v3.1: Sử dụng emotional_depth và mood_stability để tăng độ chính xác.
        """
        v = self.valence_score(song)
        a = self.arousal_score(song)

        probs = self.mood_probabilities(song, v, a)
        mood = max(probs, key=probs.get)
        conf = float(probs[mood])

        # Boost confidence nếu emotional_depth cao
        emotional_depth = _to_float(song.get("emotional_depth"))
        if self.cfg.use_emotional_depth and emotional_depth is not None:
            depth_factor = (emotional_depth - 50) / 100.0
            conf = clamp(conf + depth_factor * self.cfg.depth_confidence_boost, 0.0, 1.0)

        # Adjust prediction based on mood_stability
        mood_stability = _to_float(song.get("mood_stability"))
        if self.cfg.use_mood_stability and mood_stability is not None:
            if mood_stability > 75 and mood in ("stress", "angry"):
                alt_probs = {m: p for m, p in probs.items() if m not in ("stress", "angry")}
                if alt_probs:
                    alt_mood = max(alt_probs, key=alt_probs.get)
                    if probs[alt_mood] > conf * 0.7:
                        mood = alt_mood
                        conf = float(probs[mood])

        # NEW v4.0: Use advanced features for fine-tuning
        if self.cfg.use_advanced_features:
            # Harmonic complexity affects confidence for complex moods
            harmonic_comp = _to_float(song.get("harmonic_complexity"))
            if harmonic_comp is not None and harmonic_comp > 60:
                # Complex harmony = slightly boost confidence for stress/sad
                if mood in ("stress", "sad"):
                    conf = clamp(conf + 0.03, 0.0, 1.0)
            
            # Emotional volatility affects prediction
            volatility = _to_float(song.get("emotional_volatility"))
            if volatility is not None and volatility > 70:
                # High volatility = less stable mood, reduce confidence slightly
                conf = clamp(conf - 0.02, 0.0, 1.0)
            
            # Atmospheric depth for sad/stress distinction
            atmospheric = _to_float(song.get("atmospheric_depth"))
            if atmospheric is not None and atmospheric > 70 and mood == "stress":
                # High atmosphere often means contemplative rather than stressed
                if probs.get("sad", 0) > conf * 0.6:
                    mood = "sad"
                    conf = float(probs[mood])

        intensity_int = self.infer_intensity_int(a)
        mood_score = (v + a) / 2.0

        # Gather all advanced metrics for output
        tension_level = _to_float(song.get("tension_level"))
        groove_factor = _to_float(song.get("groove_factor"))
        harmonic_comp = _to_float(song.get("harmonic_complexity"))
        rhythmic_comp = _to_float(song.get("rhythmic_complexity"))

        return {
            "valence_score": v,
            "arousal_score": a,
            "mood": mood,
            "mood_confidence": conf,
            "intensity": intensity_int,
            "mood_score": mood_score,
            "emotional_depth": emotional_depth,
            "mood_stability": mood_stability,
            "tension_level": tension_level,
            "groove_factor": groove_factor,
            "harmonic_complexity": harmonic_comp,
            "rhythmic_complexity": rhythmic_comp,
        }

