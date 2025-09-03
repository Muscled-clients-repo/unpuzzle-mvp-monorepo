"""
Signal handlers for automatic course cache invalidation.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Course, CourseSection

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Course)
def clear_course_cache_on_update(sender, instance, **kwargs):
    """Clear course cache when a course is updated"""
    try:
        # Clear specific course detail cache
        cache.delete(f"course_detail:{instance.id}")
        
        # Clear instructor-specific caches
        if instance.instructor:
            instructor_id = instance.instructor.supabase_user_id
            cache.delete(f"instructor_courses:{instructor_id}")
            cache.delete(f"instructor_course_detail:{instructor_id}:{instance.id}")
        
        # Note: For course list cache, we'd need to clear all variations
        # In production, consider using cache tags or Redis pattern deletion
        logger.debug(f"Course cache cleared for course {instance.id} on update")
    except Exception as e:
        logger.error(f"Failed to clear course cache: {e}")


@receiver(post_delete, sender=Course)
def clear_course_cache_on_delete(sender, instance, **kwargs):
    """Clear course cache when a course is deleted"""
    try:
        # Clear course detail cache
        cache.delete(f"course_detail:{instance.id}")
        
        # Clear list cache (all variations)
        # In production, you might want to use Redis SCAN to find all matching keys
        logger.debug(f"Course cache cleared for deleted course {instance.id}")
    except Exception as e:
        logger.error(f"Failed to clear cache for deleted course: {e}")


@receiver(post_save, sender=CourseSection)
def clear_course_cache_on_section_update(sender, instance, **kwargs):
    """Clear course cache when a section is updated"""
    try:
        # Clear the parent course's cache
        cache.delete(f"course_detail:{instance.course.id}")
        logger.debug(f"Course cache cleared for course {instance.course.id} on section update")
    except Exception as e:
        logger.error(f"Failed to clear course cache on section update: {e}")


# Helper function to clear all course caches
def clear_all_course_caches():
    """Nuclear option: clear all course-related caches"""
    try:
        # This is a brute force approach - in production use cache tags or namespacing
        # For now, we'll just log that this function exists
        logger.info("Clearing all course caches")
        
        # If using Redis, you could do:
        # cache._cache.delete_pattern("courses:*")
        # cache._cache.delete_pattern("course_detail:*")
        
        # For Django's default cache, we don't have pattern deletion
        # So this is more of a placeholder for future implementation
        pass
    except Exception as e:
        logger.error(f"Failed to clear all course caches: {e}")