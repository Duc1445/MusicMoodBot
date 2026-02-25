"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - PROBE QUESTION BANK
=============================================================================

Manages the question bank for probing user emotions and context.

The question bank provides:
- Questions organized by category and depth
- Question selection with exclusion support
- Response mapping templates
- Usage tracking for analytics

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

from .types import EmotionalContext

logger = logging.getLogger(__name__)


# =============================================================================
# QUESTION DATA STRUCTURES
# =============================================================================

@dataclass
class ProbingQuestion:
    """
    A probing question with metadata.
    """
    # Identity
    question_id: str                      # e.g., 'mood_general_01'
    
    # Content
    text_vi: str                          # Vietnamese text
    text_en: Optional[str] = None         # English text (optional)
    
    # Classification
    category: str = "mood"                # 'mood', 'intensity', 'context', 'activity', 'time', 'confirmation'
    depth_level: int = 1                  # 1=surface, 2=deeper, 3=specific
    
    # Conditions
    conditions: Dict[str, Any] = field(default_factory=dict)  # When to use
    exclude_after_moods: List[str] = field(default_factory=list)  # Don't use if these moods detected
    
    # Response mapping
    response_mappings: Dict[str, str] = field(default_factory=dict)  # keyword -> mood/intensity
    
    # Ordering
    priority: int = 5                     # 1=highest, 10=lowest
    
    # Tracking
    times_asked: int = 0
    times_helpful: int = 0
    avg_clarity_gain: float = 0.0
    
    # Template placeholders
    placeholders: List[str] = field(default_factory=list)  # e.g., ['{mood}', '{intensity}']
    
    def get_text(self, lang: str = 'vi', **kwargs) -> str:
        """
        Get question text with placeholder substitution.
        
        Args:
            lang: Language code ('vi' or 'en')
            **kwargs: Placeholder values
            
        Returns:
            Formatted question text
        """
        text = self.text_vi if lang == 'vi' else (self.text_en or self.text_vi)
        
        # Substitute placeholders
        for key, value in kwargs.items():
            placeholder = f'{{{key}}}'
            if placeholder in text:
                text = text.replace(placeholder, str(value))
        
        return text
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'question_id': self.question_id,
            'text_vi': self.text_vi,
            'text_en': self.text_en,
            'category': self.category,
            'depth_level': self.depth_level,
            'conditions': self.conditions,
            'priority': self.priority,
        }


@dataclass
class QuestionSelection:
    """
    Result of question selection.
    """
    question: ProbingQuestion
    formatted_text: str
    alternatives: List[ProbingQuestion] = field(default_factory=list)
    reason: str = ""


# =============================================================================
# DEFAULT QUESTIONS
# =============================================================================

