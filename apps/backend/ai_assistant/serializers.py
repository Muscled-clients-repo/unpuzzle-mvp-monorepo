"""
AI Assistant API serializers
"""
from rest_framework import serializers
from .models import AISession, AIMessage, AIUsageMetric, TranscriptReference, AgentType


class AISessionSerializer(serializers.ModelSerializer):
    """Serializer for AI chat sessions"""
    
    class Meta:
        model = AISession
        fields = [
            'id', 'course', 'video_id', 'title', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AIMessageSerializer(serializers.ModelSerializer):
    """Serializer for AI messages"""
    
    class Meta:
        model = AIMessage
        fields = [
            'id', 'message_type', 'content', 'agent_type',
            'context', 'tokens_used', 'cached', 'created_at'
        ]
        read_only_fields = ['id', 'tokens_used', 'cached', 'created_at']


class ChatSendRequestSerializer(serializers.Serializer):
    """Serializer for chat send requests"""
    message = serializers.CharField(max_length=2000)
    session_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    context = serializers.JSONField(required=False, default=dict)


class ChatSendResponseSerializer(serializers.Serializer):
    """Serializer for chat send responses"""
    response = serializers.CharField()
    session_id = serializers.CharField()  # Backend UUID as string
    frontend_session_id = serializers.CharField(required=False, allow_null=True)  # Frontend's session ID
    message_id = serializers.UUIDField()
    tokens_used = serializers.IntegerField()
    cached = serializers.BooleanField()


class HintRequestSerializer(serializers.Serializer):
    """Serializer for hint generation requests"""
    video_id = serializers.CharField(max_length=255)
    timestamp = serializers.FloatField()
    transcript_segment = serializers.CharField(max_length=2000)
    user_difficulty = serializers.CharField(max_length=500, required=False)


class HintResponseSerializer(serializers.Serializer):
    """Serializer for hint generation responses"""
    hint = serializers.CharField()
    confidence = serializers.FloatField()
    agent_type = serializers.CharField()
    tokens_used = serializers.IntegerField()


class QuizRequestSerializer(serializers.Serializer):
    """Serializer for quiz generation requests"""
    video_id = serializers.CharField(max_length=255, required=False)
    timestamp = serializers.FloatField(required=False)
    transcript_segments = serializers.ListField(
        child=serializers.CharField(max_length=1000),
        max_length=10,
        required=False,
        default=list
    )
    difficulty_level = serializers.ChoiceField(
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        default='medium'
    )


class QuizResponseSerializer(serializers.Serializer):
    """Serializer for quiz generation responses"""
    question = serializers.CharField()
    options = serializers.ListField(
        child=serializers.CharField(max_length=500),
        max_length=4,
        min_length=4
    )
    correctAnswer = serializers.IntegerField(min_value=0, max_value=3)
    explanation = serializers.CharField()
    agent_type = serializers.CharField()
    tokens_used = serializers.IntegerField()


class ReflectionRequestSerializer(serializers.Serializer):
    """Serializer for reflection generation requests"""
    completed_topics = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        default=list
    )
    learning_objectives = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        default=list
    )
    video_id = serializers.CharField(max_length=255)


class ReflectionResponseSerializer(serializers.Serializer):
    """Serializer for reflection generation responses"""
    prompt = serializers.CharField()
    guidingQuestions = serializers.ListField(
        child=serializers.CharField(max_length=500),
        max_length=5
    )
    expectedLength = serializers.ChoiceField(
        choices=[('short', 'Short'), ('medium', 'Medium'), ('long', 'Long')]
    )
    agent_type = serializers.CharField()
    tokens_used = serializers.IntegerField()


class PathRequestSerializer(serializers.Serializer):
    """Serializer for learning path requests"""
    user_id = serializers.IntegerField()
    struggling_concepts = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        default=list
    )
    completed_concepts = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        default=list
    )
    learning_goals = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        default=list
    )


class RecommendedContentSerializer(serializers.Serializer):
    """Serializer for recommended content items"""
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    difficulty = serializers.CharField()
    estimatedTime = serializers.CharField()
    priority = serializers.IntegerField()


