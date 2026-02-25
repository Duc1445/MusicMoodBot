"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - CONTEXT SIGNAL EXTRACTOR
=============================================================================

Extracts contextual signals from user input and environment.

Context signals include:
- Time of day (morning, afternoon, evening, night)
- Activity hints (working, exercising, relaxing, etc.)
- Social context (alone, with friends, etc.)
- Location hints (home, car, office, etc.)
- Device type (if detectable)

These signals enhance mood detection and song selection.

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from __future__ import annotations

import re
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from .types import ContextSignals

logger = logging.getLogger(__name__)


# =============================================================================
# TIME PATTERNS
# =============================================================================

TIME_OF_DAY_KEYWORDS = {
    'morning': [
        r'\bsáng\b', r'\bbuổi sáng\b', r'\bmorning\b', r'\bsớm\b',
        r'\bthức dậy\b', r'\bwake up\b', r'\bwoke up\b',
        r'\bbreakfast\b', r'\bđiểm tâm\b', r'\băn sáng\b',
    ],
    'afternoon': [
        r'\bchiều\b', r'\bbuổi chiều\b', r'\bafternoon\b',
        r'\blunch\b', r'\btrưa\b', r'\bgiữa ngày\b',
        r'\bnghỉ trưa\b', r'\bmidday\b',
    ],
    'evening': [
        r'\btối\b', r'\bbuổi tối\b', r'\bevening\b',
        r'\bdinner\b', r'\băn tối\b', r'\bhoàng hôn\b',
        r'\bsunset\b', r'\bchạng vạng\b',
    ],
    'night': [
        r'\bđêm\b', r'\bkhuya\b', r'\bnight\b', r'\blate night\b',
        r'\bmidnight\b', r'\bnửa đêm\b', r'\bmuộn\b',
        r'\btrước khi ngủ\b', r'\bbefore sleep\b',
    ],
}


# =============================================================================
# ACTIVITY PATTERNS
# =============================================================================

ACTIVITY_KEYWORDS = {
    'working': [
        r'\blàm việc\b', r'\bworking\b', r'\bwork\b', r'\boffice\b',
        r'\bvăn phòng\b', r'\bmeeting\b', r'\bhọp\b', r'\bcuộc họp\b',
        r'\bdeadline\b', r'\bproject\b', r'\bdự án\b',
        r'\btập trung\b', r'\bfocus\b', r'\bconcentrate\b',
    ],
    'exercising': [
        r'\btập\b', r'\bexercise\b', r'\bgym\b', r'\bworkout\b',
        r'\bchạy bộ\b', r'\bjogging\b', r'\brunning\b',
        r'\btập luyện\b', r'\btraining\b', r'\bsport\b',
        r'\byoga\b', r'\bđạp xe\b', r'\bcycling\b',
    ],
    'relaxing': [
        r'\bthư giãn\b', r'\brelax\b', r'\bchill\b', r'\brest\b',
        r'\bnghỉ ngơi\b', r'\bgiải trí\b', r'\bgiải stress\b',
        r'\bzen\b', r'\bpeace\b', r'\bcalm\b', r'\byên bình\b',
    ],
    'studying': [
        r'\bhọc\b', r'\bstudy\b', r'\bstudying\b', r'\breading\b',
        r'\bđọc sách\b', r'\bôn thi\b', r'\bexam\b', r'\bthi\b',
        r'\bresearch\b', r'\bnghiên cứu\b', r'\blibrary\b',
    ],
    'commuting': [
        r'\bđi làm\b', r'\bcommut\b', r'\btravel\b', r'\btrên xe\b',
        r'\bdriving\b', r'\blái xe\b', r'\bcông ty\b', r'\bđường\b',
        r'\btàu\b', r'\btrain\b', r'\bbus\b', r'\bxe buýt\b',
    ],
    'sleeping': [
        r'\bngủ\b', r'\bsleep\b', r'\bnap\b', r'\brad\b',
        r'\bgiấc ngủ\b', r'\binsomnia\b', r'\bmất ngủ\b',
        r'\blullaby\b', r'\bru ngủ\b', r'\bdreaming\b',
    ],
    'socializing': [
        r'\btiệc\b', r'\bparty\b', r'\bhangout\b', r'\bgặp gỡ\b',
        r'\bđi chơi\b', r'\bfriends\b', r'\bbạn bè\b',
        r'\bget together\b', r'\bhội họp\b', r'\bkaraoke\b',
    ],
    'cooking': [
        r'\bnấu ăn\b', r'\bcooking\b', r'\bkitchen\b', r'\bbếp\b',
        r'\blàm bánh\b', r'\bbaking\b', r'\bchef\b',
    ],
    'gaming': [
        r'\bchơi game\b', r'\bgaming\b', r'\bplaystation\b',
        r'\besport\b', r'\bstreaming\b', r'\blol\b', r'\bdota\b',
        r'\bfortnite\b', r'\bpubg\b', r'\bminecraft\b',
    ],
    'creative': [
        r'\bvẽ\b', r'\bdrawing\b', r'\bpainting\b', r'\bwriting\b',
        r'\bviết\b', r'\bcompose\b', r'\bsáng tạo\b', r'\bcreative\b',
        r'\bphotography\b', r'\bdesign\b', r'\bthiết kế\b',
    ],
}


