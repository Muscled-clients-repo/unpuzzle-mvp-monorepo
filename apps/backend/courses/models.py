"""
Course management models.
"""
from django.db import models
from django.utils.text import slugify
from django.contrib.postgres.fields import ArrayField
from decimal import Decimal
from app.models import AuditableModel, RLSModelMixin


class DifficultyLevel(models.TextChoices):
    BEGINNER = 'beginner', 'Beginner'
    INTERMEDIATE = 'intermediate', 'Intermediate'
    ADVANCED = 'advanced', 'Advanced'
    ALL_LEVELS = 'all', 'All Levels'


class CourseStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'  # Alias for published
    PUBLISHED = 'published', 'Published'
    UNPUBLISHED = 'unpublished', 'Unpublished'
    ARCHIVED = 'archived', 'Archived'


class EnrollmentStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    PAUSED = 'paused', 'Paused'
    CANCELLED = 'cancelled', 'Cancelled'


class CourseCategory(AuditableModel):
    """Course category model"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
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


class Course(AuditableModel, RLSModelMixin):
    """Course model with all features and RLS support"""
    
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
    
    # Instructor - Reference to UserProfile
    instructor = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taught_courses',
        db_index=True
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
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
            base_slug = slugify(self.title)
            self.slug = base_slug
            
            # Handle duplicate slugs by appending a number
            counter = 1
            while Course.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
                # Prevent infinite loop
                if counter > 1000:
                    import uuid
                    self.slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                    break
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @classmethod
    def get_rls_policies(cls):
        """Define RLS policies for Course model"""
        return [
            # Public can view published courses
            {
                'name': 'courses_select_published',
                'operation': 'SELECT',
                'role': 'anon',
                'using': "is_published = true AND status IN ('published', 'active')"
            },
            # Authenticated users can see all published courses
            {
                'name': 'courses_select_auth',
                'operation': 'SELECT',
                'role': 'authenticated',
                'using': "is_published = true OR instructor_id = auth.uid()"
            },
            # Instructors can manage their own courses
            {
                'name': 'courses_insert_instructor',
                'operation': 'INSERT',
                'role': 'authenticated',
                'with_check': "instructor_id = auth.uid()"
            },
            {
                'name': 'courses_update_instructor',
                'operation': 'UPDATE',
                'role': 'authenticated',
                'using': "instructor_id = auth.uid()",
                'with_check': "instructor_id = auth.uid()"
            },
            {
                'name': 'courses_delete_instructor',
                'operation': 'DELETE',
                'role': 'authenticated',
                'using': "instructor_id = auth.uid()"
            }
        ]


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



