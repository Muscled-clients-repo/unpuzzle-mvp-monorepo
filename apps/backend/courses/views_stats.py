"""
Platform statistics views for public display.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Count, Avg
from django.core.cache import cache
from .models import Course, CourseCategory
from enrollments.models import Enrollment
from accounts.models import UserProfile


@api_view(['GET'])
@permission_classes([AllowAny])  # Public endpoint - no authentication required
def get_platform_stats(request):
    """
    Get platform statistics for the homepage.
    This is a public endpoint that doesn't require authentication.
    """
    # Try to get cached stats first (cache for 1 hour)
    cache_key = 'platform_stats'
    cached_stats = cache.get(cache_key)
    
    if cached_stats:
        return Response(cached_stats, status=status.HTTP_200_OK)
    
    try:
        # Calculate platform statistics
        total_courses = Course.objects.filter(
            status='published',
            is_active=True
        ).count()
        
        total_students = UserProfile.objects.filter(
            user_roles__role__name='student'
        ).distinct().count()
        
        total_instructors = UserProfile.objects.filter(
            user_roles__role__name='instructor'
        ).distinct().count()
        
        # Get average rating across all courses
        avg_rating = Course.objects.filter(
            status='published',
            is_active=True
        ).aggregate(avg=Avg('average_rating'))['avg'] or 0
        
        stats = {
            'total_courses': total_courses,
            'total_students': total_students,
            'total_instructors': total_instructors,
            'total_enrollments': Enrollment.objects.filter(is_active=True).count(),
            'average_rating': round(float(avg_rating), 1),
            'total_categories': CourseCategory.objects.filter(is_active=True).count()
        }
        
        # Cache the stats for 1 hour
        cache.set(cache_key, stats, 3600)
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Return default stats if there's an error
        return Response({
            'total_courses': 0,
            'total_students': 0,
            'total_instructors': 0,
            'total_enrollments': 0,
            'average_rating': 0,
            'total_categories': 0
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])  # Public endpoint
def get_featured_courses(request):
    """
    Get featured courses for the homepage.
    This is a public endpoint that doesn't require authentication.
    """
    # Try to get cached featured courses first (cache for 30 minutes)
    cache_key = 'featured_courses'
    cached_courses = cache.get(cache_key)
    
    if cached_courses:
        return Response(cached_courses, status=status.HTTP_200_OK)
    
    try:
        # Get top-rated published courses
        featured_courses = Course.objects.filter(
            status='published',
            is_active=True
        ).select_related(
            'instructor',
            'category'
        ).order_by(
            '-average_rating',
            '-enrollment_count'
        )[:6]  # Get top 6 courses
        
        courses_data = []
        for course in featured_courses:
            courses_data.append({
                'id': str(course.id),
                'title': course.title,
                'description': course.description[:150] + '...' if len(course.description) > 150 else course.description,
                'thumbnail': course.thumbnail,
                'instructor': {
                    'id': str(course.instructor.supabase_user_id) if course.instructor else None,
                    'name': course.instructor.full_name or course.instructor.email if course.instructor else 'Unknown'
                },
                'price': str(course.price),
                'average_rating': float(course.average_rating or 0),
                'enrollment_count': course.enrollment_count,
                'category': {
                    'id': str(course.category.id) if course.category else None,
                    'name': course.category.name if course.category else None
                }
            })
        
        result = {
            'featured_courses': courses_data,
            'count': len(courses_data)
        }
        
        # Cache the featured courses for 30 minutes
        cache.set(cache_key, result, 1800)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Return empty list if there's an error
        return Response({
            'featured_courses': [],
            'count': 0
        }, status=status.HTTP_200_OK)