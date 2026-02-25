"""
=============================================================================
GEMINI AI SERVICE
=============================================================================

Integration with Google Gemini for natural language understanding.
Provides mood detection, intent classification, and conversational responses.

Author: MusicMoodBot Team
Version: 1.0.0
=============================================================================
"""

import os
import json
import sqlite3
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Try to import google.generativeai
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


class UserIntent(str, Enum):
    """User intent classification."""
    GREETING = "greeting"
    MOOD_EXPRESSION = "mood_expression"
    MUSIC_REQUEST = "music_request"
    QUESTION = "question"
    FEEDBACK = "feedback"
    CHITCHAT = "chitchat"
    UNCLEAR = "unclear"


@dataclass
class AIResponse:
    """Response from AI service."""
    bot_message: str
    detected_mood: Optional[str] = None
    mood_confidence: float = 0.0
    intent: UserIntent = UserIntent.UNCLEAR
    should_recommend: bool = False
    suggested_genres: List[str] = None
    energy_level: Optional[str] = None  # "low", "medium", "high"
    
    def __post_init__(self):
        if self.suggested_genres is None:
            self.suggested_genres = []


class GeminiService:
    """Service for Gemini AI integration."""
    
    # Mood mapping for database queries
    MOOD_MAP = {
        "vui": "happy", "happy": "happy", "vui vẻ": "happy", "hạnh phúc": "happy",
        "buồn": "sad", "sad": "sad", "buồn bã": "sad", "u sầu": "sad", "melancholy": "sad",
        "chill": "calm", "thư giãn": "calm", "calm": "calm", "bình yên": "calm", "relaxed": "calm",
        "năng động": "energetic", "energetic": "energetic", "sôi động": "energetic", "hype": "energetic",
        "tức giận": "angry", "angry": "angry", "khó chịu": "angry", "bực": "angry",
        "stress": "stress", "căng thẳng": "stress", "lo lắng": "anxious", "anxious": "stress",
        "lãng mạn": "romantic", "romantic": "romantic", "tình cảm": "romantic",
        "tập trung": "focus", "focus": "focus", "làm việc": "focus",
        "mệt mỏi": "tired", "tired": "tired", "kiệt sức": "tired",
        "cô đơn": "lonely", "lonely": "lonely",
        "hoài niệm": "nostalgic", "nostalgic": "nostalgic", "nhớ": "nostalgic",
    }
    
    # Vietnamese mood names for responses
    MOOD_VI = {
        "happy": "vui", "sad": "buồn", "calm": "thư giãn", "energetic": "năng động",
        "angry": "khó chịu", "stress": "căng thẳng", "romantic": "lãng mạn",
        "focus": "tập trung", "tired": "mệt mỏi", "lonely": "cô đơn",
        "nostalgic": "hoài niệm", "anxious": "lo lắng"
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini service."""
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model = None
        
        # Find database path
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(backend_dir, "src", "database", "music.db")
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Try different model names - the available models depend on API key tier
                model_names = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro', 'models/gemini-pro']
                for model_name in model_names:
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        # Test the model
                        test_response = self.model.generate_content("test")
                        print(f"✓ Gemini AI initialized with model: {model_name}")
                        break
                    except Exception as model_err:
                        print(f"  Model {model_name} not available: {model_err}")
                        self.model = None
                        continue
            except Exception as e:
                print(f"⚠ Gemini init error: {e}")
                self.model = None
        else:
            if not GEMINI_AVAILABLE:
                print("⚠ google-generativeai not installed. Using fallback NLP.")
            elif not self.api_key:
                print("⚠ No Gemini API key. Set GEMINI_API_KEY env var. Using fallback NLP.")
    
    def is_available(self) -> bool:
        """Check if Gemini is available."""
        return self.model is not None
    
    def get_available_songs_context(self) -> str:
        """Get context about available songs for AI."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get unique artists
            cursor.execute("SELECT DISTINCT artist FROM songs")
            artists = [row[0] for row in cursor.fetchall()]
            
            # Get unique genres 
            cursor.execute("SELECT DISTINCT genre FROM songs")
            genres = [row[0] for row in cursor.fetchall()]
            
            # Get unique moods
            cursor.execute("SELECT DISTINCT mood FROM songs")
            moods = [row[0] for row in cursor.fetchall()]
            
            # Get sample songs
            cursor.execute("SELECT song_name, artist, genre, mood FROM songs LIMIT 10")
            samples = cursor.fetchall()
            
            conn.close()
            
            context = f"""
Database có các nghệ sĩ: {', '.join(artists[:10])}
Các thể loại: {', '.join(genres)}
Các mood trong database: {', '.join(moods)}
Ví dụ bài hát: {', '.join([f'"{s[0]}" - {s[1]} ({s[2]}, {s[3]})' for s in samples[:5]])}
"""
            return context
        except Exception as e:
            print(f"Error getting song context: {e}")
            return "Database có nhiều bài hát V-Pop, Rock, Ballad với các mood khác nhau."
    
    async def analyze_message(self, message: str, conversation_history: List[Dict] = None) -> AIResponse:
        """
        Analyze user message using Gemini AI.
        
        Args:
            message: User's message
            conversation_history: Previous conversation turns
            
        Returns:
            AIResponse with mood, intent, and bot message
        """
        if not self.is_available():
            return self._fallback_analyze(message)
        
        try:
            # Build prompt
            songs_context = self.get_available_songs_context()
            history_text = ""
            if conversation_history:
                history_text = "\n".join([
                    f"User: {h.get('user', '')}\nBot: {h.get('bot', '')}"
                    for h in conversation_history[-3:]  # Last 3 turns
                ])
            
            prompt = f"""Bạn là MusicMoodBot - một chatbot gợi ý nhạc thông minh bằng tiếng Việt.

CONTEXT DATABASE:
{songs_context}

LỊCH SỬ HỘI THOẠI:
{history_text}

TIN NHẮN MỚI CỦA USER: "{message}"

NHIỆM VỤ: Phân tích tin nhắn và trả về JSON với format sau:
{{
    "intent": "greeting|mood_expression|music_request|question|feedback|chitchat|unclear",
    "detected_mood": "happy|sad|calm|energetic|angry|stress|romantic|focus|tired|lonely|nostalgic|null",
    "mood_confidence": 0.0-1.0,
    "should_recommend": true/false,
    "energy_level": "low|medium|high|null",
    "suggested_genres": ["Pop", "Rock", "Ballad", ...] hoặc [],
    "bot_message": "Câu trả lời tự nhiên, thân thiện bằng tiếng Việt"
}}

QUY TẮC:
1. Nếu user chào hỏi → intent="greeting", should_recommend=false
2. Nếu user diễn tả cảm xúc rõ → intent="mood_expression", phân tích mood
3. Nếu user muốn nghe nhạc cụ thể → intent="music_request", should_recommend=true
4. Nếu chưa rõ mood → hỏi thêm bằng câu tự nhiên, should_recommend=false
5. Sau 2-3 turns đã hiểu user → should_recommend=true
6. Bot message phải thân thiện, tự nhiên như người thật
7. Nếu user nhắc đến nghệ sĩ/thể loại cụ thể → ghi vào suggested_genres

CHỈ TRẢ VỀ JSON, KHÔNG CÓ TEXT KHÁC."""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse JSON from response
            # Handle markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            data = json.loads(response_text)
            
            return AIResponse(
                bot_message=data.get("bot_message", "Mình hiểu rồi! Bạn muốn nghe nhạc gì?"),
                detected_mood=data.get("detected_mood"),
                mood_confidence=float(data.get("mood_confidence", 0.5)),
                intent=UserIntent(data.get("intent", "unclear")),
                should_recommend=data.get("should_recommend", False),
                suggested_genres=data.get("suggested_genres", []),
                energy_level=data.get("energy_level"),
            )
            
        except Exception as e:
            print(f"Gemini error: {e}")
            return self._fallback_analyze(message)
    
    def analyze_message_sync(self, message: str, conversation_history: List[Dict] = None) -> AIResponse:
        """Synchronous version of analyze_message."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.analyze_message(message, conversation_history))
    
    def _fallback_analyze(self, message: str) -> AIResponse:
        """Fallback analysis when Gemini is not available."""
        message_lower = message.lower()
        
        # Check for greetings
        greetings = ["chào", "hello", "hi", "xin chào", "hey"]
        if any(g in message_lower for g in greetings):
            return AIResponse(
                bot_message="Chào bạn! Hôm nay bạn cảm thấy thế nào? Mình sẽ gợi ý nhạc phù hợp cho bạn nhé! 🎵",
                intent=UserIntent.GREETING,
                should_recommend=False
            )
        
        # Check for mood keywords
        detected_mood = None
        mood_confidence = 0.0
        
        for vi_mood, en_mood in self.MOOD_MAP.items():
            if vi_mood in message_lower:
                detected_mood = en_mood
                mood_confidence = 0.7
                break
        
        # Check for music request
        music_keywords = ["nghe", "nhạc", "bài", "hát", "gợi ý", "recommend", "cho tôi", "muốn"]
        is_music_request = any(k in message_lower for k in music_keywords)
        
        # Determine energy level
        energy_level = None
        if any(w in message_lower for w in ["mạnh", "sôi động", "high", "nhanh"]):
            energy_level = "high"
        elif any(w in message_lower for w in ["nhẹ", "chậm", "thư giãn", "chill"]):
            energy_level = "low"
        else:
            energy_level = "medium"
        
        # Generate response
        if detected_mood:
            mood_vi = self.MOOD_VI.get(detected_mood, detected_mood)
            if is_music_request:
                bot_message = f"Mình hiểu rồi! Bạn đang {mood_vi} và muốn nghe nhạc. Để mình gợi ý cho bạn nhé! 🎵"
                should_recommend = True
            else:
                bot_message = f"Mình cảm nhận được bạn đang {mood_vi}. Bạn muốn nghe nhạc để đồng cảm hay để thay đổi tâm trạng?"
                should_recommend = False
        else:
            bot_message = "Bạn có thể chia sẻ thêm về tâm trạng của mình không? Ví dụ: vui, buồn, muốn thư giãn... 😊"
            should_recommend = False
        
        return AIResponse(
            bot_message=bot_message,
            detected_mood=detected_mood,
            mood_confidence=mood_confidence,
            intent=UserIntent.MUSIC_REQUEST if is_music_request else UserIntent.MOOD_EXPRESSION if detected_mood else UserIntent.UNCLEAR,
            should_recommend=should_recommend,
            energy_level=energy_level
        )
    
    def get_mood_for_db(self, mood: str) -> str:
        """Convert AI detected mood to database mood value."""
        return self.MOOD_MAP.get(mood.lower(), mood) if mood else "calm"


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create Gemini service singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
