# Django Services Architecture - Business Logic Layer
**Date**: 2025-08-23  
**Time**: 11:00:00  
**Component**: Service Layer Implementation

## Overview

Complete implementation of the service layer that encapsulates all business logic, ensuring clean separation of concerns and maintainable code architecture.

## Service Layer Design Principles

### Architecture Pattern
```python
"""
Service Layer Pattern Implementation:
1. Services contain all business logic
2. Views handle HTTP concerns only
3. Models handle data persistence
4. Services coordinate between models
5. Services are stateless and reusable
"""

# Base Service Class
# services/base.py
from typing import Any, Dict, Optional
from django.db import transaction
from django.core.cache import cache
import logging

class BaseService:
    """Base service class with common functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cache = cache
    
    @transaction.atomic
    def execute_in_transaction(self, func, *args, **kwargs):
        """Execute function in database transaction"""
        return func(*args, **kwargs)
    
    def get_cached_or_compute(self, cache_key: str, compute_func, timeout: int = 300):
        """Get from cache or compute and cache"""
        result = self.cache.get(cache_key)
        if result is None:
            result = compute_func()
            self.cache.set(cache_key, result, timeout)
        return result
    
    def invalidate_cache(self, pattern: str):
        """Invalidate cache by pattern"""
        self.cache.delete_pattern(pattern)
    
    def log_action(self, action: str, user=None, **kwargs):
        """Log service action"""
        self.logger.info(
            f"Action: {action}",
            extra={
                'user': user.id if user else None,
                **kwargs
            }
        )
```

## Authentication Service

```python
# services/auth_service.py
from typing import Optional, Tuple, Dict
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import User, UserSession, Role
from .base import BaseService
import secrets
import hashlib

class AuthService(BaseService):
    """Authentication and authorization service"""
    
    @transaction.atomic
    def register_user(
        self,
        email: str,
        password: str,
        full_name: str = '',
        role: str = 'student',
        **kwargs
    ) -> Tuple[User, Dict[str, str]]:
        """Register a new user"""
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            **kwargs
        )
        
        # Assign role
        role_obj = Role.objects.get(name=role)
        user.custom_roles.add(role_obj)
        
        # Generate tokens
        tokens = self.generate_tokens(user)
        
        # Send verification email
        self.send_verification_email(user)
        
        self.log_action('user_registered', user=user, role=role)
        
        return user, tokens
    
    def authenticate_user(
        self,
        email: str,
        password: str,
        request=None
    ) -> Optional[Tuple[User, Dict[str, str]]]:
        """Authenticate user and generate tokens"""
        user = authenticate(username=email, password=password)
        
        if not user:
            self.log_action('authentication_failed', email=email)
            return None
        
        if not user.is_active:
            self.log_action('inactive_user_login', user=user)
            return None
        
        # Generate tokens
        tokens = self.generate_tokens(user)
        
        # Create session
        self.create_session(user, request, tokens)
        
        # Update last login
        user.last_login = timezone.now()
        if request:
            user.last_login_ip = self.get_client_ip(request)
            user.last_login_device = request.META.get('HTTP_USER_AGENT', '')
        user.save(update_fields=['last_login', 'last_login_ip', 'last_login_device'])
        
        self.log_action('user_authenticated', user=user)
        
        return user, tokens
    
    def generate_tokens(self, user: User) -> Dict[str, str]:
        """Generate JWT tokens"""
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims
        refresh['email'] = user.email
        refresh['roles'] = list(user.custom_roles.values_list('name', flat=True))
        
        return {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh)
        }
    
    @transaction.atomic
    def create_session(
        self,
        user: User,
        request=None,
        tokens: Dict[str, str] = None
    ) -> UserSession:
        """Create user session"""
        session_key = secrets.token_urlsafe(32)
        
        session = UserSession.objects.create(
            user=user,
            session_key=session_key,
            access_token=tokens.get('access_token', ''),
            refresh_token=tokens.get('refresh_token', ''),
            ip_address=self.get_client_ip(request) if request else '',
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            expires_at=timezone.now() + timedelta(days=7),
            refresh_expires_at=timezone.now() + timedelta(days=30)
        )
        
        return session
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token"""
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Generate new tokens
            user = User.objects.get(id=token['user_id'])
            new_tokens = self.generate_tokens(user)
            
            # Update session
            UserSession.objects.filter(
                refresh_token=refresh_token
            ).update(
                access_token=new_tokens['access_token'],
                refresh_token=new_tokens['refresh_token'],
                last_activity=timezone.now()
            )
            
            return new_tokens
            
        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}")
            return None
    
    @transaction.atomic
    def logout_user(self, user: User, session_key: Optional[str] = None):
        """Logout user and invalidate session"""
        if session_key:
            UserSession.objects.filter(
                user=user,
                session_key=session_key
            ).update(is_active=False)
        else:
            UserSession.objects.filter(
                user=user,
                is_active=True
            ).update(is_active=False)
        
        # Clear user cache
        self.invalidate_cache(f'user:{user.id}:*')
        
        self.log_action('user_logged_out', user=user)
    
    def send_verification_email(self, user: User):
        """Send email verification"""
        from .email_service import EmailService
        
        token = self.generate_verification_token(user)
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        EmailService().send_email(
            to=user.email,
            subject='Verify your email',
            template='email/verification.html',
            context={
                'user': user,
                'verification_url': verification_url
            }
        )
    
    def generate_verification_token(self, user: User) -> str:
        """Generate email verification token"""
        token = secrets.token_urlsafe(32)
        cache_key = f'email_verification:{token}'
        self.cache.set(cache_key, user.id, timeout=86400)  # 24 hours
        return token
    
    def verify_email(self, token: str) -> bool:
        """Verify email with token"""
        cache_key = f'email_verification:{token}'
        user_id = self.cache.get(cache_key)
        
        if not user_id:
            return False
        
        User.objects.filter(id=user_id).update(
            email_verified=True,
            status='active'
        )
        
        self.cache.delete(cache_key)
        return True
    
    def get_client_ip(self, request) -> str:
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def check_permission(user: User, permission: str) -> bool:
        """Check if user has permission"""
        return user.has_perm(permission) or user.custom_roles.filter(
            permissions__codename=permission
        ).exists()
```

