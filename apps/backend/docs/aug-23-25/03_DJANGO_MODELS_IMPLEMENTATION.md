# Django Models Implementation - Complete Data Layer
**Date**: 2025-08-23  
**Time**: 10:30:00  
**Component**: Django ORM Models

## Overview

This document provides the complete Django ORM implementation for all models, migrating from SQLAlchemy to Django's powerful ORM with enhanced features and optimizations.

## Base Models

### Abstract Base Models
```python
# core/models.py
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

class UUIDModel(models.Model):
    """Abstract model with UUID as primary key"""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    class Meta:
        abstract = True

class TimeStampedModel(models.Model):
    """Abstract model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']

class AuditableModel(UUIDModel, TimeStampedModel):
    """Abstract model with full audit trail"""
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted'
    )
    
    class Meta:
        abstract = True
        
    def soft_delete(self, user=None):
        """Soft delete the record"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def restore(self):
        """Restore soft deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
```

## User Management Models

### Custom User Model
```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from core.models import AuditableModel
from .managers import UserManager

class UserStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    SUSPENDED = 'suspended', 'Suspended'
    PENDING = 'pending', 'Pending'

class User(AbstractBaseUser, PermissionsMixin, AuditableModel):
    """Custom user model with extended features"""
    
    # Authentication fields
    email = models.EmailField(
        unique=True,
        db_index=True,
        verbose_name='Email Address'
    )
    username = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    
    # Profile fields
    full_name = models.CharField(max_length=255, blank=True)
    display_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        null=True,
        blank=True
    )
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    
    # Status fields
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
        db_index=True
    )
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.TextField(blank=True)
    
    # Django specific
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Custom manager
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['username', 'status']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.full_name or self.email
    
    def get_short_name(self):
        return self.display_name or self.email.split('@')[0]

class Role(AuditableModel):
    """Role model for RBAC"""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='custom_roles'
    )
    users = models.ManyToManyField(
        User,
        through='UserRole',
        related_name='custom_roles'
    )
    
    class Meta:
        db_table = 'roles'
        ordering = ['priority', 'name']
    
    def __str__(self):
        return self.display_name

class UserRole(models.Model):
    """Through model for User-Role relationship"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='roles_assigned'
    )
    
    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']

class UserSession(AuditableModel):
    """User session management"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_key = models.CharField(max_length=255, unique=True, db_index=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.JSONField(default=dict)
    expires_at = models.DateTimeField()
    refresh_expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key', 'is_active']),
        ]
```

## Course Management Models

### Course Models
```python
# apps/courses/models.py
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils.text import slugify
from core.models import AuditableModel

class DifficultyLevel(models.TextChoices):
    BEGINNER = 'beginner', 'Beginner'
    INTERMEDIATE = 'intermediate', 'Intermediate'
    ADVANCED = 'advanced', 'Advanced'
    ALL_LEVELS = 'all', 'All Levels'

class CourseStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
    UNPUBLISHED = 'unpublished', 'Unpublished'
    ARCHIVED = 'archived', 'Archived'

class Course(AuditableModel):
    """Course model with all features"""
    
    # Core fields
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    
    # Media
    thumbnail = models.ImageField(
        upload_to='course_thumbnails/%Y/%m/',
        null=True,
        blank=True
    )
    preview_video_url = models.URLField(blank=True)
    
    # Instructor
    instructor = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='taught_courses',
        db_index=True
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    currency = models.CharField(max_length=3, default='USD')
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_free = models.BooleanField(default=False, db_index=True)
    
    # Course details
    duration = models.IntegerField(default=0, help_text='Duration in seconds')
    difficulty = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.BEGINNER,
        db_index=True
    )
    language = models.CharField(max_length=10, default='en')
    
    # Categorization
    category = models.ForeignKey(
        'CourseCategory',
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses'
    )
    tags = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list
    )
    
    # Course structure
    prerequisites = models.JSONField(default=list, blank=True)
    learning_outcomes = models.JSONField(default=list, blank=True)
    target_audience = models.JSONField(default=list, blank=True)
    course_structure = models.JSONField(null=True, blank=True)
    
    # Statistics (denormalized for performance)
    enrollment_count = models.IntegerField(default=0, db_index=True)
    completion_count = models.IntegerField(default=0)
    rating_average = models.FloatField(default=0.0, db_index=True)
    rating_count = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=CourseStatus.choices,
        default=CourseStatus.DRAFT,
        db_index=True
    )
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    seo_metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title', 'status', 'is_published']),
            models.Index(fields=['instructor', 'status']),
            models.Index(fields=['category', 'status', 'is_published']),
            models.Index(fields=['rating_average', 'enrollment_count']),
            models.Index(fields=['price', 'is_free', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class CourseCategory(AuditableModel):
    """Course category model"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    icon = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'course_categories'
        verbose_name_plural = 'Course Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class CourseSection(AuditableModel):
    """Course section for organizing content"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    is_preview = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'course_sections'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['course', 'order']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
```

## Media Management Models

