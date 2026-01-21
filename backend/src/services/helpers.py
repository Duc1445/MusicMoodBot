"""Utility functions for mood prediction and data normalization."""

from __future__ import annotations

from typing import Dict, List, Optional
import math
import re

Number = float


def _is_missing(x) -> bool:
    """Check if value is None or NaN."""
    return x is None or (isinstance(x, float) and math.isnan(x))


def _to_float(x, default: Optional[Number] = None) -> Optional[Number]:
    """Convert value to float with fallback default."""
    if _is_missing(x):
        return default
    try:
        return float(x)
    except Exception:
        return default


def clamp(x: Number, lo: Number, hi: Number) -> Number:
    """Clamp value to range [lo, hi]."""
    return lo if x < lo else hi if x > hi else x


def percentile(values: List[Number], q: float) -> Number:
    """Calculate percentile (q in [0,100]) without numpy."""
    vals = sorted(v for v in values if v is not None and not math.isnan(v))
    if not vals:
        raise ValueError("Cannot compute percentile of empty values.")
    if q <= 0:
        return vals[0]
    if q >= 100:
        return vals[-1]
    k = (len(vals) - 1) * (q / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return vals[int(k)]
    return vals[f] + (vals[c] - vals[f]) * (k - f)


def robust_minmax(x: Number, lo: Number, hi: Number) -> Number:
    """Map x to 0..100 using robust bounds [lo..hi]."""
    if hi <= lo:
        return 50.0
    x = clamp(x, lo, hi)
    return (x - lo) / (hi - lo) * 100.0


def coerce_0_100(x: Optional[Number], default: Number = 50.0) -> Number:
    """
    Accept x in [0..100] (TuneBat-like) or [0..1] (Spotify-like). Return 0..100.
    """
    if x is None:
        return default
    if 0.0 <= x <= 1.0:
        return x * 100.0
    return clamp(x, 0.0, 100.0)


def normalize_loudness_to_0_100(
    loudness: Optional[Number],
    *,
    db_floor: Number = -60.0,
    db_ceil: Number = 0.0,
    default_db: Number = -12.0,
) -> Number:
    """
    If loudness looks like dBFS (<=0), map [-60..0] -> [0..100].
    Else assume already 0..100.
    """
    if loudness is None:
        loudness = default_db

    if loudness <= 0.0:
        l = clamp(loudness, db_floor, db_ceil)
        return (l - db_floor) / (db_ceil - db_floor) * 100.0

    return clamp(loudness, 0.0, 100.0)


def softmax(logits: Dict[str, Number], temperature: Number = 1.0) -> Dict[str, Number]:
    """Compute softmax probabilities from logits."""
    t = max(1e-6, float(temperature))
    if not logits:
        return {}
    m = max(logits.values())
    exps = {k: math.exp((v - m) / t) for k, v in logits.items()}
    s = sum(exps.values()) or 1.0
    return {k: exps[k] / s for k in exps}


def tokenize_genre(genre: Optional[str]) -> List[str]:
    """
    Split mixed genre strings like 'ballad+rock, pop' into tokens.

    Supported separators: + , / ; | &
    """
    if not genre:
        return []
    g = str(genre).strip().lower()
    if not g:
        return []
    parts = re.split(r"[\+\,\/\;\|\&]+", g)
    tokens = [p.strip() for p in parts if p.strip()]
    # De-dup (stable)
    out: List[str] = []
    seen = set()
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out