## Course Service

```python
# services/course_service.py
from typing import List, Dict, Optional
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.utils.text import slugify
from apps.courses.models import Course, CourseSection, CourseCategory
from apps.enrollments.models import Enrollment
from .base import BaseService
import uuid

class CourseService(BaseService):
    """Course management service"""
    
    @transaction.atomic
    def create_course(
        self,
        instructor,
        title: str,
        description: str,
        **kwargs
    ) -> Course:
        """Create a new course"""
        # Generate unique slug
        slug = self.generate_unique_slug(title)
        
        course = Course.objects.create(
            instructor=instructor,
            title=title,
            slug=slug,
            description=description,
            **kwargs
        )
        
        # Create default section
        CourseSection.objects.create(
            course=course,
            title='Introduction',
            order=1
        )
        
        self.log_action('course_created', user=instructor, course_id=course.id)
        
        return course
    
    def generate_unique_slug(self, title: str) -> str:
        """Generate unique slug for course"""
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        
        while Course.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    @transaction.atomic
    def publish_course(self, course: Course) -> Course:
        """Publish a course"""
        errors = self.validate_for_publishing(course)
        if errors:
            raise ValueError(f"Course cannot be published: {', '.join(errors)}")
        
        course.status = 'published'
        course.is_published = True
        course.published_at = timezone.now()
        course.save()
        
        # Send notifications to followers
        self.notify_course_published(course)
        
        # Invalidate cache
        self.invalidate_cache(f'course:{course.id}')
        self.invalidate_cache('course:list:*')
        
        self.log_action('course_published', user=course.instructor, course_id=course.id)
        
        return course
    
    def validate_for_publishing(self, course: Course) -> List[str]:
        """Validate course is ready for publishing"""
        errors = []
        
        if not course.description or len(course.description) < 100:
            errors.append('Description must be at least 100 characters')
        
        if not course.thumbnail:
            errors.append('Course thumbnail is required')
        
        sections = course.sections.filter(is_deleted=False)
        if sections.count() < 2:
            errors.append('Course must have at least 2 sections')
        
        # Check if course has videos
        total_videos = 0
        for section in sections:
            total_videos += section.media_files.filter(
                file_type='video',
                is_deleted=False
            ).count()
        
        if total_videos < 5:
            errors.append('Course must have at least 5 videos')
        
        if not course.learning_outcomes or len(course.learning_outcomes) < 3:
            errors.append('At least 3 learning outcomes are required')
        
        return errors
    
    def unpublish_course(self, course: Course) -> Course:
        """Unpublish a course"""
        course.status = 'unpublished'
        course.is_published = False
        course.save()
        
        self.invalidate_cache(f'course:{course.id}')
        self.invalidate_cache('course:list:*')
        
        return course
    
    @transaction.atomic
    def duplicate_course(self, course: Course) -> Course:
        """Duplicate a course with all content"""
        new_course = Course.objects.create(
            instructor=course.instructor,
            title=f"{course.title} (Copy)",
            slug=self.generate_unique_slug(f"{course.title}-copy"),
            description=course.description,
            short_description=course.short_description,
            price=course.price,
            currency=course.currency,
            difficulty=course.difficulty,
            language=course.language,
            category=course.category,
            tags=course.tags,
            prerequisites=course.prerequisites,
            learning_outcomes=course.learning_outcomes,
            target_audience=course.target_audience,
            status='draft',
            is_published=False
        )
        
        # Duplicate sections
        for section in course.sections.filter(is_deleted=False):
            new_section = CourseSection.objects.create(
                course=new_course,
                title=section.title,
                description=section.description,
                order=section.order
            )
            
            # Note: Media files are not duplicated, they need to be re-uploaded
        
        self.log_action('course_duplicated', user=course.instructor, 
                       original_id=course.id, new_id=new_course.id)
        
        return new_course
    
    def search_courses(
        self,
        query: str = '',
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_free: Optional[bool] = None,
        min_rating: Optional[float] = None,
        language: Optional[str] = None,
        instructor: Optional[str] = None,
        order_by: str = '-created_at'
    ) -> List[Course]:
        """Advanced course search"""
        courses = Course.objects.filter(
            is_published=True,
            status='published'
        )
        
        if query:
            courses = courses.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__contains=[query])
            )
        
        if category:
            courses = courses.filter(category__slug=category)
        
        if difficulty:
            courses = courses.filter(difficulty=difficulty)
        
        if min_price is not None:
            courses = courses.filter(price__gte=min_price)
        
        if max_price is not None:
            courses = courses.filter(price__lte=max_price)
        
        if is_free is not None:
            courses = courses.filter(is_free=is_free)
        
        if min_rating is not None:
            courses = courses.filter(rating_average__gte=min_rating)
        
        if language:
            courses = courses.filter(language=language)
        
        if instructor:
            courses = courses.filter(instructor__username=instructor)
        
        # Apply ordering
        courses = courses.order_by(order_by)
        
        return courses.select_related('instructor', 'category')
    
    def get_course_recommendations(
        self,
        user,
        limit: int = 10
    ) -> List[Course]:
        """Get personalized course recommendations"""
        # Get user's enrolled courses
        enrolled_course_ids = Enrollment.objects.filter(
            user=user
        ).values_list('course_id', flat=True)
        
        # Get categories from enrolled courses
        categories = Course.objects.filter(
            id__in=enrolled_course_ids
        ).values_list('category', flat=True).distinct()
        
        # Get similar courses
        recommendations = Course.objects.filter(
            is_published=True,
            status='published'
        ).exclude(
            id__in=enrolled_course_ids
        )
        
        if categories:
            recommendations = recommendations.filter(
                category__in=categories
            )
        
        # Order by rating and enrollment count
        recommendations = recommendations.annotate(
            score=Count('enrollments') * Avg('rating_average')
        ).order_by('-score')[:limit]
        
        return recommendations
    
    def update_course_statistics(self, course: Course):
        """Update course statistics (denormalized fields)"""
        # Update enrollment count
        course.enrollment_count = course.enrollments.filter(
            status='active'
        ).count()
        
        # Update completion count
        course.completion_count = course.enrollments.filter(
            status='completed'
        ).count()
        
        # Update rating
        reviews = course.reviews.filter(is_deleted=False)
        if reviews.exists():
            course.rating_count = reviews.count()
            course.rating_average = reviews.aggregate(
                Avg('rating')
            )['rating__avg']
        else:
            course.rating_count = 0
            course.rating_average = 0.0
        
        course.save(update_fields=[
            'enrollment_count',
            'completion_count',
            'rating_count',
            'rating_average'
        ])
    
    def notify_course_published(self, course: Course):
        """Send notifications when course is published"""
        from .notification_service import NotificationService
        
        # Get instructor's followers
        followers = User.objects.filter(
            following__followed=course.instructor
        )
        
        notification_service = NotificationService()
        for follower in followers:
            notification_service.create_notification(
                user=follower,
                type='course_published',
                title=f'New course by {course.instructor.get_full_name()}',
                message=f'{course.title} is now available',
                data={'course_id': str(course.id)}
            )
```

