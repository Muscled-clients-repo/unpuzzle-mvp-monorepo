"""
Usage tracking and rate limiting service for AI assistant functionality
"""
import logging
from typing import Dict, Optional, Any
from django.db.models import Sum, Count
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
from decimal import Decimal
from ..models import AIUsageMetric, AgentType

logger = logging.getLogger(__name__)


class AIUsageService:
    """
    Service for tracking AI usage, implementing rate limits, and managing billing
    """
    
    def __init__(self):
        # Default rate limits (can be overridden by settings)
        self.rate_limits = {
            'free': {
                'daily': 3,
                'monthly': 50
            },
            'premium': {
                'daily': 50,
                'monthly': 1000
            },
            'enterprise': {
                'daily': 200,
                'monthly': 5000
            }
        }
    
    def check_usage_limits(
        self,
        user,
        agent_type: str,
        estimated_tokens: int = 50
    ) -> Dict[str, Any]:
        """
        Check if user can make AI request based on subscription limits
        """
        try:
            # Get user subscription plan and limits from actual subscription
            subscription_plan = user.subscription_plan  # Now uses property from UserProfile
            daily_limit = user.ai_daily_limit  # From subscription
            monthly_limit = user.ai_monthly_limit  # From subscription
            
            # Get current usage
            daily_usage = self._get_daily_usage(user)
            monthly_usage = self._get_monthly_usage(user)
            
            # Update subscription usage counters if user has subscription
            if hasattr(user, 'subscription'):
                user.subscription.reset_daily_usage()  # Reset if new day
            
            # Check if user can make request
            can_use_ai = (
                daily_usage['interactions'] < daily_limit and
                monthly_usage['interactions'] < monthly_limit
            )
            
            # Calculate remaining usage
            daily_remaining = max(0, daily_limit - daily_usage['interactions'])
            monthly_remaining = max(0, monthly_limit - monthly_usage['interactions'])
            
            # Estimate cost (simplified)
            cost_estimate = self._estimate_cost(estimated_tokens)
            
            # Get next reset time
            next_reset = self._get_next_daily_reset()
            
            response = {
                'can_use_ai': can_use_ai,
                'remaining_interactions': daily_remaining,
                'daily_limit': daily_limit,
                'monthly_limit': monthly_limit,
                'subscription_plan': subscription_plan,
                'reset_time': next_reset.isoformat(),
                'cost_estimate': float(cost_estimate),
                'upgrade_required': False,
                'upgrade_message': None
            }
            
            # Add upgrade message if limits exceeded
            if not can_use_ai:
                if daily_usage['interactions'] >= daily_limit:
                    response.update({
                        'upgrade_required': True,
                        'upgrade_message': f"Daily AI limit reached ({daily_usage['interactions']}/{daily_limit}). "
                                         f"{'Upgrade to Premium for unlimited AI help!' if subscription_plan == 'free' else 'Limit resets tomorrow.'}"
                    })
                elif monthly_usage['interactions'] >= monthly_limit:
                    response.update({
                        'upgrade_required': True,
                        'upgrade_message': f"Monthly AI limit reached. "
                                         f"{'Upgrade your plan for higher limits!' if subscription_plan != 'enterprise' else 'Contact support for higher limits.'}"
                    })
            
            return response
            
        except Exception as e:
            logger.error(f"Error checking usage limits: {e}")
            # Return conservative response on error
            return {
                'can_use_ai': False,
                'remaining_interactions': 0,
                'daily_limit': 0,
                'monthly_limit': 0,
                'subscription_plan': 'free',
                'reset_time': timezone.now().isoformat(),
                'cost_estimate': 0.0,
                'upgrade_required': True,
                'upgrade_message': 'Unable to check usage limits. Please try again.'
            }
    
    def record_usage(
        self,
        user,
        agent_type: str,
        tokens_used: int,
        cost: Decimal,
        session=None,
        course=None
    ) -> AIUsageMetric:
        """
        Record AI usage for billing and analytics
        """
        try:
            usage_metric = AIUsageMetric.objects.create(
                user=user,
                agent_type=agent_type,
                tokens_used=tokens_used,
                cost=cost,
                session=session,
                course=course,
                metadata={
                    'timestamp': timezone.now().isoformat(),
                    'user_agent': getattr(user, 'last_user_agent', ''),
                    'ip_address': getattr(user, 'last_ip_address', '')
                }
            )
            
            # Update subscription usage counters
            if hasattr(user, 'subscription'):
                subscription = user.subscription
                subscription.reset_daily_usage()  # Reset if new day
                subscription.ai_usage_today += 1
                subscription.ai_usage_this_period += 1
                subscription.save(update_fields=['ai_usage_today', 'ai_usage_this_period', 'last_usage_reset_date'])
            
            # Invalidate cached usage stats
            self._invalidate_usage_cache(user)
            
            logger.info(f"Recorded AI usage: {user.email} - {agent_type} - {tokens_used} tokens")
            return usage_metric
            
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
            raise UsageServiceError(f"Failed to record usage: {str(e)}")
    
    def get_user_ai_stats(self, user) -> Dict[str, Any]:
        """
        Get comprehensive AI usage statistics for user
        """
        try:
            # Check cache first
            cache_key = f"ai_stats:{user.supabase_user_id}"
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # Calculate stats
            daily_usage = self._get_daily_usage(user)
            monthly_usage = self._get_monthly_usage(user)
            total_usage = self._get_total_usage(user)
            
            # Get subscription info
            subscription_plan = getattr(user, 'subscription_plan', 'free')
            limits = self.rate_limits.get(subscription_plan, self.rate_limits['free'])
            
            # Calculate next reset time
            next_reset = self._get_next_daily_reset()
            
            stats = {
                'user_id': user.supabase_user_id,
                'metrics': {
                    'total_interactions': total_usage['interactions'],
                    'hints_generated': total_usage.get('hint', 0),
                    'quizzes_completed': total_usage.get('quiz', 0),
                    'reflections_submitted': total_usage.get('reflection', 0),
                    'learning_paths_created': total_usage.get('path', 0)
                },
                'daily_usage': {
                    'interactions_today': daily_usage['interactions'],
                    'limit': limits['daily'],
                    'remaining': max(0, limits['daily'] - daily_usage['interactions']),
                    'reset_time': next_reset.isoformat()
                },
                'monthly_usage': {
                    'interactions_this_month': monthly_usage['interactions'],
                    'limit': limits['monthly'],
                    'remaining': max(0, limits['monthly'] - monthly_usage['interactions'])
                },
                'subscription_plan': subscription_plan,
                'cost_this_month': float(monthly_usage['cost'])
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, stats, 300)
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user AI stats: {e}")
            raise UsageServiceError(f"Failed to get AI stats: {str(e)}")
    
    def _get_daily_usage(self, user) -> Dict[str, Any]:
        """Get user's AI usage for today"""
        today = timezone.now().date()
        
        usage = AIUsageMetric.objects.filter(
            user=user,
            created_at__date=today
        ).aggregate(
            interactions=Count('id'),
            total_tokens=Sum('tokens_used'),
            total_cost=Sum('cost')
        )
        
        # Get usage by agent type
        agent_usage = AIUsageMetric.objects.filter(
            user=user,
            created_at__date=today
        ).values('agent_type').annotate(
            count=Count('id')
        )
        
        usage_by_type = {item['agent_type']: item['count'] for item in agent_usage}
        
        return {
            'interactions': usage['interactions'] or 0,
            'tokens': usage['total_tokens'] or 0,
            'cost': usage['total_cost'] or Decimal('0.0'),
            **usage_by_type
        }
    
    def _get_monthly_usage(self, user) -> Dict[str, Any]:
        """Get user's AI usage for current month"""
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        usage = AIUsageMetric.objects.filter(
            user=user,
            created_at__gte=month_start
        ).aggregate(
            interactions=Count('id'),
            total_tokens=Sum('tokens_used'),
            total_cost=Sum('cost')
        )
        
        # Get usage by agent type
        agent_usage = AIUsageMetric.objects.filter(
            user=user,
            created_at__gte=month_start
        ).values('agent_type').annotate(
            count=Count('id')
        )
        
        usage_by_type = {item['agent_type']: item['count'] for item in agent_usage}
        
        return {
            'interactions': usage['interactions'] or 0,
            'tokens': usage['total_tokens'] or 0,
            'cost': usage['total_cost'] or Decimal('0.0'),
            **usage_by_type
        }
    
    def _get_total_usage(self, user) -> Dict[str, Any]:
        """Get user's total AI usage"""
        usage = AIUsageMetric.objects.filter(
            user=user
        ).aggregate(
            interactions=Count('id'),
            total_tokens=Sum('tokens_used'),
            total_cost=Sum('cost')
        )
        
        # Get usage by agent type
        agent_usage = AIUsageMetric.objects.filter(
            user=user
        ).values('agent_type').annotate(
            count=Count('id')
        )
        
        usage_by_type = {item['agent_type']: item['count'] for item in agent_usage}
        
        return {
            'interactions': usage['interactions'] or 0,
            'tokens': usage['total_tokens'] or 0,
            'cost': usage['total_cost'] or Decimal('0.0'),
            **usage_by_type
        }
    
    def _get_next_daily_reset(self) -> datetime:
        """Get next daily reset time (midnight UTC)"""
        now = timezone.now()
        next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return next_reset
    
    def _estimate_cost(self, tokens: int) -> Decimal:
        """Estimate cost based on token usage"""
        # GPT-4 approximate pricing: $0.03 per 1K tokens
        cost_per_1k_tokens = Decimal('0.03')
        return (Decimal(tokens) / 1000) * cost_per_1k_tokens
    
    def _invalidate_usage_cache(self, user):
        """Invalidate cached usage stats for user"""
        cache_key = f"ai_stats:{user.supabase_user_id}"
        cache.delete(cache_key)
    
    def get_system_usage_stats(self) -> Dict[str, Any]:
        """Get system-wide AI usage statistics (for admin)"""
        try:
            today = timezone.now().date()
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Daily stats
            daily_stats = AIUsageMetric.objects.filter(
                created_at__date=today
            ).aggregate(
                total_requests=Count('id'),
                total_tokens=Sum('tokens_used'),
                total_cost=Sum('cost'),
                unique_users=Count('user', distinct=True)
            )
            
            # Monthly stats
            monthly_stats = AIUsageMetric.objects.filter(
                created_at__gte=month_start
            ).aggregate(
                total_requests=Count('id'),
                total_tokens=Sum('tokens_used'),
                total_cost=Sum('cost'),
                unique_users=Count('user', distinct=True)
            )
            
            # Agent type breakdown
            agent_breakdown = AIUsageMetric.objects.filter(
                created_at__gte=month_start
            ).values('agent_type').annotate(
                count=Count('id'),
                tokens=Sum('tokens_used')
            )
            
            return {
                'daily': {
                    'requests': daily_stats['total_requests'] or 0,
                    'tokens': daily_stats['total_tokens'] or 0,
                    'cost': float(daily_stats['total_cost'] or 0),
                    'unique_users': daily_stats['unique_users'] or 0
                },
                'monthly': {
                    'requests': monthly_stats['total_requests'] or 0,
                    'tokens': monthly_stats['total_tokens'] or 0,
                    'cost': float(monthly_stats['total_cost'] or 0),
                    'unique_users': monthly_stats['unique_users'] or 0
                },
                'agent_breakdown': list(agent_breakdown)
            }
            
        except Exception as e:
            logger.error(f"Error getting system usage stats: {e}")
            raise UsageServiceError(f"Failed to get system usage stats: {str(e)}")


class UsageServiceError(Exception):
    """Base exception for usage service errors"""
    pass