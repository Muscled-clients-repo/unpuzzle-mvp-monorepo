"""
Core subscription management service.
"""
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Optional, Dict, Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import (
    UserProfile,
    SubscriptionPlan,
    UserSubscription,
    SubscriptionHistory,
    SubscriptionStatus,
    SubscriptionAction,
    BillingPeriod
)
from .stripe_subscription import StripeSubscriptionService

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Handle subscription lifecycle management"""
    
    def __init__(self):
        self.stripe_service = StripeSubscriptionService()
    
    @transaction.atomic
    def create_subscription(
        self,
        user: UserProfile,
        plan_id: str,
        billing_period: str = 'monthly',
        payment_method_id: Optional[str] = None,
        trial: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new subscription for a user.
        
        Args:
            user: UserProfile instance
            plan_id: ID of the subscription plan
            billing_period: 'monthly' or 'yearly'
            payment_method_id: Stripe payment method ID
            trial: Whether to start with a trial period
            
        Returns:
            Dictionary with subscription details and status
        """
        try:
            # Check if user already has a subscription
            if hasattr(user, 'subscription'):
                return {
                    'success': False,
                    'error': 'User already has an active subscription',
                    'code': 'SUBSCRIPTION_EXISTS'
                }
            
            # Get the plan
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Invalid subscription plan',
                    'code': 'INVALID_PLAN'
                }
            
            # Calculate dates
            now = timezone.now()
            if billing_period == 'yearly':
                period_end = now + timedelta(days=365)
            else:
                period_end = now + timedelta(days=30)
            
            # Handle trial period
            trial_end = None
            status = SubscriptionStatus.ACTIVE
            if trial and plan.trial_days > 0:
                trial_end = now + timedelta(days=plan.trial_days)
                status = SubscriptionStatus.TRIALING
            
            # Create Stripe subscription if not free plan
            stripe_subscription_id = None
            stripe_customer_id = None
            if plan_id != 'free':
                stripe_result = self.stripe_service.create_subscription(
                    user=user,
                    price_id=plan.get_stripe_price_id(billing_period),
                    payment_method_id=payment_method_id,
                    trial_days=plan.trial_days if trial else 0
                )
                
                if not stripe_result['success']:
                    return stripe_result
                
                stripe_subscription_id = stripe_result['subscription_id']
                stripe_customer_id = stripe_result['customer_id']
            
            # Create subscription record
            subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                status=status,
                billing_period=billing_period,
                stripe_subscription_id=stripe_subscription_id,
                stripe_customer_id=stripe_customer_id,
                current_period_start=now,
                current_period_end=period_end,
                trial_start=now if trial else None,
                trial_end=trial_end
            )
            
            # Log subscription history
            SubscriptionHistory.objects.create(
                user=user,
                to_plan=plan,
                action=SubscriptionAction.TRIAL_START if trial else SubscriptionAction.CREATE,
                amount=plan.price_monthly if billing_period == 'monthly' else plan.price_yearly,
                metadata={
                    'billing_period': billing_period,
                    'trial': trial,
                    'stripe_subscription_id': stripe_subscription_id
                }
            )
            
            logger.info(f"Subscription created for user {user.email}: {plan_id} ({billing_period})")
            
            return {
                'success': True,
                'subscription': subscription,
                'message': 'Subscription created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'SUBSCRIPTION_ERROR'
            }
    
    @transaction.atomic
    def upgrade_subscription(
        self,
        user: UserProfile,
        new_plan_id: str,
        billing_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upgrade user's subscription to a higher tier.
        
        Args:
            user: UserProfile instance
            new_plan_id: ID of the new subscription plan
            billing_period: Optional new billing period
            
        Returns:
            Dictionary with upgrade status
        """
        try:
            if not hasattr(user, 'subscription'):
                return {
                    'success': False,
                    'error': 'No active subscription found',
                    'code': 'NO_SUBSCRIPTION'
                }
            
            subscription = user.subscription
            old_plan = subscription.plan
            
            # Get new plan
            try:
                new_plan = SubscriptionPlan.objects.get(id=new_plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Invalid subscription plan',
                    'code': 'INVALID_PLAN'
                }
            
            # Check if it's actually an upgrade
            if new_plan.price_monthly <= old_plan.price_monthly:
                return {
                    'success': False,
                    'error': 'New plan must be higher tier than current plan',
                    'code': 'NOT_UPGRADE'
                }
            
            # Update billing period if provided
            if billing_period:
                subscription.billing_period = billing_period
            
            # Update Stripe subscription
            if subscription.stripe_subscription_id:
                stripe_result = self.stripe_service.update_subscription(
                    subscription_id=subscription.stripe_subscription_id,
                    new_price_id=new_plan.get_stripe_price_id(subscription.billing_period)
                )
                
                if not stripe_result['success']:
                    return stripe_result
            
            # Update subscription
            subscription.plan = new_plan
            subscription.save()
            
            # Log history
            SubscriptionHistory.objects.create(
                user=user,
                from_plan=old_plan,
                to_plan=new_plan,
                action=SubscriptionAction.UPGRADE,
                metadata={
                    'billing_period': subscription.billing_period
                }
            )
            
            logger.info(f"Subscription upgraded for {user.email}: {old_plan.id} -> {new_plan_id}")
            
            return {
                'success': True,
                'subscription': subscription,
                'message': 'Subscription upgraded successfully'
            }
            
        except Exception as e:
            logger.error(f"Error upgrading subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'UPGRADE_ERROR'
            }
    
    @transaction.atomic
    def downgrade_subscription(
        self,
        user: UserProfile,
        new_plan_id: str
    ) -> Dict[str, Any]:
        """
        Downgrade subscription to a lower tier (effective at period end).
        
        Args:
            user: UserProfile instance
            new_plan_id: ID of the new subscription plan
            
        Returns:
            Dictionary with downgrade status
        """
        try:
            if not hasattr(user, 'subscription'):
                return {
                    'success': False,
                    'error': 'No active subscription found',
                    'code': 'NO_SUBSCRIPTION'
                }
            
            subscription = user.subscription
            old_plan = subscription.plan
            
            # Get new plan
            try:
                new_plan = SubscriptionPlan.objects.get(id=new_plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Invalid subscription plan',
                    'code': 'INVALID_PLAN'
                }
            
            # Schedule downgrade for period end
            # Store the pending plan in metadata
            subscription.metadata['pending_plan_id'] = new_plan_id
            subscription.metadata['pending_action'] = 'downgrade'
            subscription.save()
            
            # If Stripe subscription exists, schedule the change
            if subscription.stripe_subscription_id:
                stripe_result = self.stripe_service.schedule_subscription_change(
                    subscription_id=subscription.stripe_subscription_id,
                    new_price_id=new_plan.get_stripe_price_id(subscription.billing_period),
                    effective_date=subscription.current_period_end
                )
                
                if not stripe_result['success']:
                    return stripe_result
            
            # Log history
            SubscriptionHistory.objects.create(
                user=user,
                from_plan=old_plan,
                to_plan=new_plan,
                action=SubscriptionAction.DOWNGRADE,
                metadata={
                    'scheduled_for': subscription.current_period_end.isoformat(),
                    'immediate': False
                }
            )
            
            logger.info(f"Subscription downgrade scheduled for {user.email}: {old_plan.id} -> {new_plan_id}")
            
            return {
                'success': True,
                'subscription': subscription,
                'message': f'Subscription will be downgraded to {new_plan.display_name} at the end of current billing period',
                'effective_date': subscription.current_period_end
            }
            
        except Exception as e:
            logger.error(f"Error downgrading subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'DOWNGRADE_ERROR'
            }
    
    @transaction.atomic
    def cancel_subscription(
        self,
        user: UserProfile,
        reason: str = '',
        immediate: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel user's subscription.
        
        Args:
            user: UserProfile instance
            reason: Cancellation reason
            immediate: If True, cancel immediately; otherwise at period end
            
        Returns:
            Dictionary with cancellation status
        """
        try:
            if not hasattr(user, 'subscription'):
                return {
                    'success': False,
                    'error': 'No active subscription found',
                    'code': 'NO_SUBSCRIPTION'
                }
            
            subscription = user.subscription
            
            # Cancel Stripe subscription
            if subscription.stripe_subscription_id:
                stripe_result = self.stripe_service.cancel_subscription(
                    subscription_id=subscription.stripe_subscription_id,
                    immediate=immediate
                )
                
                if not stripe_result['success']:
                    return stripe_result
            
            # Update subscription
            if immediate:
                subscription.status = SubscriptionStatus.CANCELED
                subscription.canceled_at = timezone.now()
            else:
                subscription.cancel_at_period_end = True
                subscription.canceled_at = timezone.now()
            
            subscription.save()
            
            # Log history
            SubscriptionHistory.objects.create(
                user=user,
                from_plan=subscription.plan,
                action=SubscriptionAction.CANCEL,
                reason=reason,
                metadata={
                    'immediate': immediate,
                    'cancel_at_period_end': not immediate
                }
            )
            
            logger.info(f"Subscription canceled for {user.email} (immediate: {immediate})")
            
            return {
                'success': True,
                'subscription': subscription,
                'message': 'Subscription canceled successfully',
                'effective_date': timezone.now() if immediate else subscription.current_period_end
            }
            
        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'CANCEL_ERROR'
            }
    
    @transaction.atomic
    def resume_subscription(self, user: UserProfile) -> Dict[str, Any]:
        """
        Resume a canceled subscription (if not past period end).
        
        Args:
            user: UserProfile instance
            
        Returns:
            Dictionary with resume status
        """
        try:
            if not hasattr(user, 'subscription'):
                return {
                    'success': False,
                    'error': 'No subscription found',
                    'code': 'NO_SUBSCRIPTION'
                }
            
            subscription = user.subscription
            
            # Check if subscription can be resumed
            if not subscription.cancel_at_period_end:
                return {
                    'success': False,
                    'error': 'Subscription is not scheduled for cancellation',
                    'code': 'NOT_CANCELABLE'
                }
            
            if subscription.current_period_end < timezone.now():
                return {
                    'success': False,
                    'error': 'Subscription period has already ended',
                    'code': 'PERIOD_ENDED'
                }
            
            # Resume Stripe subscription
            if subscription.stripe_subscription_id:
                stripe_result = self.stripe_service.resume_subscription(
                    subscription_id=subscription.stripe_subscription_id
                )
                
                if not stripe_result['success']:
                    return stripe_result
            
            # Update subscription
            subscription.cancel_at_period_end = False
            subscription.canceled_at = None
            subscription.save()
            
            # Log history
            SubscriptionHistory.objects.create(
                user=user,
                to_plan=subscription.plan,
                action=SubscriptionAction.RESUME,
                metadata={
                    'resumed_at': timezone.now().isoformat()
                }
            )
            
            logger.info(f"Subscription resumed for {user.email}")
            
            return {
                'success': True,
                'subscription': subscription,
                'message': 'Subscription resumed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error resuming subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'RESUME_ERROR'
            }
    
    def check_subscription_status(self, user: UserProfile) -> Dict[str, Any]:
        """
        Check and update subscription status.
        
        Args:
            user: UserProfile instance
            
        Returns:
            Dictionary with subscription status
        """
        try:
            if not hasattr(user, 'subscription'):
                return {
                    'has_subscription': False,
                    'plan': 'free',
                    'status': 'none'
                }
            
            subscription = user.subscription
            
            # Check if subscription has expired
            if subscription.is_expired() and subscription.status == SubscriptionStatus.ACTIVE:
                subscription.status = SubscriptionStatus.EXPIRED
                subscription.save()
                
                # Log expiration
                SubscriptionHistory.objects.create(
                    user=user,
                    from_plan=subscription.plan,
                    action=SubscriptionAction.EXPIRE
                )
            
            # Check if trial has ended
            if (subscription.status == SubscriptionStatus.TRIALING and 
                subscription.trial_end and 
                subscription.trial_end < timezone.now()):
                
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.save()
                
                # Log trial end
                SubscriptionHistory.objects.create(
                    user=user,
                    to_plan=subscription.plan,
                    action=SubscriptionAction.TRIAL_END
                )
            
            return {
                'has_subscription': True,
                'plan': subscription.plan_id,
                'plan_name': subscription.plan.display_name,
                'status': subscription.status,
                'is_active': subscription.is_active(),
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'days_until_renewal': subscription.days_until_renewal(),
                'ai_usage_today': subscription.ai_usage_today,
                'ai_usage_this_period': subscription.ai_usage_this_period,
                'ai_daily_limit': subscription.plan.ai_daily_limit,
                'ai_monthly_limit': subscription.plan.ai_monthly_limit
            }
            
        except Exception as e:
            logger.error(f"Error checking subscription status: {str(e)}")
            return {
                'has_subscription': False,
                'error': str(e)
            }
    
    def apply_trial(self, user: UserProfile, plan_id: str = 'premium', days: int = 14) -> Dict[str, Any]:
        """
        Start a trial period for a new user.
        
        Args:
            user: UserProfile instance
            plan_id: Plan to trial
            days: Trial duration
            
        Returns:
            Dictionary with trial status
        """
        try:
            # Check if user already has a subscription
            if hasattr(user, 'subscription'):
                return {
                    'success': False,
                    'error': 'User already has a subscription',
                    'code': 'SUBSCRIPTION_EXISTS'
                }
            
            # Create trial subscription
            return self.create_subscription(
                user=user,
                plan_id=plan_id,
                billing_period='monthly',
                trial=True
            )
            
        except Exception as e:
            logger.error(f"Error applying trial: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'TRIAL_ERROR'
            }
    
    def handle_payment_failed(
        self,
        subscription_id: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Handle failed payment for a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            retry_count: Number of retry attempts
            
        Returns:
            Dictionary with handling status
        """
        try:
            subscription = UserSubscription.objects.get(
                stripe_subscription_id=subscription_id
            )
            
            # Update status based on retry count
            if retry_count >= 3:
                subscription.status = SubscriptionStatus.PAST_DUE
            
            subscription.save()
            
            # Log payment failure
            SubscriptionHistory.objects.create(
                user=subscription.user,
                from_plan=subscription.plan,
                action=SubscriptionAction.PAYMENT_FAILED,
                metadata={
                    'retry_count': retry_count,
                    'subscription_id': subscription_id
                }
            )
            
            logger.warning(f"Payment failed for subscription {subscription_id} (retry: {retry_count})")
            
            return {
                'success': True,
                'subscription': subscription,
                'status': subscription.status
            }
            
        except UserSubscription.DoesNotExist:
            logger.error(f"Subscription not found: {subscription_id}")
            return {
                'success': False,
                'error': 'Subscription not found',
                'code': 'NOT_FOUND'
            }
        except Exception as e:
            logger.error(f"Error handling payment failure: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'PAYMENT_ERROR'
            }