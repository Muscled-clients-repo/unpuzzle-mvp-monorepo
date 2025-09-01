"""
AI Assistant models for managing chat sessions, messages, and AI interactions.
"""
from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid
from app.models import TimeStampedModel


class AgentType(models.TextChoices):
    CHAT = 'chat', 'Chat Assistant'
    HINT = 'hint', 'Hint Generator'
    QUIZ = 'quiz', 'Quiz Generator'
    REFLECTION = 'reflection', 'Reflection Prompt'
    PATH = 'path', 'Learning Path'


class MessageType(models.TextChoices):
    USER = 'user', 'User Message'
    ASSISTANT = 'assistant', 'AI Assistant Message'
    SYSTEM = 'system', 'System Message'


class AISession(TimeStampedModel):
    """
    AI chat session for maintaining conversation context
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='ai_sessions'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='ai_sessions',
        null=True,
        blank=True
    )
    video_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Associated video ID'
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        help_text='Session title or topic'
    )
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'ai_sessions'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['course', 'user']),
            models.Index(fields=['video_id', 'user']),
        ]
    
    def __str__(self):
        return f"AI Session {self.id} - {self.user.email}"


class AIMessage(TimeStampedModel):
    """
    Individual messages within an AI session
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    session = models.ForeignKey(
        AISession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.USER
    )
    content = models.TextField()
    agent_type = models.CharField(
        max_length=20,
        choices=AgentType.choices,
        null=True,
        blank=True
    )
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text='Video context, timestamp, etc.'
    )
    tokens_used = models.IntegerField(default=0)
    cached = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'ai_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['message_type', 'agent_type']),
        ]
    
    def __str__(self):
        return f"Message {self.id} - {self.message_type}"


class AIUsageMetric(TimeStampedModel):
    """
    Track AI usage for billing and rate limiting
    """
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='ai_usage_metrics'
    )
    agent_type = models.CharField(
        max_length=20,
        choices=AgentType.choices
    )
    tokens_used = models.IntegerField(default=0)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0.0
    )
    session = models.ForeignKey(
        AISession,
        on_delete=models.CASCADE,
        related_name='usage_metrics',
        null=True,
        blank=True
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='ai_usage_metrics',
        null=True,
        blank=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'ai_usage_metrics'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['agent_type', '-created_at']),
            models.Index(fields=['user', 'agent_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"Usage {self.user.email} - {self.agent_type}"


class TranscriptSegment(TimeStampedModel):
    """
    Video transcript chunks for AI context and search
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    video_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text='Associated video ID'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='transcript_segments'
    )
    text = models.TextField()
    start_time = models.FloatField(help_text='Start time in seconds')
    end_time = models.FloatField(help_text='End time in seconds')
    embedding = ArrayField(
        models.FloatField(),
        size=1536,  # OpenAI embedding dimensions
        null=True,
        blank=True,
        help_text='Text embedding for semantic search'
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'transcript_segments'
        ordering = ['video_id', 'start_time']
        indexes = [
            models.Index(fields=['video_id', 'start_time']),
            models.Index(fields=['course', 'video_id']),
        ]
    
    def __str__(self):
        return f"Transcript {self.video_id} - {self.start_time}s"


class TranscriptReference(TimeStampedModel):
    """
    User-selected transcript segments for AI context
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='transcript_references'
    )
    video_id = models.CharField(max_length=255, db_index=True)
    text = models.TextField()
    start_time = models.FloatField()
    end_time = models.FloatField()
    purpose = models.CharField(
        max_length=50,
        default='ai_context',
        help_text='Purpose of the reference'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this reference expires'
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'transcript_references'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'video_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Reference {self.user.email} - {self.video_id}"


class UserAIPreference(TimeStampedModel):
    """
    User preferences for AI interactions
    """
    user = models.OneToOneField(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='ai_preferences'
    )
    preferred_response_length = models.CharField(
        max_length=20,
        choices=[
            ('short', 'Short'),
            ('medium', 'Medium'),
            ('long', 'Long')
        ],
        default='medium'
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='intermediate'
    )
    learning_style = models.JSONField(
        default=dict,
        blank=True,
        help_text='Learning style preferences'
    )
    agent_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text='Per-agent customizations'
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'user_ai_preferences'
    
    def __str__(self):
        return f"AI Preferences - {self.user.email}"
