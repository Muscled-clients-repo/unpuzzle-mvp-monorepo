"""
Transcript processing endpoints for AI context and search
"""
import logging
import asyncio
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..services.transcript_service import TranscriptService, TranscriptServiceError
from ..serializers import (
    TranscriptSearchRequestSerializer, TranscriptSearchResponseSerializer,
    TranscriptReferenceRequestSerializer, TranscriptReferenceResponseSerializer
)

logger = logging.getLogger(__name__)


class TranscriptSearchView(APIView):
    """
    POST /api/v1/ai-assistant/transcript/search/
    Search transcript content for relevant segments
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = TranscriptSearchRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # TODO: Add course/video access validation here
            # Validate user has access to the video
            video_id = data['video_id']
            # if not self._validate_video_access(request.user, video_id):
            #     return Response({
            #         'error': 'access_denied',
            #         'message': 'You do not have access to this video',
            #         'code': 403
            #     }, status=status.HTTP_403_FORBIDDEN)
            
            # Perform transcript search
            transcript_service = TranscriptService()
            search_results = asyncio.run(transcript_service.search_transcript(
                video_id=data['video_id'],
                query=data['query'],
                limit=data['limit']
            ))
            
            response_serializer = TranscriptSearchResponseSerializer(data=search_results)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except TranscriptServiceError as e:
            logger.error(f"Transcript service error: {e}")
            return Response({
                'error': 'transcript_service_error',
                'message': str(e),
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error in transcript search: {e}")
            return Response({
                'error': 'server_error',
                'message': 'Transcript search temporarily unavailable',
                'code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_video_access(self, user, video_id):
        """
        Validate user has access to the video
        TODO: Implement proper video access validation
        """
        # For now, return True - implement proper validation based on your course/enrollment logic
        return True


class TranscriptReferenceView(APIView):
    """
    POST /api/v1/ai-assistant/transcript/reference/
    Save user's selected transcript segments for AI context
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = TranscriptReferenceRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            # TODO: Add course/video access validation here
            video_id = data['video_id']
            # if not self._validate_video_access(request.user, video_id):
            #     return Response({
            #         'error': 'access_denied',
            #         'message': 'You do not have access to this video',
            #         'code': 403
            #     }, status=status.HTTP_403_FORBIDDEN)
            
            # Validate time range
            if data['start_time'] >= data['end_time']:
                return Response({
                    'error': 'invalid_time_range',
                    'message': 'Start time must be less than end time',
                    'code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save transcript reference
            transcript_service = TranscriptService()
            reference_result = asyncio.run(transcript_service.save_transcript_reference(
                user=request.user,
                video_id=data['video_id'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                text=data['text'],
                purpose=data.get('purpose', 'ai_context')
            ))
            
            response_serializer = TranscriptReferenceResponseSerializer(data=reference_result)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except TranscriptServiceError as e:
            logger.error(f"Transcript service error: {e}")
            return Response({
                'error': 'transcript_service_error',
                'message': str(e),
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error saving transcript reference: {e}")
            return Response({
                'error': 'server_error',
                'message': 'Unable to save transcript reference',
                'code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_video_access(self, user, video_id):
        """
        Validate user has access to the video
        TODO: Implement proper video access validation
        """
        # For now, return True - implement proper validation based on your course/enrollment logic
        return True


class TranscriptReferenceListView(APIView):
    """
    GET /api/v1/ai-assistant/transcript/references/
    Get user's saved transcript references
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            video_id = request.query_params.get('video_id')
            active_only = request.query_params.get('active_only', 'true').lower() == 'true'
            
            transcript_service = TranscriptService()
            references = transcript_service.get_user_transcript_references(
                user=request.user,
                video_id=video_id,
                active_only=active_only
            )
            
            # Convert queryset to list and serialize
            references_data = []
            for ref in references:
                references_data.append({
                    'id': str(ref.id),
                    'video_id': ref.video_id,
                    'text': ref.text,
                    'start_time': ref.start_time,
                    'end_time': ref.end_time,
                    'purpose': ref.purpose,
                    'created_at': ref.created_at.isoformat(),
                    'expires_at': ref.expires_at.isoformat() if ref.expires_at else None
                })
            
            return Response({
                'references': references_data,
                'total_count': len(references_data)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving transcript references: {e}")
            return Response({
                'error': 'server_error',
                'message': 'Unable to retrieve transcript references',
                'code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)