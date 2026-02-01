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
    is_greeting: bool = False  # True if text is a greeting, not a mood


# ================== GREETING PATTERNS ==================
# Patterns for greetings and introductions (NOT mood expressions)
GREETING_PATTERNS = [
    # Vietnamese greetings
    r'\bchào\b', r'\bxin chào\b', r'\bchao\b', r'\bxin chao\b',
    r'\bhello\b', r'\bhi\b', r'\bhey\b', r'\bhai\b',
    # Self introductions
    r'\btôi là\b', r'\bmình là\b', r'\btên (tôi|mình) là\b',
    r'\btoi la\b', r'\bminh la\b', r'\bten (toi|minh) la\b',
    r'\bi am\b', r"\bi'm\b", r'\bmy name is\b',
    # Casual greetings
    r'\bxin lỗi\b', r'\bcảm ơn\b', r'\bxin loi\b', r'\bcam on\b',
    r'\bchào buổi sáng\b', r'\bchào buổi tối\b',
    r'\bgood morning\b', r'\bgood evening\b', r'\bgood night\b',
    # Questions about bot
    r'\bbạn là ai\b', r'\bban la ai\b', r'\bwho are you\b',
    r'\bbạn tên gì\b', r'\bban ten gi\b', r'\bwhat.s your name\b',
    # Casual
    r'^chào$', r'^hi$', r'^hello$', r'^hey$', r'^xin chào$',
]


def is_greeting(text: str) -> bool:
    """
    Check if text is a greeting/introduction, not a mood expression
    
    Args:
        text: User input text
        
    Returns:
        True if text is a greeting, False otherwise
    """
    text_lower = text.lower().strip()
    
    # Check each greeting pattern
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, text_lower):
            # Make sure it's not followed by mood words
            # e.g. "chào, tôi đang buồn" is NOT just a greeting
            mood_indicators = [
                'buồn', 'vui', 'stress', 'lo lắng', 'mệt', 'chán', 
                'hạnh phúc', 'tức giận', 'bình yên', 'năng lượng',
                'buon', 'lo lang', 'met', 'chan', 'hanh phuc', 'tuc gian', 'binh yen', 'nang luong',
                'sad', 'happy', 'stressed', 'tired', 'bored', 'angry', 'peaceful', 'energetic'
            ]
            has_mood = any(mood in text_lower for mood in mood_indicators)
            if not has_mood:
                return True
    
    return False


# ================== VIETNAMESE MOOD KEYWORDS ==================

