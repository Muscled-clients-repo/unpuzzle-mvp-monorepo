"""
Enrollment and progress tracking models.
"""
from django.db import models
from django.utils import timezone
from app.models import AuditableModel


class EnrollmentStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'
    EXPIRED = 'expired', 'Expired'
    CANCELLED = 'cancelled', 'Cancelled'
    SUSPENDED = 'suspended', 'Suspended'


class Enrollment(AuditableModel):
    """Course enrollment model"""
    
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
        db_index=True
    )
    
    # Progress tracking
    progress_percentage = models.FloatField(default=0.0)
    lessons_completed = models.IntegerField(default=0)
    total_lessons = models.IntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    
    # Dates
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    certificate_url = models.URLField(blank=True)
    
    # Payment info
    payment_method = models.CharField(max_length=50, blank=True)
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    payment_currency = models.CharField(max_length=3, default='USD')
    
    class Meta:
        db_table = 'enrollments'
        unique_together = [['user', 'course']]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['enrolled_at', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.course.title}"
    
    def update_progress(self, progress_percentage=None):
        """Update progress percentage"""
        if progress_percentage is not None:
            self.progress_percentage = progress_percentage
            if self.progress_percentage >= 100:
                self.status = EnrollmentStatus.COMPLETED
                self.completed_at = timezone.now()
            self.save()


class CourseReview(AuditableModel):
    """Course reviews and ratings"""
    
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='review'
    )
    
    # Rating
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        db_index=True
    )
    
    # Review content
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    
    # Metadata
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'course_reviews'
        indexes = [
            models.Index(fields=['rating', 'is_verified']),
            models.Index(fields=['created_at', 'rating']),
        ]
    
    def __str__(self):
        return f"{self.enrollment.user.email} - {self.rating} stars"
