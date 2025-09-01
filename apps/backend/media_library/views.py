"""
Media upload views - Django equivalent of Flask media_upload.py
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from accounts.models import UserProfile
from accounts.permissions import PermissionService, PermissionConstants
from courses.models import Course, CourseSection
from .models import MediaFile, UploadSession
from .serializers import (
    InitiateUploadSerializer, 
    CompleteUploadSerializer, 
    AssignVideoSerializer,
    MediaFileSerializer,
    VideoListSerializer
)
from .services import media_upload_service, backblaze_service
import logging

logger = logging.getLogger(__name__)


def get_user_profile(request):
    """Helper to get user profile from request"""
    if not hasattr(request, 'user_id') or not request.user_id:
        return None
    try:
        return UserProfile.objects.get(supabase_user_id=request.user_id)
    except UserProfile.DoesNotExist:
        return None


@api_view(['POST'])
def initiate_upload(request):
    """Initiate media file upload - equivalent to Flask initiate_upload"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Validate request data
    serializer = InitiateUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid request data',
            'details': serializer.errors
        }, status=400)
    
    data = serializer.validated_data
    
    try:
        # Initiate upload through service
        upload_data = media_upload_service.initiate_upload(
            user=user_profile,
            filename=data['fileName'],
            file_size=data['fileSize'],
            file_type=data['fileType'],
            media_type=data['mediaType'],
            course_id=data.get('courseId')
        )
        
        return Response({
            'success': True,
            'data': upload_data
        }, status=201)
        
    except Exception as e:
        logger.error(f"Upload initiation failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)


@api_view(['POST'])
def complete_upload(request):
    """Complete media file upload - equivalent to Flask complete_upload"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Log all possible data sources for debugging (avoid request.body to prevent RawPostDataException)
    logger.info(f"Complete upload request.data: {request.data}")
    logger.info(f"Complete upload request.POST: {request.POST}")
    logger.info(f"Complete upload request.GET: {request.GET}")
    logger.info(f"Complete upload request.FILES: {request.FILES}")
    logger.info(f"Complete upload Content-Type: {request.content_type}")
    logger.info(f"Complete upload request.META Content-Length: {request.META.get('CONTENT_LENGTH', 'Not set')}")
    
    # Try to get data from different sources
    data_to_validate = request.data or request.POST or request.GET
    
    # Special handling for empty JSON requests
    if not data_to_validate and request.content_type == 'application/json':
        logger.warning("Received empty JSON request - this might be a frontend issue")
        return Response({
            'success': False,
            'error': 'Empty request body',
            'help': 'Please ensure the frontend is sending JSON data like: {"sessionKey": "uuid", "storageKey": "path"}',
            'content_type': request.content_type,
            'content_length': request.META.get('CONTENT_LENGTH', 'Not set')
        }, status=400)
    
    # Validate request data
    serializer = CompleteUploadSerializer(data=data_to_validate)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid request data',
            'details': serializer.errors,
            'received_data': data_to_validate
        }, status=400)
    
    data = serializer.validated_data
    
    try:
        # Complete upload through service
        result = media_upload_service.complete_upload(
            session_id=str(data['sessionId']),
            user=user_profile,
            upload_id=str(data.get('uploadId')) if data.get('uploadId') else None
        )
        
        return Response({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Upload completion failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)


@api_view(['POST'])
def proxy_upload(request):
    """Proxy upload for CORS handling - equivalent to Flask proxy_upload"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get session identifier - can be session_id or storage_key/storageKey
    session_id = (request.data.get('sessionId') or 
                 request.POST.get('sessionId') or 
                 request.POST.get('session_id') or
                 request.data.get('session_id') or
                 request.data.get('sessionKey') or
                 request.POST.get('sessionKey'))
    
    storage_key_param = (request.data.get('storageKey') or 
                        request.POST.get('storageKey') or
                        request.data.get('storage_key') or
                        request.POST.get('storage_key'))
    
    # Try to find session by session_id first, then by storage_key
    session = None
    if session_id:
        try:
            session = UploadSession.objects.get(
                session_id=session_id,
                media_file__user=user_profile
            )
        except UploadSession.DoesNotExist:
            pass
    
    if not session and storage_key_param:
        # Extract storage key from URL if it's a full URL
        if storage_key_param.startswith('http'):
            # Extract the key part from URL like https://unpuzzle.s3.us-west-002.backblazeb2.com/others/...
            storage_key = '/'.join(storage_key_param.split('/')[-3:])  # Get last 3 parts: others/user_id/filename
        else:
            storage_key = storage_key_param
        
        try:
            session = UploadSession.objects.get(
                storage_key=storage_key,
                media_file__user=user_profile
            )
        except UploadSession.DoesNotExist:
            pass
    
    if not session:
        return Response({
            'error': 'Upload session not found'
        }, status=404)
    
    try:
        
        # Get file from request
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Upload directly to Backblaze using boto3
        try:
            # Read file content
            file_content = uploaded_file.read()
            uploaded_file.seek(0)
            
            # Upload to Backblaze with retry logic for SSL issues
            import time
            from botocore.exceptions import SSLError, EndpointConnectionError
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    backblaze_service.client.put_object(
                        Bucket=backblaze_service.bucket_name,
                        Key=session.storage_key,
                        Body=file_content,
                        ContentType=session.media_file.mime_type,
                        Metadata={
                            'user-id': str(user_profile.supabase_user_id),
                            'original-filename': session.media_file.original_filename,
                            'file-type': session.media_file.file_type,
                        }
                    )
                    break
                except (SSLError, EndpointConnectionError) as ssl_error:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        raise ssl_error
            
            # Update session
            session.uploaded_chunks = session.total_chunks
            session.is_active = False
            session.save()
            
            # Update media file
            session.media_file.upload_progress = 100.0
            session.media_file.processing_status = 'completed'
            session.media_file.save()
            
            logger.info(f"Proxy upload completed successfully for session {session.session_id}")
            
            return Response({
                'success': True,
                'message': 'File uploaded successfully',
                'upload_id': str(session.media_file.upload_id),
                'media_file_id': str(session.media_file.id),
                'cdn_url': session.media_file.cdn_url,
                'processing_status': session.media_file.processing_status
            })
            
        except Exception as e:
            logger.error(f"Proxy upload failed: {e}")
            return Response({
                'success': False,
                'error': f'Upload failed: {str(e)}'
            }, status=500)
            
    except UploadSession.DoesNotExist:
        return Response({'error': 'Upload session not found'}, status=404)


@api_view(['GET'])
def user_media(request):
    """List user's media files with pagination and type filtering"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get query parameters
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    media_type = request.GET.get('type')  # e.g., 'video', 'image', 'audio'
    
    print(f"=== USER_MEDIA REQUEST ===")
    print(f"User: {user_profile.supabase_user_id}, Page: {page}, Limit: {limit}, Type: {media_type}")
    logger.info(f"user_media request - User: {user_profile.supabase_user_id}, Page: {page}, Limit: {limit}, Type: {media_type}")
    
    # Build query
    queryset = MediaFile.objects.filter(
        user=user_profile,
        is_deleted=False
    )
    
    # Apply type filter if specified
    if media_type:
        queryset = queryset.filter(file_type=media_type)
    
    # Order by creation date
    queryset = queryset.order_by('-created_at')
    
    # Calculate pagination
    total_count = queryset.count()
    offset = (page - 1) * limit
    media_files = queryset[offset:offset + limit]
    
    print(f"Query results - Total count: {total_count}, Retrieved: {len(media_files)}")
    logger.info(f"user_media query results - Total count: {total_count}, Retrieved: {len(media_files)}")
    for i, media_file in enumerate(media_files[:3]):  # Log first 3 files
        print(f"  File {i+1}: ID={media_file.id}, Name='{media_file.filename}', Type={media_file.file_type}, Size={media_file.file_size}")
        logger.info(f"  File {i+1}: ID={media_file.id}, Name='{media_file.filename}', Type={media_file.file_type}, Size={media_file.file_size}")
    
    # Serialize data
    serializer = VideoListSerializer(media_files, many=True)
    
    print(f"Serialized data count: {len(serializer.data)}")
    logger.info(f"user_media serialized data count: {len(serializer.data)}")
    if serializer.data:
        print(f"First serialized item keys: {list(serializer.data[0].keys())}")
        logger.info(f"First serialized item keys: {list(serializer.data[0].keys())}")
    
    # Calculate pagination info
    total_pages = (total_count + limit - 1) // limit
    has_next = page < total_pages
    has_previous = page > 1
    
    response_data = {
        'success': True,
        'data': serializer.data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous
        }
    }
    
    print(f"Final response - Success: {response_data['success']}, Data items: {len(response_data['data'])}")
    print("=== END USER_MEDIA REQUEST ===")
    logger.info(f"user_media response - Success: {response_data['success']}, Data items: {len(response_data['data'])}")
    return Response(response_data)


@api_view(['GET'])
def list_videos(request):
    """List user's video files (all videos)"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get video files for user
    videos = MediaFile.objects.filter(
        user=user_profile,
        file_type='video',
        is_deleted=False
    ).order_by('-created_at')
    
    serializer = VideoListSerializer(videos, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['GET'])
def list_unassigned_videos(request):
    """List user's unassigned video files"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get query parameters for pagination
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    
    print(f"=== LIST_UNASSIGNED_VIDEOS REQUEST ===")
    print(f"User: {user_profile.supabase_user_id}, Page: {page}, Limit: {limit}")
    logger.info(f"list_unassigned_videos request - User: {user_profile.supabase_user_id}, Page: {page}, Limit: {limit}")
    
    # DEBUG: First, let's see ALL videos for this user and their assignment status
    all_user_videos = MediaFile.objects.filter(
        user=user_profile,
        file_type='video',
        is_deleted=False
    ).values('id', 'filename', 'course_id', 'section_id')[:10]  # Limit to first 10 for debugging
    
    print("=== ALL USER VIDEOS (first 10) ===")
    logger.info("=== ALL USER VIDEOS (first 10) ===")
    for video in all_user_videos:
        assignment_status = "UNASSIGNED"
        if video['section_id']:
            assignment_status = f"ASSIGNED TO SECTION: {video['section_id']}"
        elif video['course_id']:
            assignment_status = f"ASSIGNED TO COURSE: {video['course_id']}"
        print(f"  Video {video['id']}: {video['filename']} - {assignment_status}")
        logger.info(f"  Video {video['id']}: {video['filename']} - {assignment_status}")
    
    # Get unassigned video files for user (not assigned to any section OR course)
    # IMPORTANT: Videos should only appear as "unassigned" if they are NOT assigned to:
    # - Any section (section_id is NULL)
    # - Any course directly (course_id is NULL)
    queryset = MediaFile.objects.filter(
        user=user_profile,
        file_type='video',
        is_deleted=False,
        section__isnull=True,  # Videos not assigned to any section
        course__isnull=True    # AND not assigned to any course
    ).order_by('-created_at')
    
    # Debug: Log the query to verify it's correct
    logger.info(f"Unassigned videos query: {queryset.query}")
    logger.info(f"SQL WHERE clause includes section_id IS NULL AND course_id IS NULL: {queryset.query}")
    
    # Calculate pagination
    total_count = queryset.count()
    offset = (page - 1) * limit
    videos = queryset[offset:offset + limit]
    
    print(f"Query results - Total count: {total_count}, Retrieved: {len(videos)}")
    logger.info(f"list_unassigned_videos query results - Total count: {total_count}, Retrieved: {len(videos)}")
    for i, video in enumerate(videos[:3]):  # Log first 3 videos
        print(f"  Video {i+1}: ID={video.id}, Name='{video.filename}', Section={video.section_id}, Course={video.course_id}")
        logger.info(f"  Video {i+1}: ID={video.id}, Name='{video.filename}', Section={video.section_id}, Course={video.course_id}")
    
    # Serialize data
    serializer = VideoListSerializer(videos, many=True)
    
    print(f"Serialized data count: {len(serializer.data)}")
    logger.info(f"list_unassigned_videos serialized data count: {len(serializer.data)}")
    if serializer.data:
        print(f"First serialized video keys: {list(serializer.data[0].keys())}")
        logger.info(f"First serialized video keys: {list(serializer.data[0].keys())}")
    
    # Calculate pagination info
    total_pages = (total_count + limit - 1) // limit
    has_next = page < total_pages
    has_previous = page > 1
    
    response_data = {
        'success': True,
        'data': serializer.data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous
        }
    }
    
    print(f"Final response - Success: {response_data['success']}, Data items: {len(response_data['data'])}")
    print("=== END LIST_UNASSIGNED_VIDEOS REQUEST ===")
    logger.info(f"list_unassigned_videos response - Success: {response_data['success']}, Data items: {len(response_data['data'])}")
    return Response(response_data)


@api_view(['POST'])
def assign_video(request):
    """Assign video to course section"""
    logger.info(f"=== ASSIGN VIDEO REQUEST ===")
    logger.info(f"Request data: {request.data}")
    logger.info(f"Content type: {request.content_type}")
    
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check instructor permissions
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to assign videos'
        }, status=403)
    
    # Validate request data
    serializer = AssignVideoSerializer(data=request.data)
    if not serializer.is_valid():
        logger.error(f"Serializer validation failed: {serializer.errors}")
        return Response({'error': serializer.errors}, status=400)
    
    data = serializer.validated_data
    
    try:
        # Get video file
        video = get_object_or_404(
            MediaFile, 
            id=data['videoId'],
            user=user_profile,
            file_type='video'
        )
        
        # Get course and section, verify ownership
        course = get_object_or_404(Course, id=data['courseId'])
        section = get_object_or_404(
            CourseSection, 
            id=data['sectionId'], 
            course=course
        )
        
        # Verify user owns the course
        if course.instructor != user_profile:
            return Response({
                'error': 'Permission denied',
                'message': 'You can only assign videos to your own courses'
            }, status=403)
        
        # Assign video to course section
        with transaction.atomic():
            video.course = course
            video.section = section
            video.save()
        
        return Response({
            'success': True,
            'message': 'Video assigned to course section successfully',
            'data': {
                'video_id': str(video.id),
                'course_id': str(course.id),
                'section_id': str(section.id),
                'section_title': section.title,
                'video_url': video.cdn_url or video.storage_url,
                'duration': video.duration
            }
        })
        
    except Exception as e:
        logger.error(f"Video assignment failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)


@api_view(['DELETE'])
def delete_media(request, media_id):
    """Delete media file"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    try:
        # Get media file
        media_file = get_object_or_404(
            MediaFile,
            id=media_id,
            user=user_profile
        )
        
        # Delete from storage
        if hasattr(media_file, 'storage_key') and media_file.storage_key:
            backblaze_service.delete_file(media_file.storage_key)
        
        # Soft delete media file
        media_file.is_deleted = True
        media_file.save()
        
        return Response({
            'success': True,
            'message': 'Media file deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Media deletion failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)


@api_view(['GET'])
def get_media_info(request, media_id):
    """Get detailed media file information"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    try:
        # Get media file
        media_file = get_object_or_404(
            MediaFile,
            id=media_id,
            user=user_profile
        )
        
        serializer = MediaFileSerializer(media_file)
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Failed to get media info: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)