"""
AI Session management endpoints
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from ..models import AISession, AIMessage
from ..serializers import AISessionSerializer, AIMessageSerializer, ChatHistoryResponseSerializer

logger = logging.getLogger(__name__)


class ChatHistoryView(APIView):
    """
    GET /api/v1/ai-assistant/chat/history/<session_id>/
    Retrieve chat conversation history for session persistence
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        try:
            # Get session and verify ownership
            session = get_object_or_404(
                AISession.objects.select_related('course'),
                id=session_id,
                user=request.user
            )
            
            # Get all messages for the session
            messages = AIMessage.objects.filter(session=session).order_by('created_at')
            
            # Serialize messages
            message_serializer = AIMessageSerializer(messages, many=True)
            
            # Build response data
            response_data = {
                'session_id': session.id,
                'course_id': str(session.course.id) if session.course else '',
                'video_id': session.video_id or '',
                'messages': message_serializer.data,
                'total_messages': messages.count(),
                'created_at': session.created_at,
                'updated_at': session.updated_at
            }
            
            response_serializer = ChatHistoryResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except AISession.DoesNotExist:
            return Response({
                'error': 'session_not_found',
                'message': 'AI session not found',
                'code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return Response({
                'error': 'server_error',
                'message': 'Unable to retrieve chat history',
                'code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SessionCreateView(APIView):
    """
    POST /api/v1/ai-assistant/chat/session/
    Create new AI chat session
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Extract session data from request
            course_id = request.data.get('course_id')
            video_id = request.data.get('video_id', '')
            title = request.data.get('title', '')
            
            # Validate course access if course_id provided
            course = None
            if course_id:
                from courses.models import Course
                try:
                    course = Course.objects.get(id=course_id)
                    # TODO: Add course access validation here
                except Course.DoesNotExist:
                    return Response({
                        'error': 'course_not_found',
                        'message': 'Course not found',
                        'code': 404
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Create new session
            session = AISession.objects.create(
                user=request.user,
                course=course,
                video_id=video_id,
                title=title
            )
            
            session_serializer = AISessionSerializer(session)
            
            return Response(session_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating AI session: {e}")
            return Response({
                'error': 'server_error',
                'message': 'Unable to create AI session',
                'code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SessionListView(APIView):
    """
    GET /api/v1/ai-assistant/chat/sessions/
    List user's AI chat sessions
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get user's sessions
            sessions = AISession.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('course').order_by('-updated_at')
            
            # Apply pagination if needed
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))
            
            total_count = sessions.count()
            sessions = sessions[offset:offset + limit]
            
            session_serializer = AISessionSerializer(sessions, many=True)
            
            response_data = {
                'sessions': session_serializer.data,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error listing AI sessions: {e}")
            return Response({
                'error': 'server_error',
                'message': 'Unable to retrieve AI sessions',
                'code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)