"""
AI Assistant app URL configuration
"""
from django.urls import path
from .views import (
    # AI Agent endpoints
    ChatSendView, HintGenerateView, QuizGenerateView,
    ReflectionGenerateView, PathGenerateView,
    
    # Session management
    ChatHistoryView, SessionCreateView, SessionListView,
    
    # Transcript processing
    TranscriptSearchView, TranscriptReferenceView, TranscriptReferenceListView,
    
    # Analytics
    UserAIStatsView, CheckLimitsView, UsageSummaryView, SystemStatsView
)

app_name = 'ai_assistant'

urlpatterns = [
    # Core AI Agent Endpoints (5 endpoints)
    path('chat/send/', ChatSendView.as_view(), name='chat-send'),
    path('agents/hint/', HintGenerateView.as_view(), name='agent-hint'),
    path('agents/quiz/', QuizGenerateView.as_view(), name='agent-quiz'),
    path('agents/reflection/', ReflectionGenerateView.as_view(), name='agent-reflection'),
    path('agents/path/', PathGenerateView.as_view(), name='agent-path'),
    
    # Session Management Endpoints (3 endpoints)
    path('chat/history/<uuid:session_id>/', ChatHistoryView.as_view(), name='chat-history'),
    path('chat/session/', SessionCreateView.as_view(), name='session-create'),
    path('chat/sessions/', SessionListView.as_view(), name='session-list'),
    
    # Transcript Processing Endpoints (3 endpoints)
    path('transcript/search/', TranscriptSearchView.as_view(), name='transcript-search'),
    path('transcript/reference/', TranscriptReferenceView.as_view(), name='transcript-reference'),
    path('transcript/references/', TranscriptReferenceListView.as_view(), name='transcript-references'),
    
    # User Analytics Endpoints (4 endpoints)
    path('user/ai-stats/', UserAIStatsView.as_view(), name='user-ai-stats'),
    path('user/check-limits/', CheckLimitsView.as_view(), name='check-limits'),
    path('user/usage-summary/', UsageSummaryView.as_view(), name='usage-summary'),
    
    # Admin endpoints
    path('admin/system-stats/', SystemStatsView.as_view(), name='system-stats'),
]