```python
# apps/media_library/models.py
from django.db import models
from core.models import AuditableModel

class FileType(models.TextChoices):
    VIDEO = 'video', 'Video'
    DOCUMENT = 'document', 'Document'
    IMAGE = 'image', 'Image'
    AUDIO = 'audio', 'Audio'
    OTHER = 'other', 'Other'

class ProcessingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'

class MediaFile(AuditableModel):
    """Media file model for all uploaded content"""
    
    # Relationships
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='media_files'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='media_files'
    )
    section = models.ForeignKey(
        'courses.CourseSection',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='media_files'
    )
    
    # File information
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        db_index=True
    )
    mime_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField(help_text='File size in bytes')
    
    # Storage
    storage_provider = models.CharField(
        max_length=50,
        default='backblaze'
    )
    storage_path = models.TextField()
    public_url = models.URLField(max_length=500)
    thumbnail_url = models.URLField(max_length=500, blank=True)
    
    # Video specific
    duration = models.IntegerField(
        null=True,
        blank=True,
        help_text='Duration in seconds'
    )
    resolution = models.CharField(max_length=20, blank=True)
    video_codec = models.CharField(max_length=50, blank=True)
    audio_codec = models.CharField(max_length=50, blank=True)
    bitrate = models.IntegerField(null=True, blank=True)
    
    # Processing
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING
    )
    processing_error = models.TextField(blank=True)
    transcoding_data = models.JSONField(default=dict, blank=True)
    
    # Configuration
    is_public = models.BooleanField(default=False)
    is_downloadable = models.BooleanField(default=False)
    order_index = models.IntegerField(default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    upload_metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'media_files'
        ordering = ['order_index', 'created_at']
        indexes = [
            models.Index(fields=['course', 'section', 'order_index']),
            models.Index(fields=['user', 'file_type']),
            models.Index(fields=['processing_status']),
        ]
    
    def __str__(self):
        return self.file_name
```

## Learning & Progress Models

```python
# apps/enrollments/models.py
from django.db import models
from django.contrib.postgres.fields import ArrayField
from core.models import AuditableModel

class EnrollmentStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    DROPPED = 'dropped', 'Dropped'
    EXPIRED = 'expired', 'Expired'

class Enrollment(AuditableModel):
    """Student enrollment in courses"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
        db_index=True
    )
    progress_percentage = models.FloatField(default=0.0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    certificate_url = models.URLField(blank=True)
    
    class Meta:
        db_table = 'enrollments'
        unique_together = ['user', 'course']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.course.title}"

class CourseProgress(AuditableModel):
    """Detailed course progress tracking"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='course_progress'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    section = models.ForeignKey(
        'courses.CourseSection',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    completed_videos = ArrayField(
        models.UUIDField(),
        default=list,
        blank=True
    )
    last_video_id = models.UUIDField(null=True, blank=True)
    total_watch_time = models.IntegerField(default=0)
    completion_percentage = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_progress'
        unique_together = ['user', 'course', 'section']
        indexes = [
            models.Index(fields=['user', 'course']),
        ]

class VideoProgress(AuditableModel):
    """Individual video progress tracking"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='video_progress'
    )
    video = models.ForeignKey(
        'media_library.MediaFile',
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='video_progress'
    )
    watch_time = models.IntegerField(default=0)
    last_position = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    completion_percentage = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'video_progress'
        unique_together = ['user', 'video']
        indexes = [
            models.Index(fields=['user', 'course', 'completed']),
        ]
```

## Quiz & Assessment Models

```python
# apps/courses/quiz_models.py
from django.db import models
from core.models import AuditableModel

class QuizType(models.TextChoices):
    PRACTICE = 'practice', 'Practice'
    GRADED = 'graded', 'Graded'
    FINAL = 'final', 'Final Exam'

class QuestionType(models.TextChoices):
    MULTIPLE_CHOICE = 'multiple_choice', 'Multiple Choice'
    TRUE_FALSE = 'true_false', 'True/False'
    SHORT_ANSWER = 'short_answer', 'Short Answer'
    ESSAY = 'essay', 'Essay'

class Quiz(AuditableModel):
    """Quiz model for assessments"""
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    section = models.ForeignKey(
        'CourseSection',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quizzes'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quiz_type = models.CharField(
        max_length=20,
        choices=QuizType.choices,
        default=QuizType.PRACTICE
    )
    passing_score = models.FloatField(default=70.0)
    time_limit = models.IntegerField(
        null=True,
        blank=True,
        help_text='Time limit in minutes'
    )
    max_attempts = models.IntegerField(default=3)
    is_randomized = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    order_index = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'quizzes'
        verbose_name_plural = 'Quizzes'
        ordering = ['order_index', 'created_at']

class QuizQuestion(AuditableModel):
    """Quiz question model"""
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices
    )
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.JSONField()
    explanation = models.TextField(blank=True)
    points = models.FloatField(default=1.0)
    order_index = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'quiz_questions'
        ordering = ['order_index']

class QuizAttempt(AuditableModel):
    """Quiz attempt tracking"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0.0)
    percentage = models.FloatField(default=0.0)
    answers = models.JSONField(default=dict)
    is_passed = models.BooleanField(default=False)
    time_taken = models.IntegerField(
        default=0,
        help_text='Time taken in seconds'
    )
    
    class Meta:
        db_table = 'quiz_attempts'
        indexes = [
            models.Index(fields=['user', 'quiz']),
        ]
```

