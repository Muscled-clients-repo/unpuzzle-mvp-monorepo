"""
AI Assistant admin configuration
"""
from django.contrib import admin
from .models import (
    AISession, AIMessage, AIUsageMetric, 
    TranscriptSegment, TranscriptReference, UserAIPreference
)


@admin.register(AISession)
class AISessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'course', 'video_id', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at', 'course']
    search_fields = ['user__email', 'video_id', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'message_type', 'agent_type', 'tokens_used', 'cached', 'created_at']
    list_filter = ['message_type', 'agent_type', 'cached', 'created_at']
    search_fields = ['session__user__email', 'content']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(AIUsageMetric)
class AIUsageMetricAdmin(admin.ModelAdmin):
    list_display = ['user', 'agent_type', 'tokens_used', 'cost', 'session', 'course', 'created_at']
    list_filter = ['agent_type', 'created_at', 'course']
    search_fields = ['user__email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(TranscriptSegment)
class TranscriptSegmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'video_id', 'course', 'start_time', 'end_time', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['video_id', 'text', 'course__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['video_id', 'start_time']


@admin.register(TranscriptReference)
class TranscriptReferenceAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'video_id', 'start_time', 'end_time', 'purpose', 'expires_at', 'created_at']
    list_filter = ['purpose', 'created_at', 'expires_at']
    search_fields = ['user__email', 'video_id', 'text']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(UserAIPreference)
class UserAIPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_response_length', 'difficulty_level', 'created_at', 'updated_at']
    list_filter = ['preferred_response_length', 'difficulty_level', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
