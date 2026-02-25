"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - INTENT CLASSIFIER
=============================================================================

Classifies user intent from text input to determine conversation flow.

The IntentClassifier analyzes user messages to determine:
- What the user wants (mood expression, song request, feedback, etc.)
- Whether they're confirming, negating, or correcting
- Confidence level of the classification

Classification uses pattern matching and keyword detection, with support
for both Vietnamese and English inputs.

Intent Categories:
- MOOD_EXPRESSION: User expressing their current mood
- MOOD_REQUEST: User requesting mood-specific music
- MOOD_CORRECTION: User correcting detected mood
- PREFERENCE_EXPRESSION: User stating preferences
- PREFERENCE_CONSTRAINT: User adding constraints (no rock, etc.)
- GREETING: User greeting the bot
- CONFIRMATION: User confirming something (yes, ok, etc.)
- NEGATION: User denying/negating (no, not, etc.)
- SKIP: User wants to skip questions
- HELP: User asking for help
- PLAY_REQUEST: User wants to play music
- SEARCH_REQUEST: User searching for specific song/artist
- FEEDBACK_POSITIVE: User gave positive feedback
- FEEDBACK_NEGATIVE: User gave negative feedback
- CONTEXT_EXPRESSION: User providing context
- UNKNOWN: Could not classify

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Pattern, Any

from .types import Intent

logger = logging.getLogger(__name__)


# =============================================================================
# PATTERNS AND KEYWORDS
# =============================================================================

# Confidence thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.65
CONFIDENCE_LOW = 0.45

# Intent patterns (compiled regex patterns)
# Pattern format: (pattern_string, confidence_boost)

GREETING_PATTERNS: List[Tuple[str, float]] = [
    (r'^(chào|xin chào|chao|xin chao|hello|hi|hey|hai)\b', CONFIDENCE_HIGH),
    (r'\b(chào bạn|chao ban|hi there|hey there)\b', CONFIDENCE_HIGH),
    (r'\b(good (morning|afternoon|evening|night))\b', CONFIDENCE_HIGH),
    (r'^(yo|heya|sup|hii+)\b', CONFIDENCE_MEDIUM),
    (r'\b(chào buổi sáng|chào buổi tối|buổi sáng tốt lành)\b', CONFIDENCE_HIGH),
]

CONFIRMATION_PATTERNS: List[Tuple[str, float]] = [
    (r'^(yes|yeah|yep|yup|ok|okay|uh huh|sure|alright)\b', CONFIDENCE_HIGH),
    (r'^(ừ|ừm|ừm ừm|ờ|ờm|đúng|đúng rồi|ok|okê|okie|được|đc)\b', CONFIDENCE_HIGH),
    (r'^(vâng|dạ|dạ vâng|phải|chính xác)\b', CONFIDENCE_HIGH),
    (r'^(đồng ý|tôi đồng ý|mình đồng ý)\b', CONFIDENCE_HIGH),
    (r'\b(sounds good|that works|exactly|correct)\b', CONFIDENCE_MEDIUM),
    (r'\b(nghe hay|nghe được|nghe tốt|được đấy)\b', CONFIDENCE_MEDIUM),
]

NEGATION_PATTERNS: List[Tuple[str, float]] = [
    (r'^(no|nope|nah|not|nuh uh)\b', CONFIDENCE_HIGH),
    (r'^(không|ko|khong|hông|k|éo|éo phải)\b', CONFIDENCE_HIGH),
    (r'^(không đúng|không phải|sai rồi|sai)\b', CONFIDENCE_HIGH),
    (r'^(chưa|chưa đúng|chưa phải)\b', CONFIDENCE_HIGH),
    (r'\b(i don.t|i do not|not really|not quite)\b', CONFIDENCE_MEDIUM),
    (r'\b(thực ra không|không hẳn|không phải thế)\b', CONFIDENCE_MEDIUM),
]

