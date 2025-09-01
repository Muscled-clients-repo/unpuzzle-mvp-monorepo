"""
AI Agent API endpoints for chat, hint, quiz, reflection, and learning path generation
"""
import logging
import asyncio
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from decimal import Decimal

from ..models import AISession, AIMessage, MessageType, AgentType
from ..services.ai_agents import AIAgentService
from ..services.usage_service import AIUsageService
from ..services.srt_context_service import srt_context_service
from ..serializers import (
    ChatSendRequestSerializer, ChatSendResponseSerializer,
    HintRequestSerializer, HintResponseSerializer,
    QuizRequestSerializer, QuizResponseSerializer,
    ReflectionRequestSerializer, ReflectionResponseSerializer,
    PathRequestSerializer, PathResponseSerializer
)

logger = logging.getLogger(__name__)


class ChatSendView(APIView):
    """
    POST /api/v1/ai-assistant/chat/send/
    Send message to AI chat assistant with video context
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            logger.info(f"ChatSendView: Received request from user: {getattr(request, 'user', 'No user')}")
            logger.info(f"ChatSendView: Request data: {request.data}")
            
            serializer = ChatSendRequestSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"ChatSendView: Validation failed - {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            logger.info(f"ChatSendView: Validated data: {data}")
            
            user = request.user
            logger.info(f"ChatSendView: User authenticated: {user.email if user else 'None'}")
            
            # Check usage limits
            usage_service = AIUsageService()
            limits_check = usage_service.check_usage_limits(
                user=user,
                agent_type='chat',
                estimated_tokens=100
            )
            logger.info(f"ChatSendView: Usage limits check: {limits_check}")
            
            if not limits_check['can_use_ai']:
                return Response({
                    'error': 'rate_limit_exceeded',
                    'message': limits_check.get('upgrade_message', 'Daily AI limit reached'),
                    'code': 429,
                    'details': limits_check
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Get or create session
            session_id = data.get('session_id')
            if session_id:
                # Try to get existing session - could be UUID or string ID from frontend
                try:
                    # First try as UUID
                    import uuid
                    try:
                        uuid.UUID(session_id)
                        session = AISession.objects.get(id=session_id, user=user)
                    except (ValueError, AISession.DoesNotExist):
                        # Not a UUID or doesn't exist, create new session
                        session = AISession.objects.create(
                            user=user,
                            title=f"Chat Session - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                            metadata={'frontend_session_id': session_id}
                        )
                        logger.info(f"Created new AI session with frontend ID: {session_id}")
                except Exception as e:
                    logger.error(f"Error handling session: {e}")
                    # Create new session on any error
                    session = AISession.objects.create(
                        user=user,
                        title=f"Chat Session - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                    )
            else:
                # No session ID provided, create new session
                session = AISession.objects.create(
                    user=user,
                    title=f"Chat Session - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                )
                logger.info(f"Created new AI session: {session.id}")
            
            # Add SRT subtitle context if video_id provided
            context = data.get('context', {})
            if context.get('video_id') and context.get('timestamp'):
                logger.info(f"ChatSendView: Extracting SRT context for video {context['video_id']} at timestamp {context['timestamp']}")
                srt_context = srt_context_service.get_video_context_from_srt(
                    video_id=context['video_id'],
                    timestamp=context['timestamp']
                )
                if srt_context:
                    logger.info(f"ChatSendView: Found SRT context: {srt_context[:100]}...")
                    context['transcript_segment'] = srt_context
                else:
                    logger.warning(f"ChatSendView: No SRT context found for video {context['video_id']} at timestamp {context['timestamp']}")
            
            # Save user message
            user_message = AIMessage.objects.create(
                session=session,
                message_type=MessageType.USER,
                content=data['message'],
                context=context
            )
            
            # Generate AI response
            ai_service = AIAgentService()
            ai_response = asyncio.run(ai_service.generate_chat_response(
                message=data['message'],
                context=context
            ))
            
            # Save AI response
            ai_message = AIMessage.objects.create(
                session=session,
                message_type=MessageType.ASSISTANT,
                content=ai_response['response'],
                agent_type=AgentType.CHAT,
                context=context,
                tokens_used=ai_response['tokens_used'],
                cached=ai_response['cached']
            )
            
            # Record usage
            usage_service.record_usage(
                user=user,
                agent_type='chat',
                tokens_used=ai_response['tokens_used'],
                cost=Decimal('0.003') * ai_response['tokens_used'] / 1000,  # Approximate cost
                session=session,
                course=session.course
            )
            
            # Update session
            session.updated_at = timezone.now()
            session.save()
            
            response_data = {
                'response': ai_response['response'],
                'session_id': str(session.id),  # Backend session UUID
                'frontend_session_id': session_id if session_id else None,  # Echo frontend session ID
                'message_id': ai_message.id,
                'tokens_used': ai_response['tokens_used'],
                'cached': ai_response['cached']
            }
            
            response_serializer = ChatSendResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in chat send: {e}")
            return Response({
                'error': 'ai_service_error',
                'message': 'AI service temporarily unavailable',
                'code': 503
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class HintGenerateView(APIView):
    """
    POST /api/v1/ai-assistant/agents/hint/
    Generate contextual learning hint based on video content
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = HintRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            user = request.user
            
            # Check usage limits
            usage_service = AIUsageService()
            limits_check = usage_service.check_usage_limits(
                user=user,
                agent_type='hint',
                estimated_tokens=50
            )
            
            if not limits_check['can_use_ai']:
                return Response({
                    'error': 'rate_limit_exceeded',
                    'message': limits_check.get('upgrade_message', 'Daily AI limit reached'),
                    'code': 429,
                    'details': limits_check
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Add SRT context to hint data
            hint_context = dict(data)
            if hint_context.get('video_id') and hint_context.get('timestamp'):
                logger.info(f"HintGenerateView: Adding SRT context for video {hint_context['video_id']} at timestamp {hint_context['timestamp']}")
                srt_context = srt_context_service.get_video_context_from_srt(
                    video_id=hint_context['video_id'],
                    timestamp=hint_context['timestamp']
                )
                if srt_context:
                    hint_context['transcript_segment'] = srt_context
                    logger.info(f"HintGenerateView: Added SRT context: {srt_context[:100]}...")
            
            # Generate hint
            ai_service = AIAgentService()
            hint_response = asyncio.run(ai_service.generate_hint(context=hint_context))
            
            # Record usage
            usage_service.record_usage(
                user=user,
                agent_type='hint',
                tokens_used=hint_response['tokens_used'],
                cost=Decimal('0.003') * hint_response['tokens_used'] / 1000
            )
            
            response_serializer = HintResponseSerializer(data=hint_response)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in hint generation: {e}")
            return Response({
                'error': 'ai_service_error',
                'message': 'AI service temporarily unavailable',
                'code': 503
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class QuizGenerateView(APIView):
    """
    POST /api/v1/ai-assistant/agents/quiz/
    Generate knowledge check quiz from video content
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = QuizRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            user = request.user
            
            # Check usage limits
            usage_service = AIUsageService()
            limits_check = usage_service.check_usage_limits(
                user=user,
                agent_type='quiz',
                estimated_tokens=150
            )
            
            if not limits_check['can_use_ai']:
                return Response({
                    'error': 'rate_limit_exceeded',
                    'message': limits_check.get('upgrade_message', 'Daily AI limit reached'),
                    'code': 429,
                    'details': limits_check
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Build quiz context
            quiz_context = dict(data)
            
            # Add SRT context if video_id and timestamp provided
            if quiz_context.get('video_id') and quiz_context.get('timestamp') is not None:
                logger.info(f"QuizGenerateView: Extracting SRT context for video {quiz_context['video_id']} at timestamp {quiz_context['timestamp']}")
                srt_context = srt_context_service.get_video_context_from_srt(
                    video_id=quiz_context['video_id'],
                    timestamp=quiz_context['timestamp'],
                    context_window=60  # Get 60 seconds of context for quiz generation
                )
                if srt_context:
                    # If transcript_segments is empty, use SRT context
                    if not quiz_context.get('transcript_segments'):
                        quiz_context['transcript_segments'] = [srt_context]
                    logger.info(f"QuizGenerateView: Added SRT context: {srt_context[:100]}...")
            
            # Generate quiz
            ai_service = AIAgentService()
            quiz_response = asyncio.run(ai_service.generate_quiz(context=quiz_context))
            
            # Record usage
            usage_service.record_usage(
                user=user,
                agent_type='quiz',
                tokens_used=quiz_response['tokens_used'],
                cost=Decimal('0.003') * quiz_response['tokens_used'] / 1000
            )
            
            response_serializer = QuizResponseSerializer(data=quiz_response)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in quiz generation: {e}")
            return Response({
                'error': 'ai_service_error',
                'message': 'AI service temporarily unavailable',
                'code': 503
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ReflectionGenerateView(APIView):
    """
    POST /api/v1/ai-assistant/agents/reflection/
    Generate reflection prompts for learning consolidation
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = ReflectionRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            user = request.user
            
            # Check usage limits
            usage_service = AIUsageService()
            limits_check = usage_service.check_usage_limits(
                user=user,
                agent_type='reflection',
                estimated_tokens=100
            )
            
            if not limits_check['can_use_ai']:
                return Response({
                    'error': 'rate_limit_exceeded',
                    'message': limits_check.get('upgrade_message', 'Daily AI limit reached'),
                    'code': 429,
                    'details': limits_check
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Generate reflection
            ai_service = AIAgentService()
            reflection_response = asyncio.run(ai_service.generate_reflection(context=data))
            
            # Record usage
            usage_service.record_usage(
                user=user,
                agent_type='reflection',
                tokens_used=reflection_response['tokens_used'],
                cost=Decimal('0.003') * reflection_response['tokens_used'] / 1000
            )
            
            response_serializer = ReflectionResponseSerializer(data=reflection_response)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in reflection generation: {e}")
            return Response({
                'error': 'ai_service_error',
                'message': 'AI service temporarily unavailable',
                'code': 503
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class PathGenerateView(APIView):
    """
    POST /api/v1/ai-assistant/agents/path/
    Generate personalized learning path recommendations
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = PathRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            user = request.user
            
            # Check usage limits
            usage_service = AIUsageService()
            limits_check = usage_service.check_usage_limits(
                user=user,
                agent_type='path',
                estimated_tokens=200
            )
            
            if not limits_check['can_use_ai']:
                return Response({
                    'error': 'rate_limit_exceeded',
                    'message': limits_check.get('upgrade_message', 'Daily AI limit reached'),
                    'code': 429,
                    'details': limits_check
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Generate learning path
            ai_service = AIAgentService()
            path_response = asyncio.run(ai_service.generate_learning_path(context=data))
            
            # Record usage
            usage_service.record_usage(
                user=user,
                agent_type='path',
                tokens_used=path_response['tokens_used'],
                cost=Decimal('0.003') * path_response['tokens_used'] / 1000
            )
            
            response_serializer = PathResponseSerializer(data=path_response)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in learning path generation: {e}")
            return Response({
                'error': 'ai_service_error',
                'message': 'AI service temporarily unavailable',
                'code': 503
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)