MOOD_KEYWORDS_VI = {
    "Vui": {
        "high": ["hạnh phúc", "sung sướng", "phấn khởi", "tuyệt vời", "hân hoan", "vui sướng", "rất vui",
                 "hanh phuc", "sung suong", "phan khoi", "tuyet voi", "han hoan", "vui suong", "rat vui"],
        "medium": ["vui", "vui vẻ", "tươi vui", "thích", "yêu đời", "hào hứng", "phấn chấn",
                   "vui ve", "tuoi vui", "thich", "yeu doi", "hao hung", "phan chan", "happy"],
        "low": ["ok", "ổn", "được", "tạm", "bình thường", "cũng được", "on", "duoc", "tam", "binh thuong", "cung duoc"]
    },
    "Buồn": {
        "high": ["đau khổ", "tan nát", "tuyệt vọng", "khóc", "thất vọng", "đau lòng", "chết lặng",
                 "dau kho", "tan nat", "tuyet vong", "khoc", "that vong", "dau long", "chet lang"],
        "medium": ["buồn", "buồn bã", "u sầu", "thất tình", "nhớ nhung", "cô đơn", "lẻ loi",
                   "buon", "buon ba", "u sau", "that tinh", "nho nhung", "co don", "le loi", "sad"],
        "low": ["hơi buồn", "tâm trạng", "không vui", "chán", "mệt mỏi", "uể oải",
                "hoi buon", "tam trang", "khong vui", "chan", "met moi", "ue oai"]
    },
    "Suy tư": {
        "high": ["suy nghĩ nhiều", "trăn trở", "dằn vặt", "lo lắng", "hoang mang",
                 "suy nghi nhieu", "tran tro", "dan vat", "lo lang", "hoang mang"],
        "medium": ["suy tư", "nghĩ ngợi", "suy ngẫm", "tập trung", "trầm ngâm", "thư thái",
                   "suy tu", "nghi ngoi", "suy ngam", "tap trung", "tram ngam", "thu thai", "thinking"],
        "low": ["nghĩ", "đang nghĩ", "suy", "tĩnh lặng", "nghi", "dang nghi", "tinh lang"]
    },
    "Chill": {  
        "high": ["cực chill", "thư giãn cực", "siêu relax", "bình yên tuyệt đối",
                 "cuc chill", "thu gian cuc", "sieu relax", "binh yen tuyet doi"],
        "medium": ["chill", "thư giãn", "relax", "bình yên", "nhẹ nhàng", "êm đềm", "an yên",
                   "thu gian", "binh yen", "nhe nhang", "em dem", "an yen", "thoai mai", "thoải mái"],
        "low": ["nghỉ ngơi", "thảnh thơi", "rảnh", "nhàn nhã", "nghi ngoi", "thanh thoi", "ranh", "nhan nha"]
    },
    "Năng lượng": {
        "high": ["cực kỳ hứng khởi", "bùng nổ", "siêu năng lượng", "cuồng nhiệt", "cháy hết mình",
                 "cuc ky hung khoi", "bung no", "sieu nang luong", "cuong nhiet", "chay het minh"],
        "medium": ["năng lượng", "sôi động", "hứng khởi", "quẩy", "nhảy", "dance", "chạy",
                   "nang luong", "soi dong", "hung khoi", "quay", "nhay", "chay", "energy", "workout"],
        "low": ["có năng lượng", "tỉnh táo", "sảng khoái", "khỏe", "co nang luong", "tinh tao", "sang khoai", "khoe"]
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


# ================== AI-POWERED MOOD DETECTION ==================

import os
import json

# Supported AI providers
AI_PROVIDERS = ["gemini", "openai", "ollama"]

def _get_ai_config() -> Dict:
    """Get AI configuration from environment or .env file"""
    config = {
        "provider": os.environ.get("AI_PROVIDER", "gemini"),
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
        "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
        "ollama_url": os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        "ollama_model": os.environ.get("OLLAMA_MODEL", "llama2"),
    }
    
    # Try to load from .env file
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key == "GEMINI_API_KEY" and value:
                            config["gemini_api_key"] = value
                        elif key == "OPENAI_API_KEY" and value:
                            config["openai_api_key"] = value
                        elif key == "AI_PROVIDER" and value:
                            config["provider"] = value
        except:
            pass
    
    return config


def detect_mood_with_ai(text: str) -> Optional[MoodScore]:
    """
    Use AI to detect mood when keyword matching fails
    Supports: Google Gemini (free), OpenAI GPT, Local Ollama
    
    Args:
        text: User input text
        
    Returns:
        MoodScore if successful, None if AI unavailable
    """
    config = _get_ai_config()
    
    prompt = f"""Analyze this Vietnamese/English text and detect the user's mood.
Text: "{text}"

Choose ONE mood from: Vui (happy), Buồn (sad), Suy tư (thoughtful), Chill (relaxed), Năng lượng (energetic)
Choose intensity from: Nhẹ (light), Vừa (medium), Mạnh (strong)

Respond in JSON format only:
{{"mood": "...", "intensity": "...", "confidence": 0.0-1.0, "reason": "..."}}"""

    try:
        # Try Gemini first (free tier available)
        if config["gemini_api_key"]:
            result = _call_gemini(prompt, config["gemini_api_key"])
            if result:
                return result
        
        # Try OpenAI
        if config["openai_api_key"]:
            result = _call_openai(prompt, config["openai_api_key"])
            if result:
                return result
        
        # Try local Ollama
        result = _call_ollama(prompt, config["ollama_url"], config["ollama_model"])
        if result:
            return result
            
    except Exception as e:
        print(f"AI mood detection error: {e}")
    
    return None


def _call_gemini(prompt: str, api_key: str) -> Optional[MoodScore]:
    """Call Google Gemini API"""
    import requests
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 200
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_ai_response(text)
    except Exception as e:
        print(f"Gemini API error: {e}")
    
    return None


def _call_openai(prompt: str, api_key: str) -> Optional[MoodScore]:
    """Call OpenAI GPT API"""
    import requests
    
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            return _parse_ai_response(text)
    except Exception as e:
        print(f"OpenAI API error: {e}")
    
    return None


def _call_ollama(prompt: str, base_url: str, model: str) -> Optional[MoodScore]:
    """Call local Ollama API"""
    import requests
    
    url = f"{base_url}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            text = data.get("response", "")
            return _parse_ai_response(text)
    except:
        pass  # Ollama might not be running
    
    return None


def _parse_ai_response(text: str) -> Optional[MoodScore]:
    """Parse AI response JSON to MoodScore"""
    try:
        # Extract JSON from response
        json_match = re.search(r'\{[^{}]*\}', text)
        if json_match:
            data = json.loads(json_match.group())
            
            mood = data.get("mood", "Chill")
            # Normalize mood names
            mood_map = {
                "happy": "Vui", "vui": "Vui",
                "sad": "Buồn", "buon": "Buồn", "buồn": "Buồn",
                "thoughtful": "Suy tư", "suy tu": "Suy tư", "suy tư": "Suy tư",
                "relaxed": "Chill", "chill": "Chill",
                "energetic": "Năng lượng", "nang luong": "Năng lượng", "năng lượng": "Năng lượng"
            }
            mood = mood_map.get(mood.lower(), mood)
            
            intensity = data.get("intensity", "Vừa")
            intensity_map = {
                "light": "Nhẹ", "nhe": "Nhẹ", "nhẹ": "Nhẹ",
                "medium": "Vừa", "vua": "Vừa", "vừa": "Vừa",
                "strong": "Mạnh", "manh": "Mạnh", "mạnh": "Mạnh"
            }
            intensity = intensity_map.get(intensity.lower(), intensity)
            
            confidence = float(data.get("confidence", 0.7))
            reason = data.get("reason", "AI detected")
            
            return MoodScore(
                mood=mood,
                confidence=min(0.95, confidence),
                keywords_matched=[f"AI: {reason}"],
                intensity=intensity
            )
    except Exception as e:
        print(f"AI response parse error: {e}")
    
    return None


def detect_mood_smart(text: str) -> MoodScore:
    """
    Smart mood detection: greeting check -> keyword -> AI fallback
    
    Args:
        text: User input text
        
    Returns:
        MoodScore with best detection result, or greeting indicator
    """
    # Check for greetings/introductions first
    if is_greeting(text):
        return MoodScore(
            mood="greeting",  # Special indicator
            confidence=1.0,
            keywords_matched=["greeting detected"],
            intensity="",
            is_greeting=True
        )
    
    # Try keyword matching first (fast)
    result = text_mood_detector.detect(text)
    
    # If confidence is high enough, return
    if result.confidence >= 0.4 and result.keywords_matched:
        return result
    
    # Try AI fallback (slower but smarter)
    ai_result = detect_mood_with_ai(text)
    if ai_result and ai_result.confidence > result.confidence:
        return ai_result
    
    # Return keyword result even if low confidence
    return result


# ================== CONVERSATIONAL AI FUNCTIONS ==================

def generate_conversation_response(conversation_history: list, turn_number: int) -> str:
    """
    Generate a natural conversational response using Gemini AI
    to understand user's mood through 3-4 turns of dialogue
    
    Args:
        conversation_history: List of {"role": "user/bot", "text": "..."}
        turn_number: Current conversation turn (1-4)
        
    Returns:
        Bot's response text
    """
    config = _get_ai_config()
    
    if not config["gemini_api_key"]:
        # Fallback responses if no API
        fallback_questions = [
            "Chào bạn! Hôm nay của bạn thế nào? Có chuyện gì vui không? 😊",
            "Mình hiểu rồi. Vậy gần đây bạn có điều gì khiến bạn suy nghĩ nhiều không?",
            "Cảm ơn bạn đã chia sẻ! Bạn muốn nghe nhạc để thư giãn hay để có thêm năng lượng?",
            "Okay! Mình đã hiểu mood của bạn rồi. Để mình tìm bài hát phù hợp nhé! 🎵"
        ]
        return fallback_questions[min(turn_number - 1, 3)]
    
    # Build conversation context for Gemini
    history_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Bot'}: {msg['text']}" 
        for msg in conversation_history
    ])
    
    prompt = f"""Bạn là MusicMoodBot - một chatbot thân thiện giúp người dùng tìm nhạc theo tâm trạng.
Nhiệm vụ: Trò chuyện tự nhiên 3-4 câu để hiểu cảm xúc/tâm trạng của người dùng.

Cuộc hội thoại hiện tại (turn {turn_number}/4):
{history_text}

Hướng dẫn:
- Turn 1: Chào hỏi thân thiện, hỏi về ngày hôm nay/cảm xúc
- Turn 2: Hỏi thêm chi tiết, thể hiện sự quan tâm
- Turn 3: Hỏi về mong muốn nghe nhạc như thế nào
- Turn 4: Tổng kết và nói sẽ tìm nhạc phù hợp

Quy tắc:
- Trả lời ngắn gọn (1-2 câu), tự nhiên, thân thiện
- Dùng emoji phù hợp
- Không hỏi về mood trực tiếp, mà hỏi về cuộc sống/ngày hôm nay
- Nếu user đã thể hiện rõ mood, có thể kết thúc sớm

Chỉ trả về câu trả lời của Bot, không giải thích thêm."""

    try:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={config['gemini_api_key']}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 150
            }
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Gemini conversation error: {e}")
    
    # Fallback
    return "Mình hiểu rồi! Bạn có thể kể thêm về cảm xúc của bạn được không? 😊"


