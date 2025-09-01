"""
Media file and upload session serializers.
"""
from rest_framework import serializers
from .models import MediaFile, UploadSession, FileType, ProcessingStatus


class MediaFileSerializer(serializers.ModelSerializer):
    """Serializer for media files"""
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    section_title = serializers.CharField(source='section.title', read_only=True)
    
    class Meta:
        model = MediaFile
        fields = [
            'id', 'filename', 'original_filename', 'file_size', 'file_type',
            'mime_type', 'storage_url', 'cdn_url', 'thumbnail_url', 'upload_id',
            'processing_status', 'upload_progress', 'user', 'user_name',
            'course', 'course_title', 'section', 'section_title', 
            'duration', 'width', 'height', 'bitrate', 'resolution', 
            'processed_at', 'processing_error', 'metadata', 'is_public', 
            'is_archived', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'upload_id', 'user', 'user_name', 'course_title',
            'section_title', 'created_at', 'updated_at'
        ]


class UploadSessionSerializer(serializers.ModelSerializer):
    """Serializer for upload sessions"""
    media_file = MediaFileSerializer(read_only=True)
    
    class Meta:
        model = UploadSession
        fields = [
            'id', 'session_id', 'media_file', 'total_chunks',
            'uploaded_chunks', 'chunk_size', 'is_active',
            'expires_at', 'completed_at', 'storage_provider',
            'storage_key', 'upload_urls', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_id', 'created_at', 'updated_at'
        ]


class InitiateUploadSerializer(serializers.Serializer):
    """Serializer for initiating upload"""
    # Support both Flask format (filename) and camelCase (fileName)
    fileName = serializers.CharField(max_length=255, required=False)
    filename = serializers.CharField(max_length=255, required=False)
    fileSize = serializers.IntegerField(min_value=1)
    fileType = serializers.CharField(max_length=100, default='application/octet-stream', required=False)
    contentType = serializers.CharField(max_length=100, required=False)  # Flask format
    mediaType = serializers.ChoiceField(
        choices=['video', 'image', 'document', 'audio', 'other'],
        default='other',
        required=False
    )
    courseId = serializers.UUIDField(required=False, allow_null=True)
    
    def validate(self, data):
        # Ensure either fileName or filename is provided
        file_name = data.get('fileName') or data.get('filename')
        if not file_name:
            raise serializers.ValidationError("Either 'fileName' or 'filename' is required")
        
        # Normalize to fileName for internal use
        data['fileName'] = file_name
        
        # Handle content type (contentType or fileType)
        content_type = data.get('contentType') or data.get('fileType', 'application/octet-stream')
        data['fileType'] = content_type
        
        return data
    
    def validate_fileSize(self, value):
        max_size = 500 * 1024 * 1024  # 500MB
        if value > max_size:
            raise serializers.ValidationError(
                f"File size exceeds maximum of {max_size / (1024*1024)}MB"
            )
        return value


class CompleteUploadSerializer(serializers.Serializer):
    """Serializer for completing upload"""
    # Support multiple naming conventions
    uploadId = serializers.CharField(required=False)
    sessionId = serializers.CharField(required=False)
    sessionKey = serializers.CharField(required=False)  # Flask format
    session_key = serializers.CharField(required=False)  # Snake case
    storageKey = serializers.CharField(required=False)  # Flask format
    storage_key = serializers.CharField(required=False)  # Snake case
    upload_id = serializers.CharField(required=False)   # Snake case
    
    def validate(self, data):
        # Check all possible session identifier fields
        session_id = (data.get('sessionId') or 
                     data.get('sessionKey') or 
                     data.get('session_key') or
                     data.get('session_id'))
        
        if not session_id:
            available_fields = list(data.keys())
            raise serializers.ValidationError(
                f"Session identifier required. Expected one of: sessionId, sessionKey, session_key. "
                f"Received fields: {available_fields}"
            )
        
        # Normalize to sessionId for internal use
        data['sessionId'] = session_id
        
        # Handle upload ID if provided
        upload_id = (data.get('uploadId') or 
                    data.get('upload_id'))
        if upload_id:
            data['uploadId'] = upload_id
            
        return data


class AssignVideoSerializer(serializers.Serializer):
    """Serializer for assigning video to course section"""
    videoId = serializers.UUIDField()
    courseId = serializers.UUIDField()
    sectionId = serializers.UUIDField()


class VideoListSerializer(serializers.ModelSerializer):
    """Simplified serializer for video listings"""
    
    class Meta:
        model = MediaFile
        fields = [
            'id', 'filename', 'file_size', 'cdn_url', 'thumbnail_url',
            'duration', 'processing_status', 'created_at'
        ]