MOOD_CORRECTION_PATTERNS: List[Tuple[str, float]] = [
    (r'\b(không phải|chưa đúng|sai rồi).*(mà là|tôi đang|mình đang)\b', CONFIDENCE_HIGH),
    (r'\b(not|actually).*(i.m|i am|feeling)\b', CONFIDENCE_HIGH),
    (r'\b(thực ra tôi|thực ra mình).*(đang|cảm thấy)\b', CONFIDENCE_HIGH),
    (r'\b(correction|let me correct|i meant)\b', CONFIDENCE_HIGH),
    (r'\b(ý tôi là|ý mình là|không, tôi|không, mình)\b', CONFIDENCE_HIGH),
]

SKIP_PATTERNS: List[Tuple[str, float]] = [
    (r'\b(skip|bỏ qua|bo qua|pass|next)\b', CONFIDENCE_HIGH),
    (r'\b(chơi ngay|play now|just play|chơi luôn)\b', CONFIDENCE_HIGH),
    (r'\b(nghe ngay|cho xem|show me|đi thôi|let.s go)\b', CONFIDENCE_HIGH),
    (r'\b(không cần hỏi|đừng hỏi nữa|đủ rồi)\b', CONFIDENCE_HIGH),
    (r'\b(gợi ý đi|recommend|suggest already)\b', CONFIDENCE_MEDIUM),
    (r'^(thôi|đủ rồi|đi|go)$', CONFIDENCE_MEDIUM),
]

HELP_PATTERNS: List[Tuple[str, float]] = [
    (r'\b(help|giúp|trợ giúp|hướng dẫn)\b', CONFIDENCE_HIGH),
    (r'\b(how do i|làm sao|cách|how to)\b', CONFIDENCE_MEDIUM),
    (r'\b(what can you do|bạn làm được gì)\b', CONFIDENCE_HIGH),
    (r'\b(hỗ trợ|assist|assistance)\b', CONFIDENCE_MEDIUM),
]

PLAY_REQUEST_PATTERNS: List[Tuple[str, float]] = [
    (r'\b(play|chơi|phát|mở|bật).*(nhạc|music|song|bài)\b', CONFIDENCE_HIGH),
    (r'\b(cho (tôi|mình) nghe|muốn nghe|wanna hear)\b', CONFIDENCE_HIGH),
    (r'\b(put on|turn on).*(music|song)\b', CONFIDENCE_MEDIUM),
    (r'\b(mở bài|bật bài|phát bài)\b', CONFIDENCE_HIGH),
]

SEARCH_REQUEST_PATTERNS: List[Tuple[str, float]] = [
    (r'\b(tìm|search|find|kiếm).*(bài|song|nhạc)\b', CONFIDENCE_HIGH),
    (r'\b(có bài|có nhạc|have.*song)\b', CONFIDENCE_MEDIUM),
    (r'\b(của|by|from).*(ca sĩ|artist|singer)\b', CONFIDENCE_HIGH),
    (r'\bnhạc của\s+\w+', CONFIDENCE_HIGH),  # "nhạc của [artist]"
]

FEEDBACK_POSITIVE_PATTERNS: List[Tuple[str, float]] = [
    (r'\b(thích|like|love|yêu|hay|tuyệt|great|awesome)\b', CONFIDENCE_MEDIUM),
    (r'\b(thích bài này|love this|hay quá|tuyệt vời)\b', CONFIDENCE_HIGH),
    (r'\b(good choice|nice|perfect|exactly)\b', CONFIDENCE_MEDIUM),
    (r'\b(đúng gu|hợp|phù hợp|chuẩn)\b', CONFIDENCE_HIGH),
    (r'👍|❤️|🎉|😊|😍', CONFIDENCE_HIGH),  # Emoji
]

