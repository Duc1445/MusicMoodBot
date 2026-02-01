"""High-level mood prediction service for Flet backends."""

from __future__ import annotations

from typing import Dict, Optional
import sqlite3
import time

from backend.src.pipelines.mood_engine import MoodEngine, EngineConfig
from backend.src.repo.song_repo import (
    connect, fetch_songs, fetch_song_by_id, update_song, ensure_columns
)
from backend.src.services.constants import Song, TABLE_SONGS




class DBMoodEngine:
    """
    Caching-friendly wrapper for Flet backends.

    - Keeps a fitted MoodEngine in memory
    - Re-fits automatically when song count changes (or when forced)
    """

    def __init__(
        self,
        db_path: str = "music.db",
        *,
        cfg: Optional[EngineConfig] = None,
        add_debug_cols: bool = False,
        auto_fit: bool = True,
        refit_on_change: bool = True,
        min_refit_interval_sec: int = 2,
    ):
        self.db_path = db_path
        self.cfg = cfg or EngineConfig()
        self.add_debug_cols = add_debug_cols
        self.auto_fit = auto_fit
        self.refit_on_change = refit_on_change
        self.min_refit_interval_sec = max(0, int(min_refit_interval_sec))

        self._engine: Optional[MoodEngine] = None
        self._last_fit_song_count: Optional[int] = None
        self._last_fit_ts: float = 0.0

    def _song_count(self, con: sqlite3.Connection) -> int:
        cur = con.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_SONGS}")
        return int(cur.fetchone()[0])

    def _maybe_prepare_schema(self, con: sqlite3.Connection) -> None:
        if self.add_debug_cols:
            ensure_columns(con, TABLE_SONGS, [
                "valence_score REAL",
                "arousal_score REAL",
                "mood_confidence REAL",
            ])

    def fit(self, *, force: bool = False) -> MoodEngine:
        now = time.time()
        if not force and (now - self._last_fit_ts) < self.min_refit_interval_sec and self._engine is not None:
            return self._engine

        con = connect(self.db_path)
        try:
            self._maybe_prepare_schema(con)
            songs = fetch_songs(con)
            eng = MoodEngine(cfg=self.cfg)
            if self.auto_fit:
                eng.fit(songs)
            else:
                eng.fit([])
            self._engine = eng
            self._last_fit_song_count = len(songs)
            self._last_fit_ts = time.time()
            return eng
        finally:
            con.close()

    def _ensure_engine(self) -> MoodEngine:
        if self._engine is None:
            return self.fit(force=True)

        if not self.refit_on_change:
            return self._engine

        con = connect(self.db_path)
        try:
            cnt = self._song_count(con)
        finally:
            con.close()

        # if changed, refit (but respect min_refit_interval_sec)
        if self._last_fit_song_count is None or cnt != self._last_fit_song_count:
            return self.fit(force=False)

        return self._engine

    def predict_one(self, song: Song) -> Dict[str, object]:
        eng = self._ensure_engine()
        return eng.predict(song)

    def update_one(self, song_id: int) -> bool:
        eng = self._ensure_engine()
        con = connect(self.db_path)
        try:
            self._maybe_prepare_schema(con)
            s = fetch_song_by_id(con, song_id)
            if not s:
                return False

            pred = eng.predict(s)
            updates = {
                "mood": pred["mood"],
                "intensity": int(pred["intensity"]),
                "mood_score": float(pred["mood_score"]),
            }
            if self.add_debug_cols:
                updates.update({
                    "valence_score": float(pred["valence_score"]),
                    "arousal_score": float(pred["arousal_score"]),
                    "mood_confidence": float(pred["mood_confidence"]),
                })
            update_song(con, song_id, updates)
            con.commit()
            return True
        finally:
            con.close()

    def update_missing(self, where: Optional[str] = None) -> int:
        eng = self._ensure_engine()
        con = connect(self.db_path)
        try:
            self._maybe_prepare_schema(con)
            w = where or _default_missing_where()
            targets = fetch_songs(con, w)
            for s in targets:
                pred = eng.predict(s)
                updates = {
                    "mood": pred["mood"],
                    "intensity": int(pred["intensity"]),
                    "mood_score": float(pred["mood_score"]),
                }
                if self.add_debug_cols:
                    updates.update({
                        "valence_score": float(pred["valence_score"]),
                        "arousal_score": float(pred["arousal_score"]),
                        "mood_confidence": float(pred["mood_confidence"]),
                    })
                update_song(con, int(s["song_id"]), updates)
            con.commit()
            return len(targets)
        finally:
            con.close()

    def update_all(self) -> int:
        eng = self._ensure_engine()
        con = connect(self.db_path)
        try:
            self._maybe_prepare_schema(con)
            songs = fetch_songs(con)
            for s in songs:
                pred = eng.predict(s)
                updates = {
                    "mood": pred["mood"],
                    "intensity": int(pred["intensity"]),
                    "mood_score": float(pred["mood_score"]),
                }
                if self.add_debug_cols:
                    updates.update({
                        "valence_score": float(pred["valence_score"]),
                        "arousal_score": float(pred["arousal_score"]),
                        "mood_confidence": float(pred["mood_confidence"]),
                    })
                update_song(con, int(s["song_id"]), updates)
            con.commit()
            # engine was fit on previous distribution; update cached count
            self._last_fit_song_count = len(songs)
            return len(songs)
        finally:
            con.close()


