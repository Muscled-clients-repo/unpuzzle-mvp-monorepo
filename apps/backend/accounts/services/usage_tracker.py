"""
Usage tracking service for subscription-based AI limits.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from django.conf import settings
from django.core.cache import cache
from django.db.models import Sum, Count
from django.utils import timezone

from accounts.models import UserProfile, UserSubscription

logger = logging.getLogger(__name__)


class UsageTrackerService:
    """Track and manage AI usage within subscription limits"""
    
    def __init__(self):
        self.cache_prefix = 'ai_usage'
        self.cache_ttl = 3600  # 1 hour
    
    def get_usage_key(self, user_id: str, period: str = 'daily') -> str:
        """Generate cache key for usage tracking"""
        today = timezone.now().date()
        return f"{self.cache_prefix}:{period}:{user_id}:{today}"
    
    def increment_usage(
        self,
        user: UserProfile,
        amount: int = 1,
        agent_type: str = 'chat'
    ) -> Dict[str, Any]:
        """
        Increment AI usage counter for a user.
        
        Args:
            user: UserProfile instance
            amount: Usage amount to increment
            agent_type: Type of AI agent used
            
        Returns:
            Dictionary with updated usage information
        """
        try:
            # Get or create subscription
            if hasattr(user, 'subscription'):
                subscription = user.subscription
                subscription.reset_daily_usage()  # Reset if new day
                
                # Increment usage counters
                subscription.ai_usage_today += amount
                subscription.ai_usage_this_period += amount
                subscription.save(update_fields=[
                    'ai_usage_today',
                    'ai_usage_this_period',
                    'last_usage_reset_date'
                ])
                
                # Update cache
                cache_key = self.get_usage_key(str(user.supabase_user_id))
                cache.set(cache_key, subscription.ai_usage_today, self.cache_ttl)
                
                return {
                    'success': True,
                    'usage_today': subscription.ai_usage_today,
                    'usage_this_period': subscription.ai_usage_this_period,
                    'daily_limit': subscription.plan.ai_daily_limit,
                    'monthly_limit': subscription.plan.ai_monthly_limit,
                    'remaining_today': max(0, subscription.plan.ai_daily_limit - subscription.ai_usage_today)
                }
            else:
                # Track free tier usage in cache
                cache_key = self.get_usage_key(str(user.supabase_user_id))
                current_usage = cache.get(cache_key, 0)
                new_usage = current_usage + amount
                cache.set(cache_key, new_usage, self.cache_ttl)
                
                return {
                    'success': True,
                    'usage_today': new_usage,
                    'usage_this_period': new_usage,
                    'daily_limit': settings.AI_RATE_LIMIT_FREE,
                    'monthly_limit': 50,
                    'remaining_today': max(0, settings.AI_RATE_LIMIT_FREE - new_usage)
                }
                
        except Exception as e:
            logger.error(f"Error incrementing usage: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_usage_limits(
        self,
        user: UserProfile,
        agent_type: str = 'chat',
        estimated_usage: int = 1
    ) -> Dict[str, Any]:
        """
        Check if user has available AI usage within their subscription limits.
        
        Args:
            user: UserProfile instance
            agent_type: Type of AI agent to check
            estimated_usage: Estimated usage for the operation
            
        Returns:
            Dictionary with usage check result
        """
        try:
            # Check feature availability first
            features = user.subscription_features
            feature_map = {
                'chat': 'ai_chat',
                'hint': 'ai_hints',
                'quiz': 'ai_quiz',
                'reflection': 'ai_reflection',
                'path': 'ai_path'
            }
            
            feature_key = feature_map.get(agent_type, 'ai_chat')
            if not features.get(feature_key, False):
                return {
                    'can_use': False,
                    'reason': 'feature_not_available',
                    'message': f'{agent_type.title()} feature is not available in your plan',
                    'upgrade_required': True
                }
            
            # Get current usage
            if hasattr(user, 'subscription'):
                subscription = user.subscription
                subscription.reset_daily_usage()  # Reset if new day
                
                current_usage = subscription.ai_usage_today
                daily_limit = subscription.plan.ai_daily_limit
                monthly_usage = subscription.ai_usage_this_period
                monthly_limit = subscription.plan.ai_monthly_limit
            else:
                # Free tier
                cache_key = self.get_usage_key(str(user.supabase_user_id))
                current_usage = cache.get(cache_key, 0)
                daily_limit = settings.AI_RATE_LIMIT_FREE
                monthly_usage = current_usage  # Simplified for free tier
                monthly_limit = 50
            
            # Check daily limit
            if current_usage + estimated_usage > daily_limit:
                return {
                    'can_use': False,
                    'reason': 'daily_limit_exceeded',
                    'message': f'Daily AI limit reached ({daily_limit} interactions)',
                    'current_usage': current_usage,
                    'daily_limit': daily_limit,
                    'reset_time': self.get_next_reset_time(),
                    'upgrade_required': True
                }
            
            # Check monthly limit
            if monthly_usage + estimated_usage > monthly_limit:
                return {
                    'can_use': False,
                    'reason': 'monthly_limit_exceeded',
                    'message': f'Monthly AI limit reached ({monthly_limit} interactions)',
                    'current_usage': monthly_usage,
                    'monthly_limit': monthly_limit,
                    'upgrade_required': True
                }
            
            return {
                'can_use': True,
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'remaining_today': daily_limit - current_usage,
                'monthly_usage': monthly_usage,
                'monthly_limit': monthly_limit,
                'remaining_this_month': monthly_limit - monthly_usage
            }
            
        except Exception as e:
            logger.error(f"Error checking usage limits: {str(e)}")
            return {
                'can_use': False,
                'reason': 'error',
                'message': 'Error checking usage limits',
                'error': str(e)
            }
    
    def get_usage_stats(self, user: UserProfile) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics for a user.
        
        Args:
            user: UserProfile instance
            
        Returns:
            Dictionary with usage statistics
        """
        try:
            stats = {
                'subscription_plan': user.subscription_plan,
                'subscription_status': user.subscription_status,
                'features': user.subscription_features
            }
            
            if hasattr(user, 'subscription'):
                subscription = user.subscription
                subscription.reset_daily_usage()
                
                stats.update({
                    'usage_today': subscription.ai_usage_today,
                    'usage_this_period': subscription.ai_usage_this_period,
                    'daily_limit': subscription.plan.ai_daily_limit,
                    'monthly_limit': subscription.plan.ai_monthly_limit,
                    'remaining_today': max(0, subscription.plan.ai_daily_limit - subscription.ai_usage_today),
                    'remaining_this_period': max(0, subscription.plan.ai_monthly_limit - subscription.ai_usage_this_period),
                    'current_period_start': subscription.current_period_start,
                    'current_period_end': subscription.current_period_end,
                    'days_until_renewal': subscription.days_until_renewal()
                })
                
                # Get usage breakdown by agent type from AIUsageMetric
                from ai_assistant.models import AIUsageMetric
                
                # Daily breakdown
                today = timezone.now().date()
                daily_breakdown = AIUsageMetric.objects.filter(
                    user=user,
                    created_at__date=today
                ).values('agent_type').annotate(
                    count=Count('id'),
                    tokens=Sum('tokens_used')
                )
                
                stats['daily_breakdown'] = list(daily_breakdown)
                
                # Period breakdown
                period_breakdown = AIUsageMetric.objects.filter(
                    user=user,
                    created_at__gte=subscription.current_period_start
                ).values('agent_type').annotate(
                    count=Count('id'),
                    tokens=Sum('tokens_used'),
                    cost=Sum('cost')
                )
                
                stats['period_breakdown'] = list(period_breakdown)
                
            else:
                # Free tier stats
                cache_key = self.get_usage_key(str(user.supabase_user_id))
                current_usage = cache.get(cache_key, 0)
                
                stats.update({
                    'usage_today': current_usage,
                    'usage_this_period': current_usage,
                    'daily_limit': settings.AI_RATE_LIMIT_FREE,
                    'monthly_limit': 50,
                    'remaining_today': max(0, settings.AI_RATE_LIMIT_FREE - current_usage),
                    'remaining_this_period': max(0, 50 - current_usage)
                })
            
            # Calculate usage percentage
            if stats['daily_limit'] > 0:
                stats['daily_usage_percentage'] = round(
                    (stats['usage_today'] / stats['daily_limit']) * 100, 1
                )
            else:
                stats['daily_usage_percentage'] = 0
            
            if stats['monthly_limit'] > 0:
                stats['monthly_usage_percentage'] = round(
                    (stats['usage_this_period'] / stats['monthly_limit']) * 100, 1
                )
            else:
                stats['monthly_usage_percentage'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            return {
                'error': str(e),
                'subscription_plan': 'free',
                'usage_today': 0,
                'daily_limit': settings.AI_RATE_LIMIT_FREE
            }
    
    def reset_daily_usage(self) -> None:
        """Reset daily usage counters for all users (scheduled task)"""
        try:
            today = timezone.now().date()
            
            # Reset all subscription daily counters
            UserSubscription.objects.filter(
                last_usage_reset_date__lt=today
            ).update(
                ai_usage_today=0,
                last_usage_reset_date=today
            )
            
            logger.info(f"Daily usage reset completed for {today}")
            
        except Exception as e:
            logger.error(f"Error resetting daily usage: {str(e)}")
    
    def reset_period_usage(self) -> None:
        """Reset period usage counters for expired periods (scheduled task)"""
        try:
            now = timezone.now()
            
            # Find subscriptions with expired periods
            expired_subscriptions = UserSubscription.objects.filter(
                current_period_end__lt=now,
                ai_usage_this_period__gt=0
            )
            
            for subscription in expired_subscriptions:
                # Calculate new period dates
                if subscription.billing_period == 'yearly':
                    new_period_end = subscription.current_period_end + timedelta(days=365)
                else:
                    new_period_end = subscription.current_period_end + timedelta(days=30)
                
                # Update subscription
                subscription.current_period_start = subscription.current_period_end
                subscription.current_period_end = new_period_end
                subscription.ai_usage_this_period = 0
                subscription.save()
                
                logger.info(f"Period usage reset for user {subscription.user.email}")
            
        except Exception as e:
            logger.error(f"Error resetting period usage: {str(e)}")
    
    def get_next_reset_time(self) -> datetime:
        """Get the time when daily usage will reset"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        return timezone.make_aware(
            datetime.combine(tomorrow, datetime.min.time())
        )
    
    def get_upgrade_message(self, user: UserProfile, agent_type: str) -> str:
        """
        Get appropriate upgrade message based on user's current plan.
        
        Args:
            user: UserProfile instance
            agent_type: Type of AI agent
            
        Returns:
            Upgrade message string
        """
        plan = user.subscription_plan
        
        if plan == 'free':
            return (
                "Upgrade to Premium for 50 daily AI interactions, "
                "or Enterprise for 200 daily interactions and advanced features."
            )
        elif plan == 'premium':
            return (
                "Upgrade to Enterprise for 200 daily AI interactions, "
                "custom models, and API access."
            )
        else:
            return "You've reached your daily AI interaction limit."