## Enrollment Service

```python
# services/enrollment_service.py
from typing import Tuple, Optional
from django.db import transaction
from django.utils import timezone
from apps.enrollments.models import Enrollment, CourseProgress, VideoProgress
from apps.courses.models import Course
from apps.media_library.models import MediaFile
from .base import BaseService

class EnrollmentService(BaseService):
    """Enrollment and progress management service"""
    
    @transaction.atomic
    def enroll_student(self, user, course_id: str) -> Enrollment:
        """Enroll a student in a course"""
        # Check if already enrolled
        existing = Enrollment.objects.filter(
            user=user,
            course_id=course_id
        ).first()
        
        if existing:
            if existing.status == 'dropped':
                # Re-activate enrollment
                existing.status = 'active'
                existing.save()
                return existing
            raise ValueError('Already enrolled in this course')
        
        # Get course
        course = Course.objects.get(id=course_id)
        
        # Check if course is published
        if not course.is_published:
            raise ValueError('Course is not available for enrollment')
        
        # Create enrollment
        enrollment = Enrollment.objects.create(
            user=user,
            course=course,
            status='active'
        )
        
        # Create initial progress record
        CourseProgress.objects.create(
            user=user,
            course=course
        )
        
        # Update course statistics
        course.enrollment_count += 1
        course.save(update_fields=['enrollment_count'])
        
        # Send notifications
        self.send_enrollment_notifications(enrollment)
        
        self.log_action('student_enrolled', user=user, course_id=course_id)
        
        return enrollment
    
    def drop_course(self, enrollment: Enrollment):
        """Drop a course enrollment"""
        enrollment.status = 'dropped'
        enrollment.save()
        
        # Update course statistics
        course = enrollment.course
        course.enrollment_count = course.enrollments.filter(
            status='active'
        ).count()
        course.save(update_fields=['enrollment_count'])
        
        self.log_action('course_dropped', user=enrollment.user, 
                       course_id=enrollment.course_id)
    
    @transaction.atomic
    def update_progress(
        self,
        user,
        video_id: str,
        course_id: str,
        watch_time: int,
        last_position: int,
        completed: bool = False
    ) -> Tuple[VideoProgress, CourseProgress]:
        """Update video and course progress"""
        # Get or create video progress
        video_progress, created = VideoProgress.objects.get_or_create(
            user=user,
            video_id=video_id,
            defaults={'course_id': course_id}
        )
        
        # Update video progress
        video_progress.watch_time = watch_time
        video_progress.last_position = last_position
        
        # Get video duration
        video = MediaFile.objects.get(id=video_id)
        if video.duration:
            video_progress.completion_percentage = (
                last_position / video.duration * 100
            )
            
            # Mark as completed if watched 90% or more
            if video_progress.completion_percentage >= 90:
                video_progress.completed = True
                completed = True
        
        video_progress.completed = completed
        video_progress.save()
        
        # Update course progress
        course_progress = self.update_course_progress(
            user, course_id, video_id, completed
        )
        
        # Check for course completion
        self.check_course_completion(user, course_id)
        
        return video_progress, course_progress
    
    def update_course_progress(
        self,
        user,
        course_id: str,
        video_id: str,
        completed: bool
    ) -> CourseProgress:
        """Update overall course progress"""
        progress, created = CourseProgress.objects.get_or_create(
            user=user,
            course_id=course_id
        )
        
        # Update completed videos
        if completed and video_id not in progress.completed_videos:
            progress.completed_videos.append(video_id)
        
        progress.last_video_id = video_id
        
        # Calculate completion percentage
        course = Course.objects.get(id=course_id)
        total_videos = MediaFile.objects.filter(
            course=course,
            file_type='video',
            is_deleted=False
        ).count()
        
        if total_videos > 0:
            progress.completion_percentage = (
                len(progress.completed_videos) / total_videos * 100
            )
        
        # Update total watch time
        total_watch = VideoProgress.objects.filter(
            user=user,
            course_id=course_id
        ).aggregate(Sum('watch_time'))['watch_time__sum'] or 0
        
        progress.total_watch_time = total_watch
        progress.save()
        
        # Update enrollment progress
        Enrollment.objects.filter(
            user=user,
            course_id=course_id
        ).update(
            progress_percentage=progress.completion_percentage,
            last_accessed=timezone.now()
        )
        
        return progress
    
    def check_course_completion(self, user, course_id: str):
        """Check if course is completed"""
        progress = CourseProgress.objects.get(
            user=user,
            course_id=course_id
        )
        
        if progress.completion_percentage >= 100:
            enrollment = Enrollment.objects.get(
                user=user,
                course_id=course_id
            )
            
            if enrollment.status != 'completed':
                enrollment.status = 'completed'
                enrollment.completed_at = timezone.now()
                enrollment.save()
                
                # Generate certificate
                self.generate_certificate(enrollment)
                
                # Update course statistics
                course = enrollment.course
                course.completion_count += 1
                course.save(update_fields=['completion_count'])
                
                self.log_action('course_completed', user=user, course_id=course_id)
    
    def generate_certificate(self, enrollment: Enrollment):
        """Generate course completion certificate"""
        from .certificate_service import CertificateService
        
        certificate_url = CertificateService().generate_certificate(
            user=enrollment.user,
            course=enrollment.course,
            completed_at=enrollment.completed_at
        )
        
        enrollment.certificate_issued = True
        enrollment.certificate_url = certificate_url
        enrollment.save(update_fields=['certificate_issued', 'certificate_url'])
    
    def send_enrollment_notifications(self, enrollment: Enrollment):
        """Send enrollment notifications"""
        from .notification_service import NotificationService
        from .email_service import EmailService
        
        # Notify instructor
        NotificationService().create_notification(
            user=enrollment.course.instructor,
            type='new_enrollment',
            title='New student enrolled',
            message=f'{enrollment.user.get_full_name()} enrolled in {enrollment.course.title}',
            data={'enrollment_id': str(enrollment.id)}
        )
        
        # Email student
        EmailService().send_email(
            to=enrollment.user.email,
            subject=f'Welcome to {enrollment.course.title}',
            template='email/enrollment_confirmation.html',
            context={
                'user': enrollment.user,
                'course': enrollment.course
            }
        )
```