DEFAULT_QUESTIONS: List[ProbingQuestion] = [
    # =========================================================================
    # MOOD QUESTIONS - Level 1 (Surface)
    # =========================================================================
    ProbingQuestion(
        question_id='mood_general_01',
        text_vi='Hôm nay bạn cảm thấy thế nào?',
        text_en='How are you feeling today?',
        category='mood',
        depth_level=1,
        priority=1,
        conditions={'turn_number': 0},
    ),
    ProbingQuestion(
        question_id='mood_general_02',
        text_vi='Bạn đang có tâm trạng gì lúc này?',
        text_en='What mood are you in right now?',
        category='mood',
        depth_level=1,
        priority=2,
        conditions={'turn_number': 0},
    ),
    ProbingQuestion(
        question_id='mood_general_03',
        text_vi='Tâm trạng của bạn hôm nay ra sao?',
        text_en='How would you describe your mood today?',
        category='mood',
        depth_level=1,
        priority=3,
        conditions={'turn_number': 0},
    ),
    ProbingQuestion(
        question_id='mood_general_04',
        text_vi='Bạn muốn nghe nhạc phù hợp với tâm trạng nào?',
        text_en='What mood do you want music for?',
        category='mood',
        depth_level=1,
        priority=4,
    ),
    
    # =========================================================================
    # MOOD QUESTIONS - Level 2 (Deeper)
    # =========================================================================
    ProbingQuestion(
        question_id='mood_deeper_01',
        text_vi='Có chuyện gì khiến bạn cảm thấy như vậy không?',
        text_en='Is there something that makes you feel this way?',
        category='mood',
        depth_level=2,
        priority=1,
        conditions={'has_mood': True},
    ),
    ProbingQuestion(
        question_id='mood_deeper_02',
        text_vi='Bạn có thể mô tả thêm về cảm xúc hiện tại không?',
        text_en='Can you describe your current emotions more?',
        category='mood',
        depth_level=2,
        priority=2,
        conditions={'has_mood': True, 'confidence_below': 0.6},
    ),
    ProbingQuestion(
        question_id='mood_deeper_03',
        text_vi='Cảm xúc này đã kéo dài bao lâu rồi?',
        text_en='How long have you been feeling this way?',
        category='mood',
        depth_level=2,
        priority=3,
    ),
    
    # =========================================================================
    # INTENSITY QUESTIONS
    # =========================================================================
    ProbingQuestion(
        question_id='intensity_01',
        text_vi='Bạn đang cảm nhận điều này mạnh mẽ đến mức nào?',
        text_en='How strongly are you feeling this?',
        category='intensity',
        depth_level=1,
        priority=1,
        conditions={'has_mood': True, 'needs_intensity': True},
        response_mappings={
            'rất': 'Mạnh', 'cực': 'Mạnh', 'siêu': 'Mạnh', 'very': 'Mạnh', 'extremely': 'Mạnh',
            'bình thường': 'Vừa', 'vừa': 'Vừa', 'normal': 'Vừa', 'moderate': 'Vừa',
            'hơi': 'Nhẹ', 'chút': 'Nhẹ', 'a little': 'Nhẹ', 'slightly': 'Nhẹ',
        },
    ),
    ProbingQuestion(
        question_id='intensity_02',
        text_vi='Cảm xúc này có mãnh liệt không hay chỉ nhẹ nhàng thôi?',
        text_en='Is this feeling intense or subtle?',
        category='intensity',
        depth_level=1,
        priority=2,
        conditions={'has_mood': True, 'needs_intensity': True},
        response_mappings={
            'mãnh liệt': 'Mạnh', 'intense': 'Mạnh', 'strong': 'Mạnh',
            'nhẹ nhàng': 'Nhẹ', 'subtle': 'Nhẹ', 'gentle': 'Nhẹ',
        },
    ),
    ProbingQuestion(
        question_id='intensity_03',
        text_vi='Nếu cho điểm từ 1-10, bạn sẽ đánh giá cường độ cảm xúc này như thế nào?',
        text_en='On a scale of 1-10, how would you rate this feeling?',
        category='intensity',
        depth_level=2,
        priority=3,
        conditions={'has_mood': True, 'needs_intensity': True},
        response_mappings={
            '1': 'Nhẹ', '2': 'Nhẹ', '3': 'Nhẹ',
            '4': 'Vừa', '5': 'Vừa', '6': 'Vừa', '7': 'Vừa',
            '8': 'Mạnh', '9': 'Mạnh', '10': 'Mạnh',
        },
    ),
    
    # =========================================================================
    # CONTEXT QUESTIONS - Activity
    # =========================================================================
    ProbingQuestion(
        question_id='context_activity_01',
        text_vi='Bạn đang làm gì vậy? Làm việc, thư giãn hay đang di chuyển?',
        text_en='What are you doing? Working, relaxing, or commuting?',
        category='activity',
        depth_level=1,
        priority=1,
        conditions={'needs_context': True},
        response_mappings={
            'làm việc': 'working', 'work': 'working', 'working': 'working',
            'thư giãn': 'relaxing', 'relax': 'relaxing', 'rest': 'relaxing',
            'di chuyển': 'commuting', 'commuting': 'commuting', 'driving': 'commuting',
            'tập': 'exercising', 'gym': 'exercising', 'workout': 'exercising',
        },
    ),
    ProbingQuestion(
        question_id='context_activity_02',
        text_vi='Bạn muốn nghe nhạc để tập trung làm việc hay để thư giãn?',
        text_en='Do you want music to focus on work or to relax?',
        category='activity',
        depth_level=1,
        priority=2,
        conditions={'needs_context': True},
        response_mappings={
            'tập trung': 'working', 'focus': 'working',
            'thư giãn': 'relaxing', 'relax': 'relaxing',
        },
    ),
    
    # =========================================================================
    # CONTEXT QUESTIONS - Time
    # =========================================================================
    ProbingQuestion(
        question_id='context_time_01',
        text_vi='Đây có phải là buổi sáng để bắt đầu ngày mới không?',
        text_en='Is this morning to start your day?',
        category='time',
        depth_level=1,
        priority=3,
        conditions={'needs_time_context': True},
    ),
    
    # =========================================================================
    # CONTEXT QUESTIONS - Social
    # =========================================================================
    ProbingQuestion(
        question_id='context_social_01',
        text_vi='Bạn đang ở một mình hay cùng bạn bè?',
        text_en='Are you alone or with friends?',
        category='context',
        depth_level=2,
        priority=4,
        conditions={'needs_social_context': True},
        response_mappings={
            'một mình': 'alone', 'alone': 'alone',
            'bạn bè': 'with_friends', 'friends': 'with_friends', 'party': 'party',
        },
    ),
    
    # =========================================================================
    # CONFIRMATION QUESTIONS
    # =========================================================================
    ProbingQuestion(
        question_id='confirm_mood_01',
        text_vi='Vậy là bạn đang muốn nghe nhạc {mood} {intensity} đúng không?',
        text_en='So you want to listen to {mood} {intensity} music, right?',
        category='confirmation',
        depth_level=1,
        priority=1,
        conditions={'ready_to_confirm': True},
        placeholders=['mood', 'intensity'],
    ),
    ProbingQuestion(
        question_id='confirm_mood_02',
        text_vi='Tôi hiểu bạn đang cảm thấy {mood}. Bạn muốn nhạc giúp duy trì hay thay đổi tâm trạng?',
        text_en='I understand you are feeling {mood}. Do you want music to maintain or change your mood?',
        category='confirmation',
        depth_level=2,
        priority=2,
        conditions={'ready_to_confirm': True},
        placeholders=['mood'],
    ),
    
    # =========================================================================
    # SKIP / EARLY EXIT QUESTIONS
    # =========================================================================
    ProbingQuestion(
        question_id='skip_01',
        text_vi='Bạn có muốn tôi gợi ý nhạc ngay không? Hay muốn chat thêm?',
        text_en='Do you want me to suggest music now? Or chat more?',
        category='confirmation',
        depth_level=1,
        priority=5,
        conditions={'can_recommend': True},
    ),
]


