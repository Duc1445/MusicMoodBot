"""
Text-based Mood Detection using NLP
Detects user mood from Vietnamese/English text input
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MoodScore:
    """Mood detection result"""
    mood: str
    confidence: float
    keywords_matched: List[str]
    intensity: str  # "Nhẹ", "Vừa", "Mạnh"


# ================== VIETNAMESE MOOD KEYWORDS ==================

MOOD_KEYWORDS_VI = {
    "Vui": {
        "high": ["hạnh phúc", "sung sướng", "phấn khởi", "tuyệt vời", "hân hoan", "vui sướng", "rất vui"],
        "medium": ["vui", "vui vẻ", "tươi vui", "thích", "yêu đời", "hào hứng", "phấn chấn"],
        "low": ["ok", "ổn", "được", "tạm", "bình thường", "cũng được"]
    },
    "Buồn": {
        "high": ["đau khổ", "tan nát", "tuyệt vọng", "khóc", "thất vọng", "đau lòng", "chết lặng"],
        "medium": ["buồn", "buồn bã", "u sầu", "thất tình", "nhớ nhung", "cô đơn", "lẻ loi"],
        "low": ["hơi buồn", "tâm trạng", "không vui", "chán", "mệt mỏi", "uể oải"]
    },
    "Suy tư": {
        "high": ["suy nghĩ nhiều", "trăn trở", "dằn vặt", "lo lắng", "hoang mang"],
        "medium": ["suy tư", "nghĩ ngợi", "suy ngẫm", "tập trung", "trầm ngâm", "thư thái"],
        "low": ["nghĩ", "đang nghĩ", "suy", "tĩnh lặng"]
    },
    "Chill": {
        "high": ["cực chill", "thư giãn cực", "siêu relax", "bình yên tuyệt đối"],
        "medium": ["chill", "thư giãn", "relax", "bình yên", "nhẹ nhàng", "êm đềm", "an yên"],
        "low": ["nghỉ ngơi", "thảnh thơi", "rảnh", "nhàn nhã"]
    },
    "Năng lượng": {
        "high": ["cực kỳ hứng khởi", "bùng nổ", "siêu năng lượng", "cuồng nhiệt", "cháy hết mình"],
        "medium": ["năng lượng", "sôi động", "hứng khởi", "quẩy", "nhảy", "dance", "chạy"],
        "low": ["có năng lượng", "tỉnh táo", "sảng khoái", "khỏe"]
    }
}

# English mood keywords
MOOD_KEYWORDS_EN = {
    "Vui": {
        "high": ["ecstatic", "thrilled", "overjoyed", "elated", "euphoric"],
        "medium": ["happy", "joyful", "cheerful", "delighted", "glad", "pleased"],
        "low": ["okay", "fine", "alright", "content"]
    },
    "Buồn": {
        "high": ["devastated", "heartbroken", "depressed", "miserable", "crying"],
        "medium": ["sad", "unhappy", "upset", "down", "blue", "lonely", "gloomy"],
        "low": ["a bit sad", "melancholy", "wistful"]
    },
    "Suy tư": {
        "high": ["deeply thinking", "contemplating", "overthinking", "anxious"],
        "medium": ["thinking", "thoughtful", "pensive", "reflective", "focused"],
        "low": ["wondering", "curious"]
    },
    "Chill": {
        "high": ["super relaxed", "totally zen", "peaceful"],
        "medium": ["chill", "relaxed", "calm", "peaceful", "tranquil", "serene"],
        "low": ["resting", "taking it easy"]
    },
    "Năng lượng": {
        "high": ["pumped", "fired up", "hyper", "on fire", "explosive"],
        "medium": ["energetic", "excited", "active", "lively", "dynamic", "workout"],
        "low": ["awake", "alert", "ready"]
    }
}

# Intensity modifiers
INTENSITY_BOOSTERS = ["rất", "cực", "siêu", "quá", "vô cùng", "cực kỳ", "very", "super", "extremely", "so"]
INTENSITY_REDUCERS = ["hơi", "một chút", "tí", "chút", "a bit", "a little", "slightly", "somewhat"]

# Negation words
NEGATIONS = ["không", "chẳng", "chả", "đâu", "not", "no", "don't", "doesn't", "never", "isn't"]


class TextMoodDetector:
    """
    Detects mood from Vietnamese/English text using keyword matching
    and simple sentiment analysis
    """
    
    def __init__(self):
        self.mood_keywords_vi = MOOD_KEYWORDS_VI
        self.mood_keywords_en = MOOD_KEYWORDS_EN
        
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching"""
        text = text.lower().strip()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove punctuation except essential
        text = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF]', ' ', text)
        return text
    
    def _check_negation(self, text: str, keyword: str) -> bool:
        """Check if keyword is negated"""
        pattern = rf'({"|".join(NEGATIONS)})\s+\w*\s*{re.escape(keyword)}'
        return bool(re.search(pattern, text))
    
    def _calculate_intensity(self, text: str, base_intensity: str) -> str:
        """Calculate final intensity based on modifiers"""
        intensity_map = {"low": 1, "medium": 2, "high": 3}
        reverse_map = {1: "Nhẹ", 2: "Vừa", 3: "Mạnh"}
        
        score = intensity_map.get(base_intensity, 2)
        
        # Check for boosters
        for booster in INTENSITY_BOOSTERS:
            if booster in text:
                score = min(3, score + 1)
                break
        
        # Check for reducers
        for reducer in INTENSITY_REDUCERS:
            if reducer in text:
                score = max(1, score - 1)
                break
        
        return reverse_map[score]
    
    def _match_keywords(self, text: str, keywords_dict: Dict) -> Tuple[List[str], str]:
        """Match keywords and return matched words with intensity"""
        matched = []
        best_intensity = "low"
        intensity_order = ["low", "medium", "high"]
        
        for intensity in intensity_order:
            for keyword in keywords_dict.get(intensity, []):
                if keyword in text:
                    if not self._check_negation(text, keyword):
                        matched.append(keyword)
                        if intensity_order.index(intensity) > intensity_order.index(best_intensity):
                            best_intensity = intensity
        
        return matched, best_intensity
    
    def detect(self, text: str) -> MoodScore:
        """
        Detect mood from text
        
        Args:
            text: User input text (Vietnamese or English)
            
        Returns:
            MoodScore with detected mood, confidence, and keywords
        """
        normalized = self._normalize_text(text)
        
        mood_scores: Dict[str, Tuple[float, List[str], str]] = {}
        
        for mood in self.mood_keywords_vi:
            # Check Vietnamese keywords
            matched_vi, intensity_vi = self._match_keywords(normalized, self.mood_keywords_vi[mood])
            # Check English keywords
            matched_en, intensity_en = self._match_keywords(normalized, self.mood_keywords_en[mood])
            
            all_matched = matched_vi + matched_en
            
            # Calculate score based on matches
            if all_matched:
                # Weight by number of matches and keyword length
                score = sum(len(kw) for kw in all_matched) / 10.0
                score = min(1.0, score * len(all_matched))
                
                # Determine best intensity
                best_intensity = intensity_en if len(matched_en) > len(matched_vi) else intensity_vi
                
                mood_scores[mood] = (score, all_matched, best_intensity)
        
        if not mood_scores:
            # Default to Chill if no mood detected
            return MoodScore(
                mood="Chill",
                confidence=0.3,
                keywords_matched=[],
                intensity="Vừa"
            )
        
        # Find best matching mood
        best_mood = max(mood_scores, key=lambda m: mood_scores[m][0])
        score, matched, base_intensity = mood_scores[best_mood]
        
        # Calculate final intensity considering text modifiers
        final_intensity = self._calculate_intensity(normalized, base_intensity)
        
        return MoodScore(
            mood=best_mood,
            confidence=min(0.95, score),
            keywords_matched=matched,
            intensity=final_intensity
        )
    
    def detect_with_alternatives(self, text: str, top_k: int = 3) -> List[MoodScore]:
        """
        Detect mood with alternative suggestions
        
        Args:
            text: User input text
            top_k: Number of mood alternatives to return
            
        Returns:
            List of MoodScore sorted by confidence
        """
        normalized = self._normalize_text(text)
        results = []
        
        for mood in self.mood_keywords_vi:
            matched_vi, intensity_vi = self._match_keywords(normalized, self.mood_keywords_vi[mood])
            matched_en, intensity_en = self._match_keywords(normalized, self.mood_keywords_en[mood])
            
            all_matched = matched_vi + matched_en
            
            if all_matched:
                score = sum(len(kw) for kw in all_matched) / 10.0
                score = min(1.0, score * len(all_matched))
                best_intensity = intensity_en if len(matched_en) > len(matched_vi) else intensity_vi
                final_intensity = self._calculate_intensity(normalized, best_intensity)
                
                results.append(MoodScore(
                    mood=mood,
                    confidence=min(0.95, score),
                    keywords_matched=all_matched,
                    intensity=final_intensity
                ))
        
        # Sort by confidence descending
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        # If no results, add default
        if not results:
            results.append(MoodScore(
                mood="Chill",
                confidence=0.3,
                keywords_matched=[],
                intensity="Vừa"
            ))
        
        return results[:top_k]


# Singleton instance
text_mood_detector = TextMoodDetector()


def detect_mood_from_text(text: str) -> Dict:
    """
    Convenience function to detect mood from text
    
    Args:
        text: User input text
        
    Returns:
        Dict with mood, confidence, keywords, intensity
    """
    result = text_mood_detector.detect(text)
    return {
        "mood": result.mood,
        "confidence": result.confidence,
        "keywords_matched": result.keywords_matched,
        "intensity": result.intensity
    }
