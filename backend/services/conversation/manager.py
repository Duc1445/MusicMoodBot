"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - CONVERSATION MANAGER
=============================================================================

Main orchestrator for multi-turn conversations.

The ConversationManager coordinates:
- Session management (creation, retrieval, expiry)
- Turn processing pipeline
- FSM state transitions
- Emotion tracking and clarity scoring
- Response generation

This is the primary entry point for the conversation system.

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from __future__ import annotations

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING

from .types import (
    ConversationSession,
    ConversationTurn,
    TurnRequest,
    TurnResponse,
    EnrichedRequest,
    DialogueState,
    Intent,
    InputType,
    ResponseType,
    EmotionalSignals,
    ContextSignals,
    SESSION_TIMEOUT_SECONDS,
    MAX_TURNS_PER_SESSION,
    CLARITY_THRESHOLD,
)

from .state_machine import DialogueFSM
from .emotion_tracker import EmotionDepthTracker
from .clarity_scorer import EmotionClarityModel
from .intent_classifier import IntentClassifier
from .strategy_engine import ClarificationStrategyEngine
from .question_bank import ProbeQuestionBank
from .session_store import SessionStore
from .context_extractor import ContextSignalExtractor

logger = logging.getLogger(__name__)


# =============================================================================
# RESPONSE TEMPLATES
# =============================================================================

GREETING_RESPONSES = {
    'vi': [
        "Chào bạn! Hôm nay bạn cảm thấy thế nào? 🎵",
        "Xin chào! Tâm trạng của bạn hiện tại ra sao? 😊",
        "Hello! Bạn đang có tâm trạng như thế nào hôm nay? 🎶",
    ],
    'en': [
        "Hello! How are you feeling today? 🎵",
        "Hi there! What's your mood like right now? 😊",
        "Hey! How are you doing today? 🎶",
    ],
}

ACKNOWLEDGMENT_RESPONSES = {
    'vi': {
        'happy': "Tuyệt vời! Mình cảm nhận được sự vui vẻ của bạn! 🎉",
        'sad': "Mình hiểu. Đôi khi cuộc sống cũng có những lúc như vậy. 💙",
        'energetic': "Wow, bạn đang tràn đầy năng lượng! ⚡",
        'calm': "Thư thái quá! Cảm giác bình yên thật dễ chịu. 🍃",
        'angry': "Mình hiểu bạn đang không vui. Để mình tìm nhạc giúp bạn nhé. 🎧",
        'nostalgic': "Hoài niệm... những kỷ niệm đôi khi thật đẹp. ✨",
        'romantic': "Ôi, tình yêu trong không khí! 💕",
        'default': "Mình hiểu rồi! Cảm ơn bạn đã chia sẻ. 🎵",
    },
    'en': {
        'happy': "Wonderful! I can feel your joy! 🎉",
        'sad': "I understand. Life has its moments. 💙",
        'energetic': "Wow, you're full of energy! ⚡",
        'calm': "How peaceful! A calm state of mind is lovely. 🍃",
        'angry': "I understand you're not in the best mood. Let me find some music. 🎧",
        'nostalgic': "Nostalgia... memories can be so beautiful. ✨",
        'romantic': "Oh, love is in the air! 💕",
        'default': "I got it! Thanks for sharing. 🎵",
    },
}

RECOMMENDATION_INTROS = {
    'vi': [
        "Dựa trên tâm trạng của bạn, mình gợi ý những bài này:",
        "Mình nghĩ những bài này sẽ phù hợp với bạn:",
        "Đây là những gợi ý tuyệt vời cho bạn:",
        "Mình đã chọn những bài này cho cảm xúc của bạn:",
    ],
    'en': [
        "Based on your mood, I suggest these songs:",
        "I think these songs will suit you:",
        "Here are some great picks for you:",
        "I've selected these for your mood:",
    ],
}

