"""
Content management views for courses (sections, lessons, media).
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from accounts.models import UserProfile
from accounts.permissions import PermissionService, PermissionConstants
from .models import Course, CourseSection
from .serializers import (
    CourseSectionSerializer, 
    CourseSectionCreateUpdateSerializer
)
from media_library.models import MediaFile
from media_library.serializers import MediaFileSerializer


def get_user_profile(request):
    """Helper to get user profile from request"""
    if not hasattr(request, 'user_id') or not request.user_id:
        return None
    try:
        return UserProfile.objects.get(supabase_user_id=request.user_id)
    except UserProfile.DoesNotExist:
        return None


# ============================================================================
# SECTION MANAGEMENT
# ============================================================================

@api_view(['GET', 'POST'])
def manage_course_sections(request, course_id):
    """Get all sections for a course or create a new section"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has instructor role
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to manage sections'
        }, status=403)
    
    # Get the course and verify ownership
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    
    if request.method == 'GET':
        # Get all sections with lessons
        sections = course.sections.prefetch_related('lessons').order_by('order')
        serializer = CourseSectionSerializer(sections, many=True, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'POST':
        # Create a new section
        serializer = CourseSectionCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({'error': serializer.errors, 'success': False}, status=400)
        
        # Set the course and save
        section = serializer.save(course=course)
        
        response_serializer = CourseSectionSerializer(section, context={'request': request})
        return Response({
            'success': True,
            'data': response_serializer.data
        }, status=201)


@api_view(['GET', 'PUT', 'DELETE'])
def manage_section_detail(request, course_id, section_id):
    """Get, update, or delete a specific section"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has instructor role
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to manage sections'
        }, status=403)
    
    # Get the course and section
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    section = get_object_or_404(CourseSection, id=section_id, course=course)
    
    if request.method == 'GET':
        serializer = CourseSectionSerializer(section, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = CourseSectionCreateUpdateSerializer(
            section,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({'error': serializer.errors, 'success': False}, status=400)
        
        section = serializer.save()
        response_serializer = CourseSectionSerializer(section, context={'request': request})
        return Response({
            'success': True,
            'data': response_serializer.data
        })
    
    elif request.method == 'DELETE':
        section.delete()
        return Response({
            'success': True,
            'message': 'Section deleted successfully'
        })


@api_view(['GET', 'PUT', 'DELETE'])
def manage_section_by_id(request, section_id):
    """Get, update, or delete a specific section by ID only (for frontend compatibility)"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has instructor role
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to manage sections'
        }, status=403)
    
    # Get the section and verify ownership through course
    section = get_object_or_404(CourseSection, id=section_id, course__instructor=user_profile)
    
    if request.method == 'GET':
        serializer = CourseSectionSerializer(section, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = CourseSectionCreateUpdateSerializer(
            section,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({'error': serializer.errors, 'success': False}, status=400)
        
        section = serializer.save()
        response_serializer = CourseSectionSerializer(section, context={'request': request})
        return Response({
            'success': True,
            'data': response_serializer.data
        })
    
    elif request.method == 'DELETE':
        section.delete()
        return Response({
            'success': True,
            'message': 'Section deleted successfully'
        })


@api_view(['POST'])
def reorder_sections(request, course_id):
    """Reorder sections within a course"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check permissions
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to reorder sections'
        }, status=403)
    
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    
    section_ids = request.data.get('section_ids', [])
    if not section_ids:
        return Response({'error': 'section_ids required'}, status=400)
    
    with transaction.atomic():
        for index, section_id in enumerate(section_ids):
            CourseSection.objects.filter(
                id=section_id, 
                course=course
            ).update(order=index)
    
    return Response({
        'success': True,
        'message': 'Sections reordered successfully'
    })


# ============================================================================
# LESSON MANAGEMENT
# ============================================================================

@api_view(['GET', 'POST'])
def manage_section_lessons(request, course_id, section_id):
    """Get all lessons for a section or create a new lesson"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check permissions
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to manage lessons'
        }, status=403)
    
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    section = get_object_or_404(CourseSection, id=section_id, course=course)
    
    if request.method == 'GET':
        lessons = section.lessons.order_by('order')
        serializer = LessonSerializer(lessons, many=True, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'POST':
        serializer = LessonCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({'error': serializer.errors, 'success': False}, status=400)
        
        lesson = serializer.save(section=section)
        response_serializer = LessonSerializer(lesson, context={'request': request})
        return Response({
            'success': True,
            'data': response_serializer.data
        }, status=201)


@api_view(['GET', 'PUT', 'DELETE'])
def manage_lesson_detail(request, course_id, section_id, lesson_id):
    """Get, update, or delete a specific lesson"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check permissions
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to manage lessons'
        }, status=403)
    
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    section = get_object_or_404(CourseSection, id=section_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, section=section)
    
    if request.method == 'GET':
        serializer = LessonSerializer(lesson, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = LessonCreateUpdateSerializer(
            lesson,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({'error': serializer.errors, 'success': False}, status=400)
        
        lesson = serializer.save()
        response_serializer = LessonSerializer(lesson, context={'request': request})
        return Response({
            'success': True,
            'data': response_serializer.data
        })
    
    elif request.method == 'DELETE':
        lesson.delete()
        return Response({
            'success': True,
            'message': 'Lesson deleted successfully'
        })


# ============================================================================
# MEDIA MANAGEMENT
# ============================================================================

@api_view(['GET'])
def get_course_media(request, course_id):
    """Get all media files associated with a course"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check permissions
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to view course media'
        }, status=403)
    
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    
    # Get all media files for this course
    media_files = MediaFile.objects.filter(
        course=course,
        user=user_profile
    ).order_by('-created_at')
    
    serializer = MediaFileSerializer(media_files, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['POST'])