FEEDBACK_NEGATIVE_PATTERNS: List[Tuple[str, float]] = [
    (r'\b(không thích|dislike|hate|ghét|dở|bad)\b', CONFIDENCE_HIGH),
    (r'\b(không hay|not good|terrible|awful)\b', CONFIDENCE_HIGH),
    (r'\b(bỏ|skip this|next|tiếp|không phải gu)\b', CONFIDENCE_MEDIUM),
    (r'\b(đổi bài|change|khác|another)\b', CONFIDENCE_MEDIUM),
    (r'👎|😞|😠|🙁', CONFIDENCE_HIGH),  # Emoji
]

CONTEXT_EXPRESSION_PATTERNS: List[Tuple[str, float]] = [
    (r'\b(đang làm việc|working|at work|ở văn phòng)\b', CONFIDENCE_HIGH),
    (r'\b(đang nghỉ|relaxing|taking a break|nghỉ ngơi)\b', CONFIDENCE_HIGH),
    (r'\b(đang tập|exercising|workout|gym|running)\b', CONFIDENCE_HIGH),
    (r'\b(đang lái xe|driving|commuting|trên xe)\b', CONFIDENCE_HIGH),
    (r'\b(ở nhà|at home|in my room|trong phòng)\b', CONFIDENCE_HIGH),
    (r'\b(buổi sáng|morning|sáng sớm)\b', CONFIDENCE_MEDIUM),
    (r'\b(buổi tối|evening|night|đêm)\b', CONFIDENCE_MEDIUM),
    (r'\b(một mình|alone|by myself)\b', CONFIDENCE_HIGH),
    (r'\b(với bạn|with friends|party|tiệc)\b', CONFIDENCE_HIGH),
]

PREFERENCE_CONSTRAINT_PATTERNS: List[Tuple[str, float]] = [
    (r'\b(không muốn|không thích|no|don.t want).*(rock|pop|rap|ballad)\b', CONFIDENCE_HIGH),
    (r'\b(tránh|avoid|skip).*(genre|thể loại|loại)\b', CONFIDENCE_MEDIUM),
    (r'\b(chỉ|only|just).*(ballad|pop|rock|vpop|kpop)\b', CONFIDENCE_HIGH),
    (r'\b(không nghe|don.t listen).*(rock|pop|rap)\b', CONFIDENCE_HIGH),
]

# Mood expression keywords (combined with text_mood_detector)
MOOD_KEYWORDS: Dict[str, List[str]] = {
    "Vui": ["vui", "happy", "hạnh phúc", "sung sướng", "hào hứng", "excited"],
    "Buồn": ["buồn", "sad", "đau khổ", "thất vọng", "unhappy", "down"],
    "Suy tư": ["suy tư", "nghĩ", "trầm ngâm", "thoughtful", "thinking"],
    "Chill": ["chill", "thư giãn", "relax", "bình yên", "peaceful"],
    "Năng lượng": ["năng lượng", "sôi động", "energetic", "pumped", "hype"],
    "Tập trung": ["tập trung", "focus", "focused", "concentrate"],
}


# =============================================================================
# CLASSIFICATION RESULT
# =============================================================================

@dataclass
class IntentClassification:
    """
    Result of intent classification.
    """
    intent: Intent
    confidence: float
    matched_pattern: Optional[str] = None
    matched_text: Optional[str] = None
    secondary_intents: List[Tuple[Intent, float]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'intent': self.intent.name,
            'confidence': self.confidence,
            'matched_pattern': self.matched_pattern,
            'matched_text': self.matched_text,
            'secondary_intents': [(i.name, c) for i, c in self.secondary_intents],
        }


# =============================================================================
# INTENT CLASSIFIER
# =============================================================================

