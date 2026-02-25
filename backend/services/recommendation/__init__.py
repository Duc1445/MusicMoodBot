"""
=============================================================================
INTELLIGENT RECOMMENDATION ENGINE
=============================================================================

Production-level music recommendation system with:
- Hybrid multi-factor ranking
- Emotional vector space matching
- Adaptive learning from feedback
- Analytics and evaluation
- v5.0: Thompson Sampling, Cold Start, Adaptive Weights

Author: MusicMoodBot Team
Version: 5.0.0
=============================================================================
"""

from .ranking_engine import (
    HybridRankingEngine,
    RankingConfig,
    RankingResult,
    RankingExplanation,
    ScoringComponents,
)

from .emotional_space import (
    EmotionalVectorSpace,
    EmotionalCoordinate,
    MoodVector,
    compute_va_similarity,
    mood_to_va_coordinates,
)

from .adaptive_learner import (
    AdaptiveLearner,
    LearningConfig,
    FeedbackSignal,
    WeightUpdate,
)

from .analytics_engine import (
    AnalyticsEngine,
    SystemMetrics,
    SessionMetrics,
    RecommendationMetrics,
)

from .robustness import (
    RobustnessManager,
    RobustnessConfig,
    TurnSafeguard,
    ConfidenceDecay,
    ContradictoryMoodResolver,
    TimeoutHandler,
    IdempotencyHandler,
    FSMErrorHandler,
    with_robustness,
)

# v5.0 Scoring Engine
from .scoring_engine import (
    ScoredSong,
    ThompsonSamplingBandit,
    ScoringEngine,
)

# v5.0 Weight Adapter
from .weight_adapter import (
    WeightAdjustment,
    WeightAdapter,
    DEFAULT_WEIGHTS,
)

# v5.0 Cold Start Handler
from .cold_start import (
    ColdStartSong,
    ColdStartHandler,
    ColdStartTransitionManager,
    get_cold_start_handler,
)

__version__ = '5.0.0'

__all__ = [
    # Ranking Engine
    'HybridRankingEngine',
    'RankingConfig',
    'RankingResult',
    'RankingExplanation',
    'ScoringComponents',
    
    # Emotional Space
    'EmotionalVectorSpace',
    'EmotionalCoordinate',
    'MoodVector',
    'compute_va_similarity',
    'mood_to_va_coordinates',
    
    # Adaptive Learning
    'AdaptiveLearner',
    'LearningConfig',
    'FeedbackSignal',
    'WeightUpdate',
    
    # Analytics
    'AnalyticsEngine',
    'SystemMetrics',
    'SessionMetrics',
    'RecommendationMetrics',
    
    # Robustness
    'RobustnessManager',
    'RobustnessConfig',
    'TurnSafeguard',
    'ConfidenceDecay',
    'ContradictoryMoodResolver',
    'TimeoutHandler',
    'IdempotencyHandler',
    'FSMErrorHandler',
    'with_robustness',
    
    # v5.0 Scoring Engine
    'ScoredSong',
    'ThompsonSamplingBandit',
    'ScoringEngine',
    
    # v5.0 Weight Adapter
    'WeightAdjustment',
    'WeightAdapter',
    'DEFAULT_WEIGHTS',
    
    # v5.0 Cold Start Handler
    'ColdStartSong',
    'ColdStartHandler',
    'ColdStartTransitionManager',
    'get_cold_start_handler',
    
    '__version__',
]
