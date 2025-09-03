"""
Utility functions for course management including cache warming.
"""
import logging
from django.core.cache import cache
from django.db.models import Count, Sum, Q, Prefetch, Exists, OuterRef
from .models import Course, CourseSection
from enrollments.models import Enrollment

logger = logging.getLogger(__name__)


def warm_course_cache():
    """
    Pre-populate cache with frequently accessed course data.
    This can be called on server startup or periodically via cron/celery.
    """
    try:
        logger.info("[CACHE WARM] Starting course cache warming...")
        
        # Warm the public course list cache (most common query)
        from .serializers import CourseListSerializer
        
        # Get the most common course queries
        queryset = Course.objects.filter(
            is_published=True,
            status__in=['published', 'active']
        ).select_related(
            'instructor',
            'category'
        ).prefetch_related(
            Prefetch('sections', queryset=CourseSection.objects.filter(is_published=True))
        ).annotate(
            published_sections_count=Count(
                'sections',
                filter=Q(sections__is_published=True)
            )
        ).order_by('-created_at')[:20]  # Top 20 newest courses
        
        # Cache the first page of courses
        courses_data = []
        for course in queryset:
            # Simple serialization for cache warming
            courses_data.append({
                'id': str(course.id),
                'title': course.title,
                'instructor': {
                    'full_name': course.instructor.full_name if course.instructor else None,
                    'email': course.instructor.email if course.instructor else None,
                },
                'price': float(course.price),
                'rating_average': float(course.rating_average),
                'enrollment_count': course.enrollment_count,
            })
        
        # Store in cache with standard key
        cache_key = "courses:v2:warmup_default"
        cache.set(cache_key, {
            'count': len(courses_data),
            'results': courses_data,
            'success': True
        }, 300)  # 5 minutes
        
        logger.info(f"[CACHE WARM] Warmed cache with {len(courses_data)} courses")
        
        # Warm instructor course caches for active instructors
        from accounts.models import UserProfile
        
        active_instructors = UserProfile.objects.filter(
            taught_courses__isnull=False,  # Use the correct related name
            status='active'
        ).distinct()[:10]  # Top 10 active instructors
        
        for instructor in active_instructors:
            warm_instructor_courses_cache(instructor)
        
        logger.info(f"[CACHE WARM] Completed cache warming for {active_instructors.count()} instructors")
        
    except Exception as e:
        logger.error(f"[CACHE WARM] Error warming cache: {e}")


def warm_instructor_courses_cache(instructor):
    """
    Warm cache for a specific instructor's courses.
    """
    try:
        cache_key = f"instructor_courses:{instructor.supabase_user_id}"
        
        # Optimized query for instructor courses
        courses = Course.objects.filter(
            instructor=instructor
        ).select_related(
            'category'
        ).prefetch_related(
            Prefetch('sections', queryset=CourseSection.objects.filter(is_published=True).order_by('order')),
            Prefetch('enrollments', queryset=Enrollment.objects.filter(status='active').select_related('user'))
        ).annotate(
            active_students_count=Count('enrollments', filter=Q(enrollments__status='active')),
            total_revenue=Sum('enrollments__payment_amount', filter=Q(enrollments__status='active')),
            completed_students=Count('enrollments', filter=Q(enrollments__status='active', enrollments__progress_percentage__gte=100))
        ).order_by('-created_at')
        
        # Build minimal response data for cache
        courses_data = []
        for course in courses:
            total_students = course.active_students_count
            completion_rate = (course.completed_students / total_students * 100) if total_students > 0 else 0
            
            courses_data.append({
                'id': str(course.id),
                'title': course.title,
                'status': course.status,
                'is_published': course.is_published,
                'analytics': {
                    'total_revenue': float(course.total_revenue or 0),
                    'active_students': course.active_students_count,
                    'completion_rate': completion_rate
                }
            })
        
        # Cache the data
        cache.set(cache_key, {
            'success': True,
            'data': courses_data
        }, 300)  # 5 minutes
        
        logger.debug(f"[CACHE WARM] Warmed cache for instructor {instructor.email} with {len(courses_data)} courses")
        
    except Exception as e:
        logger.error(f"[CACHE WARM] Error warming instructor cache: {e}")


def optimize_course_queryset(queryset):
    """
    Apply standard optimizations to any course queryset.
    This reduces the number of database queries.
    """
    return queryset.select_related(
        'instructor',
        'category'
    ).prefetch_related(
        Prefetch('sections', 
                 queryset=CourseSection.objects.filter(is_published=True).only(
                     'id', 'title', 'order', 'is_published'
                 ))
    )


def get_course_list_optimized(filters=None, user_id=None):
    """
    Get optimized course list with minimal database hits.
    Uses .only() to fetch only required fields.
    """
    # Base queryset with only necessary fields
    queryset = Course.objects.filter(
        is_published=True,
        status__in=['published', 'active']
    ).only(
        'id', 'title', 'slug', 'short_description', 'thumbnail',
        'price', 'discount_price', 'currency', 'is_free',
        'duration', 'difficulty', 'language',
        'enrollment_count', 'rating_average', 'rating_count',
        'published_at', 'created_at', 'updated_at',
        'instructor_id', 'category_id'
    ).select_related(
        'instructor',
        'category'
    )
    
    # Apply filters if provided
    if filters:
        if 'search' in filters:
            queryset = queryset.filter(
                Q(title__icontains=filters['search']) |
                Q(description__icontains=filters['search'])
            )
        if 'difficulty' in filters:
            queryset = queryset.filter(difficulty=filters['difficulty'])
        if 'category' in filters:
            queryset = queryset.filter(category__slug=filters['category'])
    
    # Add enrollment status for authenticated users
    if user_id:
        queryset = queryset.annotate(
            user_is_enrolled=Exists(
                Enrollment.objects.filter(
                    user__supabase_user_id=user_id,
                    course=OuterRef('pk'),
                    status='active'
                )
            )
        )
    
    # Add sections count
    queryset = queryset.annotate(
        published_sections_count=Count(
            'sections',
            filter=Q(sections__is_published=True)
        )
    )
    
    return queryset