"""
User Analytics & Management endpoints for AI assistant
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..services.usage_service import AIUsageService, UsageServiceError
from ..serializers import (
    CheckLimitsRequestSerializer, CheckLimitsResponseSerializer,
    UserAIStatsResponseSerializer
)

logger = logging.getLogger(__name__)


class UserAIStatsView(APIView):
    """
    GET /api/v1/ai-assistant/user/ai-stats/
    Get user's AI usage statistics and metrics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            usage_service = AIUsageService()
            stats = usage_service.get_user_ai_stats(user=request.user)
            
            response_serializer = UserAIStatsResponseSerializer(data=stats)
            response_serializer.is_valid(raise_exception=True)
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except UsageServiceError as e:
            logger.error(f"Usage service error: {e}")
            return Response({
                'error': 'usage_service_error',
                'message': str(e),
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error getting user AI stats: {e}")
            return Response({
                'error': 'server_error',
                'message': 'Unable to retrieve AI usage statistics',
                'code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckLimitsView(APIView):
    """
    POST /api/v1/ai-assistant/user/check-limits/
    Check if user can make AI requests based on subscription limits
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = CheckLimitsRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            
            usage_service = AIUsageService()
            limits_check = usage_service.check_usage_limits(
                user=request.user,
                agent_type=data['agent_type'],
                estimated_tokens=data['estimated_tokens']
            )
            
            response_serializer = CheckLimitsResponseSerializer(data=limits_check)
            response_serializer.is_valid(raise_exception=True)
            
            # Return appropriate status code based on limits
            response_status = status.HTTP_200_OK
            if not limits_check['can_use_ai']:
                response_status = status.HTTP_429_TOO_MANY_REQUESTS
            
            return Response(response_serializer.data, status=response_status)
            
        except UsageServiceError as e:
            logger.error(f"Usage service error: {e}")
            return Response({
                'error': 'usage_service_error',
                'message': str(e),
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error checking usage limits: {e}")
            return Response({
                'error': 'server_error',
                'message': 'Unable to check usage limits',
                'code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UsageSummaryView(APIView):
    """
    GET /api/v1/ai-assistant/user/usage-summary/
    Get a simplified usage summary for quick display
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            usage_service = AIUsageService()
            stats = usage_service.get_user_ai_stats(user=request.user)
            
            # Return simplified summary
            summary = {
                'daily_usage': {
                    'used': stats['daily_usage']['interactions_today'],
                    'limit': stats['daily_usage']['limit'],
                    'remaining': stats['daily_usage']['remaining']
                },
                'monthly_usage': {
                    'used': stats['monthly_usage']['interactions_this_month'],
                    'limit': stats['monthly_usage']['limit'],
                    'remaining': stats['monthly_usage']['remaining']
                },
                'subscription_plan': stats['subscription_plan'],
                'can_use_ai': stats['daily_usage']['remaining'] > 0 and stats['monthly_usage']['remaining'] > 0
            }
            
            return Response(summary, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return Response({
                'error': 'server_error',
                'message': 'Unable to retrieve usage summary',
                'code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SystemStatsView(APIView):
    """
    GET /api/v1/ai-assistant/admin/system-stats/
    Get system-wide AI usage statistics (admin only)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # TODO: Add admin permission check
            # if not request.user.is_staff:
            #     return Response({
            #         'error': 'permission_denied',
            #         'message': 'Admin access required',
            #         'code': 403
            #     }, status=status.HTTP_403_FORBIDDEN)
            
            usage_service = AIUsageService()
            system_stats = usage_service.get_system_usage_stats()
            
            return Response(system_stats, status=status.HTTP_200_OK)
            
        except UsageServiceError as e:
            logger.error(f"Usage service error: {e}")
            return Response({
                'error': 'usage_service_error',
                'message': str(e),
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return Response({
                'error': 'server_error',
                'message': 'Unable to retrieve system statistics',
                'code': 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)