class IntentClassifier:
    """
    Classifies user intent from text input.
    
    Uses pattern matching with confidence scoring to determine
    what the user wants to do.
    
    Usage:
        classifier = IntentClassifier()
        result = classifier.classify("Tôi muốn nghe nhạc buồn")
        
        if result.intent == Intent.MOOD_REQUEST:
            # Handle mood request
    """
    
    def __init__(self):
        # Compile all patterns for efficiency
        self._intent_patterns: Dict[Intent, List[Tuple[Pattern, float]]] = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """
        Compile all pattern strings to regex Pattern objects.
        """
        pattern_map = {
            Intent.GREETING: GREETING_PATTERNS,
            Intent.CONFIRMATION: CONFIRMATION_PATTERNS,
            Intent.NEGATION: NEGATION_PATTERNS,
            Intent.MOOD_CORRECTION: MOOD_CORRECTION_PATTERNS,
            Intent.SKIP: SKIP_PATTERNS,
            Intent.HELP: HELP_PATTERNS,
            Intent.PLAY_REQUEST: PLAY_REQUEST_PATTERNS,
            Intent.SEARCH_REQUEST: SEARCH_REQUEST_PATTERNS,
            Intent.FEEDBACK_POSITIVE: FEEDBACK_POSITIVE_PATTERNS,
            Intent.FEEDBACK_NEGATIVE: FEEDBACK_NEGATIVE_PATTERNS,
            Intent.CONTEXT_EXPRESSION: CONTEXT_EXPRESSION_PATTERNS,
            Intent.PREFERENCE_CONSTRAINT: PREFERENCE_CONSTRAINT_PATTERNS,
        }
        
        for intent, patterns in pattern_map.items():
            compiled = []
            for pattern_str, confidence in patterns:
                try:
                    compiled.append((re.compile(pattern_str, re.IGNORECASE), confidence))
                except re.error as e:
                    logger.warning(f"Invalid pattern for {intent}: {pattern_str} - {e}")
            self._intent_patterns[intent] = compiled
    
    def classify(self, text: str) -> IntentClassification:
        """
        Classify the intent of user text.
        
        Args:
            text: User input text
            
        Returns:
            IntentClassification with intent and confidence
        """
        if not text or not text.strip():
            return IntentClassification(
                intent=Intent.UNKNOWN,
                confidence=0.0,
            )
        
        text = text.strip()
        text_lower = text.lower()
        
        # Collect all matching intents
        matches: List[Tuple[Intent, float, str, str]] = []
        
        # Check each intent's patterns
        for intent, patterns in self._intent_patterns.items():
            for pattern, base_confidence in patterns:
                match = pattern.search(text_lower)
                if match:
                    matches.append((intent, base_confidence, pattern.pattern, match.group()))
        
        # Check for mood expression
        mood_match = self._check_mood_expression(text_lower)
        if mood_match:
            matches.append(mood_match)
        
        # Check for mood request (combination of request + mood)
        mood_request = self._check_mood_request(text_lower)
        if mood_request:
            matches.append(mood_request)
        
        # Check for preference expression
        pref_match = self._check_preference_expression(text_lower)
        if pref_match:
            matches.append(pref_match)
        
        if not matches:
            return IntentClassification(
                intent=Intent.UNKNOWN,
                confidence=CONFIDENCE_LOW,
            )
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Primary intent is highest confidence match
        primary = matches[0]
        
        # Secondary intents are other high-confidence matches
        secondary = [
            (intent, conf) 
            for intent, conf, _, _ in matches[1:] 
            if conf >= CONFIDENCE_MEDIUM
        ]
        
        return IntentClassification(
            intent=primary[0],
            confidence=primary[1],
            matched_pattern=primary[2],
            matched_text=primary[3],
            secondary_intents=secondary[:3],  # Top 3 secondary
        )
    
    def _check_mood_expression(self, text: str) -> Optional[Tuple[Intent, float, str, str]]:
        """
        Check if text is a mood expression.
        """
        for mood, keywords in MOOD_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    # Check if it's an expression pattern
                    expression_patterns = [
                        rf'\b(tôi|mình|i|i.m|i am)\s+.*(đang|cảm thấy|feeling|feel)\s+.*{re.escape(keyword)}',
                        rf'\b(đang|cảm thấy|feeling)\s+.*{re.escape(keyword)}',
                        rf'^{re.escape(keyword)}$',
                        rf'\b{re.escape(keyword)}\s+quá\b',
                    ]
                    for pattern in expression_patterns:
                        if re.search(pattern, text, re.IGNORECASE):
                            return (Intent.MOOD_EXPRESSION, CONFIDENCE_HIGH, pattern, keyword)
                    
                    # Simple keyword match (lower confidence)
                    return (Intent.MOOD_EXPRESSION, CONFIDENCE_MEDIUM, f"keyword:{keyword}", keyword)
        
        return None
    
    def _check_mood_request(self, text: str) -> Optional[Tuple[Intent, float, str, str]]:
        """
        Check if text is a request for mood-specific music.
        """
        request_indicators = [
            r'\b(muốn nghe|want to listen|cho tôi|give me|play me)\b',
            r'\b(gợi ý|recommend|suggest)\b.*\b(nhạc|music|song)\b',
            r'\b(nhạc|music)\b.*\b(cho|for)\b',
        ]
        
        has_request = any(re.search(p, text, re.IGNORECASE) for p in request_indicators)
        
        if has_request:
            # Check for mood in request
            for mood, keywords in MOOD_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        return (Intent.MOOD_REQUEST, CONFIDENCE_HIGH, 
                               "mood_request", f"{keyword} music")
        
        return None
    
    def _check_preference_expression(self, text: str) -> Optional[Tuple[Intent, float, str, str]]:
        """
        Check if text expresses a preference.
        """
        preference_patterns = [
            (r'\b(tôi thích|i like|mình thích)\s+(\w+)', CONFIDENCE_HIGH),
            (r'\b(prefer|ưa|thích hơn)\s+(\w+)', CONFIDENCE_MEDIUM),
        ]
        
        for pattern, conf in preference_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return (Intent.PREFERENCE_EXPRESSION, conf, pattern, match.group())
        
        return None
    
    def is_affirmative(self, text: str) -> bool:
        """
        Quick check if text is affirmative (yes, ok, etc.)
        """
        result = self.classify(text)
        return result.intent == Intent.CONFIRMATION and result.confidence >= CONFIDENCE_MEDIUM
    
    def is_negative(self, text: str) -> bool:
        """
        Quick check if text is negative (no, not, etc.)
        """
        result = self.classify(text)
        return result.intent in (Intent.NEGATION, Intent.MOOD_CORRECTION) and \
               result.confidence >= CONFIDENCE_MEDIUM
    
    def is_skip_request(self, text: str) -> bool:
        """
        Quick check if text is a skip request.
        """
        result = self.classify(text)
        return result.intent == Intent.SKIP and result.confidence >= CONFIDENCE_MEDIUM
    
    def extract_intent_features(self, text: str) -> Dict[str, Any]:
        """
        Extract intent-related features for analytics.
        """
        result = self.classify(text)
        
        return {
            'text_length': len(text),
            'word_count': len(text.split()),
            'has_question_mark': '?' in text,
            'has_exclamation': '!' in text,
            'primary_intent': result.intent.name,
            'confidence': result.confidence,
            'has_secondary_intents': len(result.secondary_intents) > 0,
            'is_vietnamese': self._detect_vietnamese(text),
        }
    
    def _detect_vietnamese(self, text: str) -> bool:
        """
        Simple Vietnamese detection based on diacritics.
        """
        vn_chars = set('àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ')
        return any(c in vn_chars for c in text.lower())


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_intent_classifier() -> IntentClassifier:
    """
    Create an IntentClassifier instance.
    """
    return IntentClassifier()


def quick_classify(text: str) -> Intent:
    """
    Quick classification without full result object.
    
    Args:
        text: User input
        
    Returns:
        Intent enum value
    """
    classifier = IntentClassifier()
    return classifier.classify(text).intent
