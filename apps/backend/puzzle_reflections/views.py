"""
API views for puzzle reflections.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from accounts.models import UserProfile
from media_library.models import MediaFile, FileType, ProcessingStatus
from media_library.services import media_upload_service
from .models import PuzzleReflection, ReflectionType
from .serializers import (
    PuzzleReflectionListSerializer,
    PuzzleReflectionDetailSerializer, 
    PuzzleReflectionCreateUpdateSerializer,
    ReflectionSummarySerializer
)
from .filters import PuzzleReflectionFilter


def get_user_profile(request):
    """Helper to get user profile from request"""
    if not hasattr(request, 'user_id') or not request.user_id:
        return None
    try:
        return UserProfile.objects.get(supabase_user_id=request.user_id)
    except UserProfile.DoesNotExist:
        return None


class PuzzleReflectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing puzzle reflections.
    Provides CRUD operations with proper user isolation.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PuzzleReflectionFilter
    search_fields = ['title', 'description', 'text_content']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return reflections for the authenticated user only"""
        user_profile = get_user_profile(self.request)
        if not user_profile:
            return PuzzleReflection.objects.none()
        
        return PuzzleReflection.objects.filter(
            user=user_profile,
            is_deleted=False
        ).select_related(
            'user', 'course', 'media_file'
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PuzzleReflectionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PuzzleReflectionCreateUpdateSerializer
        else:
            return PuzzleReflectionDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create reflection with optional direct file upload.
        Handles both JSON payload with media_file UUID and multipart form data with file upload.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # DEBUG: Comprehensive request logging
        print("=== PUZZLE REFLECTION CREATE DEBUG ===")
        print(f"Request method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Request headers: {dict(request.headers)}")
        
        # Access body BEFORE accessing request.data
        try:
            raw_body = request._request.body if hasattr(request, '_request') else None
            print(f"Raw body: {raw_body}")
            if raw_body:
                import json
                try:
                    parsed = json.loads(raw_body.decode('utf-8'))
                    print(f"Parsed JSON: {parsed}")
                except:
                    print("Failed to parse as JSON")
        except Exception as e:
            print(f"Error accessing raw body: {e}")
        
        print(f"Request data: {request.data}")
        print(f"Request POST: {getattr(request, 'POST', {})}")
        print(f"Request FILES: {getattr(request, 'FILES', {})}")
        
        logger.error(f"=== DEBUG: Request data received: {request.data} ===")
        
        # Check if this is a multipart request with file upload
        uploaded_file = request.FILES.get('file')
        logger.info(f"Uploaded file: {uploaded_file}")
        
        if uploaded_file:
            print(f"Processing uploaded file: {uploaded_file.name}")
            # Use same pattern as existing media library proxy_upload
            try:
                user_profile = get_user_profile(request)
                if not user_profile:
                    print("ERROR: No user_profile found in request")
                    return Response(
                        {'error': 'Authentication required'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Import backblaze_service from media_library
                from media_library.services import backblaze_service
                
                # Determine file type
                content_type = uploaded_file.content_type
                if content_type.startswith('video/'):
                    file_type = FileType.VIDEO
                elif content_type.startswith('audio/'):
                    file_type = FileType.AUDIO
                elif content_type.startswith('image/'):
                    file_type = FileType.IMAGE
                elif content_type in ['application/pdf', 'application/msword', 'text/plain']:
                    file_type = FileType.DOCUMENT
                else:
                    file_type = FileType.OTHER
                
                # Generate storage key (same pattern as backblaze service)
                import hashlib
                from django.utils import timezone
                timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                file_hash = hashlib.md5(f"{user_profile.supabase_user_id}-{uploaded_file.name}-{timestamp}".encode()).hexdigest()[:8]
                safe_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in uploaded_file.name)
                safe_filename = "_".join(filter(None, safe_filename.split("_")))
                storage_key = f"reflections/{user_profile.supabase_user_id}/{timestamp}_{file_hash}_{safe_filename}"
                
                # Generate URLs
                storage_url = f"https://{backblaze_service.bucket_name}.{backblaze_service.client._endpoint.host}/{storage_key}"
                cdn_url = f"{backblaze_service.cdn_base_url}/{storage_key}" if backblaze_service.cdn_base_url else storage_url
                
                print(f"Uploading to Backblaze B2: {storage_key}")
                
                # Create MediaFile record first
                media_file = MediaFile.objects.create(
                    user=user_profile,
                    filename=f"reflection_{user_profile.supabase_user_id}_{uploaded_file.name}",
                    original_filename=uploaded_file.name,
                    file_type=file_type,
                    mime_type=content_type,
                    file_size=uploaded_file.size,
                    storage_provider='backblaze',
                    storage_bucket=backblaze_service.bucket_name,
                    storage_key=storage_key,
                    storage_url=storage_url,
                    cdn_url=cdn_url,
                    processing_status=ProcessingStatus.PENDING
                )
                
                print(f"MediaFile created: {media_file.id}")
                
                # Upload to Backblaze B2 (same as proxy_upload)
                # Read file content properly for blob data
                uploaded_file.seek(0)  # Ensure we're at the start
                file_content = uploaded_file.read()
                
                print(f"File content length: {len(file_content)} bytes")
                print(f"Original file size: {uploaded_file.size} bytes")
                print(f"Content type: {content_type}")
                print(f"File name: {uploaded_file.name}")
                
                # Debug: Check if file content is valid
                if len(file_content) != uploaded_file.size:
                    print(f"WARNING: File content length mismatch!")
                if len(file_content) == 0:
                    print(f"ERROR: File content is empty!")
                    raise Exception("File content is empty")
                
                # Upload with retry logic for SSL issues
                import time
                from botocore.exceptions import SSLError, EndpointConnectionError
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        backblaze_service.client.put_object(
                            Bucket=backblaze_service.bucket_name,
                            Key=storage_key,
                            Body=file_content,
                            ContentType=content_type,
                            Metadata={
                                'user-id': str(user_profile.supabase_user_id),
                                'original-filename': uploaded_file.name,
                                'file-type': file_type,
                            }
                        )
                        break
                    except (SSLError, EndpointConnectionError) as ssl_error:
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        else:
                            raise ssl_error
                
                # Update MediaFile as completed
                media_file.processing_status = ProcessingStatus.COMPLETED
                media_file.save()
                
                print(f"Upload completed successfully: {cdn_url}")
                
                # Add media_file ID to request data
                request.data._mutable = True if hasattr(request.data, '_mutable') else None
                request.data['media_file'] = media_file.id
                
            except Exception as e:
                print(f"ERROR processing file: {str(e)}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                # Clean up MediaFile if it was created
                if 'media_file' in locals():
                    media_file.delete()
                return Response(
                    {'error': f'Failed to process file: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Continue with standard creation
        logger.info(f"Final request data before serializer: {dict(request.data)}")
        
        serializer = self.get_serializer(data=request.data)
        logger.info(f"Using serializer: {serializer.__class__.__name__}")
        logger.info(f"Serializer initial data: {serializer.initial_data}")
        
        if not serializer.is_valid():
            logger.error(f"Serializer validation errors: {serializer.errors}")
            logger.info(f"Serializer validated data: {getattr(serializer, 'validated_data', 'No validated data')}")
            
        serializer.is_valid(raise_exception=True)
        logger.info(f"Serializer validated data: {serializer.validated_data}")
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        logger.info(f"Successfully created reflection: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """Set user when creating reflection"""
        user_id = getattr(self.request, 'user_id', None)
        user_profile = get_user_profile(self.request)
        if not user_profile:
            raise ValueError("User profile not found in request")
        serializer.save(
            user=user_profile,
            created_by=user_id
        )
    
    def perform_update(self, serializer):
        """Set updated_by when updating"""
        user_id = getattr(self.request, 'user_id', None)
        serializer.save(updated_by=user_id)
    
    def perform_destroy(self, instance):
        """Soft delete instead of hard delete"""
        user_id = getattr(self.request, 'user_id', None)
        instance.soft_delete(user_id=user_id)
    
    @action(detail=False, methods=['get'])
    def by_video(self, request):
        """Get reflections for a specific video"""
        video_id = request.query_params.get('video_id')
        if not video_id:
            return Response(
                {'error': 'video_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reflections = self.get_queryset().filter(video_id=video_id)
        serializer = PuzzleReflectionListSerializer(reflections, many=True)
        
        return Response({
            'video_id': video_id,
            'total_reflections': reflections.count(),
            'reflections': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get reflection summary statistics"""
        queryset = self.get_queryset()
        
        # Overall stats
        total_reflections = queryset.count()
        
        # By type
        type_stats = queryset.values('reflection_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # By video
        video_stats = queryset.values('video_id').annotate(
            count=Count('id')
        ).order_by('-count')[:10]  # Top 10 videos
        
        # Recent activity
        recent_reflections = queryset[:5]
        recent_serializer = PuzzleReflectionListSerializer(recent_reflections, many=True)
        
        return Response({
            'total_reflections': total_reflections,
            'by_type': type_stats,
            'top_videos': video_stats,
            'recent_reflections': recent_serializer.data
        })
    