def assign_media_to_lesson(request, course_id, section_id, lesson_id):
    """Assign a media file to a lesson"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check permissions
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to assign media'
        }, status=403)
    
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    section = get_object_or_404(CourseSection, id=section_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, section=section)
    
    media_id = request.data.get('media_id')
    if not media_id:
        return Response({'error': 'media_id required'}, status=400)
    
    media_file = get_object_or_404(MediaFile, id=media_id, user=user_profile)
    
    # Assign media to lesson
    media_file.lesson = lesson
    media_file.course = course
    media_file.save()
    
    # Update lesson video URL if it's a video
    if media_file.file_type == 'video':
        lesson.video_url = media_file.cdn_url or media_file.storage_url
        lesson.video_duration = media_file.duration
        lesson.save()
    
    return Response({
        'success': True,
        'message': 'Media assigned to lesson successfully',
        'data': MediaFileSerializer(media_file).data
    })


@api_view(['POST'])
def add_media_to_section(request, section_id):
    """Add existing media to a course section"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has instructor role
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to add media to sections'
        }, status=403)
    
    # Get the section and verify ownership
    section = get_object_or_404(CourseSection, id=section_id)
    
    # Verify the user owns the course
    if section.course.instructor != user_profile:
        return Response({
            'error': 'Permission denied',
            'message': 'You can only add media to your own course sections'
        }, status=403)
    
    # Get mediaFileId from request data (matching frontend expectations)
    media_file_id = request.data.get('mediaFileId')
    if not media_file_id:
        return Response({
            'error': 'mediaFileId is required',
            'success': False
        }, status=400)
    
    # Get the media file and verify ownership
    media_file = get_object_or_404(MediaFile, id=media_file_id, user=user_profile)
    
    # Check if media is already assigned to another section's lesson
    if media_file.lesson and media_file.lesson.section != section:
        return Response({
            'error': 'Media already assigned to another section',
            'message': 'This media file is already assigned to a lesson in a different section'
        }, status=400)
    
    # Associate media with the course (sections don't have direct media relations in this model)
    # The media will be associated with the course, and can later be assigned to specific lessons
    media_file.course = section.course
    
    # Store section association and other metadata in the metadata field
    metadata = media_file.metadata or {}
    metadata['section_id'] = str(section_id)
    metadata['title'] = request.data.get('title', media_file.original_filename)
    metadata['description'] = request.data.get('description', '')
    metadata['order'] = request.data.get('order', 0)
    metadata['is_preview'] = request.data.get('isPreview', False)
    metadata['is_published'] = request.data.get('isPublished', True)
    
    media_file.metadata = metadata
    media_file.save()
    
    return Response({
        'success': True,
        'message': 'Media added to section successfully',
        'data': MediaFileSerializer(media_file).data
    })