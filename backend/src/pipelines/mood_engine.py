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

    # arousal weights
    w_energy: Number = 0.45
    w_tempo: Number = 0.20
    w_loudness: Number = 0.20
    w_dance_arousal: Number = 0.10
    w_acoustic_penalty: Number = 0.05

    # valence weights
    w_valence_happiness: Number = 0.85
    w_valence_dance: Number = 0.15

    # prototype training
    proto_min_std: Number = 8.0
    proto_temperature: Number = 1.0

    # weak-label angry proxy thresholds
    angry_loudness_hi: Number = 75.0
    angry_tempo_hi: Number = 70.0

    # genre adaptation (tokens, safe for "ballad+rock")
    use_genre_tokens: bool = True
    genre_min_count: int = 25    # use token prototypes only when token has enough samples
    genre_weight: Number = 0.5   # blend weight (0..1): global vs genre tokens

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
        happiness = coerce_0_100(_to_float(song.get("happiness")), default=50.0)
        dance = coerce_0_100(_to_float(song.get("danceability")), default=50.0)
        v = self.cfg.w_valence_happiness * happiness + self.cfg.w_valence_dance * dance
        return clamp(v, 0.0, 100.0)

    def arousal_score(self, song: Song) -> Number:
        energy = coerce_0_100(_to_float(song.get("energy")), default=50.0)
        tempo = self.tempo_score(_to_float(song.get("tempo")))
        loud = self.loudness_score(_to_float(song.get("loudness")))
        dance = coerce_0_100(_to_float(song.get("danceability")), default=50.0)
        acoustic = coerce_0_100(_to_float(song.get("acousticness")), default=50.0)

        a = (
            self.cfg.w_energy * energy
            + self.cfg.w_tempo * tempo
            + self.cfg.w_loudness * loud
            + self.cfg.w_dance_arousal * dance
            - self.cfg.w_acoustic_penalty * acoustic
        )
        return clamp(a, 0.0, 100.0)

    # --- bootstrap weak labels (no human labels needed)
    def _weak_label(self, song: Song, v: Number, a: Number) -> str:
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
        if loud >= self.cfg.angry_loudness_hi and tempo >= self.cfg.angry_tempo_hi:
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
        v = self.valence_score(song)
        a = self.arousal_score(song)

        probs = self.mood_probabilities(song, v, a)
        mood = max(probs, key=probs.get)
        conf = float(probs[mood])

        intensity_int = self.infer_intensity_int(a)
        mood_score = (v + a) / 2.0

        return {
            "valence_score": v,
            "arousal_score": a,
            "mood": mood,
            "mood_confidence": conf,
            "intensity": intensity_int,
            "mood_score": mood_score,
        }

