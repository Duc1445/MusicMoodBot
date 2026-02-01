"""
TF-IDF based search engine for songs with Vietnamese support.

Features:
- Vietnamese diacritics normalization
- Synonym expansion  
- Phonetic matching for typo tolerance
- Query intent detection (mood/artist/title/similar)
- Hybrid search with exact match fast path
- LRU caching for repeated queries
- BM25-inspired scoring
"""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple, NamedTuple
from enum import Enum
from functools import lru_cache
from collections import OrderedDict
import pickle
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher
import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from scipy.sparse import csr_matrix
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Try to import rapidfuzz for faster fuzzy matching
try:
    from rapidfuzz import fuzz as rapidfuzz_fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


# ================== QUERY INTENT DETECTION ==================

class QueryIntent(Enum):
    """Types of search intent"""
    TITLE = "title"      # Looking for a specific song
    ARTIST = "artist"    # Looking for songs by artist
    MOOD = "mood"        # Looking for mood-based songs
    GENRE = "genre"      # Looking for genre
    SIMILAR = "similar"  # Looking for similar songs
    GENERAL = "general"  # General search


class IntentResult(NamedTuple):
    """Result of intent detection"""
    intent: QueryIntent
    confidence: float
    extracted_value: str  # The main search term


# Intent detection keywords
ARTIST_INDICATORS = [
    'của', 'by', 'ca sĩ', 'nghệ sĩ', 'artist', 'singer', 
    'nhạc của', 'bài của', 'hát bởi', 'performed by'
]
MOOD_INDICATORS = [
    'nhạc', 'bài', 'mood', 'tâm trạng', 'cảm xúc', 'feeling',
    'nghe', 'muốn nghe', 'cho tôi', 'gợi ý'
]
SIMILAR_INDICATORS = [
    'giống', 'tương tự', 'similar', 'like', 'giống như', 
    'kiểu như', 'na ná', 'y như'
]
GENRE_INDICATORS = [
    'thể loại', 'genre', 'loại nhạc', 'dòng nhạc', 'style'
]


def detect_query_intent(query: str, known_artists: set = None, known_moods: set = None) -> IntentResult:
    """
    Detect what the user is searching for.
    
    Args:
        query: Search query
        known_artists: Set of known artist names (normalized)
        known_moods: Set of known mood names (normalized)
        
    Returns:
        IntentResult with detected intent, confidence, and extracted value
    """
    query_lower = query.lower().strip()
    query_norm = normalize_vietnamese(query_lower)
    
    # Check for similar song indicators
    for indicator in SIMILAR_INDICATORS:
        if indicator in query_lower:
            # Extract song name after indicator
            idx = query_lower.find(indicator)
            extracted = query_lower[idx + len(indicator):].strip()
            return IntentResult(QueryIntent.SIMILAR, 0.9, extracted)
    
    # Check for artist indicators
    for indicator in ARTIST_INDICATORS:
        if indicator in query_lower:
            # Extract artist name
            idx = query_lower.find(indicator)
            extracted = query_lower[idx + len(indicator):].strip()
            if extracted:
                return IntentResult(QueryIntent.ARTIST, 0.85, extracted)
    
    # Check against known artists
    if known_artists:
        for artist in known_artists:
            if artist in query_norm or query_norm in artist:
                return IntentResult(QueryIntent.ARTIST, 0.8, query)
    
    # Check for mood indicators + known moods
    has_mood_indicator = any(ind in query_lower for ind in MOOD_INDICATORS)
    if known_moods:
        for mood in known_moods:
            if mood in query_norm:
                confidence = 0.9 if has_mood_indicator else 0.7
                return IntentResult(QueryIntent.MOOD, confidence, mood)
    
    # Check for genre indicators
    for indicator in GENRE_INDICATORS:
        if indicator in query_lower:
            idx = query_lower.find(indicator)
            extracted = query_lower[idx + len(indicator):].strip()
            return IntentResult(QueryIntent.GENRE, 0.8, extracted or query)
    
    # Default: if short query, likely title; if long, general search
    if len(query.split()) <= 3:
        return IntentResult(QueryIntent.TITLE, 0.5, query)
    
    return IntentResult(QueryIntent.GENERAL, 0.4, query)