## Media Service

```python
# services/media_service.py
from typing import Dict, Optional
from django.core.files.storage import default_storage
from django.db import transaction
from apps.media_library.models import MediaFile
from .base import BaseService
from .storage_service import BackblazeService
import mimetypes
import uuid

class MediaService(BaseService):
    """Media file management service"""
    
    def __init__(self):
        super().__init__()
        self.storage_service = BackblazeService()
    
    @transaction.atomic
    def initialize_upload(
        self,
        user,
        file_name: str,
        file_size: int,
        mime_type: str,
        course_id: Optional[str] = None,
        section_id: Optional[str] = None
    ) -> Dict:
        """Initialize file upload to Backblaze"""
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Determine file type
        file_type = self.get_file_type(mime_type)
        
        # Create media file record
        media_file = MediaFile.objects.create(
            id=file_id,
            user=user,
            course_id=course_id,
            section_id=section_id,
            file_name=file_name,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            processing_status='pending'
        )
        
        # Get upload URL from Backblaze
        upload_data = self.storage_service.get_upload_url(
            file_name=f"{file_id}/{file_name}",
            content_type=mime_type
        )
        
        upload_data['upload_id'] = file_id
        
        self.log_action('upload_initialized', user=user, file_id=file_id)
        
        return upload_data
    
    @transaction.atomic
    def complete_upload(
        self,
        user,
        upload_id: str,
        file_id: str
    ) -> MediaFile:
        """Complete file upload"""
        media_file = MediaFile.objects.get(id=upload_id)
        
        # Verify ownership
        if media_file.user != user:
            raise PermissionError('Unauthorized')
        
        # Update storage information
        file_info = self.storage_service.get_file_info(file_id)
        
        media_file.storage_path = file_info['path']
        media_file.public_url = file_info['url']
        media_file.processing_status = 'processing'
        media_file.save()
        
        # Process based on file type
        if media_file.file_type == 'video':
            self.process_video.delay(media_file.id)
        elif media_file.file_type == 'image':
            self.process_image.delay(media_file.id)
        
        self.log_action('upload_completed', user=user, file_id=upload_id)
        
        return media_file
    
    @transaction.atomic
    def direct_upload(
        self,
        user,
        file,
        course_id: Optional[str] = None,
        section_id: Optional[str] = None
    ) -> MediaFile:
        """Direct file upload (for small files)"""
        file_name = file.name
        file_size = file.size
        mime_type = mimetypes.guess_type(file_name)[0]
        file_type = self.get_file_type(mime_type)
        
        # Create media file record
        media_file = MediaFile.objects.create(
            user=user,
            course_id=course_id,
            section_id=section_id,
            file_name=file_name,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            processing_status='processing'
        )
        
        # Upload to storage
        storage_path = f"media/{media_file.id}/{file_name}"
        saved_path = default_storage.save(storage_path, file)
        
        media_file.storage_path = saved_path
        media_file.public_url = default_storage.url(saved_path)
        media_file.processing_status = 'completed'
        media_file.save()
        
        # Process if needed
        if file_type in ['video', 'image']:
            self.process_media.delay(media_file.id)
        
        return media_file
    
    def get_file_type(self, mime_type: str) -> str:
        """Determine file type from MIME type"""
        if mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type in ['application/pdf', 'application/msword', 
                          'application/vnd.openxmlformats-officedocument']:
            return 'document'
        else:
            return 'other'
    
    @celery_task
    def process_video(self, media_file_id: str):
        """Process video file (transcoding, thumbnail)"""
        from .video_processing_service import VideoProcessingService
        
        media_file = MediaFile.objects.get(id=media_file_id)
        
        try:
            # Process video
            processing_result = VideoProcessingService().process_video(
                media_file.public_url
            )
            
            # Update media file
            media_file.duration = processing_result['duration']
            media_file.resolution = processing_result['resolution']
            media_file.video_codec = processing_result['video_codec']
            media_file.audio_codec = processing_result['audio_codec']
            media_file.bitrate = processing_result['bitrate']
            media_file.thumbnail_url = processing_result['thumbnail_url']
            media_file.transcoding_data = processing_result
            media_file.processing_status = 'completed'
            media_file.save()
            
        except Exception as e:
            media_file.processing_status = 'failed'
            media_file.processing_error = str(e)
            media_file.save()
            self.logger.error(f"Video processing failed: {e}")
    
    @celery_task
    def process_image(self, media_file_id: str):
        """Process image file (resize, optimize)"""
        from PIL import Image
        import io
        
        media_file = MediaFile.objects.get(id=media_file_id)
        
        try:
            # Download image
            image_data = self.storage_service.download_file(
                media_file.storage_path
            )
            
            # Process image
            img = Image.open(io.BytesIO(image_data))
            
            # Create thumbnail
            thumbnail = img.copy()
            thumbnail.thumbnail((300, 300))
            
            # Save thumbnail
            thumb_io = io.BytesIO()
            thumbnail.save(thumb_io, format='JPEG', quality=85)
            thumb_io.seek(0)
            
            # Upload thumbnail
            thumb_path = f"thumbnails/{media_file.id}.jpg"
            thumb_url = self.storage_service.upload_file(
                thumb_path,
                thumb_io.read(),
                'image/jpeg'
            )
            
            media_file.thumbnail_url = thumb_url
            media_file.processing_status = 'completed'
            media_file.save()
            
        except Exception as e:
            media_file.processing_status = 'failed'
            media_file.processing_error = str(e)
            media_file.save()
            self.logger.error(f"Image processing failed: {e}")
```