# =============================================================================
# QUESTION BANK
# =============================================================================

class ProbeQuestionBank:
    """
    Manages probing questions for conversation.
    
    Provides:
    - Question lookup by ID
    - Category-based selection
    - Random selection with exclusions
    - Response pattern matching
    
    Usage:
        bank = ProbeQuestionBank()
        
        # Select a mood question
        selection = bank.select(
            category='mood',
            depth=1,
            exclude=['mood_general_01']
        )
        
        # Get formatted question
        text = selection.formatted_text
    """
    
    def __init__(self, questions: Optional[List[ProbingQuestion]] = None):
        """
        Initialize question bank.
        
        Args:
            questions: Custom questions, or None for defaults
        """
        self._questions: Dict[str, ProbingQuestion] = {}
        self._by_category: Dict[str, List[ProbingQuestion]] = {}
        
        # Load questions
        questions = questions or DEFAULT_QUESTIONS
        for q in questions:
            self.add_question(q)
    
    def add_question(self, question: ProbingQuestion):
        """
        Add a question to the bank.
        """
        self._questions[question.question_id] = question
        
        # Index by category
        if question.category not in self._by_category:
            self._by_category[question.category] = []
        self._by_category[question.category].append(question)
        
        # Sort by priority
        self._by_category[question.category].sort(key=lambda q: q.priority)
    
    def get(self, question_id: str) -> Optional[ProbingQuestion]:
        """
        Get question by ID.
        """
        return self._questions.get(question_id)
    
    def select(self, category: str,
               depth: int = 1,
               exclude: Optional[List[str]] = None,
               context: Optional[EmotionalContext] = None,
               **format_kwargs) -> Optional[QuestionSelection]:
        """
        Select a question from the bank.
        
        Args:
            category: Question category
            depth: Depth level (1-3)
            exclude: Question IDs to exclude
            context: EmotionalContext for condition checking
            **format_kwargs: Placeholder values
            
        Returns:
            QuestionSelection or None if no suitable question
        """
        exclude = exclude or []
        
        # Get candidates
        candidates = self._by_category.get(category, [])
        
        # Filter by depth and exclusions
        filtered = [
            q for q in candidates
            if q.depth_level <= depth 
            and q.question_id not in exclude
            and self._check_conditions(q, context)
        ]
        
        if not filtered:
            # Try any depth
            filtered = [
                q for q in candidates
                if q.question_id not in exclude
                and self._check_conditions(q, context)
            ]
        
        if not filtered:
            return None
        
        # Select by priority (with some randomization among same priority)
        best_priority = filtered[0].priority
        top_priority = [q for q in filtered if q.priority == best_priority]
        
        selected = random.choice(top_priority)
        
        # Format text
        format_kwargs.setdefault('mood', context.primary_mood if context else '')
        format_kwargs.setdefault('intensity', context.primary_intensity if context else '')
        
        formatted = selected.get_text('vi', **format_kwargs)
        
        # Get alternatives
        alternatives = [q for q in filtered if q != selected][:2]
        
        return QuestionSelection(
            question=selected,
            formatted_text=formatted,
            alternatives=alternatives,
            reason=f"Selected {selected.question_id} (priority={selected.priority}, depth={selected.depth_level})",
        )
    
    def _check_conditions(self, question: ProbingQuestion,
                         context: Optional[EmotionalContext]) -> bool:
        """
        Check if question conditions are met.
        """
        if not question.conditions:
            return True
        
        if context is None:
            return True
        
        conditions = question.conditions
        
        # Check has_mood condition
        if conditions.get('has_mood') and not context.primary_mood:
            return False
        
        # Check needs_intensity condition
        if conditions.get('needs_intensity') and context.intensity_specified:
            return False
        
        # Check confidence threshold
        if 'confidence_below' in conditions:
            if context.mood_confidence >= conditions['confidence_below']:
                return False
        
        # Check excluded moods
        if question.exclude_after_moods:
            if context.primary_mood in question.exclude_after_moods:
                return False
        
        return True
    
    def select_by_strategy(self, strategy_type: str,
                          question_category: str,
                          depth_level: int,
                          avoid: Optional[List[str]] = None,
                          preferred: Optional[List[str]] = None,
                          context: Optional[EmotionalContext] = None,
                          **format_kwargs) -> Optional[QuestionSelection]:
        """
        Select question based on strategy recommendation.
        
        Args:
            strategy_type: From ClarificationStrategy
            question_category: Category to select from
            depth_level: Maximum depth
            avoid: Questions to avoid
            preferred: Preferred question IDs
            context: EmotionalContext
            **format_kwargs: Placeholder values
            
        Returns:
            QuestionSelection or None
        """
        avoid = avoid or []
        preferred = preferred or []
        
        # Try preferred questions first
        for qid in preferred:
            q = self.get(qid)
            if q and qid not in avoid and self._check_conditions(q, context):
                format_kwargs.setdefault('mood', context.primary_mood if context else '')
                format_kwargs.setdefault('intensity', context.primary_intensity if context else '')
                formatted = q.get_text('vi', **format_kwargs)
                return QuestionSelection(
                    question=q,
                    formatted_text=formatted,
                    reason=f"Preferred question {qid}",
                )
        
        # Fall back to normal selection
        return self.select(
            category=question_category,
            depth=depth_level,
            exclude=avoid,
            context=context,
            **format_kwargs,
        )
    
    def get_response_mapping(self, question_id: str, response: str) -> Optional[str]:
        """
        Map user response to mood/intensity using question's response mappings.
        
        Args:
            question_id: Question that was asked
            response: User's response text
            
        Returns:
            Mapped value or None
        """
        question = self.get(question_id)
        if not question or not question.response_mappings:
            return None
        
        response_lower = response.lower()
        
        for keyword, value in question.response_mappings.items():
            if keyword in response_lower:
                return value
        
        return None
    
    def record_usage(self, question_id: str, was_helpful: bool, clarity_gain: float):
        """
        Record question usage for analytics.
        
        Args:
            question_id: Question that was used
            was_helpful: Did it help clarify?
            clarity_gain: Change in clarity score
        """
        question = self.get(question_id)
        if question:
            question.times_asked += 1
            if was_helpful:
                question.times_helpful += 1
            
            # Update rolling average
            n = question.times_asked
            old_avg = question.avg_clarity_gain
            question.avg_clarity_gain = old_avg + (clarity_gain - old_avg) / n
    
    def get_all_categories(self) -> List[str]:
        """Get all available question categories."""
        return list(self._by_category.keys())
    
    def get_questions_by_category(self, category: str) -> List[ProbingQuestion]:
        """Get all questions in a category."""
        return self._by_category.get(category, [])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_question_bank() -> ProbeQuestionBank:
    """
    Create a ProbeQuestionBank with default questions.
    """
    return ProbeQuestionBank()