# =============================================================================
# SOCIAL CONTEXT PATTERNS
# =============================================================================

SOCIAL_KEYWORDS = {
    'alone': [
        r'\bmột mình\b', r'\balone\b', r'\bsolitary\b', r'\blonely\b',
        r'\bcô đơn\b', r'\btự mình\b', r'\bby myself\b', r'\bsolo\b',
        r'\briêng\b', r'\bprivate\b', r'\bquiet time\b',
    ],
    'with_partner': [
        r'\bvới bạn trai\b', r'\bvới bạn gái\b', r'\bwith boyfriend\b',
        r'\bwith girlfriend\b', r'\bdate\b', r'\bhẹn hò\b',
        r'\bvới chồng\b', r'\bvới vợ\b', r'\bcouple\b',
        r'\bromantic\b', r'\blãng mạn\b', r'\bvalentine\b',
    ],
    'with_friends': [
        r'\bvới bạn\b', r'\bwith friends\b', r'\bfriend\b', r'\bbạn bè\b',
        r'\bhội\b', r'\bgang\b', r'\bcrew\b', r'\bsquad\b',
        r'\bgroup\b', r'\bnhóm\b', r'\bbạn thân\b',
    ],
    'with_family': [
        r'\bgia đình\b', r'\bfamily\b', r'\bvới ba\b', r'\bvới mẹ\b',
        r'\bparents\b', r'\bchildren\b', r'\bcon cái\b',
        r'\bsiblings\b', r'\banh chị em\b', r'\brelatives\b',
    ],
    'public': [
        r'\bnơi đông\b', r'\bcrowd\b', r'\bpublic\b',
        r'\bquán\b', r'\bcafe\b', r'\bcoffee shop\b',
        r'\brestaurant\b', r'\bnhà hàng\b', r'\bmall\b',
    ],
}


# =============================================================================
# LOCATION PATTERNS
# =============================================================================

LOCATION_KEYWORDS = {
    'home': [
        r'\bnhà\b', r'\bhome\b', r'\broom\b', r'\bphòng\b',
        r'\bbed\b', r'\bgiường\b', r'\bliving room\b', r'\bphòng khách\b',
        r'\bapartment\b', r'\bcăn hộ\b',
    ],
    'office': [
        r'\bvăn phòng\b', r'\boffice\b', r'\bworkplace\b', r'\bcông ty\b',
        r'\bmeeting room\b', r'\bphòng họp\b', r'\bdesk\b', r'\bcubicle\b',
    ],
    'outdoor': [
        r'\bngoài trời\b', r'\boutdoor\b', r'\boutside\b',
        r'\bpark\b', r'\bcông viên\b', r'\bgarden\b', r'\bvườn\b',
        r'\bbeach\b', r'\bbiển\b', r'\bmountain\b', r'\bnúi\b',
    ],
    'vehicle': [
        r'\btrên xe\b', r'\bin car\b', r'\bdriving\b', r'\bon bus\b',
        r'\btrain\b', r'\btàu\b', r'\bmetro\b', r'\bmotorbike\b',
        r'\bxe máy\b', r'\bxe hơi\b',
    ],
    'gym': [
        r'\bgym\b', r'\bphòng tập\b', r'\bfitness\b', r'\bsport center\b',
        r'\btrung tâm thể dục\b', r'\bstudio\b',
    ],
    'school': [
        r'\btrường\b', r'\bschool\b', r'\buniversity\b', r'\bđại học\b',
        r'\blớp\b', r'\bclass\b', r'\blibrary\b', r'\bthư viện\b',
    ],
    'cafe': [
        r'\bquán cafe\b', r'\bcoffee shop\b', r'\bstarbucks\b',
        r'\bhighlands\b', r'\bthe coffee house\b', r'\bcafeteria\b',
    ],
}