## Analytics Service

```python
# services/analytics_service.py
from typing import Dict, List
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from apps.courses.models import Course
from apps.enrollments.models import Enrollment, CourseProgress
from .base import BaseService

class AnalyticsService(BaseService):
    """Analytics and reporting service"""
    
    def get_instructor_overview(self, instructor) -> Dict:
        """Get instructor dashboard overview"""
        courses = Course.objects.filter(instructor=instructor)
        
        total_courses = courses.count()
        published_courses = courses.filter(is_published=True).count()
        
        # Calculate total enrollments
        total_enrollments = Enrollment.objects.filter(
            course__instructor=instructor,
            status='active'
        ).count()
        
        # Calculate revenue
        total_revenue = Enrollment.objects.filter(
            course__instructor=instructor,
            status__in=['active', 'completed']
        ).aggregate(
            revenue=Sum('course__price')
        )['revenue'] or 0
        
        # Calculate average rating
        avg_rating = courses.aggregate(
            avg=Avg('rating_average')
        )['avg'] or 0
        
        # Recent enrollments (last 30 days)
        recent_enrollments = Enrollment.objects.filter(
            course__instructor=instructor,
            enrolled_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return {
            'total_courses': total_courses,
            'published_courses': published_courses,
            'total_enrollments': total_enrollments,
            'total_revenue': float(total_revenue),
            'average_rating': round(avg_rating, 2),
            'recent_enrollments': recent_enrollments,
            'courses': self.get_courses_summary(courses)
        }
    
    def get_courses_summary(self, courses) -> List[Dict]:
        """Get summary for multiple courses"""
        summaries = []
        
        for course in courses:
            summaries.append({
                'id': str(course.id),
                'title': course.title,
                'status': course.status,
                'enrollments': course.enrollment_count,
                'completion_rate': self.calculate_completion_rate(course),
                'revenue': float(course.price * course.enrollment_count),
                'rating': course.rating_average
            })
        
        return summaries
    
    def calculate_completion_rate(self, course) -> float:
        """Calculate course completion rate"""
        total = course.enrollments.filter(status='active').count()
        completed = course.enrollments.filter(status='completed').count()
        
        if total == 0:
            return 0.0
        
        return round((completed / total) * 100, 2)
    
    def get_course_analytics(self, course_id: str, instructor) -> Dict:
        """Get detailed course analytics"""
        course = Course.objects.get(id=course_id, instructor=instructor)
        
        # Enrollment trend (last 30 days)
        enrollment_trend = self.get_enrollment_trend(course, days=30)
        
        # Student progress distribution
        progress_distribution = self.get_progress_distribution(course)
        
        # Video analytics
        video_analytics = self.get_video_analytics(course)
        
        # Revenue analytics
        revenue = float(course.price * course.enrollment_count)
        
        return {
            'course': {
                'id': str(course.id),
                'title': course.title,
                'status': course.status
            },
            'enrollments': {
                'total': course.enrollment_count,
                'active': course.enrollments.filter(status='active').count(),
                'completed': course.completion_count,
                'dropped': course.enrollments.filter(status='dropped').count()
            },
            'completion_rate': self.calculate_completion_rate(course),
            'average_progress': self.calculate_average_progress(course),
            'enrollment_trend': enrollment_trend,
            'progress_distribution': progress_distribution,
            'video_analytics': video_analytics,
            'revenue': {
                'total': revenue,
                'per_student': float(course.price)
            },
            'rating': {
                'average': course.rating_average,
                'count': course.rating_count,
                'distribution': self.get_rating_distribution(course)
            }
        }
    
    def get_enrollment_trend(self, course, days: int = 30) -> List[Dict]:
        """Get enrollment trend over time"""
        trend = []
        today = timezone.now().date()
        
        for i in range(days):
            date = today - timedelta(days=i)
            count = course.enrollments.filter(
                enrolled_at__date=date
            ).count()
            
            trend.append({
                'date': date.isoformat(),
                'count': count
            })
        
        trend.reverse()
        return trend
    
    def get_progress_distribution(self, course) -> Dict:
        """Get student progress distribution"""
        progress_records = CourseProgress.objects.filter(course=course)
        
        distribution = {
            '0-25': 0,
            '26-50': 0,
            '51-75': 0,
            '76-100': 0
        }
        
        for progress in progress_records:
            percentage = progress.completion_percentage
            if percentage <= 25:
                distribution['0-25'] += 1
            elif percentage <= 50:
                distribution['26-50'] += 1
            elif percentage <= 75:
                distribution['51-75'] += 1
            else:
                distribution['76-100'] += 1
        
        return distribution
    
    def get_video_analytics(self, course) -> List[Dict]:
        """Get analytics for course videos"""
        from apps.media_library.models import MediaFile
        
        videos = MediaFile.objects.filter(
            course=course,
            file_type='video',
            is_deleted=False
        )
        
        analytics = []
        for video in videos:
            views = video.progress_records.count()
            completions = video.progress_records.filter(
                completed=True
            ).count()
            
            avg_watch_time = video.progress_records.aggregate(
                avg=Avg('watch_time')
            )['avg'] or 0
            
            analytics.append({
                'id': str(video.id),
                'title': video.file_name,
                'views': views,
                'completions': completions,
                'completion_rate': round((completions / views * 100) if views > 0 else 0, 2),
                'average_watch_time': int(avg_watch_time)
            })
        
        return sorted(analytics, key=lambda x: x['views'], reverse=True)[:10]
    
    def get_rating_distribution(self, course) -> Dict:
        """Get rating distribution"""
        distribution = {str(i): 0 for i in range(1, 6)}
        
        reviews = course.reviews.filter(is_deleted=False)
        for review in reviews:
            distribution[str(review.rating)] += 1
        
        return distribution
    
    def calculate_average_progress(self, course) -> float:
        """Calculate average student progress"""
        avg_progress = CourseProgress.objects.filter(
            course=course
        ).aggregate(
            avg=Avg('completion_percentage')
        )['avg'] or 0
        
        return round(avg_progress, 2)
```