# ================== SEARCH CACHE ==================

class LRUCache:
    """Simple LRU cache for search results"""
    
    def __init__(self, max_size: int = 100):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[List]:
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def put(self, key: str, value: List):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # Remove oldest
                self.cache.popitem(last=False)
        self.cache[key] = value
    
    def clear(self):
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# ================== TYPO CORRECTION ==================

# Common Vietnamese typo patterns
TYPO_CORRECTIONS = {
    # Keyboard proximity typos
    'tg': 'tôi', 'mk': 'mình', 'dc': 'được', 'ko': 'không',
    'j': 'gì', 'z': 'vậy', 'ck': 'chồng', 'vk': 'vợ',
    # Common misspellings  
    'buon': 'buồn', 'vui ve': 'vui vẻ', 'hanh phuc': 'hạnh phúc',
    'nang luong': 'năng lượng', 'soi dong': 'sôi động',
    'thu gian': 'thư giãn', 'tam trang': 'tâm trạng',
    # Artist name typos (add common ones)
    'son tung': 'sơn tùng', 'mtp': 'sơn tùng mtp',
    'jack': 'jack', 'den vau': 'đen vâu',
}


def correct_typos(query: str) -> str:
    """
    Attempt to correct common typos in query.
    
    Args:
        query: Original query
        
    Returns:
        Corrected query
    """
    result = query.lower()
    
    for typo, correction in TYPO_CORRECTIONS.items():
        # Use word boundary matching
        pattern = r'\b' + re.escape(typo) + r'\b'
        result = re.sub(pattern, correction, result)
    
    return result


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