# =============================================================================
# CONTEXT EXTRACTOR
# =============================================================================

class ContextSignalExtractor:
    """
    Extracts contextual signals from user input and environment.
    
    Detects:
    - Time of day preferences/mentions
    - Activity context
    - Social situation
    - Location hints
    
    Usage:
        extractor = ContextSignalExtractor()
        signals = extractor.extract("Tôi đang làm việc ở văn phòng")
        # signals.activity = 'working'
        # signals.location = 'office'
    """
    
    def __init__(self):
        """Initialize extractor with compiled patterns."""
        # Compile all patterns
        self._time_patterns = self._compile_patterns(TIME_OF_DAY_KEYWORDS)
        self._activity_patterns = self._compile_patterns(ACTIVITY_KEYWORDS)
        self._social_patterns = self._compile_patterns(SOCIAL_KEYWORDS)
        self._location_patterns = self._compile_patterns(LOCATION_KEYWORDS)
    
    def _compile_patterns(self, pattern_dict: Dict[str, List[str]]) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficiency."""
        compiled = {}
        for category, patterns in pattern_dict.items():
            compiled[category] = [
                re.compile(p, re.IGNORECASE | re.UNICODE)
                for p in patterns
            ]
        return compiled
    
    def extract(self, text: str,
                timestamp: Optional[datetime] = None,
                client_info: Optional[Dict] = None) -> ContextSignals:
        """
        Extract context signals from text and environment.
        
        Args:
            text: User input text
            timestamp: Request timestamp (for time-based inference)
            client_info: Optional client metadata (device, etc.)
            
        Returns:
            ContextSignals with detected values
        """
        signals = ContextSignals()
        
        # Extract from text
        signals.time_of_day = self._extract_time_of_day(text, timestamp)
        signals.activity = self._extract_activity(text)
        signals.social_context = self._extract_social_context(text)
        signals.location = self._extract_location(text)
        
        # Extract from client info
        if client_info:
            if 'device_type' in client_info:
                signals.device_type = client_info['device_type']
            if 'platform' in client_info:
                signals.platform = client_info['platform']
        
        # Calculate confidence
        signals.confidence = self._calculate_confidence(signals)
        
        return signals
    
    def _extract_time_of_day(self, text: str,
                            timestamp: Optional[datetime] = None) -> Optional[str]:
        """Extract time of day from text or timestamp."""
        # Try pattern matching first
        time_result = self._match_patterns(text, self._time_patterns)
        if time_result:
            return time_result
        
        # Fall back to timestamp
        if timestamp:
            hour = timestamp.hour
            if 5 <= hour < 12:
                return 'morning'
            elif 12 <= hour < 17:
                return 'afternoon'
            elif 17 <= hour < 21:
                return 'evening'
            else:
                return 'night'
        
        # Default to current time
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def _extract_activity(self, text: str) -> Optional[str]:
        """Extract activity context from text."""
        return self._match_patterns(text, self._activity_patterns)
    
    def _extract_social_context(self, text: str) -> Optional[str]:
        """Extract social context from text."""
        return self._match_patterns(text, self._social_patterns)
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from text."""
        return self._match_patterns(text, self._location_patterns)
    
    def _match_patterns(self, text: str,
                        patterns: Dict[str, List[re.Pattern]]) -> Optional[str]:
        """
        Find first matching category.
        
        Uses priority order (first in dict wins).
        """
        text_lower = text.lower()
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern.search(text_lower):
                    return category
        
        return None
    
    def _match_all_patterns(self, text: str,
                           patterns: Dict[str, List[re.Pattern]]) -> List[str]:
        """Find all matching categories."""
        text_lower = text.lower()
        matches = []
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern.search(text_lower):
                    matches.append(category)
                    break
        
        return matches
    
    def _calculate_confidence(self, signals: ContextSignals) -> float:
        """
        Calculate confidence score for extracted signals.
        
        More signals = higher confidence (up to a point).
        """
        score = 0.0
        
        # Base score for having any signal
        if signals.time_of_day:
            score += 0.2
        if signals.activity:
            score += 0.3
        if signals.social_context:
            score += 0.2
        if signals.location:
            score += 0.2
        if signals.device_type:
            score += 0.1
        
        return min(score, 1.0)
    
    # =========================================================================
    # ADVANCED ANALYSIS
    # =========================================================================
    
    def extract_detailed(self, text: str,
                        timestamp: Optional[datetime] = None,
                        client_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract detailed context analysis.
        
        Returns all matches and confidence scores.
        """
        signals = self.extract(text, timestamp, client_info)
        
        # Get all matches
        all_activities = self._match_all_patterns(text, self._activity_patterns)
        all_social = self._match_all_patterns(text, self._social_patterns)
        all_locations = self._match_all_patterns(text, self._location_patterns)
        
        return {
            'signals': signals,
            'all_activities': all_activities,
            'all_social_contexts': all_social,
            'all_locations': all_locations,
            'analysis': {
                'text_length': len(text),
                'word_count': len(text.split()),
                'has_vietnamese': self._has_vietnamese(text),
                'has_english': self._has_english(text),
            },
        }
    
    def _has_vietnamese(self, text: str) -> bool:
        """Check if text contains Vietnamese characters."""
        vietnamese_chars = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.IGNORECASE)
        return bool(vietnamese_chars.search(text))
    
    def _has_english(self, text: str) -> bool:
        """Check if text contains English words."""
        english_words = ['the', 'is', 'are', 'am', 'was', 'were', 'be', 'been',
                         'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                         'could', 'should', 'may', 'might', 'must', 'i', 'you', 'we',
                         'they', 'he', 'she', 'it', 'this', 'that', 'what', 'which']
        text_lower = text.lower()
        for word in english_words:
            if re.search(rf'\b{word}\b', text_lower):
                return True
        return False
    
    # =========================================================================
    # MUSIC CONTEXT RECOMMENDATIONS
    # =========================================================================
    
    def suggest_music_context(self, signals: ContextSignals) -> Dict[str, Any]:
        """
        Suggest music parameters based on context.
        
        Maps context signals to music attributes.
        """
        suggestions = {
            'energy_preference': 0.5,
            'tempo_range': (80, 130),
            'instrumental_preference': 0.0,
            'acoustic_preference': 0.0,
            'vocals_important': True,
            'language_preference': None,
        }
        
        # Activity-based adjustments
        if signals.activity == 'exercising':
            suggestions['energy_preference'] = 0.9
            suggestions['tempo_range'] = (120, 180)
            suggestions['vocals_important'] = True
        elif signals.activity == 'working':
            suggestions['energy_preference'] = 0.5
            suggestions['tempo_range'] = (100, 140)
            suggestions['instrumental_preference'] = 0.6
        elif signals.activity == 'sleeping':
            suggestions['energy_preference'] = 0.2
            suggestions['tempo_range'] = (50, 90)
            suggestions['acoustic_preference'] = 0.7
        elif signals.activity == 'studying':
            suggestions['energy_preference'] = 0.4
            suggestions['tempo_range'] = (60, 100)
            suggestions['instrumental_preference'] = 0.8
        elif signals.activity == 'relaxing':
            suggestions['energy_preference'] = 0.3
            suggestions['tempo_range'] = (70, 110)
            suggestions['acoustic_preference'] = 0.5
        elif signals.activity == 'socializing':
            suggestions['energy_preference'] = 0.7
            suggestions['tempo_range'] = (100, 150)
            suggestions['vocals_important'] = True
        
        # Time-based adjustments
        if signals.time_of_day == 'night':
            suggestions['energy_preference'] = max(0.2, suggestions['energy_preference'] - 0.2)
        elif signals.time_of_day == 'morning':
            suggestions['energy_preference'] = min(0.8, suggestions['energy_preference'] + 0.1)
        
        # Social context adjustments
        if signals.social_context == 'alone':
            suggestions['instrumental_preference'] += 0.1
        elif signals.social_context in ('with_partner', 'with_friends'):
            suggestions['vocals_important'] = True
        
        return suggestions


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_context_extractor() -> ContextSignalExtractor:
    """Create a ContextSignalExtractor instance."""
    return ContextSignalExtractor()