# ----------------------------
# Convenience functions (no caching)
# ----------------------------

def update_one(db_path: str, song_id: int, *, add_debug_cols: bool = False, auto_fit: bool = True) -> bool:
    svc = DBMoodEngine(db_path, add_debug_cols=add_debug_cols, auto_fit=auto_fit)
    svc.fit(force=True)
    return svc.update_one(song_id)


def update_missing(db_path: str, *, add_debug_cols: bool = False, auto_fit: bool = True) -> int:
    svc = DBMoodEngine(db_path, add_debug_cols=add_debug_cols, auto_fit=auto_fit)
    svc.fit(force=True)
    return svc.update_missing()


def update_all(db_path: str, *, add_debug_cols: bool = False, auto_fit: bool = True) -> int:
    svc = DBMoodEngine(db_path, add_debug_cols=add_debug_cols, auto_fit=auto_fit)
    svc.fit(force=True)
    return svc.update_all()


# ----------------------------
# CLI
# ----------------------------

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Compute mood/intensity/mood_score and write back to SQLite DB")
    p.add_argument("--db", default="music.db", help="Path to SQLite database (default: music.db)")
    p.add_argument("--no-fit", action="store_true", help="Do not fit thresholds/prototypes from DB (use defaults)")
    p.add_argument("--debug-cols", action="store_true", help="Add/fill valence_score/arousal_score/mood_confidence columns")

    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("update-missing", help="Update only rows where mood/intensity/mood_score is NULL")
    sub.add_parser("update-all", help="Recompute for every row")

    one = sub.add_parser("update-one", help="Update a single song by song_id")
    one.add_argument("--id", type=int, required=True, help="song_id")

    return p


def main() -> None:
    args = _build_argparser().parse_args()

    auto_fit = not args.no_fit
    svc = DBMoodEngine(args.db, add_debug_cols=args.debug_cols, auto_fit=auto_fit)
    svc.fit(force=True)

    if args.cmd == "update-missing":
        n = svc.update_missing()
        print(f"Updated {n} rows (missing only)")
    elif args.cmd == "update-all":
        n = svc.update_all()
        print(f"Updated {n} rows (all)")
    elif args.cmd == "update-one":
        ok = svc.update_one(args.id)
        print("Updated 1 row" if ok else "song_id not found")


if __name__ == "__main__":
    main()