class PathResponseSerializer(serializers.Serializer):
    """Serializer for learning path responses"""
    detectedIssues = serializers.ListField(
        child=serializers.CharField(max_length=500),
        max_length=10
    )
    recommendedContent = serializers.ListField(
        child=RecommendedContentSerializer(),
        max_length=5
    )
    nextSteps = serializers.ListField(
        child=serializers.CharField(max_length=500),
        max_length=5
    )
    agent_type = serializers.CharField()
    tokens_used = serializers.IntegerField()


class ChatHistoryResponseSerializer(serializers.Serializer):
    """Serializer for chat history responses"""
    session_id = serializers.UUIDField()
    course_id = serializers.CharField()
    video_id = serializers.CharField()
    messages = AIMessageSerializer(many=True)
    total_messages = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class TranscriptSearchRequestSerializer(serializers.Serializer):
    """Serializer for transcript search requests"""
    video_id = serializers.CharField(max_length=255)
    query = serializers.CharField(max_length=500)
    limit = serializers.IntegerField(default=5, min_value=1, max_value=20)


class TranscriptSearchResultSerializer(serializers.Serializer):
    """Serializer for transcript search result items"""
    text = serializers.CharField()
    start_time = serializers.FloatField()
    end_time = serializers.FloatField()
    similarity = serializers.FloatField()
    chunk_id = serializers.CharField()


class TranscriptSearchResponseSerializer(serializers.Serializer):
    """Serializer for transcript search responses"""
    results = TranscriptSearchResultSerializer(many=True)
    total_results = serializers.IntegerField()
    search_time_ms = serializers.IntegerField()


class TranscriptReferenceRequestSerializer(serializers.Serializer):
    """Serializer for transcript reference requests"""
    video_id = serializers.CharField(max_length=255)
    start_time = serializers.FloatField()
    end_time = serializers.FloatField()
    text = serializers.CharField(max_length=2000)
    purpose = serializers.CharField(default='ai_context', max_length=50)


class TranscriptReferenceResponseSerializer(serializers.Serializer):
    """Serializer for transcript reference responses"""
    reference_id = serializers.UUIDField()
    saved = serializers.BooleanField()
    message = serializers.CharField()
    expires_at = serializers.DateTimeField()


class AIUsageMetricsSerializer(serializers.Serializer):
    """Serializer for AI usage metrics"""
    total_interactions = serializers.IntegerField()
    hints_generated = serializers.IntegerField()
    quizzes_completed = serializers.IntegerField()
    reflections_submitted = serializers.IntegerField()
    learning_paths_created = serializers.IntegerField()


class DailyUsageSerializer(serializers.Serializer):
    """Serializer for daily usage stats"""
    interactions_today = serializers.IntegerField()
    limit = serializers.IntegerField()
    remaining = serializers.IntegerField()
    reset_time = serializers.DateTimeField()


class MonthlyUsageSerializer(serializers.Serializer):
    """Serializer for monthly usage stats"""
    interactions_this_month = serializers.IntegerField()
    limit = serializers.IntegerField()
    remaining = serializers.IntegerField()


class UserAIStatsResponseSerializer(serializers.Serializer):
    """Serializer for user AI stats responses"""
    user_id = serializers.UUIDField()
    metrics = AIUsageMetricsSerializer()
    daily_usage = DailyUsageSerializer()
    monthly_usage = MonthlyUsageSerializer()
    subscription_plan = serializers.CharField()
    cost_this_month = serializers.FloatField()


class CheckLimitsRequestSerializer(serializers.Serializer):
    """Serializer for check limits requests"""
    agent_type = serializers.ChoiceField(choices=AgentType.choices)
    estimated_tokens = serializers.IntegerField(default=50, min_value=1, max_value=2000)


class CheckLimitsResponseSerializer(serializers.Serializer):
    """Serializer for check limits responses"""
    can_use_ai = serializers.BooleanField()
    remaining_interactions = serializers.IntegerField()
    daily_limit = serializers.IntegerField()
    monthly_limit = serializers.IntegerField()
    subscription_plan = serializers.CharField()
    reset_time = serializers.DateTimeField()
    cost_estimate = serializers.FloatField()
    upgrade_required = serializers.BooleanField()
    upgrade_message = serializers.CharField(allow_null=True)