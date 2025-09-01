"""
Stripe subscription integration service.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeSubscriptionService:
    """Handle Stripe subscription operations"""
    
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata
            
        Returns:
            Dictionary with customer creation result
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name or email,
                metadata=metadata or {}
            )
            
            return {
                'success': True,
                'customer_id': customer.id,
                'customer': customer
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'STRIPE_ERROR'
            }
    
    def create_subscription(
        self,
        user,
        price_id: str,
        payment_method_id: Optional[str] = None,
        trial_days: int = 0
    ) -> Dict[str, Any]:
        """
        Create a Stripe subscription.
        
        Args:
            user: UserProfile instance
            price_id: Stripe price ID
            payment_method_id: Payment method ID
            trial_days: Trial period in days
            
        Returns:
            Dictionary with subscription creation result
        """
        try:
            # Get or create Stripe customer
            from payments.models import StripeCustomer
            
            try:
                stripe_customer = StripeCustomer.objects.get(user=user)
                customer_id = stripe_customer.stripe_customer_id
            except StripeCustomer.DoesNotExist:
                # Create new customer
                customer_result = self.create_customer(
                    email=user.email,
                    name=user.full_name,
                    metadata={'user_id': str(user.supabase_user_id)}
                )
                
                if not customer_result['success']:
                    return customer_result
                
                customer_id = customer_result['customer_id']
                
                # Save customer reference
                StripeCustomer.objects.create(
                    user=user,
                    stripe_customer_id=customer_id
                )
            
            # Attach payment method if provided
            if payment_method_id:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=customer_id
                )
                
                # Set as default payment method
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={'default_payment_method': payment_method_id}
                )
            
            # Create subscription
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'metadata': {
                    'user_id': str(user.supabase_user_id),
                    'user_email': user.email
                }
            }
            
            # Add trial period if specified
            if trial_days > 0:
                subscription_data['trial_period_days'] = trial_days
            
            # If no payment method and not trial, require payment method
            if not payment_method_id and trial_days == 0:
                subscription_data['payment_behavior'] = 'default_incomplete'
                subscription_data['expand'] = ['latest_invoice.payment_intent']
            
            subscription = stripe.Subscription.create(**subscription_data)
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'customer_id': customer_id,
                'status': subscription.status,
                'subscription': subscription
            }
            
        except stripe.error.CardError as e:
            logger.error(f"Card error creating subscription: {str(e)}")
            return {
                'success': False,
                'error': 'Your card was declined. Please check your payment details.',
                'code': 'CARD_ERROR'
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'STRIPE_ERROR'
            }
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'SYSTEM_ERROR'
            }
    
    def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_behavior: str = 'create_prorations'
    ) -> Dict[str, Any]:
        """
        Update an existing Stripe subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New price ID
            proration_behavior: How to handle proration
            
        Returns:
            Dictionary with update result
        """
        try:
            # Retrieve current subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Update subscription item with new price
            stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': new_price_id,
                }],
                proration_behavior=proration_behavior
            )
            
            return {
                'success': True,
                'message': 'Subscription updated successfully'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'STRIPE_ERROR'
            }
    
    def cancel_subscription(
        self,
        subscription_id: str,
        immediate: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel a Stripe subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            immediate: If True, cancel immediately; otherwise at period end
            
        Returns:
            Dictionary with cancellation result
        """
        try:
            if immediate:
                # Cancel immediately
                stripe.Subscription.delete(subscription_id)
            else:
                # Cancel at period end
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            return {
                'success': True,
                'message': 'Subscription canceled successfully'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'STRIPE_ERROR'
            }
    
    def resume_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Resume a subscription that was set to cancel at period end.
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Dictionary with resume result
        """
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            
            return {
                'success': True,
                'message': 'Subscription resumed successfully'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error resuming subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'STRIPE_ERROR'
            }
    
    def schedule_subscription_change(
        self,
        subscription_id: str,
        new_price_id: str,
        effective_date: datetime
    ) -> Dict[str, Any]:
        """
        Schedule a subscription change for a future date.
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New price ID
            effective_date: When the change should take effect
            
        Returns:
            Dictionary with scheduling result
        """
        try:
            # Create a subscription schedule
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            stripe.SubscriptionSchedule.create(
                from_subscription=subscription_id,
                phases=[
                    {
                        'items': [{'price': new_price_id}],
                        'start_date': int(effective_date.timestamp()),
                    }
                ]
            )
            
            return {
                'success': True,
                'message': 'Subscription change scheduled successfully'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error scheduling change: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'STRIPE_ERROR'
            }
    
    def add_payment_method(
        self,
        customer_id: str,
        payment_method_id: str,
        set_default: bool = True
    ) -> Dict[str, Any]:
        """
        Add a payment method to a customer.
        
        Args:
            customer_id: Stripe customer ID
            payment_method_id: Payment method ID
            set_default: Whether to set as default
            
        Returns:
            Dictionary with result
        """
        try:
            # Attach payment method
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            # Set as default if requested
            if set_default:
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={'default_payment_method': payment_method_id}
                )
            
            return {
                'success': True,
                'message': 'Payment method added successfully'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error adding payment method: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'STRIPE_ERROR'
            }
    
    def list_payment_methods(self, customer_id: str) -> Dict[str, Any]:
        """
        List payment methods for a customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Dictionary with payment methods
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            
            return {
                'success': True,
                'payment_methods': payment_methods.data
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error listing payment methods: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'STRIPE_ERROR'
            }
    
    def get_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get invoices for a customer.
        
        Args:
            customer_id: Stripe customer ID
            limit: Number of invoices to retrieve
            
        Returns:
            Dictionary with invoices
        """
        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
            
            return {
                'success': True,
                'invoices': invoices.data
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting invoices: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'STRIPE_ERROR'
            }
    
    def get_upcoming_invoice(self, customer_id: str) -> Dict[str, Any]:
        """
        Get upcoming invoice for a customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Dictionary with upcoming invoice
        """
        try:
            upcoming = stripe.Invoice.upcoming(customer=customer_id)
            
            return {
                'success': True,
                'invoice': upcoming
            }
            
        except stripe.error.InvalidRequestError:
            # No upcoming invoice
            return {
                'success': True,
                'invoice': None
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting upcoming invoice: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'STRIPE_ERROR'
            }
    
    def handle_webhook_event(self, event: Dict) -> Dict[str, Any]:
        """
        Handle Stripe webhook events for subscriptions.
        
        Args:
            event: Stripe webhook event
            
        Returns:
            Dictionary with handling result
        """
        try:
            event_type = event['type']
            data = event['data']['object']
            
            # Import here to avoid circular import
            from accounts.models import UserSubscription
            from accounts.services.subscription_service import SubscriptionService
            
            service = SubscriptionService()
            
            if event_type == 'customer.subscription.created':
                # New subscription created
                logger.info(f"Subscription created: {data['id']}")
                
            elif event_type == 'customer.subscription.updated':
                # Subscription updated
                try:
                    subscription = UserSubscription.objects.get(
                        stripe_subscription_id=data['id']
                    )
                    
                    # Update status
                    subscription.status = data['status']
                    subscription.current_period_start = datetime.fromtimestamp(
                        data['current_period_start']
                    )
                    subscription.current_period_end = datetime.fromtimestamp(
                        data['current_period_end']
                    )
                    subscription.save()
                    
                except UserSubscription.DoesNotExist:
                    logger.warning(f"Subscription not found: {data['id']}")
                
            elif event_type == 'customer.subscription.deleted':
                # Subscription canceled
                try:
                    subscription = UserSubscription.objects.get(
                        stripe_subscription_id=data['id']
                    )
                    subscription.status = 'canceled'
                    subscription.save()
                    
                except UserSubscription.DoesNotExist:
                    logger.warning(f"Subscription not found: {data['id']}")
                
            elif event_type == 'invoice.payment_failed':
                # Payment failed
                subscription_id = data['subscription']
                service.handle_payment_failed(
                    subscription_id=subscription_id,
                    retry_count=data.get('attempt_count', 1)
                )
                
            elif event_type == 'invoice.payment_succeeded':
                # Payment succeeded
                try:
                    subscription = UserSubscription.objects.get(
                        stripe_subscription_id=data['subscription']
                    )
                    subscription.last_payment_amount = data['amount_paid'] / 100
                    subscription.last_payment_date = datetime.fromtimestamp(
                        data['created']
                    )
                    subscription.save()
                    
                except UserSubscription.DoesNotExist:
                    logger.warning(f"Subscription not found: {data['subscription']}")
            
            return {
                'success': True,
                'message': f'Webhook event {event_type} handled'
            }
            
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'WEBHOOK_ERROR'
            }