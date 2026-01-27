"""TF-IDF based search engine for songs with Vietnamese support."""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple
import pickle
import re
import unicodedata
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine
import numpy as np


# Vietnamese diacritics mapping for normalization
VIETNAMESE_DIACRITICS = {
    # a variants
    'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
    'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
    'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
    # e variants
    'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
    'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
    # i variants
    'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
    # o variants
    'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
    'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
    'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
    # u variants
    'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
    'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
    # y variants
    'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    # d variant
    'đ': 'd',
}

# Vietnamese mood keywords mapping (Vietnamese -> English mood)
VIETNAMESE_MOOD_KEYWORDS = {
    # Happy / Vui
    'vui': 'happy', 'vui vẻ': 'happy', 'hạnh phúc': 'happy', 'sung sướng': 'happy',
    'phấn khởi': 'happy', 'hân hoan': 'happy', 'tươi vui': 'happy',
    # Sad / Buồn
    'buồn': 'sad', 'buồn bã': 'sad', 'u sầu': 'sad', 'đau buồn': 'sad',
    'tâm trạng': 'sad', 'thất tình': 'sad', 'cô đơn': 'sad', 'nhớ nhung': 'sad',
    'sầu': 'sad', 'lẻ loi': 'sad', 'trầm': 'sad',
    # Energetic / Năng lượng
    'năng lượng': 'energetic', 'sôi động': 'energetic', 'hứng khởi': 'energetic',
    'bùng nổ': 'energetic', 'mạnh mẽ': 'energetic', 'cuồng nhiệt': 'energetic',
    'phấn khích': 'energetic', 'quẩy': 'energetic', 'nhảy': 'energetic',
    # Stress / Căng thẳng
    'căng thẳng': 'stress', 'lo lắng': 'stress', 'áp lực': 'stress',
    'bất an': 'stress', 'hồi hộp': 'stress', 'lo âu': 'stress',
    # Angry / Giận
    'giận': 'angry', 'tức giận': 'angry', 'phẫn nộ': 'angry', 'bực bội': 'angry',
    'khó chịu': 'angry', 'nổi điên': 'angry', 'cáu': 'angry',
    # Calm / Thư giãn
    'thư giãn': 'calm', 'nhẹ nhàng': 'calm', 'êm dịu': 'calm', 'bình yên': 'calm',
    'thanh thản': 'calm', 'tĩnh lặng': 'calm', 'an yên': 'calm', 'chill': 'calm',
    # Romantic / Lãng mạn
    'lãng mạn': 'romantic', 'tình yêu': 'romantic', 'yêu': 'romantic',
    'tình cảm': 'romantic', 'ngọt ngào': 'romantic',
}

# Vietnamese genre keywords
VIETNAMESE_GENRE_KEYWORDS = {
    'nhạc trẻ': 'pop', 'nhạc pop': 'pop', 'vpop': 'pop',
    'nhạc trữ tình': 'ballad', 'bolero': 'bolero',
    'nhạc điện tử': 'electronic', 'edm': 'electronic',
    'nhạc rock': 'rock', 'rock': 'rock',
    'nhạc rap': 'hip hop', 'rap': 'hip hop', 'hip hop': 'hip hop',
    'nhạc jazz': 'jazz', 'jazz': 'jazz',
    'r&b': 'r&b', 'rnb': 'r&b',
    'nhạc cổ điển': 'classical', 'nhạc không lời': 'instrumental',
    'nhạc indie': 'indie', 'indie': 'indie',
    'nhạc acoustic': 'acoustic', 'acoustic': 'acoustic',
}


def normalize_vietnamese(text: str) -> str:
    """
    Normalize Vietnamese text by removing diacritics.
    
    Args:
        text: Vietnamese text with diacritics
        
    Returns:
        Normalized text without diacritics (ASCII-safe)
    """
    if not text:
        return ''
    
    result = []
    for char in text.lower():
        if char in VIETNAMESE_DIACRITICS:
            result.append(VIETNAMESE_DIACRITICS[char])
        else:
            result.append(char)
    
    return ''.join(result)


def translate_vietnamese_keywords(text: str) -> str:
    """
    Translate Vietnamese mood/genre keywords to English for search.
    
    Args:
        text: Vietnamese input text
        
    Returns:
        Text with Vietnamese keywords translated to English equivalents
    """
    if not text:
        return ''
    
    text_lower = text.lower()
    translated_parts = [text_lower]  # Keep original
    
    # Check for mood keywords
    for vn_word, en_word in VIETNAMESE_MOOD_KEYWORDS.items():
        if vn_word in text_lower:
            translated_parts.append(en_word)
    
    # Check for genre keywords
    for vn_word, en_word in VIETNAMESE_GENRE_KEYWORDS.items():
        if vn_word in text_lower:
            translated_parts.append(en_word)
    
    return ' '.join(translated_parts)


