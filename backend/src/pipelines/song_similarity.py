"""
Song similarity engine using audio features and mood analysis.
Provides related songs and "more like this" recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import math
import logging

from backend.src.services.constants import Song, MOODS

logger = logging.getLogger(__name__)


@dataclass
class SimilarityConfig:
    """Configuration for similarity calculations."""
    # Feature weights for overall similarity
    w_energy: float = 0.20
    w_happiness: float = 0.20
    w_danceability: float = 0.15
    w_tempo: float = 0.10
    w_loudness: float = 0.05
    w_acousticness: float = 0.10
    w_mood: float = 0.15
    w_genre: float = 0.05
    
    # Normalization ranges
    tempo_min: float = 50.0
    tempo_max: float = 200.0
    loudness_min: float = -60.0
    loudness_max: float = 0.0
    
    # Similarity thresholds
    high_similarity: float = 0.8
    medium_similarity: float = 0.5
    
    # Diversity bonus for recommendations
    diversity_bonus: float = 0.1


@dataclass
class SimilarityResult:
    """Result of similarity comparison."""
    song_id: int
    song: Song
    similarity_score: float
    feature_similarities: Dict[str, float]
    mood_match: bool
    genre_match: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "song": self.song,
            "similarity_score": round(self.similarity_score, 4),
            "feature_similarities": {
                k: round(v, 4) for k, v in self.feature_similarities.items()
            },
            "mood_match": self.mood_match,
            "genre_match": self.genre_match
        }


class SongSimilarityEngine:
    """
    Engine for calculating song similarity based on audio features.
    
    Features:
    - Multi-dimensional feature comparison
    - Mood-aware similarity
    - Genre token matching
    - Configurable weights
    """
    
    def __init__(self, config: Optional[SimilarityConfig] = None):
        self.config = config or SimilarityConfig()
        self._feature_cache: Dict[int, Dict[str, float]] = {}
    
    def _normalize(self, value: Optional[float], min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range."""
        if value is None:
            return 0.5
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
    
    def _extract_features(self, song: Song) -> Dict[str, float]:
        """Extract normalized features from a song."""
        song_id = song.get("song_id")
        
        # Check cache
        if song_id and song_id in self._feature_cache:
            return self._feature_cache[song_id]
        
        features = {
            "energy": self._normalize(song.get("energy"), 0, 100),
            "happiness": self._normalize(
                song.get("happiness") or song.get("valence"), 0, 100
            ),
            "danceability": self._normalize(song.get("danceability"), 0, 100),
            "acousticness": self._normalize(song.get("acousticness"), 0, 100),
            "tempo": self._normalize(
                song.get("tempo"),
                self.config.tempo_min,
                self.config.tempo_max
            ),
            "loudness": self._normalize(
                song.get("loudness"),
                self.config.loudness_min,
                self.config.loudness_max
            ),
        }
        
        # Cache if has song_id
        if song_id:
            self._feature_cache[song_id] = features
        
        return features
    
    def _tokenize_genre(self, genre: Optional[str]) -> set:
        """Tokenize genre string into set of tokens."""
        if not genre:
            return set()
        # Split on +, /, -, space
        tokens = set()
        for delimiter in ["+", "/", "-", " ", ","]:
            genre = genre.replace(delimiter, "|")
        for token in genre.split("|"):
            token = token.strip().lower()
            if token:
                tokens.add(token)
        return tokens
    
    def _genre_similarity(self, genre1: Optional[str], genre2: Optional[str]) -> float:
        """Calculate genre similarity using Jaccard index."""
        tokens1 = self._tokenize_genre(genre1)
        tokens2 = self._tokenize_genre(genre2)
        
        if not tokens1 or not tokens2:
            return 0.5  # Neutral when missing
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _mood_similarity(self, mood1: Optional[str], mood2: Optional[str]) -> float:
        """Calculate mood similarity."""
        if mood1 == mood2:
            return 1.0
        
        if not mood1 or not mood2:
            return 0.5
        
        # Define mood proximity
        mood_distances = {
            ("energetic", "happy"): 0.7,
            ("energetic", "stress"): 0.4,
            ("energetic", "angry"): 0.5,
            ("energetic", "sad"): 0.2,
            ("happy", "sad"): 0.2,
            ("happy", "stress"): 0.3,
            ("happy", "angry"): 0.3,
            ("sad", "stress"): 0.5,
            ("sad", "angry"): 0.3,
            ("stress", "angry"): 0.6,
        }
        
        key = tuple(sorted([mood1.lower(), mood2.lower()]))
        return mood_distances.get(key, 0.3)
    
    def calculate_similarity(
        self,
        song1: Song,
        song2: Song
    ) -> SimilarityResult:
        """Calculate similarity between two songs."""
        feat1 = self._extract_features(song1)
        feat2 = self._extract_features(song2)
        
        # Calculate per-feature similarities (1 - abs difference)
        feature_sims = {}
        for key in feat1.keys():
            diff = abs(feat1[key] - feat2[key])
            feature_sims[key] = 1.0 - diff
        
        # Mood similarity
        mood1 = song1.get("mood")
        mood2 = song2.get("mood")
        mood_sim = self._mood_similarity(mood1, mood2)
        feature_sims["mood"] = mood_sim
        
        # Genre similarity
        genre_sim = self._genre_similarity(
            song1.get("genre"),
            song2.get("genre")
        )
        feature_sims["genre"] = genre_sim
        
        # Calculate weighted similarity
        cfg = self.config
        total_similarity = (
            cfg.w_energy * feature_sims["energy"] +
            cfg.w_happiness * feature_sims["happiness"] +
            cfg.w_danceability * feature_sims["danceability"] +
            cfg.w_tempo * feature_sims["tempo"] +
            cfg.w_loudness * feature_sims["loudness"] +
            cfg.w_acousticness * feature_sims["acousticness"] +
            cfg.w_mood * feature_sims["mood"] +
            cfg.w_genre * feature_sims["genre"]
        )
        
        return SimilarityResult(
            song_id=song2.get("song_id", 0),
            song=song2,
            similarity_score=total_similarity,
            feature_similarities=feature_sims,
            mood_match=(mood1 == mood2),
            genre_match=(genre_sim >= 0.5)
        )
    
    def find_similar_songs(
        self,
        target_song: Song,
        candidates: List[Song],
        top_k: int = 10,
        exclude_same_artist: bool = False,
        min_similarity: float = 0.0
    ) -> List[SimilarityResult]:
        """Find songs most similar to target."""
        target_id = target_song.get("song_id")
        target_artist = target_song.get("artist", "").lower()
        
        results = []
        for song in candidates:
            # Skip self
            if song.get("song_id") == target_id:
                continue
            
            # Skip same artist if requested
            if exclude_same_artist:
                if song.get("artist", "").lower() == target_artist:
                    continue
            
            result = self.calculate_similarity(target_song, song)
            
            if result.similarity_score >= min_similarity:
                results.append(result)
        
        # Sort by similarity descending
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        
        return results[:top_k]
    
    def find_diverse_similar(
        self,
        target_song: Song,
        candidates: List[Song],
        top_k: int = 10,
        diversity_weight: float = 0.3
    ) -> List[SimilarityResult]:
        """
        Find similar songs with diversity.
        Uses greedy MMR-like selection to balance similarity and diversity.
        """
        target_id = target_song.get("song_id")
        
        # Calculate all similarities
        all_results = []
        for song in candidates:
            if song.get("song_id") == target_id:
                continue
            result = self.calculate_similarity(target_song, song)
            all_results.append(result)
        
        if not all_results:
            return []
        
        # Greedy selection with diversity
        selected: List[SimilarityResult] = []
        remaining = all_results.copy()
        
        # First pick: most similar
        remaining.sort(key=lambda r: r.similarity_score, reverse=True)
        selected.append(remaining.pop(0))
        
        while len(selected) < top_k and remaining:
            best_score = -1
            best_idx = 0
            
            for i, candidate in enumerate(remaining):
                # Similarity to target
                sim_to_target = candidate.similarity_score
                
                # Max similarity to already selected (penalize)
                max_sim_to_selected = 0.0
                for sel in selected:
                    pair_sim = self.calculate_similarity(
                        candidate.song, sel.song
                    ).similarity_score
                    max_sim_to_selected = max(max_sim_to_selected, pair_sim)
                
                # MMR score: balance similarity and diversity
                mmr_score = (
                    (1 - diversity_weight) * sim_to_target -
                    diversity_weight * max_sim_to_selected
                )
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            selected.append(remaining.pop(best_idx))
        
        return selected
    
    def cluster_by_similarity(
        self,
        songs: List[Song],
        n_clusters: int = 5
    ) -> Dict[int, List[Song]]:
        """
        Simple clustering based on similarity.
        Uses iterative closest assignment.
        """
        if len(songs) < n_clusters:
            return {0: songs}
        
        # Initialize centroids with diverse songs
        import random
        centroids_idx = [random.randint(0, len(songs) - 1)]
        
        while len(centroids_idx) < n_clusters:
            # Find song most different from current centroids
            max_min_dist = -1
            best_idx = 0
            
            for i, song in enumerate(songs):
                if i in centroids_idx:
                    continue
                
                min_sim = 1.0
                for c_idx in centroids_idx:
                    sim = self.calculate_similarity(song, songs[c_idx]).similarity_score
                    min_sim = min(min_sim, sim)
                
                # We want max of min distances (most different)
                dist = 1 - min_sim
                if dist > max_min_dist:
                    max_min_dist = dist
                    best_idx = i
            
            centroids_idx.append(best_idx)
        
        # Assign songs to clusters
        clusters: Dict[int, List[Song]] = {i: [] for i in range(n_clusters)}
        
        for song in songs:
            best_cluster = 0
            best_sim = -1
            
            for c_id, c_idx in enumerate(centroids_idx):
                sim = self.calculate_similarity(song, songs[c_idx]).similarity_score
                if sim > best_sim:
                    best_sim = sim
                    best_cluster = c_id
            
            clusters[best_cluster].append(song)
        
        return clusters
    
    def get_feature_distribution(self, songs: List[Song]) -> Dict[str, Dict[str, float]]:
        """Analyze feature distribution of a song set."""
        if not songs:
            return {}
        
        features = ["energy", "happiness", "danceability", "acousticness", "tempo", "loudness"]
        stats = {}
        
        for feat in features:
            values = []
            for song in songs:
                val = song.get(feat)
                if val is not None:
                    values.append(float(val))
            
            if values:
                stats[feat] = {
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "count": len(values)
                }
        
        # Mood distribution
        mood_counts = {}
        for song in songs:
            mood = song.get("mood", "unknown")
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        stats["mood_distribution"] = mood_counts
        
        return stats


# Convenience functions
def find_similar(
    target_song: Song,
    all_songs: List[Song],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """Quick function to find similar songs."""
    engine = SongSimilarityEngine()
    results = engine.find_similar_songs(target_song, all_songs, top_k)
    return [r.to_dict() for r in results]


def get_song_neighbors(
    song_id: int,
    db_path: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Get similar songs from database."""
    from backend.src.repo.song_repo import connect, fetch_songs, fetch_song_by_id
    
    con = connect(db_path)
    target = fetch_song_by_id(con, song_id)
    
    if not target:
        con.close()
        return []
    
    all_songs = fetch_songs(con)
    con.close()
    
    engine = SongSimilarityEngine()
    results = engine.find_similar_songs(target, all_songs, top_k)
    
    return [
        {
            "song": r.song,
            "similarity": round(r.similarity_score, 3),
            "mood_match": r.mood_match
        }
        for r in results
    ]


# Global instance
_similarity_engine: Optional[SongSimilarityEngine] = None


def get_similarity_engine() -> SongSimilarityEngine:
    """Get or create similarity engine instance."""
    global _similarity_engine
    if _similarity_engine is None:
        _similarity_engine = SongSimilarityEngine()
    return _similarity_engine
