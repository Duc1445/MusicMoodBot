"""TF-IDF based search engine for songs."""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple
import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine
import numpy as np


class TFIDFSearchEngine:
    """
    TF-IDF search engine for songs.
    
    Indexes songs by title, artist, genre, and mood description.
    Returns ranked results based on query relevance.
    """
    
    def __init__(self, cache_path: Optional[str] = None):
        """
        Initialize search engine.
        
        Args:
            cache_path: Path to save/load vectorizer cache
        """
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.songs: List[Dict] = []
        self.cache_path = cache_path
        
    def fit(self, songs: List[Dict]) -> TFIDFSearchEngine:
        """
        Fit TF-IDF model on songs.
        
        Args:
            songs: List of song dictionaries with fields:
                   - title, artist, genre, mood, intensity
                   
        Returns:
            self for chaining
        """
        self.songs = songs
        
        # Create documents: combine title, artist, genre, mood, intensity
        documents = []
        for song in songs:
            doc = self._create_document(song)
            documents.append(doc)
        
        # Fit TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(2, 3),
            max_features=500,
            lowercase=True,
            stop_words='english'
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)
        
        return self
    
    def _create_document(self, song: Dict) -> str:
        """Create searchable document from song metadata."""
        parts = [
            song.get('title', ''),
            song.get('artist', ''),
            song.get('genre', ''),
            song.get('mood', ''),
            self._intensity_to_text(song.get('intensity', 2))
        ]
        return ' '.join(filter(None, parts))
    
    @staticmethod
    def _intensity_to_text(intensity: int) -> str:
        """Convert intensity number to text."""
        mapping = {1: 'low energy calm', 2: 'medium energy', 3: 'high energy intense'}
        return mapping.get(intensity, '')
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[Dict, float]]:
        """
        Search for songs matching query.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of (song, score) tuples, ranked by relevance
        """
        if self.vectorizer is None or self.tfidf_matrix is None:
            raise ValueError("Search engine not fitted. Call fit() first.")
        
        # Vectorize query
        query_vec = self.vectorizer.transform([query])
        
        # Compute similarity scores
        similarities = []
        for i, song in enumerate(self.songs):
            # Use cosine similarity (1 - cosine distance)
            score = 1 - cosine(query_vec.toarray()[0], self.tfidf_matrix[i].toarray()[0])
            if score >= min_score:
                similarities.append((i, score))
        
        # Sort by score descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        results = [
            (self.songs[idx], score)
            for idx, score in similarities[:top_k]
        ]
        
        return results
    
    def search_by_field(
        self,
        field: str,
        value: str,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Search for exact field match (simpler than full-text search).
        
        Args:
            field: Field name (title, artist, genre, mood)
            value: Value to search for
            top_k: Max results
            
        Returns:
            List of matching songs
        """
        results = []
        value_lower = value.lower()
        
        for song in self.songs:
            field_value = str(song.get(field, '')).lower()
            if value_lower in field_value or field_value in value_lower:
                results.append(song)
        
        return results[:top_k]
    
    def suggest(self, prefix: str, top_k: int = 5) -> List[str]:
        """
        Suggest songs by prefix (title or artist).
        
        Args:
            prefix: Prefix to match
            top_k: Number of suggestions
            
        Returns:
            List of song titles/artists
        """
        suggestions = []
        prefix_lower = prefix.lower()
        
        for song in self.songs:
            title = song.get('title', '').lower()
            artist = song.get('artist', '').lower()
            
            if title.startswith(prefix_lower):
                suggestions.append(f"{song['title']} - {song['artist']}")
            elif artist.startswith(prefix_lower):
                suggestions.append(f"{song['title']} - {song['artist']}")
        
        # Remove duplicates
        suggestions = list(dict.fromkeys(suggestions))
        
        return suggestions[:top_k]
    
    def save(self, path: str) -> None:
        """Save vectorizer to file."""
        with open(path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
    
    def load(self, path: str) -> None:
        """Load vectorizer from file."""
        with open(path, 'rb') as f:
            self.vectorizer = pickle.load(f)


def create_search_engine(songs: List[Dict]) -> TFIDFSearchEngine:
    """
    Create and fit a search engine.
    
    Args:
        songs: List of songs to index
        
    Returns:
        Fitted search engine
    """
    engine = TFIDFSearchEngine()
    engine.fit(songs)
    return engine