## Notification Service

```python
# services/notification_service.py
from typing import Dict, List, Optional
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .base import BaseService

class NotificationService(BaseService):
    """Notification management service"""
    
    def __init__(self):
        super().__init__()
        self.channel_layer = get_channel_layer()
    
    @transaction.atomic
    def create_notification(
        self,
        user,
        type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None
    ):
        """Create and send notification"""
        from apps.notifications.models import Notification
        
        notification = Notification.objects.create(
            user=user,
            type=type,
            title=title,
            message=message,
            data=data or {}
        )
        
        # Send real-time notification via WebSocket
        self.send_websocket_notification(user, notification)
        
        # Send push notification if enabled
        if user.preferences.get('push_notifications', False):
            self.send_push_notification(user, notification)
        
        # Send email notification if enabled
        if user.preferences.get('email_notifications', False):
            self.send_email_notification(user, notification)
        
        return notification
    
    def send_websocket_notification(self, user, notification):
        """Send notification via WebSocket"""
        async_to_sync(self.channel_layer.group_send)(
            f"user_{user.id}",
            {
                'type': 'notification',
                'notification': {
                    'id': str(notification.id),
                    'type': notification.type,
                    'title': notification.title,
                    'message': notification.message,
                    'data': notification.data,
                    'created_at': notification.created_at.isoformat()
                }
            }
        )
    
    def send_push_notification(self, user, notification):
        """Send push notification to mobile/web"""
        # Implement push notification logic
        # Using FCM, OneSignal, or similar service
        pass
    
    def send_email_notification(self, user, notification):
        """Send email notification"""
        from .email_service import EmailService
        
        EmailService().send_email(
            to=user.email,
            subject=notification.title,
            template='email/notification.html',
            context={
                'user': user,
                'notification': notification
            }
        )
    
    def mark_as_read(self, user, notification_ids: List[str]):
        """Mark notifications as read"""
        from apps.notifications.models import Notification
        
        Notification.objects.filter(
            user=user,
            id__in=notification_ids
        ).update(is_read=True)
    
    def get_unread_count(self, user) -> int:
        """Get unread notification count"""
        from apps.notifications.models import Notification
        
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).count()
```

## Email Service

```python
# services/email_service.py
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .base import BaseService
import celery

class EmailService(BaseService):
    """Email sending service"""
    
    @celery.task
    def send_email(
        self,
        to: str,
        subject: str,
        template: str,
        context: Dict,
        from_email: Optional[str] = None
    ):
        """Send templated email"""
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        # Render templates
        html_content = render_to_string(template, context)
        text_content = render_to_string(
            template.replace('.html', '.txt'),
            context
        )
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        self.log_action('email_sent', to=to, subject=subject)
    
    def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        template: str,
        context: Dict
    ):
        """Send bulk emails"""
        for recipient in recipients:
            self.send_email.delay(
                to=recipient,
                subject=subject,
                template=template,
                context=context
            )
```

---
**Document Version**: 1.0  
**Last Updated**: 2025-08-23  
**Next Document**: Django Deployment Configuration