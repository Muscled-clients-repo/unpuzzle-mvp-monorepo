"""
Media file management models.
"""
from django.db import models
from app.models import AuditableModel
import uuid


class FileType(models.TextChoices):
    VIDEO = 'video', 'Video'
    DOCUMENT = 'document', 'Document'
    IMAGE = 'image', 'Image'
    AUDIO = 'audio', 'Audio'
    OTHER = 'other', 'Other'


class ProcessingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    UPLOADING = 'uploading', 'Uploading'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class MediaFile(AuditableModel):
    """Media file model for all uploaded content"""
    
    # Relationships
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='media_files'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='media_files'
    )
    section = models.ForeignKey(
        'courses.CourseSection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='media_files'
    )
    
    # File information
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        db_index=True
    )
    mime_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    
    # Upload tracking
    upload_id = models.UUIDField(default=uuid.uuid4, unique=True)
    upload_progress = models.FloatField(default=0.0)
    
    # Storage
    storage_provider = models.CharField(max_length=50, default='backblaze')
    storage_bucket = models.CharField(max_length=100)
    storage_key = models.CharField(max_length=500, unique=True)
    storage_url = models.URLField(max_length=1000)
    cdn_url = models.URLField(max_length=1000, blank=True)
    
    # Processing
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True
    )
    processing_metadata = models.JSONField(default=dict, blank=True)
    
    # Video specific
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    bitrate = models.IntegerField(null=True, blank=True)
    resolution = models.CharField(max_length=20, blank=True)
    thumbnail_url = models.URLField(blank=True)
    subtitles = models.URLField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="CDN URL of the SRT subtitle file uploaded to Backblaze"
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    
    # Processing timestamps
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)
    
    class Meta:
        db_table = 'media_files'
        indexes = [
            models.Index(fields=['user', 'file_type']),
            models.Index(fields=['course', 'file_type']),
            models.Index(fields=['section', 'file_type']),
            models.Index(fields=['processing_status', 'created_at']),
        ]
    
    def __str__(self):
        return self.filename


class UploadSession(AuditableModel):
    """Model for chunked upload sessions"""
    
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    media_file = models.ForeignKey(
        MediaFile,
        on_delete=models.CASCADE,
        related_name='upload_sessions'
    )
    
    # Upload details
    total_chunks = models.IntegerField(default=0)
    uploaded_chunks = models.IntegerField(default=0)
    chunk_size = models.IntegerField(default=5242880)  # 5MB default
    
    # Status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Storage info
    storage_provider = models.CharField(max_length=50, default='backblaze')
    storage_key = models.CharField(max_length=500)
    upload_urls = models.JSONField(default=list)
    
    class Meta:
        db_table = 'upload_sessions'
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['is_active', 'expires_at']),
        ]
        # PostgreSQL RLS policies
        permissions = (
            ('upload_sessions_rls', 'Row Level Security for upload sessions'),
        )
    
    def __str__(self):
        return f"Upload session {self.session_id}"
