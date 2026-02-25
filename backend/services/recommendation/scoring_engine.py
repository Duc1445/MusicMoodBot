"""
=============================================================================
SCORING ENGINE - v5.0
=============================================================================

Context-aware song scoring with multi-factor weighting.

Features:
- Weighted feature scoring
- Context modifier application
- Thompson Sampling strategy selection
- Explainable score breakdown

Author: MusicMoodBot Team
Version: 5.0.0
=============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import math
import random
import sqlite3
import os


@dataclass
class ScoredSong:
    """Song with calculated score and explanation."""
    song_id: int
    name: str
    artist: str
    genre: Optional[str]
    mood: Optional[str]
    
    # Audio features
    valence: float = 0.0
    energy: float = 0.0
    tempo: float = 120.0
    
    # Scoring results
    final_score: float = 0.0
    raw_score: float = 0.0
    score_components: Dict[str, float] = field(default_factory=dict)
    strategy_used: str = ""
    explanation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "name": self.name,
            "artist": self.artist,
            "genre": self.genre,
            "mood": self.mood,
            "valence": round(self.valence, 3),
            "energy": round(self.energy, 3),
            "tempo": self.tempo,
            "final_score": round(self.final_score, 4),
            "raw_score": round(self.raw_score, 4),
            "score_components": {k: round(v, 4) for k, v in self.score_components.items()},
            "strategy_used": self.strategy_used,
            "explanation": self.explanation,
        }


class ThompsonSamplingBandit:
    """
    Thompson Sampling for strategy selection.
    
    Maintains Beta distribution priors for each strategy.
    """
    
    def __init__(self, strategies: List[str], prior_alpha: float = 1.0, prior_beta: float = 1.0):
        self.strategies = strategies
        self._alphas = {s: prior_alpha for s in strategies}
        self._betas = {s: prior_beta for s in strategies}
    
    def sample(self) -> Tuple[str, Dict[str, float]]:
        """
        Sample from each strategy's distribution and return the winner.
        
        Returns:
            Tuple of (winning_strategy, all_samples)
        """
        samples = {}
        for strategy in self.strategies:
            # Sample from Beta(alpha, beta)
            samples[strategy] = random.betavariate(
                self._alphas[strategy],
                self._betas[strategy]
            )
        
        winner = max(samples.keys(), key=lambda k: samples[k])
        return winner, samples
    
    def update(self, strategy: str, reward: float):
        """
        Update strategy's distribution based on reward.
        
        Args:
            strategy: Strategy that was used
            reward: Reward value (0 to 1)
        """
        if strategy not in self.strategies:
            return
        
        # Update based on reward (treat as Bernoulli)
        if reward >= 0.5:
            self._alphas[strategy] += reward
        else:
            self._betas[strategy] += (1.0 - reward)
    
    def get_expected_rewards(self) -> Dict[str, float]:
        """Get expected reward (mean of Beta distribution) for each strategy."""
        return {
            s: self._alphas[s] / (self._alphas[s] + self._betas[s])
            for s in self.strategies
        }
    
    def get_state(self) -> Dict[str, Dict[str, float]]:
        """Get bandit state for serialization."""
        return {
            "alphas": self._alphas.copy(),
            "betas": self._betas.copy(),
        }
    
    def load_state(self, state: Dict):
        """Load bandit state from dictionary."""
        self._alphas = state.get("alphas", self._alphas)
        self._betas = state.get("betas", self._betas)


class ScoringEngine:
    """
    Context-aware song scoring engine.
    
    Combines multiple scoring strategies with Thompson Sampling selection.
    """
    
    STRATEGIES = ["emotion", "content", "collaborative", "diversity", "exploration"]
    
    # Default feature weights
    DEFAULT_WEIGHTS = {
        "mood_match": 1.0,
        "emotional_resonance": 1.0,
        "valence_alignment": 1.0,
        "energy_alignment": 1.0,
        "artist_preference": 1.0,
        "genre_preference": 1.0,
        "tempo_comfort": 1.0,
        "popularity": 0.5,
        "recency": 0.3,
    }
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__),
            "..", "..", "src", "database", "music.db"
        )
        self.bandit = ThompsonSamplingBandit(self.STRATEGIES)
        self._user_weights: Dict[int, Dict[str, float]] = {}
    
    def get_user_weights(self, user_id: int) -> Dict[str, float]:
        """Get weights for a user, or default if not set."""
        return self._user_weights.get(user_id, self.DEFAULT_WEIGHTS.copy())
    
    def set_user_weights(self, user_id: int, weights: Dict[str, float]):
        """Set custom weights for a user."""
        self._user_weights[user_id] = weights.copy()
    
    def score_songs(
        self,
        user_id: int,
        target_mood: Optional[str] = None,
        target_valence: float = 0.0,
        target_arousal: float = 0.0,
        context_modifiers: Optional[Dict[str, float]] = None,
        strategy: Optional[str] = None,
        limit: int = 10,
    ) -> Tuple[List[ScoredSong], str, Dict[str, float]]:
        """
        Score and rank songs based on context and preferences.
        
        Args:
            user_id: User ID
            target_mood: Target mood label
            target_valence: Target valence (-1 to 1)
            target_arousal: Target arousal (-1 to 1)
            context_modifiers: Modifiers from ConversationContextMemory
            strategy: Force specific strategy (or use Thompson Sampling)
            limit: Number of songs to return
            
        Returns:
            Tuple of (scored_songs, strategy_used, thompson_samples)
        """
        # Select strategy
        if strategy and strategy in self.STRATEGIES:
            selected_strategy = strategy
            thompson_samples = {s: 0.0 for s in self.STRATEGIES}
            thompson_samples[strategy] = 1.0
        else:
            selected_strategy, thompson_samples = self.bandit.sample()
        
        # Get candidate songs
        candidates = self._get_candidate_songs(target_mood, limit * 3)
        
        if not candidates:
            return [], selected_strategy, thompson_samples
        
        # Get user weights
        weights = self.get_user_weights(user_id)
        
        # Apply context modifiers
        modifiers = context_modifiers or {}
        
        # Score each candidate
        scored = []
        for song in candidates:
            score_result = self._score_single_song(
                song=song,
                strategy=selected_strategy,
                target_mood=target_mood,
                target_valence=target_valence,
                target_arousal=target_arousal,
                weights=weights,
                modifiers=modifiers,
            )
            scored.append(score_result)
        
        # Sort by score descending
        scored.sort(key=lambda s: s.final_score, reverse=True)
        
        # Apply diversity filter if needed
        if selected_strategy != "diversity":
            scored = self._apply_diversity_filter(scored, limit)
        else:
            scored = scored[:limit]
        
        return scored, selected_strategy, thompson_samples
    
    def _get_candidate_songs(
        self,
        target_mood: Optional[str],
        limit: int
    ) -> List[Dict]:
        """Retrieve candidate songs from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get songs, optionally filtered by mood
            if target_mood:
                cursor.execute("""
                    SELECT 
                        song_id, name, artist, genre, moods as mood,
                        COALESCE(valence, 0) as valence,
                        COALESCE(energy, 0) as energy,
                        COALESCE(tempo, 120) as tempo,
                        COALESCE(popularity, 50) as popularity
                    FROM songs
                    WHERE moods LIKE ? OR moods IS NULL
                    LIMIT ?
                """, (f"%{target_mood}%", limit))
            else:
                cursor.execute("""
                    SELECT 
                        song_id, name, artist, genre, moods as mood,
                        COALESCE(valence, 0) as valence,
                        COALESCE(energy, 0) as energy,
                        COALESCE(tempo, 120) as tempo,
                        COALESCE(popularity, 50) as popularity
                    FROM songs
                    LIMIT ?
                """, (limit,))
            
            songs = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return songs
            
        except Exception as e:
            print(f"Error getting candidates: {e}")
            return []
    
    def _score_single_song(
        self,
        song: Dict,
        strategy: str,
        target_mood: Optional[str],
        target_valence: float,
        target_arousal: float,
        weights: Dict[str, float],
        modifiers: Dict[str, float],
    ) -> ScoredSong:
        """Score a single song."""
        components = {}
        
        # Mood match
        if target_mood and song.get("mood"):
            mood_match = 1.0 if target_mood.lower() in song["mood"].lower() else 0.3
        else:
            mood_match = 0.5
        components["mood_match"] = mood_match * weights.get("mood_match", 1.0)
        
        # Valence alignment
        song_valence = float(song.get("valence", 0))
        valence_diff = abs(target_valence - song_valence)
        valence_score = max(0, 1.0 - valence_diff)
        components["valence_alignment"] = valence_score * weights.get("valence_alignment", 1.0)
        
        # Energy/Arousal alignment
        song_energy = float(song.get("energy", 0))
        energy_diff = abs(target_arousal - song_energy)
        energy_score = max(0, 1.0 - energy_diff)
        components["energy_alignment"] = energy_score * weights.get("energy_alignment", 1.0)
        
        # Emotional resonance (combined VA distance)
        va_distance = math.sqrt(valence_diff ** 2 + energy_diff ** 2)
        emotional_resonance = max(0, 1.0 - va_distance / 2.0)
        components["emotional_resonance"] = emotional_resonance * weights.get("emotional_resonance", 1.0)
        
        # Tempo comfort (normalized around 100-140 bpm sweet spot)
        tempo = float(song.get("tempo", 120))
        tempo_score = 1.0 - abs(tempo - 120) / 80
        tempo_score = max(0, min(1, tempo_score))
        components["tempo_comfort"] = tempo_score * weights.get("tempo_comfort", 1.0)
        
        # Popularity
        popularity = float(song.get("popularity", 50)) / 100
        components["popularity"] = popularity * weights.get("popularity", 0.5)
        
        # Apply context modifiers
        mood_stability_mod = modifiers.get("mood_stability_weight", 1.0)
        components["mood_match"] *= mood_stability_mod
        components["emotional_resonance"] *= mood_stability_mod
        
        comfort_boost = modifiers.get("comfort_music_boost", 0.0)
        if comfort_boost > 0:
            # Boost calming songs
            if song_energy < 0.5 and song_valence > 0:
                components["emotional_resonance"] += comfort_boost
        
        diversity_boost = modifiers.get("diversity_boost", 0.0)
        if strategy == "diversity":
            components["popularity"] *= (1.0 + diversity_boost)
        
        # Strategy-specific adjustments
        if strategy == "emotion":
            components["emotional_resonance"] *= 1.5
            components["mood_match"] *= 1.3
        elif strategy == "content":
            components["valence_alignment"] *= 1.3
            components["energy_alignment"] *= 1.3
        elif strategy == "exploration":
            # Reduce weight of personalization
            for key in components:
                components[key] *= 0.7
            # Add randomness
            components["exploration_bonus"] = random.uniform(0.2, 0.5)
        
        # Calculate final score
        raw_score = sum(components.values())
        max_possible = sum(weights.values()) * 1.5  # Approximate max
        final_score = min(1.0, raw_score / max_possible)
        
        # Generate explanation
        top_factors = sorted(components.items(), key=lambda x: x[1], reverse=True)[:2]
        explanation = self._generate_explanation(
            strategy, target_mood, top_factors, final_score
        )
        
        return ScoredSong(
            song_id=song["song_id"],
            name=song["name"],
            artist=song["artist"],
            genre=song.get("genre"),
            mood=song.get("mood"),
            valence=song_valence,
            energy=song_energy,
            tempo=tempo,
            final_score=final_score,
            raw_score=raw_score,
            score_components=components,
            strategy_used=strategy,
            explanation=explanation,
        )
    
    def _generate_explanation(
        self,
        strategy: str,
        target_mood: Optional[str],
        top_factors: List[Tuple[str, float]],
        score: float,
    ) -> str:
        """Generate human-readable explanation."""
        factor_names = {
            "mood_match": "matches your mood",
            "emotional_resonance": "resonates emotionally",
            "valence_alignment": "has the right feeling",
            "energy_alignment": "matches your energy level",
            "tempo_comfort": "has a comfortable tempo",
            "popularity": "is popular with others",
            "exploration_bonus": "could be a nice discovery",
        }
        
        if not top_factors:
            return "Recommended for you"
        
        primary_factor = factor_names.get(top_factors[0][0], "fits your preferences")
        
        if target_mood:
            return f"This {target_mood} track {primary_factor}"
        else:
            return f"This track {primary_factor}"
    
    def _apply_diversity_filter(
        self,
        songs: List[ScoredSong],
        limit: int
    ) -> List[ScoredSong]:
        """Apply diversity filter to avoid repetition."""
        if len(songs) <= limit:
            return songs
        
        selected = [songs[0]]  # Take top song
        seen_artists = {songs[0].artist}
        seen_genres = {songs[0].genre} if songs[0].genre else set()
        
        for song in songs[1:]:
            if len(selected) >= limit:
                break
            
            # Penalize same artist appearing consecutively
            if song.artist in seen_artists and len(selected) < 3:
                continue
            
            selected.append(song)
            seen_artists.add(song.artist)
            if song.genre:
                seen_genres.add(song.genre)
        
        # Fill remaining slots if needed
        while len(selected) < limit and len(selected) < len(songs):
            for song in songs:
                if song not in selected:
                    selected.append(song)
                    if len(selected) >= limit:
                        break
        
        return selected
    
    def update_bandit(self, strategy: str, reward: float):
        """Update Thompson Sampling bandit with reward."""
        self.bandit.update(strategy, reward)
    
    def get_bandit_state(self) -> Dict:
        """Get current bandit state."""
        return {
            "state": self.bandit.get_state(),
            "expected_rewards": self.bandit.get_expected_rewards(),
        }


# Global scoring engine instance
_scoring_engine: Optional[ScoringEngine] = None


def get_scoring_engine(db_path: Optional[str] = None) -> ScoringEngine:
    """Get or create the global scoring engine."""
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = ScoringEngine(db_path)
    return _scoring_engine