def analyze_conversation_mood(conversation_history: list) -> MoodScore:
    """
    Analyze the entire conversation to determine user's mood
    
    Args:
        conversation_history: List of {"role": "user/bot", "text": "..."}
        
    Returns:
        MoodScore with detected mood from conversation
    """
    config = _get_ai_config()
    
    # Extract only user messages for analysis
    user_messages = [msg["text"] for msg in conversation_history if msg["role"] == "user"]
    combined_text = " ".join(user_messages)
    
    if not config["gemini_api_key"]:
        # Fallback to keyword detection on combined text
        return text_mood_detector.detect(combined_text)
    
    history_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Bot'}: {msg['text']}" 
        for msg in conversation_history
    ])
    
    prompt = f"""Phân tích cuộc hội thoại sau và xác định tâm trạng của người dùng.

Cuộc hội thoại:
{history_text}

Chọn MỘT mood phù hợp nhất từ: Vui, Buồn, Suy tư, Chill, Năng lượng
Chọn intensity: Nhẹ, Vừa, Mạnh

Trả lời theo format JSON:
{{"mood": "...", "intensity": "...", "confidence": 0.0-1.0, "reason": "giải thích ngắn gọn"}}"""

    try:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={config['gemini_api_key']}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 200
            }
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            result = _parse_ai_response(text)
            if result:
                return result
    except Exception as e:
        print(f"Gemini mood analysis error: {e}")
    
    # Fallback to keyword detection
    return text_mood_detector.detect(combined_text)


def should_end_conversation(conversation_history: list, turn_number: int) -> bool:
    """
    Check if conversation should end early (user expressed clear mood)
    
    Args:
        conversation_history: Conversation history
        turn_number: Current turn
        
    Returns:
        True if should end and recommend songs
    """
    if turn_number >= 4:
        return True
    
    if turn_number < 2:
        return False
    
    # Check last user message for clear mood indicators
    if conversation_history:
        last_user_msgs = [m for m in conversation_history if m["role"] == "user"]
        if last_user_msgs:
            last_text = last_user_msgs[-1]["text"].lower()
            
            # Clear mood keywords
            clear_indicators = [
                # Direct mood statements
                "tôi buồn", "toi buon", "đang buồn", "rất buồn",
                "tôi vui", "toi vui", "đang vui", "rất vui",
                "tôi stress", "đang stress", "căng thẳng",
                "muốn chill", "muon chill", "thư giãn",
                "cần năng lượng", "can nang luong", "cần hưng phấn",
                # Direct requests
                "cho tôi nghe", "gợi ý bài", "recommend", "đề xuất",
                "tìm bài", "nghe nhạc đi", "bật nhạc"
            ]
            
            if any(ind in last_text for ind in clear_indicators):
                return True
    
    return False