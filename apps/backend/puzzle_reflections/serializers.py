"""
Serializers for puzzle reflections API.
"""
from rest_framework import serializers
from media_library.serializers import MediaFileSerializer
from .models import PuzzleReflection, ReflectionType


class PuzzleReflectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reflections"""
    
    media_url = serializers.ReadOnlyField()
    media_thumbnail = serializers.ReadOnlyField()
    has_media = serializers.ReadOnlyField()
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PuzzleReflection
        fields = [
            'id', 'video_id', 'reflection_type', 'title',
            'media_url', 'media_thumbnail', 'has_media',
            'loom_link', 'user_name', 'created_at'
        ]
    
    def get_user_name(self, obj):
        """Get user display name"""
        if hasattr(obj.user, 'full_name') and obj.user.full_name:
            return obj.user.full_name
        return obj.user.email if hasattr(obj.user, 'email') else str(obj.user)


class PuzzleReflectionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with full media information"""
    
    # Include full media file details
    media_file_details = MediaFileSerializer(source='media_file', read_only=True)
    
    # Computed fields for easy frontend access
    media_url = serializers.ReadOnlyField()
    media_thumbnail = serializers.ReadOnlyField()
    has_media = serializers.ReadOnlyField()
    
    # Media metadata
    file_type = serializers.CharField(source='media_file.file_type', read_only=True)
    file_size = serializers.IntegerField(source='media_file.file_size', read_only=True)
    duration = serializers.IntegerField(source='media_file.duration', read_only=True)
    
    # User info
    user_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = PuzzleReflection
        fields = [
            'id', 'video_id', 'reflection_type', 'title', 'description',
            'media_file', 'media_file_details', 'media_url', 'media_thumbnail',
            'has_media', 'file_type', 'file_size', 'duration',
            'loom_link', 'text_content', 'course', 'course_title',
            'user_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        """Get user display name"""
        if hasattr(obj.user, 'full_name') and obj.user.full_name:
            return obj.user.full_name
        return obj.user.email if hasattr(obj.user, 'email') else str(obj.user)


class PuzzleReflectionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating reflections"""
    
    class Meta:
        model = PuzzleReflection
        fields = [
            'video_id', 'reflection_type', 'title', 'description',
            'media_file', 'loom_link', 'text_content', 'course'
        ]
    
    def validate(self, data):
        """Ensure at least one content type is provided"""
        import logging
        logger = logging.getLogger(__name__)
        
        content_fields = ['media_file', 'loom_link', 'text_content']
        logger.info(f"=== SERIALIZER VALIDATION DEBUG ===")
        logger.info(f"Validation data: {data}")
        logger.info(f"Content fields to check: {content_fields}")
        
        content_values = []
        for field in content_fields:
            value = data.get(field)
            content_values.append(f"{field}: {repr(value)}")
            logger.info(f"Field '{field}' value: {repr(value)} (truthy: {bool(value)})")
        
        logger.info(f"All content field values: {', '.join(content_values)}")
        
        has_content = any(data.get(field) for field in content_fields)
        logger.info(f"Has any content: {has_content}")
        
        if not has_content:
            logger.error("Validation failed: No content fields provided")
            raise serializers.ValidationError(
                "At least one of media_file, loom_link, or text_content must be provided."
            )
        
        logger.info("Validation passed: At least one content field provided")
        return data


class ReflectionSummarySerializer(serializers.Serializer):
    """Serializer for reflection summaries by video"""
    video_id = serializers.CharField()
    total_reflections = serializers.IntegerField()
    reflection_types = serializers.ListField(
        child=serializers.DictField()
    )
    latest_reflection = PuzzleReflectionListSerializer(read_only=True)


class PuzzleReflectionUploadSerializer(serializers.Serializer):
    """Serializer for creating reflection with file upload"""
    file = serializers.FileField(required=False, help_text="File to upload (video/audio/document)")
    video_id = serializers.CharField(max_length=255, required=True)
    reflection_type = serializers.ChoiceField(
        choices=ReflectionType.choices,
        default=ReflectionType.VOICE
    )
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    loom_link = serializers.URLField(required=False, allow_blank=True)
    text_content = serializers.CharField(required=False, allow_blank=True)
    course = serializers.UUIDField(required=False, allow_null=True)
    
    def validate(self, data):
        """Ensure at least one content type is provided"""
        if not any([data.get('file'), data.get('loom_link'), data.get('text_content')]):
            raise serializers.ValidationError(
                "At least one of file, loom_link, or text_content must be provided."
            )
        
        # Validate file size if file is provided
        file = data.get('file')
        if file:
            max_size = 100 * 1024 * 1024  # 100MB
            if file.size > max_size:
                raise serializers.ValidationError(
                    f"File size exceeds maximum allowed size of {max_size / (1024*1024)}MB"
                )
        
        return data