EXIT_RESPONSES = {
    'vi': [
        "Chúc bạn nghe nhạc vui vẻ! 🎵 Hẹn gặp lại nhé!",
        "Tạm biệt! Hy vọng âm nhạc sẽ làm ngày của bạn tươi đẹp hơn. 😊",
        "Bye bye! Quay lại bất cứ lúc nào bạn muốn nhé! 👋",
    ],
    'en': [
        "Enjoy your music! 🎵 See you soon!",
        "Goodbye! Hope the music brightens your day. 😊",
        "Bye! Come back anytime! 👋",
    ],
}


# =============================================================================
# CONVERSATION MANAGER
# =============================================================================

class ConversationManager:
    """
    Main orchestrator for multi-turn conversations.
    
    Coordinates all components:
    - SessionStore: Persistence
    - DialogueFSM: State management
    - EmotionDepthTracker: Emotion accumulation
    - EmotionClarityModel: Clarity scoring
    - IntentClassifier: Intent detection
    - ClarificationStrategyEngine: Question strategy
    - ProbeQuestionBank: Question selection
    - ContextSignalExtractor: Context extraction
    
    Usage:
        manager = ConversationManager()
        
        # Process user input
        response = manager.process_turn(
            user_id=123,
            input_text="Tôi đang buồn quá",
            session_id=None  # Will create new session
        )
        
        # Get enriched request for recommendation
        enriched = manager.get_enriched_request(session_id)
    """
    
    def __init__(self, db_path: Optional[str] = None,
                 text_mood_detector: Optional[Any] = None):
        """
        Initialize conversation manager.
        
        Args:
            db_path: Optional database path
            text_mood_detector: Optional TextMoodDetector instance
        """
        # Core components
        self.session_store = SessionStore(db_path)
        self.fsm = DialogueFSM()
        self.emotion_tracker = EmotionDepthTracker()
        self.clarity_model = EmotionClarityModel()
        self.intent_classifier = IntentClassifier()
        self.strategy_engine = ClarificationStrategyEngine()
        self.question_bank = ProbeQuestionBank()
        self.context_extractor = ContextSignalExtractor()
        
        # External dependency (mood detector)
        self._text_mood_detector = text_mood_detector
        
        # Configuration
        self.max_turns = MAX_TURNS_PER_SESSION
        self.clarity_threshold = CLARITY_THRESHOLD
        self.language = 'vi'  # Default language
    
    def set_text_mood_detector(self, detector: Any):
        """Set external text mood detector."""
        self._text_mood_detector = detector
    
    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================
    
    def process_turn(self, user_id: int, input_text: str,
                     session_id: Optional[str] = None,
                     input_type: InputType = InputType.TEXT,
                     client_info: Optional[Dict] = None) -> TurnResponse:
        """
        Process a conversation turn.
        
        This is the main entry point for the conversation system.
        
        Args:
            user_id: User ID
            input_text: User's input text
            session_id: Optional existing session ID
            input_type: Type of input (text, emoji, tap)
            client_info: Optional client metadata
            
        Returns:
            TurnResponse with bot response and session info
        """
        start_time = time.time()
        
        # Get or create session
        session = self._get_or_create_session(user_id, session_id, client_info)
        
        # Check idempotency
        idempotency_key = self.session_store.generate_idempotency_key(
            session.session_id,
            session.turn_count + 1,
            input_text
        )
        cached = self.session_store.check_idempotency(idempotency_key)
        if cached:
            logger.info(f"Returning cached response for key {idempotency_key}")
            return TurnResponse.from_dict(cached)
        
        # Create turn object
        turn = ConversationTurn(
            session_id=session.session_id,
            turn_number=session.turn_count + 1,
            user_input=input_text,
            input_type=input_type,
            state_before=session.state,
            clarity_score_before=session.emotional_context.clarity_score,
        )
        
        # Extract context signals
        context_signals = self.context_extractor.extract(
            input_text,
            timestamp=datetime.now(),
            client_info=client_info
        )
        turn.context_signals = context_signals
        
        # Classify intent
        intent, intent_confidence = self.intent_classifier.classify(
            input_text,
            session.state
        )
        turn.intent = intent
        turn.intent_confidence = intent_confidence
        
        # Handle special intents
        if intent in (Intent.EXIT, Intent.GOODBYE):
            return self._handle_exit(session, turn, start_time, idempotency_key)
        
        if intent == Intent.HELP:
            return self._handle_help(session, turn, start_time, idempotency_key)
        
        if intent == Intent.START_OVER:
            return self._handle_restart(session, turn, user_id, client_info, start_time)
        
        # Detect mood from text
        mood_result = self._detect_mood(input_text)
        turn.detected_mood = mood_result.get('mood')
        turn.detected_intensity = mood_result.get('intensity', 0.5)
        turn.mood_confidence = mood_result.get('confidence', 0.0)
        turn.keywords_matched = mood_result.get('keywords', [])
        
        # Create emotional signals
        emotional_signals = EmotionalSignals(
            mood=turn.detected_mood,
            intensity=turn.detected_intensity,
            confidence=turn.mood_confidence,
            valence=mood_result.get('valence', 0.0),
            arousal=mood_result.get('arousal', 0.5),
        )
        turn.emotional_signals = emotional_signals
        
        # Update emotion tracker
        self.emotion_tracker.add_signal(emotional_signals)
        
        # Update session's emotional context
        session.emotional_context = self.emotion_tracker.get_context()
        
        # Calculate clarity score
        clarity_score = self.clarity_model.compute_clarity(session.emotional_context)
        session.emotional_context.clarity_score = clarity_score
        turn.clarity_score_after = clarity_score
        turn.clarity_delta = clarity_score - turn.clarity_score_before
        
        # Determine next state using FSM
        context = {
            'clarity_score': clarity_score,
            'turn_count': session.turn_count + 1,
            'mood_detected': turn.detected_mood is not None,
            'has_context': context_signals.activity is not None,
            'intent': intent,
        }
        
        new_state = self.fsm.transition(session.state, context)
        session.state = new_state
        turn.state_after = new_state
        
        # Generate response based on state
        response_text, response_type, question = self._generate_response(
            session, turn, new_state
        )
        turn.bot_response = response_text
        turn.response_type = response_type
        turn.question_asked = question
        
        # Calculate processing time
        turn.processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Save turn
        self.session_store.save_turn(session, turn)
        
        # Build response
        response = TurnResponse(
            session_id=session.session_id,
            turn_number=turn.turn_number,
            bot_response=response_text,
            response_type=response_type,
            detected_mood=turn.detected_mood,
            detected_intensity=turn.detected_intensity,
            clarity_score=clarity_score,
            current_state=new_state.name,
            should_recommend=new_state in (
                DialogueState.RECOMMENDATION,
                DialogueState.DELIVERY,
            ),
            emotional_context=session.emotional_context,
            processing_time_ms=turn.processing_time_ms,
        )
        
        # Cache for idempotency
        self.session_store.save_idempotency(
            idempotency_key,
            session.session_id,
            turn.turn_id or 0,
            response.to_dict()
        )
        
        return response
    
    def _get_or_create_session(self, user_id: int,
                               session_id: Optional[str],
                               client_info: Optional[Dict]) -> ConversationSession:
        """Get existing session or create new one."""
        if session_id:
            session = self.session_store.get_session(session_id)
            if session and session.is_active:
                return session
        
        # Try to get active session for user
        session = self.session_store.get_active_session(user_id)
        if session:
            # Reset state for new conversation
            self.emotion_tracker = EmotionDepthTracker()
            return session
        
        # Create new session
        self.emotion_tracker = EmotionDepthTracker()
        return self.session_store.create_session(
            user_id=user_id,
            max_turns=self.max_turns,
            client_info=client_info
        )
    
    def _detect_mood(self, text: str) -> Dict[str, Any]:
        """Detect mood from text using TextMoodDetector."""
        if self._text_mood_detector:
            try:
                result = self._text_mood_detector.detect(text)
                return {
                    'mood': result.get('mood'),
                    'intensity': result.get('intensity', 0.5),
                    'confidence': result.get('confidence', 0.0),
                    'keywords': result.get('keywords', []),
                    'valence': result.get('valence', 0.0),
                    'arousal': result.get('arousal', 0.5),
                }
            except Exception as e:
                logger.warning(f"Mood detection failed: {e}")
        
        # Fallback to basic detection
        return self._basic_mood_detection(text)
    
    def _basic_mood_detection(self, text: str) -> Dict[str, Any]:
        """Basic mood detection fallback."""
        text_lower = text.lower()
        
        # Simple keyword matching
        happy_words = ['vui', 'happy', 'hạnh phúc', 'yêu', 'tuyệt', 'thích', 'excited']
        sad_words = ['buồn', 'sad', 'depressed', 'khóc', 'chán', 'thất vọng', 'unhappy']
        angry_words = ['tức', 'angry', 'bực', 'ghét', 'frustrated', 'annoyed']
        calm_words = ['bình', 'calm', 'thư giãn', 'relax', 'peaceful', 'zen']
        energetic_words = ['năng lượng', 'energetic', 'hype', 'excited', 'pumped']
        
        if any(w in text_lower for w in sad_words):
            return {'mood': 'sad', 'intensity': 0.7, 'confidence': 0.6, 'valence': -0.7, 'arousal': 0.3}
        if any(w in text_lower for w in angry_words):
            return {'mood': 'angry', 'intensity': 0.8, 'confidence': 0.6, 'valence': -0.8, 'arousal': 0.8}
        if any(w in text_lower for w in happy_words):
            return {'mood': 'happy', 'intensity': 0.7, 'confidence': 0.6, 'valence': 0.7, 'arousal': 0.6}
        if any(w in text_lower for w in energetic_words):
            return {'mood': 'energetic', 'intensity': 0.8, 'confidence': 0.6, 'valence': 0.5, 'arousal': 0.9}
        if any(w in text_lower for w in calm_words):
            return {'mood': 'calm', 'intensity': 0.5, 'confidence': 0.6, 'valence': 0.3, 'arousal': 0.2}
        
        return {'mood': None, 'intensity': 0.5, 'confidence': 0.0}
    
    def _generate_response(self, session: ConversationSession,
                          turn: ConversationTurn,
                          state: DialogueState) -> Tuple[str, ResponseType, Optional[str]]:
        """
        Generate bot response based on state.
        
        Returns:
            Tuple of (response_text, response_type, question_asked)
        """
        lang = self.language
        
        if state == DialogueState.GREETING:
            import random
            response = random.choice(GREETING_RESPONSES[lang])
            return response, ResponseType.GREETING, None
        
        elif state == DialogueState.ACKNOWLEDGING:
            mood = turn.detected_mood or 'default'
            ack = ACKNOWLEDGMENT_RESPONSES[lang].get(mood, ACKNOWLEDGMENT_RESPONSES[lang]['default'])
            return ack, ResponseType.ACKNOWLEDGMENT, None
        
        elif state == DialogueState.PROBING_DEPTH:
            # Get probing question
            strategy = self.strategy_engine.determine_strategy(session)
            question = self.question_bank.select_by_strategy(
                strategy=strategy,
                current_mood=turn.detected_mood,
                language=lang
            )
            
            # Build response
            ack = ACKNOWLEDGMENT_RESPONSES[lang].get(
                turn.detected_mood or 'default',
                ACKNOWLEDGMENT_RESPONSES[lang]['default']
            )
            response = f"{ack}\n\n{question.text}"
            return response, ResponseType.PROBING, question.text
        
        elif state == DialogueState.EXPLORING_CONTEXT:
            # Ask about context
            question = self.question_bank.select(
                category='context',
                language=lang
            )
            response = question.text if question else "Bạn đang ở đâu/làm gì vậy?"
            return response, ResponseType.PROBING, response
        
        elif state == DialogueState.CONFIRMING_MOOD:
            final_mood = session.emotional_context.dominant_mood
            intensity = session.emotional_context.average_intensity
            
            intensity_word = 'rất ' if intensity > 0.7 else ('hơi ' if intensity < 0.4 else '')
            
            if lang == 'vi':
                response = f"Vậy là bạn đang cảm thấy {intensity_word}{final_mood} đúng không? Mình sẽ tìm nhạc phù hợp cho bạn! 🎵"
            else:
                response = f"So you're feeling {intensity_word}{final_mood}, right? Let me find some music for you! 🎵"
            
            return response, ResponseType.CONFIRMATION, None
        
        elif state == DialogueState.RECOMMENDATION:
            import random
            intro = random.choice(RECOMMENDATION_INTROS[lang])
            return intro, ResponseType.RECOMMENDATION, None
        
        elif state == DialogueState.DELIVERY:
            if lang == 'vi':
                response = "Đây là danh sách nhạc mình chọn cho bạn! Hy vọng bạn thích! 🎶"
            else:
                response = "Here's your playlist! Hope you enjoy! 🎶"
            return response, ResponseType.DELIVERY, None
        
        elif state == DialogueState.REFINING:
            if lang == 'vi':
                response = "Bạn muốn điều chỉnh gì cho danh sách nhạc không?"
            else:
                response = "Would you like me to adjust the playlist?"
            return response, ResponseType.PROBING, response
        
        elif state == DialogueState.ENDED:
            import random
            response = random.choice(EXIT_RESPONSES[lang])
            return response, ResponseType.FAREWELL, None
        
        # Default fallback
        return "...", ResponseType.ACKNOWLEDGMENT, None
    
    # =========================================================================
    # SPECIAL HANDLERS
    # =========================================================================
    
    def _handle_exit(self, session: ConversationSession,
                    turn: ConversationTurn,
                    start_time: float,
                    idempotency_key: str) -> TurnResponse:
        """Handle exit/goodbye intent."""
        import random
        lang = self.language
        
        response_text = random.choice(EXIT_RESPONSES[lang])
        turn.bot_response = response_text
        turn.response_type = ResponseType.FAREWELL
        turn.state_after = DialogueState.ENDED
        turn.processing_time_ms = int((time.time() - start_time) * 1000)
        
        # End session
        self.session_store.save_turn(session, turn)
        self.session_store.end_session(session.session_id, reason='user_exit')
        
        response = TurnResponse(
            session_id=session.session_id,
            turn_number=turn.turn_number,
            bot_response=response_text,
            response_type=ResponseType.FAREWELL,
            current_state='ENDED',
            should_recommend=False,
            session_ended=True,
        )
        
        self.session_store.save_idempotency(
            idempotency_key,
            session.session_id,
            turn.turn_id or 0,
            response.to_dict()
        )
        
        return response
    
    def _handle_help(self, session: ConversationSession,
                    turn: ConversationTurn,
                    start_time: float,
                    idempotency_key: str) -> TurnResponse:
        """Handle help intent."""
        lang = self.language
        
        if lang == 'vi':
            response_text = """🎵 **Hướng dẫn sử dụng MusicMoodBot**

• Chia sẻ tâm trạng của bạn (vui, buồn, phấn khích...)
• Mình sẽ hỏi thêm để hiểu rõ hơn cảm xúc của bạn
• Sau đó mình sẽ gợi ý nhạc phù hợp nhất!

Bạn có thể nói:
- "Hôm nay mình vui quá"
- "Đang buồn vì chuyện tình cảm"
- "Cần nhạc để tập trung làm việc"

Hãy bắt đầu bằng cách chia sẻ tâm trạng hiện tại nhé! 😊"""
        else:
            response_text = """🎵 **MusicMoodBot Help**

• Share how you're feeling (happy, sad, energetic...)
• I'll ask questions to understand your mood better
• Then I'll recommend music that fits perfectly!

You can say things like:
- "I'm feeling happy today"
- "I'm sad because of a breakup"
- "I need music to focus on work"

Start by sharing your current mood! 😊"""
        
        turn.bot_response = response_text
        turn.response_type = ResponseType.HELP
        turn.state_after = session.state
        turn.processing_time_ms = int((time.time() - start_time) * 1000)
        
        self.session_store.save_turn(session, turn)
        
        response = TurnResponse(
            session_id=session.session_id,
            turn_number=turn.turn_number,
            bot_response=response_text,
            response_type=ResponseType.HELP,
            current_state=session.state.name,
            should_recommend=False,
        )
        
        self.session_store.save_idempotency(
            idempotency_key,
            session.session_id,
            turn.turn_id or 0,
            response.to_dict()
        )
        
        return response
    
    def _handle_restart(self, session: ConversationSession,
                       turn: ConversationTurn,
                       user_id: int,
                       client_info: Optional[Dict],
                       start_time: float) -> TurnResponse:
        """Handle restart/start over intent."""
        # End current session
        self.session_store.end_session(session.session_id, reason='restart')
        
        # Create new session
        self.emotion_tracker = EmotionDepthTracker()
        new_session = self.session_store.create_session(
            user_id=user_id,
            max_turns=self.max_turns,
            client_info=client_info
        )
        
        import random
        lang = self.language
        response_text = random.choice(GREETING_RESPONSES[lang])
        
        response = TurnResponse(
            session_id=new_session.session_id,
            turn_number=0,
            bot_response=response_text,
            response_type=ResponseType.GREETING,
            current_state='GREETING',
            should_recommend=False,
        )
        
        return response
    
    # =========================================================================
    # ENRICHED REQUEST
    # =========================================================================
    
    def get_enriched_request(self, session_id: str) -> Optional[EnrichedRequest]:
        """
        Get enriched request from session for recommendation.
        
        This aggregates all conversation data into a format
        suitable for the recommendation pipeline.
        
        Args:
            session_id: Session ID
            
        Returns:
            EnrichedRequest or None
        """
        session = self.session_store.get_session(session_id)
        if not session:
            return None
        
        # Get latest turn for context
        latest_turn = session.turns[-1] if session.turns else None
        
        # Build enriched request
        context = session.emotional_context
        
        return EnrichedRequest(
            session_id=session.session_id,
            user_id=session.user_id,
            final_mood=context.dominant_mood,
            final_intensity=context.average_intensity,
            clarity_score=context.clarity_score,
            valence=context.average_valence,
            arousal=context.average_arousal,
            mood_history=context.mood_history[-5:],
            intensity_history=context.intensity_history[-5:],
            context_signals=latest_turn.context_signals if latest_turn else ContextSignals(),
            turn_count=session.turn_count,
            conversation_duration_seconds=int(
                (datetime.now() - session.started_at).total_seconds()
            ) if session.started_at else 0,
        )
    
    def get_final_mood_for_recommendation(self, session_id: str) -> Dict[str, Any]:
        """
        Get final mood parameters for recommendation pipeline.
        
        Returns a dict compatible with the existing mood engine.
        """
        enriched = self.get_enriched_request(session_id)
        if not enriched:
            return {}
        
        return {
            'mood': enriched.final_mood,
            'intensity': enriched.final_intensity,
            'valence': enriched.valence,
            'arousal': enriched.arousal,
            'confidence': enriched.clarity_score,
            'context': {
                'activity': enriched.context_signals.activity if enriched.context_signals else None,
                'time_of_day': enriched.context_signals.time_of_day if enriched.context_signals else None,
                'location': enriched.context_signals.location if enriched.context_signals else None,
            },
        }
    
    # =========================================================================
    # SESSION UTILITIES
    # =========================================================================
    
    def end_session(self, session_id: str, reason: str = 'manual'):
        """End a session manually."""
        self.session_store.end_session(session_id, reason)
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a session."""
        session = self.session_store.get_session(session_id)
        if not session:
            return None
        
        return {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'turn_count': session.turn_count,
            'final_mood': session.emotional_context.dominant_mood,
            'final_intensity': session.emotional_context.average_intensity,
            'clarity_score': session.emotional_context.clarity_score,
            'state': session.state.name if session.state else 'UNKNOWN',
            'is_active': session.is_active,
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'ended_at': session.ended_at.isoformat() if session.ended_at else None,
        }
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        return self.session_store.cleanup_expired()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_conversation_manager(db_path: Optional[str] = None,
                                text_mood_detector: Optional[Any] = None) -> ConversationManager:
    """
    Create a ConversationManager instance.
    
    Args:
        db_path: Optional database path
        text_mood_detector: Optional TextMoodDetector instance
        
    Returns:
        ConversationManager instance
    """
    return ConversationManager(db_path, text_mood_detector)
