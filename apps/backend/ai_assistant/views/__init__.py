"""
AI Assistant views package
"""
from .ai_agents import (
    ChatSendView, HintGenerateView, QuizGenerateView,
    ReflectionGenerateView, PathGenerateView
)
from .sessions import (
    ChatHistoryView, SessionCreateView, SessionListView
)
from .transcripts import (
    TranscriptSearchView, TranscriptReferenceView, TranscriptReferenceListView
)
from .analytics import (
    UserAIStatsView, CheckLimitsView, UsageSummaryView, SystemStatsView
)

__all__ = [
    # AI Agents
    'ChatSendView', 'HintGenerateView', 'QuizGenerateView',
    'ReflectionGenerateView', 'PathGenerateView',
    # Sessions
    'ChatHistoryView', 'SessionCreateView', 'SessionListView',
    # Transcripts
    'TranscriptSearchView', 'TranscriptReferenceView', 'TranscriptReferenceListView',
    # Analytics
    'UserAIStatsView', 'CheckLimitsView', 'UsageSummaryView', 'SystemStatsView'
]