# Synonym expansion for music search
SYNONYMS = {
    # Mood synonyms
    'sad': ['buồn', 'u sầu', 'đau', 'tâm trạng', 'sầu', 'thất tình', 'cô đơn', 'melancholy', 'blue'],
    'happy': ['vui', 'hạnh phúc', 'tươi', 'phấn khởi', 'hân hoan', 'joyful', 'cheerful'],
    'chill': ['relax', 'thư giãn', 'nhẹ nhàng', 'êm dịu', 'bình yên', 'calm', 'peaceful'],
    'energetic': ['sôi động', 'năng lượng', 'mạnh mẽ', 'bùng nổ', 'upbeat', 'hype'],
    'romantic': ['lãng mạn', 'tình yêu', 'ngọt ngào', 'love', 'sweet'],
    # Genre synonyms
    'pop': ['nhạc trẻ', 'vpop', 'kpop', 'cpop'],
    'ballad': ['trữ tình', 'slow', 'nhẹ'],
    'rock': ['alternative', 'punk', 'metal'],
    'electronic': ['edm', 'house', 'techno', 'nhạc điện tử'],
    'hip hop': ['rap', 'trap', 'hiphop'],
    'r&b': ['rnb', 'soul', 'rhythm and blues'],
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


def expand_synonyms(text: str) -> str:
    """
    Expand query with synonyms for better recall.
    
    Args:
        text: Search query
        
    Returns:
        Query expanded with synonyms
    """
    if not text:
        return ''
    
    text_lower = text.lower()
    expanded_parts = [text_lower]
    
    for main_word, synonyms in SYNONYMS.items():
        # If main word in query, add synonyms
        if main_word in text_lower:
            expanded_parts.extend(synonyms[:3])  # Limit to avoid bloat
        # If any synonym in query, add main word
        for syn in synonyms:
            if syn in text_lower:
                expanded_parts.append(main_word)
                break
    
    return ' '.join(expanded_parts)


def fuzzy_match(s1: str, s2: str, threshold: float = 0.7) -> float:
    """
    Calculate fuzzy similarity between two strings.
    Uses rapidfuzz if available (5-10x faster), falls back to SequenceMatcher.
    
    Args:
        s1: First string
        s2: Second string
        threshold: Minimum ratio to consider a match
        
    Returns:
        Similarity ratio (0-1)
    """
    if not s1 or not s2:
        return 0.0
    
    # Normalize both strings
    s1_norm = normalize_vietnamese(s1.lower())
    s2_norm = normalize_vietnamese(s2.lower())
    
    # Use rapidfuzz if available (much faster)
    if HAS_RAPIDFUZZ:
        # rapidfuzz returns 0-100, convert to 0-1
        ratio = rapidfuzz_fuzz.ratio(s1_norm, s2_norm) / 100.0
        # Also try partial ratio for substring matching
        partial = rapidfuzz_fuzz.partial_ratio(s1_norm, s2_norm) / 100.0
        ratio = max(ratio, partial * 0.9)  # Slightly discount partial matches
    else:
        # Fallback to SequenceMatcher
        ratio = SequenceMatcher(None, s1_norm, s2_norm).ratio()
    
    return ratio if ratio >= threshold else 0.0


def fuzzy_match_best(query: str, candidates: List[str], threshold: float = 0.6, top_k: int = 3) -> List[Tuple[str, float]]:
    """
    Find best fuzzy matches from a list of candidates.
    
    Args:
        query: Search query
        candidates: List of candidate strings
        threshold: Minimum score
        top_k: Number of results
        
    Returns:
        List of (candidate, score) tuples
    """
    scores = []
    for candidate in candidates:
        score = fuzzy_match(query, candidate, threshold=0.0)  # Get all scores
        if score >= threshold:
            scores.append((candidate, score))
    
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def phonetic_normalize(text: str) -> str:
    """
    Normalize text phonetically for Vietnamese.
    Maps similar-sounding consonants to the same representation.
    
    Args:
        text: Vietnamese text
        
    Returns:
        Phonetically normalized text (ASCII + phonetic mapping)
    """
    if not text:
        return ''
    
    # First normalize Vietnamese diacritics
    result = normalize_vietnamese(text.lower())
    
    # Apply phonetic mappings (longer patterns first to avoid partial matches)
    phonetic_map = [
        ('ngh', 'ng'), ('gh', 'g'), ('kh', 'k'),
        ('tr', 'ch'), ('gi', 'd'), ('qu', 'kw'),
        ('ph', 'f'), ('th', 't'),
    ]
    
    for pattern, replacement in phonetic_map:
        result = result.replace(pattern, replacement)
    
    return result


def preprocess_query(query: str, expand_syn: bool = True) -> str:
    """
    Preprocess search query to handle Vietnamese input.
    
    Args:
        query: User search query (Vietnamese or English)
        expand_syn: Whether to expand with synonyms
        
    Returns:
        Preprocessed query optimized for search
    """
    if not query:
        return ''
    
    # Step 1: Translate Vietnamese keywords to English
    translated = translate_vietnamese_keywords(query)
    
    # Step 2: Expand with synonyms if enabled
    if expand_syn:
        translated = expand_synonyms(translated)
    
    # Step 3: Normalize Vietnamese diacritics for fuzzy matching
    normalized = normalize_vietnamese(translated)
    
    # Step 3: Clean up - remove extra whitespace
    cleaned = ' '.join(normalized.split())
    
    return cleaned


class TFIDFSearchEngine:
    """
    TF-IDF search engine for songs with advanced features.
    
    Features:
    - Vietnamese text normalization
    - Synonym expansion
    - Fuzzy matching (with rapidfuzz if available)
    - Smart ranking with exact match boost
    - Phonetic matching for typo tolerance
    - Query intent detection
    - Hybrid search with fast exact match path
    - LRU caching for repeated queries
    - Typo autocorrection
    """
    
    def __init__(self, cache_path: Optional[str] = None, enable_cache: bool = True):
        """
        Initialize search engine.
        
        Args:
            cache_path: Path to save/load vectorizer cache
            enable_cache: Enable LRU caching for search results
        """
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.songs: List[Dict] = []
        self.cache_path = cache_path
        
        # Index for fast lookup
        self._title_index: Dict[str, List[int]] = {}
        self._artist_index: Dict[str, List[int]] = {}
        self._mood_index: Dict[str, List[int]] = {}
        self._genre_index: Dict[str, List[int]] = {}
        
        # Known entities for intent detection
        self._known_artists: set = set()
        self._known_moods: set = set()
        self._known_genres: set = set()
        
        # Search cache
        self._cache = LRUCache(max_size=100) if enable_cache else None
        
        # Stats
        self._search_count = 0
        self._avg_search_time = 0.0
        
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
        
        # Build inverted indexes for fast exact matching
        self._build_indexes()
        
        # Extract known entities
        self._extract_known_entities()
        
        # Clear cache when data changes
        if self._cache:
            self._cache.clear()
        
        # Create documents: combine song_name, artist, genre, mood, intensity
        documents = []
        for song in songs:
            doc = self._create_document(song)
            documents.append(doc)
        
        # Fit TF-IDF vectorizer with word + char n-grams for better matching
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',  # Word-boundary aware char n-grams
            ngram_range=(2, 4),  # 2-4 char n-grams
            max_features=1000,   # More features for better precision
            lowercase=True,
            sublinear_tf=True,   # Use log(1 + tf) for better scaling
            norm='l2',  # L2 normalization (default)
            use_idf=True,
            smooth_idf=True,
            dtype=np.float32,  # Use float32 to save memory
        )
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(documents)
            # Convert to CSR format for efficient computation
            if not isinstance(self.tfidf_matrix, csr_matrix):
                self.tfidf_matrix = csr_matrix(self.tfidf_matrix)
        except Exception as e:
            print(f"Error fitting TF-IDF vectorizer: {e}")
            # Fallback to simple implementation
            self.vectorizer = None
            self.tfidf_matrix = None
        
        return self
    
    def _extract_known_entities(self):
        """Extract known artists, moods, genres for intent detection."""
        self._known_artists.clear()
        self._known_moods.clear()
        self._known_genres.clear()
        
        for song in self.songs:
            artist = normalize_vietnamese(song.get('artist', '').lower())
            if artist:
                self._known_artists.add(artist)
            
            mood = normalize_vietnamese(song.get('mood', '').lower())
            if mood:
                self._known_moods.add(mood)
            
            genre = normalize_vietnamese(song.get('genre', '').lower())
            if genre:
                self._known_genres.add(genre)
    
    def _build_indexes(self):
        """Build inverted indexes for fast lookup."""
        self._title_index.clear()
        self._artist_index.clear()
        self._mood_index.clear()
        self._genre_index.clear()
        
        for i, song in enumerate(self.songs):
            # Index by title
            title = normalize_vietnamese(song.get('song_name', '').lower())
            for word in title.split():
                if word not in self._title_index:
                    self._title_index[word] = []
                self._title_index[word].append(i)
            
            # Index by artist
            artist = normalize_vietnamese(song.get('artist', '').lower())
            for word in artist.split():
                if word not in self._artist_index:
                    self._artist_index[word] = []
                self._artist_index[word].append(i)
            
            # Index by mood
            mood = normalize_vietnamese(song.get('mood', '').lower())
            if mood:
                if mood not in self._mood_index:
                    self._mood_index[mood] = []
                self._mood_index[mood].append(i)
            
            # Index by genre
            genre = normalize_vietnamese(song.get('genre', '').lower())
            if genre:
                if genre not in self._genre_index:
                    self._genre_index[genre] = []
                self._genre_index[genre].append(i)
    
    def _create_document(self, song: Dict) -> str:
        """Create searchable document from song metadata with Vietnamese support."""
        parts = [
            song.get('song_name', ''),
            song.get('artist', ''),
            song.get('genre', ''),
            song.get('mood', ''),
            self._intensity_to_text(song.get('intensity', 2)),
            # Add lyrics if available (limited to reduce memory)
            (song.get('lyrics', '') or '')[:100]
        ]
        doc = ' '.join(filter(None, parts))
        
        # Add normalized version for Vietnamese fuzzy matching
        normalized = normalize_vietnamese(doc)
        
        # Add phonetic version for typo tolerance (already normalized inside)
        phonetic = phonetic_normalize(doc)
        
        return f"{doc} {normalized} {phonetic}"
    
    @staticmethod
    def _intensity_to_text(intensity: int) -> str:
        """Convert intensity number to text (Vietnamese + English)."""
        mapping = {
            1: 'low energy calm nhẹ nhàng thư giãn êm dịu peaceful quiet', 
            2: 'medium energy trung bình moderate balanced', 
            3: 'high energy intense sôi động mạnh mẽ powerful loud hype'
        }
        return mapping.get(intensity, '')
    
    def _calculate_exact_match_boost(self, query: str, song: Dict) -> float:
        """
        Calculate boost score for exact matches.
        Exact title/artist matches get significant boost.
        """
        query_norm = normalize_vietnamese(query.lower())
        query_words = set(query_norm.split())
        
        boost = 0.0
        
        # Title exact match = big boost
        title_norm = normalize_vietnamese(song.get('song_name', '').lower())
        if query_norm in title_norm or title_norm in query_norm:
            boost += 0.5
        elif query_words & set(title_norm.split()):
            boost += 0.2
        
        # Artist exact match = medium boost
        artist_norm = normalize_vietnamese(song.get('artist', '').lower())
        if query_norm in artist_norm or artist_norm in query_norm:
            boost += 0.3
        elif query_words & set(artist_norm.split()):
            boost += 0.1
        
        return min(boost, 0.6)  # Cap boost
    
    def _calculate_fuzzy_score(self, query: str, song: Dict) -> float:
        """Calculate fuzzy match score for typo tolerance."""
        title = song.get('song_name', '')
        artist = song.get('artist', '')
        
        title_score = fuzzy_match(query, title, threshold=0.6)
        artist_score = fuzzy_match(query, artist, threshold=0.6)
        
        return max(title_score, artist_score) * 0.3  # Weight fuzzy score
    
    def _exact_match_search(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Fast exact match search using inverted indexes.
        Returns immediately if exact match found.
        """
        query_norm = normalize_vietnamese(query.lower().strip())
        results = []
        
        # Check exact title match
        for i, song in enumerate(self.songs):
            title_norm = normalize_vietnamese(song.get('song_name', '').lower())
            if query_norm == title_norm:
                # Perfect match
                results.append((song, 1.0))
            elif query_norm in title_norm:
                # Substring match
                results.append((song, 0.9))
        
        if results:
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        
        return []
    
    def smart_search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0,
        use_fuzzy: bool = True,
        auto_correct: bool = True
    ) -> List[Tuple[Dict, float]]:
        """
        Intelligent search with intent detection and hybrid search.
        
        Flow:
        1. Detect query intent (title/artist/mood/genre/similar)
        2. Try exact match first (fast path)
        3. Route to appropriate search method
        4. Fall back to TF-IDF if needed
        
        Args:
            query: Search query
            top_k: Number of results
            min_score: Minimum score threshold
            use_fuzzy: Enable fuzzy matching
            auto_correct: Enable typo autocorrection
            
        Returns:
            List of (song, score) tuples
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{query}_{top_k}_{min_score}"
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
        
        # Auto-correct typos if enabled
        corrected_query = correct_typos(query) if auto_correct else query
        
        # Detect intent
        intent = detect_query_intent(
            corrected_query, 
            self._known_artists, 
            self._known_moods
        )
        
        results = []
        
        # Route based on intent
        if intent.intent == QueryIntent.ARTIST:
            # Search by artist
            results = self._search_by_artist(intent.extracted_value, top_k)
            
        elif intent.intent == QueryIntent.MOOD:
            # Search by mood
            mood_results = self.search_by_mood(intent.extracted_value, top_k=top_k)
            results = [(song, 0.8) for song in mood_results]
            
        elif intent.intent == QueryIntent.GENRE:
            # Search by genre using index
            genre_norm = normalize_vietnamese(intent.extracted_value.lower())
            if genre_norm in self._genre_index:
                indices = self._genre_index[genre_norm][:top_k]
                results = [(self.songs[i], 0.8) for i in indices]
            
        elif intent.intent == QueryIntent.TITLE and intent.confidence > 0.6:
            # Try exact match first
            results = self._exact_match_search(corrected_query, top_k)
        
        # If no results from intent-based search, fall back to TF-IDF
        if not results or len(results) < top_k // 2:
            tfidf_results = self.search(corrected_query, top_k, min_score, use_fuzzy)
            # Merge results, avoiding duplicates
            seen_ids = {song.get('song_id') for song, _ in results}
            for song, score in tfidf_results:
                if song.get('song_id') not in seen_ids:
                    results.append((song, score))
                    seen_ids.add(song.get('song_id'))
        
        # Sort by score and limit
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:top_k]
        
        # Cache results
        if self._cache:
            self._cache.put(cache_key, results)
        
        # Update stats
        elapsed = time.time() - start_time
        self._search_count += 1
        self._avg_search_time = (self._avg_search_time * (self._search_count - 1) + elapsed) / self._search_count
        
        return results
    
    def _search_by_artist(self, artist_query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """Search songs by artist name."""
        artist_norm = normalize_vietnamese(artist_query.lower())
        results = []
        
        # Use index if possible
        for word in artist_norm.split():
            if word in self._artist_index:
                for idx in self._artist_index[word]:
                    song = self.songs[idx]
                    song_artist = normalize_vietnamese(song.get('artist', '').lower())
                    score = fuzzy_match(artist_norm, song_artist, threshold=0.5)
                    if score > 0:
                        results.append((song, score))
        
        # Fallback: scan all songs
        if not results:
            for song in self.songs:
                song_artist = song.get('artist', '')
                score = fuzzy_match(artist_query, song_artist, threshold=0.5)
                if score > 0:
                    results.append((song, score))
        
        # Remove duplicates
        seen = set()
        unique_results = []
        for song, score in results:
            song_id = song.get('song_id')
            if song_id not in seen:
                seen.add(song_id)
                unique_results.append((song, score))
        
        unique_results.sort(key=lambda x: x[1], reverse=True)
        return unique_results[:top_k]
    
    def get_stats(self) -> Dict:
        """Get search engine statistics."""
        return {
            'total_songs': len(self.songs),
            'search_count': self._search_count,
            'avg_search_time_ms': self._avg_search_time * 1000,
            'cache_hit_rate': self._cache.hit_rate if self._cache else 0,
            'has_rapidfuzz': HAS_RAPIDFUZZ,
        }

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0,
        use_fuzzy: bool = True
    ) -> List[Tuple[Dict, float]]:
        """
        Search for songs matching query (supports Vietnamese input).
        
        Args:
            query: Search query string (Vietnamese or English)
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1)
            use_fuzzy: Enable fuzzy matching for typo tolerance
            
        Returns:
            List of (song, score) tuples, ranked by relevance
        """
        if self.vectorizer is None or self.tfidf_matrix is None:
            raise ValueError("Search engine not fitted. Call fit() first.")
        
        # Preprocess query for Vietnamese support
        processed_query = preprocess_query(query)
        
        try:
            # Vectorize query
            query_vec = self.vectorizer.transform([processed_query])
            
            # Fast cosine similarity using sklearn (10-50x faster than loop)
            # Use dense_output=False for sparse matrix efficiency
            tfidf_scores_dense = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        except Exception as e:
            print(f"Error in vectorization/similarity: {e}")
            # Return empty list if vectorization fails
            return []
        
        # Pre-filter candidates using inverted index for short queries
        candidate_indices = None
        query_normalized = normalize_vietnamese(query.lower())
        query_words = query_normalized.split()
        
        if len(query_words) <= 2:
            # Use index for short queries
            candidate_set = set()
            for word in query_words:
                if word in self._title_index:
                    candidate_set.update(self._title_index[word])
                if word in self._artist_index:
                    candidate_set.update(self._artist_index[word])
            if candidate_set:
                candidate_indices = candidate_set
        
        # Compute final scores with boost and fuzzy
        similarities = []
        indices_to_check = candidate_indices if candidate_indices else range(len(self.songs))
        
        for i in indices_to_check:
            try:
                # Safely get TFIDF score with fallback
                try:
                    tfidf_score = float(tfidf_scores_dense[i])
                except (TypeError, ValueError, IndexError):
                    tfidf_score = 0.0
                
                # Handle NaN values
                if tfidf_score != tfidf_score or np.isnan(tfidf_score):  # NaN check
                    tfidf_score = 0.0
                
                # Ensure score is in valid range
                tfidf_score = max(0.0, min(1.0, tfidf_score))
                
                song = self.songs[i]
                
                # Add exact match boost
                boost = self._calculate_exact_match_boost(query, song)
                
                # Add fuzzy match score if enabled and TF-IDF score is low
                fuzzy_score = 0.0
                if use_fuzzy and tfidf_score < 0.3:
                    fuzzy_score = self._calculate_fuzzy_score(query, song)
                
                # Weighted score (more explicit weighting)
                # TF-IDF: 60%, Exact boost: 30%, Fuzzy: 10%
                score = min(1.0, 0.6 * float(tfidf_score) + 0.3 * (float(boost) / 0.6 if boost > 0 else 0) + 0.1 * (float(fuzzy_score) / 0.3 if fuzzy_score > 0 else 0))
                
            except Exception as e:
                print(f"Warning: Error calculating score for song {i}: {e}")
                score = 0.0
                
            if score >= min_score:
                similarities.append((i, float(score)))
        
        # If using index but no results, fallback to full search
        if candidate_indices and not similarities:
            for i in range(len(self.songs)):
                if i in candidate_indices:
                    continue
                try:
                    tfidf_score = tfidf_scores[i]
                    if tfidf_score >= min_score:
                        similarities.append((i, tfidf_score))
                except Exception:
                    pass
        
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
    
    def search_similar(self, song_id: int, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Find songs similar to a given song (vectorized for performance).
        
        Args:
            song_id: ID of the reference song
            top_k: Number of similar songs to return
            
        Returns:
            List of (song, similarity_score) tuples
        """
        # Find the song in our list
        ref_song = None
        ref_idx = None
        for i, song in enumerate(self.songs):
            if song.get('song_id') == song_id:
                ref_song = song
                ref_idx = i
                break
        
        if ref_song is None or self.tfidf_matrix is None:
            return []
        
        try:
            # Fast vectorized cosine similarity
            ref_vec = self.tfidf_matrix[ref_idx]
            all_scores = cosine_similarity(ref_vec, self.tfidf_matrix)[0]
            
            # Build results with mood/genre boost
            similarities = []
            for i, song in enumerate(self.songs):
                if i == ref_idx:
                    continue  # Skip the reference song
                
                try:
                    score = float(all_scores[i])
                    if score != score or np.isnan(score):  # NaN check
                        score = 0.0
                except (TypeError, ValueError):
                    score = 0.0
                
                # Boost if same mood/genre
                if song.get('mood') == ref_song.get('mood'):
                    score = min(1.0, score + 0.1)
                if song.get('genre') == ref_song.get('genre'):
                    score = min(1.0, score + 0.1)
                
                similarities.append((song, score))
            
            # Sort and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
        except Exception as e:
            print(f"Error in search_similar: {e}")
            return []
    
    def search_by_mood(self, mood: str, intensity: Optional[int] = None, top_k: int = 10) -> List[Dict]:
        """
        Search songs by mood with optional intensity filter.
        
        Args:
            mood: Mood to search for (e.g., "Vui", "Buồn", "Chill")
            intensity: Optional intensity filter (1, 2, or 3)
            top_k: Number of results
            
        Returns:
            List of matching songs
        """
        mood_normalized = normalize_vietnamese(mood.lower())
        results = []
        
        for song in self.songs:
            song_mood = normalize_vietnamese(song.get('mood', '').lower())
            
            # Check mood match
            if mood_normalized in song_mood or song_mood in mood_normalized:
                # Check intensity if specified
                if intensity is None or song.get('intensity') == intensity:
                    results.append(song)
        
        return results[:top_k]
    
    def save(self, path: str) -> None:
        """Save vectorizer and indexes to file."""
        data = {
            'vectorizer': self.vectorizer,
            'songs': self.songs,
            'title_index': self._title_index,
            'artist_index': self._artist_index,
            'mood_index': self._mood_index,
            'genre_index': self._genre_index,
            'known_artists': self._known_artists,
            'known_moods': self._known_moods,
            'known_genres': self._known_genres,
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, path: str) -> None:
        """Load vectorizer and indexes from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self.vectorizer = data.get('vectorizer')
        self.songs = data.get('songs', [])
        self._title_index = data.get('title_index', {})
        self._artist_index = data.get('artist_index', {})
        self._mood_index = data.get('mood_index', {})
        self._genre_index = data.get('genre_index', {})
        self._known_artists = data.get('known_artists', set())
        self._known_moods = data.get('known_moods', set())
        self._known_genres = data.get('known_genres', set())
        
        # Rebuild TF-IDF matrix if songs are loaded
        if self.songs and self.vectorizer:
            documents = [self._create_document(song) for song in self.songs]
            self.tfidf_matrix = self.vectorizer.transform(documents)


# ================== CONVENIENCE FUNCTIONS ==================

# Global cached engine for repeated use
_cached_engine: Optional[TFIDFSearchEngine] = None
_cached_songs_hash: Optional[int] = None


def get_engine(songs: List[Dict], force_rebuild: bool = False) -> TFIDFSearchEngine:
    """
    Get or create a cached search engine instance.
    Avoids rebuilding the engine for every search.
    
    Args:
        songs: List of songs
        force_rebuild: Force rebuilding the engine
        
    Returns:
        Cached or new search engine
    """
    global _cached_engine, _cached_songs_hash
    
    songs_hash = hash(tuple(song.get('song_id') for song in songs))
    
    if force_rebuild or _cached_engine is None or _cached_songs_hash != songs_hash:
        _cached_engine = TFIDFSearchEngine(enable_cache=True)
        _cached_engine.fit(songs)
        _cached_songs_hash = songs_hash
    
    return _cached_engine


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


def smart_search(query: str, songs: List[Dict], top_k: int = 10) -> List[Tuple[Dict, float]]:
    """
    Intelligent search with caching, intent detection, and hybrid search.
    Uses cached engine for better performance.
    
    Args:
        query: Search query
        songs: List of songs
        top_k: Number of results
        
    Returns:
        List of (song, score) tuples
    """
    engine = get_engine(songs)
    return engine.smart_search(query, top_k=top_k)


def quick_search(query: str, songs: List[Dict], top_k: int = 10) -> List[Tuple[Dict, float]]:
    """
    Quick TF-IDF search without intent detection.
    
    Args:
        query: Search query
        songs: List of songs
        top_k: Number of results
        
    Returns:
        List of (song, score) tuples
    """
    engine = get_engine(songs)
    return engine.search(query, top_k=top_k)


def autocomplete(prefix: str, songs: List[Dict], top_k: int = 5) -> List[str]:
    """
    Quick autocomplete suggestions.
    
    Args:
        prefix: Prefix to match
        songs: List of songs
        top_k: Number of suggestions
        
    Returns:
        List of song title suggestions
    """
    engine = get_engine(songs)
    return engine.suggest(prefix, top_k=top_k)


def search_by_mood(mood: str, songs: List[Dict], intensity: int = None, top_k: int = 10) -> List[Dict]:
    """
    Search songs by mood.
    
    Args:
        mood: Mood name
        songs: List of songs
        intensity: Optional intensity filter (1, 2, 3)
        top_k: Number of results
        
    Returns:
        List of matching songs
    """
    engine = get_engine(songs)
    return engine.search_by_mood(mood, intensity=intensity, top_k=top_k)


def find_similar(song_id: int, songs: List[Dict], top_k: int = 5) -> List[Tuple[Dict, float]]:
    """
    Find songs similar to a given song.
    
    Args:
        song_id: ID of reference song
        songs: List of songs
        top_k: Number of results
        
    Returns:
        List of (song, score) tuples
    """
    engine = get_engine(songs)
    return engine.search_similar(song_id, top_k=top_k)