def preprocess_query(query: str) -> str:
    """
    Preprocess search query to handle Vietnamese input.
    
    Args:
        query: User search query (Vietnamese or English)
        
    Returns:
        Preprocessed query optimized for search
    """
    if not query:
        return ''
    
    # Step 1: Translate Vietnamese keywords to English
    translated = translate_vietnamese_keywords(query)
    
    # Step 2: Normalize Vietnamese diacritics for fuzzy matching
    normalized = normalize_vietnamese(translated)
    
    # Step 3: Clean up - remove extra whitespace
    cleaned = ' '.join(normalized.split())
    
    return cleaned


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
        
        # Create documents: combine song_name, artist, genre, mood, intensity
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
        """Create searchable document from song metadata with Vietnamese support."""
        parts = [
            song.get('song_name', ''),
            song.get('artist', ''),
            song.get('genre', ''),
            song.get('mood', ''),
            self._intensity_to_text(song.get('intensity', 2))
        ]
        doc = ' '.join(filter(None, parts))
        
        # Also add normalized version for Vietnamese fuzzy matching
        normalized = normalize_vietnamese(doc)
        return f"{doc} {normalized}"
    
    @staticmethod
    def _intensity_to_text(intensity: int) -> str:
        """Convert intensity number to text (Vietnamese + English)."""
        mapping = {
            1: 'low energy calm nhẹ nhàng thư giãn êm dịu', 
            2: 'medium energy trung bình', 
            3: 'high energy intense sôi động mạnh mẽ'
        }
        return mapping.get(intensity, '')
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[Tuple[Dict, float]]:
        """
        Search for songs matching query (supports Vietnamese input).
        
        Args:
            query: Search query string (Vietnamese or English)
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of (song, score) tuples, ranked by relevance
        """
        if self.vectorizer is None or self.tfidf_matrix is None:
            raise ValueError("Search engine not fitted. Call fit() first.")
        
        # Preprocess query for Vietnamese support
        processed_query = preprocess_query(query)
        
        # Vectorize query
        query_vec = self.vectorizer.transform([processed_query])
        
        # Compute similarity scores
        similarities = []
        for i, song in enumerate(self.songs):
            # Use cosine similarity (1 - cosine distance)
            try:
                query_arr = query_vec.toarray()[0]
                doc_arr = self.tfidf_matrix[i].toarray()[0]
                
                # Handle zero vectors (would cause NaN in cosine)
                query_norm = np.linalg.norm(query_arr)
                doc_norm = np.linalg.norm(doc_arr)
                
                if query_norm == 0 or doc_norm == 0:
                    score = 0.0
                else:
                    score = 1 - cosine(query_arr, doc_arr)
                    # Handle NaN from cosine function
                    if np.isnan(score):
                        score = 0.0
            except Exception:
                score = 0.0
                
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
        Search for exact field match (supports Vietnamese input).
        
        Args:
            field: Field name (title, artist, genre, mood)
            value: Value to search for (Vietnamese or English)
            top_k: Max results
            
        Returns:
            List of matching songs
        """
        results = []
        
        # Normalize search value for Vietnamese
        value_lower = value.lower()
        value_normalized = normalize_vietnamese(value_lower)
        
        # Translate Vietnamese mood/genre keywords
        value_translated = translate_vietnamese_keywords(value_lower)
        
        for song in self.songs:
            field_value = str(song.get(field, '')).lower()
            field_normalized = normalize_vietnamese(field_value)
            
            # Check multiple match conditions
            if (value_lower in field_value or 
                field_value in value_lower or
                value_normalized in field_normalized or
                field_normalized in value_normalized or
                any(word in field_value for word in value_translated.split())):
                results.append(song)
        
        return results[:top_k]
    
    def suggest(self, prefix: str, top_k: int = 5) -> List[str]:
        """
        Suggest songs by prefix (supports Vietnamese input).
        
        Args:
            prefix: Prefix to match (Vietnamese or English)
            top_k: Number of suggestions
            
        Returns:
            List of song titles/artists
        """
        suggestions = []
        prefix_lower = prefix.lower()
        prefix_normalized = normalize_vietnamese(prefix_lower)
        
        for song in self.songs:
            song_name = song.get('song_name', '').lower()
            artist = song.get('artist', '').lower()
            song_name_normalized = normalize_vietnamese(song_name)
            artist_normalized = normalize_vietnamese(artist)
            
            # Match with both original and normalized versions
            if (song_name.startswith(prefix_lower) or 
                song_name_normalized.startswith(prefix_normalized)):
                suggestions.append(f"{song['song_name']} - {song['artist']}")
            elif (artist.startswith(prefix_lower) or 
                  artist_normalized.startswith(prefix_normalized)):
                suggestions.append(f"{song['song_name']} - {song['artist']}")
        
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
