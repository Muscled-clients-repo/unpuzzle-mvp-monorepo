"""
Content management views for courses (sections only).
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


@api_view(['GET', 'POST'])
def manage_course_sections(request, course_id):
    """Manage course sections"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check instructor permissions
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to manage course content'
        }, status=403)
    
    # Get course and verify ownership
    course = get_object_or_404(Course, id=course_id)
    if course.instructor != user_profile:
        return Response({
            'error': 'Permission denied',
            'message': 'You can only manage your own courses'
        }, status=403)
    
    if request.method == 'GET':
        # List course sections
        sections = CourseSection.objects.filter(course=course).order_by('order', 'created_at')
        serializer = CourseSectionSerializer(sections, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'POST':
        # Create new section
        serializer = CourseSectionCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=400)
        
        with transaction.atomic():
            section = serializer.save(course=course)
        
        response_serializer = CourseSectionSerializer(section)
        return Response({
            'success': True,
            'message': 'Course section created successfully',
            'data': response_serializer.data
        }, status=201)


@api_view(['GET', 'PUT', 'DELETE'])
def manage_section_detail(request, course_id, section_id):
    """Manage individual course section"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check instructor permissions
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to manage course content'
        }, status=403)
    
    # Get course, section and verify ownership
    course = get_object_or_404(Course, id=course_id)
    section = get_object_or_404(CourseSection, id=section_id, course=course)
    
    if course.instructor != user_profile:
        return Response({
            'error': 'Permission denied',
            'message': 'You can only manage your own courses'
        }, status=403)
    
    if request.method == 'GET':
        # Get section details
        serializer = CourseSectionSerializer(section)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'PUT':
        # Update section
        serializer = CourseSectionCreateUpdateSerializer(section, data=request.data)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=400)
        
        with transaction.atomic():
            section = serializer.save()
        
        response_serializer = CourseSectionSerializer(section)
        return Response({
            'success': True,
            'message': 'Course section updated successfully',
            'data': response_serializer.data
        })
    
    elif request.method == 'DELETE':
        # Delete section
        with transaction.atomic():
            section.delete()
        
        return Response({
            'success': True,
            'message': 'Course section deleted successfully'
        })


@api_view(['GET'])
def get_section_media(request, course_id, section_id):
    """Get media files assigned to a course section"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get course, section and verify ownership
    course = get_object_or_404(Course, id=course_id)
    section = get_object_or_404(CourseSection, id=section_id, course=course)
    
    if course.instructor != user_profile:
        return Response({
            'error': 'Permission denied',
            'message': 'You can only view your own course content'
        }, status=403)
    
    # Get media files for this section
    media_files = MediaFile.objects.filter(
        section=section,
        is_deleted=False
    ).order_by('-created_at')
    
    serializer = MediaFileSerializer(media_files, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['POST'])
def assign_media_to_section(request, section_id):
    """Assign media files to a course section"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Log request details for debugging
    logger.info(f"=== ASSIGN MEDIA TO SECTION REQUEST ===")
    logger.info(f"Section ID: {section_id}")
    logger.info(f"Request data: {request.data}")
    logger.info(f"Request POST: {request.POST}")
    logger.info(f"Content type: {request.content_type}")
    
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check instructor permissions
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to assign media'
        }, status=403)
    
    # Get section and verify ownership
    section = get_object_or_404(CourseSection, id=section_id)
    if section.course.instructor != user_profile:
        return Response({
            'error': 'Permission denied',
            'message': 'You can only assign media to your own courses'
        }, status=403)
    
    # Handle different payload formats from frontend
    media_file_ids = []
    
    # Format 1: Array of IDs
    if 'media_file_ids' in request.data:
        media_file_ids = request.data.get('media_file_ids', [])
    elif 'mediaFileIds' in request.data:
        media_file_ids = request.data.get('mediaFileIds', [])
    elif 'videoIds' in request.data:
        media_file_ids = request.data.get('videoIds', [])
    
    # Format 2: Single ID
    elif 'videoId' in request.data:
        media_file_ids = [request.data['videoId']]
    elif 'video_id' in request.data:
        media_file_ids = [request.data['video_id']]
    elif 'mediaFileId' in request.data:
        media_file_ids = [request.data['mediaFileId']]
    elif 'id' in request.data:
        media_file_ids = [request.data['id']]
    
    # Format 3: Direct list (if frontend sends array directly)
    elif isinstance(request.data, list):
        media_file_ids = request.data
    
    # Format 4: Handle form data or different structures
    elif hasattr(request.data, 'getlist'):
        media_file_ids = request.data.getlist('ids', [])
    
    logger.info(f"Extracted media_file_ids: {media_file_ids}")
    logger.info(f"Request data keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'Not dict-like'}")
    
    if not media_file_ids:
        return Response({
            'error': 'No media files specified',
            'message': 'Please provide one of: media_file_ids[], videoId, mediaFileId, or ids[]',
            'received_data': request.data,
            'available_keys': list(request.data.keys()) if hasattr(request.data, 'keys') else str(request.data)
        }, status=400)
    
    try:
        with transaction.atomic():
            # Get media files and verify ownership
            media_files = MediaFile.objects.filter(
                id__in=media_file_ids,
                user=user_profile
            )
            
            if len(media_files) != len(media_file_ids):
                return Response({
                    'error': 'Some media files not found or not owned by you'
                }, status=404)
            
            # Assign media files to section
            for media_file in media_files:
                media_file.course = section.course
                media_file.section = section
                media_file.save()
        
        return Response({
            'success': True,
            'message': f'Successfully assigned {len(media_files)} media files to section',
            'data': {
                'section_id': str(section.id),
                'section_title': section.title,
                'assigned_count': len(media_files)
            }
        })
        
    except Exception as e:
        logger.error(f"Media assignment failed: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        return Response({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }, status=400)


@api_view(['GET'])
def get_course_media(request, course_id):
    """Get unassigned media files for a course (media with course_id but no section_id)"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get course and verify ownership
    course = get_object_or_404(Course, id=course_id)
    if course.instructor != user_profile:
        return Response({
            'error': 'Permission denied',
            'message': 'You can only view your own course content'
        }, status=403)
    
    # Get media files for this course that are NOT assigned to any section
    # These are media files with course_id but section_id is NULL
    media_files = MediaFile.objects.filter(
        course=course,
        section__isnull=True,  # Only get media not assigned to sections
        is_deleted=False
    ).order_by('-created_at')
    
    serializer = MediaFileSerializer(media_files, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['POST'])
def unassign_media(request, media_id):
    """Unassign media from section (remove section_id but keep course_id)"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get media file
    media_file = get_object_or_404(MediaFile, id=media_id)
    
    # Verify user owns the media
    if media_file.user != user_profile:
        return Response({
            'error': 'Permission denied',
            'message': 'You can only unassign your own media files'
        }, status=403)
    
    # Unassign from section (keep course_id, remove section_id)
    media_file.section = None
    media_file.save()
    
    return Response({
        'success': True,
        'message': 'Media unassigned from section successfully',
        'data': {
            'media_id': str(media_file.id),
            'course_id': str(media_file.course_id) if media_file.course_id else None,
            'section_id': None
        }
    })