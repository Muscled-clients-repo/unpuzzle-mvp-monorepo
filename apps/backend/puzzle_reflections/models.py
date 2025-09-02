"""
Puzzle reflection models following project architecture patterns.
"""
from django.db import models
from app.models import AuditableModel, RLSModelMixin


class ReflectionType(models.TextChoices):
    """Reflection type choices based on content type"""
    VOICE = 'voice', 'Voice Reflection'
    IMAGE = 'image', 'Image Reflection'
    LOOM_LINK = 'loom_link', 'Loom Video Link'


class PuzzleReflection(AuditableModel, RLSModelMixin):
    """
    Model for storing user puzzle reflections with media integration.
    Follows the project's AuditableModel pattern with RLS support.
    """
    
    # Core relationships (using proper FK references)
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='puzzle_reflections',
        help_text="User who created this reflection"
    )
    
    # Content association
    video_id = models.ForeignKey(
        'media_library.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='video_reflections',
        db_index=True,
        help_text="Video MediaFile this reflection is for"
    )
    
    # Reflection categorization
    reflection_type = models.CharField(
        max_length=20,
        choices=ReflectionType.choices,
        default=ReflectionType.VOICE,
        db_index=True
    )
    
    # Media file integration (KEY ARCHITECTURAL DECISION)
    media_file = models.ForeignKey(
        'media_library.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puzzle_reflections',
        help_text="Uploaded reflection media file (video/audio/document)"
    )
    
    # Alternative content options
    loom_link = models.URLField(
        null=True,
        blank=True,
        help_text="Optional Loom video link"
    )
    
    text_content = models.TextField(
        blank=True,
        null=True,
        help_text="Optional text reflection content"
    )
    
    # Metadata
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    # Optional course association for analytics
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puzzle_reflections'
    )
    
    class Meta:
        db_table = 'puzzle_reflections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'video_id']),
            models.Index(fields=['reflection_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['media_file']),
            models.Index(fields=['course', 'user']),
        ]
        # RLS permissions
        permissions = (
            ('puzzle_reflections_rls', 'Row Level Security for puzzle reflections'),
        )
    
    def __str__(self):
        user_display = self.user.full_name if hasattr(self.user, 'full_name') and self.user.full_name else self.user.email
        video_display = self.video_id.filename if self.video_id else "Unknown video"
        return f"Reflection by {user_display} for video {video_display}"
    
    @property
    def has_media(self):
        """Check if reflection has any media content"""
        return bool(self.media_file or self.loom_link)
    
    @property
    def media_url(self):
        """Get the primary media URL (MediaFile CDN or Loom)"""
        if self.media_file and self.media_file.cdn_url:
            return self.media_file.cdn_url
        elif self.media_file and self.media_file.storage_url:
            return self.media_file.storage_url
        elif self.loom_link:
            return self.loom_link
        return None
    
    @property
    def media_thumbnail(self):
        """Get thumbnail URL if available"""
        if self.media_file and self.media_file.thumbnail_url:
            return self.media_file.thumbnail_url
        return None
    
    # RLS Implementation
    @classmethod
    def get_rls_policies(cls):
        """Define RLS policies for user data isolation"""
        return [
            {
                'name': 'puzzle_reflections_user_isolation',
                'operation': 'ALL',
                'role': 'authenticated',
                'using': 'user_id = (auth.jwt() ->> \'sub\')::uuid',
                'with_check': 'user_id = (auth.jwt() ->> \'sub\')::uuid'
            }
        ]