## Review & Rating Models

```python
# apps/courses/review_models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import AuditableModel

class Review(AuditableModel):
    """Course review and rating"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=True)
    helpful_count = models.IntegerField(default=0)
    reported_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'reviews'
        unique_together = ['user', 'course']
        indexes = [
            models.Index(fields=['course', 'rating']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.course.title} ({self.rating}★)"
```

## AI Chat Models

```python
# apps/ai_assistant/models.py
from django.db import models
from core.models import AuditableModel

class MessageType(models.TextChoices):
    QUESTION = 'question', 'Question'
    ANSWER = 'answer', 'Answer'
    SUGGESTION = 'suggestion', 'Suggestion'

class AIChat(AuditableModel):
    """AI chat conversation history"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='ai_chats'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ai_chats'
    )
    session_id = models.UUIDField(db_index=True)
    message = models.TextField()
    response = models.TextField()
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.QUESTION
    )
    context_data = models.JSONField(default=dict, blank=True)
    tokens_used = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'ai_chats'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'session_id']),
            models.Index(fields=['course', 'created_at']),
        ]
```

## Model Managers

```python
# apps/accounts/managers.py
from django.contrib.auth.models import BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    
    def active_users(self):
        return self.filter(is_active=True, status='active')

class CourseManager(models.Manager):
    """Custom course manager"""
    
    def published(self):
        return self.filter(is_published=True, status='published')
    
    def by_instructor(self, instructor):
        return self.filter(instructor=instructor)
    
    def popular(self):
        return self.published().order_by('-enrollment_count', '-rating_average')
    
    def free_courses(self):
        return self.published().filter(is_free=True)

class EnrollmentManager(models.Manager):
    """Custom enrollment manager"""
    
    def active(self):
        return self.filter(status='active')
    
    def completed(self):
        return self.filter(status='completed')
    
    def by_user(self, user):
        return self.filter(user=user)
    
    def by_course(self, course):
        return self.filter(course=course)
```

## Model Signals

```python
# apps/courses/signals.py
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Course, Enrollment, Review

@receiver(post_save, sender=Course)
def invalidate_course_cache(sender, instance, **kwargs):
    """Invalidate course cache on save"""
    cache_key = f'course:{instance.id}'
    cache.delete(cache_key)
    cache.delete('course:list:*')

@receiver(post_save, sender=Enrollment)
def update_course_enrollment_count(sender, instance, created, **kwargs):
    """Update course enrollment count"""
    if created:
        course = instance.course
        course.enrollment_count = course.enrollments.filter(
            status='active'
        ).count()
        course.save(update_fields=['enrollment_count'])

@receiver(post_save, sender=Review)
def update_course_rating(sender, instance, **kwargs):
    """Update course rating average"""
    course = instance.course
    reviews = course.reviews.filter(is_deleted=False)
    if reviews.exists():
        total_rating = sum(r.rating for r in reviews)
        course.rating_count = reviews.count()
        course.rating_average = total_rating / course.rating_count
    else:
        course.rating_count = 0
        course.rating_average = 0.0
    course.save(update_fields=['rating_count', 'rating_average'])

@receiver(pre_save, sender=Course)
def generate_course_slug(sender, instance, **kwargs):
    """Auto-generate course slug"""
    if not instance.slug:
        from django.utils.text import slugify
        base_slug = slugify(instance.title)
        slug = base_slug
        counter = 1
        while Course.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        instance.slug = slug
```

## Database Migrations

```python
# Example migration file
# apps/courses/migrations/0001_initial.py
from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    initial = True
    
    dependencies = [
        ('accounts', '0001_initial'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(db_index=True, max_length=255)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                # ... other fields
            ],
            options={
                'db_table': 'courses',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='course',
            index=models.Index(
                fields=['title', 'status', 'is_published'],
                name='idx_course_search'
            ),
        ),
    ]
```

## Performance Optimizations

### Query Optimization
```python
# Efficient query with select_related and prefetch_related
from django.db.models import Prefetch

# Optimize course queries
courses = Course.objects.select_related(
    'instructor',
    'category'
).prefetch_related(
    'sections',
    'sections__media_files',
    Prefetch(
        'enrollments',
        queryset=Enrollment.objects.filter(status='active'),
        to_attr='active_enrollments'
    )
).filter(
    is_published=True
)

# Use only() for specific fields
users = User.objects.only(
    'id', 'email', 'full_name'
).filter(status='active')

# Use defer() to exclude heavy fields
courses = Course.objects.defer(
    'description',
    'course_structure',
    'metadata'
).filter(is_published=True)
```

---
**Document Version**: 1.0  
**Last Updated**: 2025-08-23  
**Next Document**: Django API Implementation