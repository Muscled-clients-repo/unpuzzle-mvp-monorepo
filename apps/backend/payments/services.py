"""
Stripe payment services for handling payment operations.
"""
import stripe
import logging
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from typing import Dict, Optional, Tuple
from .models import (
    PaymentIntent, PaymentTransaction, StripeCustomer, 
    WebhookEvent, PaymentStatus
)
from enrollments.models import Enrollment

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class StripePaymentService:
    """Service for handling Stripe payment operations"""

    @staticmethod
    def get_or_create_customer(user_profile) -> StripeCustomer:
        """Get or create a Stripe customer for a user"""
        try:
            # Try to get existing customer
            stripe_customer = StripeCustomer.objects.get(user=user_profile)
            return stripe_customer
        except StripeCustomer.DoesNotExist:
            # Create new Stripe customer
            try:
                customer = stripe.Customer.create(
                    email=user_profile.email,
                    name=user_profile.full_name or user_profile.email,
                    metadata={
                        'user_id': str(user_profile.supabase_user_id),
                        'user_email': user_profile.email,
                    }
                )
                
                # Create local customer record
                stripe_customer = StripeCustomer.objects.create(
                    user=user_profile,
                    stripe_customer_id=customer.id,
                    email=user_profile.email,
                    name=user_profile.full_name or user_profile.email,
                )
                
                logger.info(f"Created new Stripe customer {customer.id} for user {user_profile.email}")
                return stripe_customer
                
            except stripe.error.StripeError as e:
                logger.error(f"Failed to create Stripe customer for user {user_profile.email}: {str(e)}")
                raise

    @staticmethod
    def create_payment_intent(
        user_profile, 
        course, 
        amount: Decimal,
        currency: str = 'usd',
        metadata: Dict = None
    ) -> Tuple[PaymentIntent, str]:
        """Create a payment intent for course purchase"""
        
        if metadata is None:
            metadata = {}

        try:
            # Get or create Stripe customer
            stripe_customer = StripePaymentService.get_or_create_customer(user_profile)
            
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                customer=stripe_customer.stripe_customer_id,
                metadata={
                    'user_id': str(user_profile.supabase_user_id),
                    'course_id': str(course.id),
                    'user_email': user_profile.email,
                    'course_title': course.title,
                    **metadata
                },
                automatic_payment_methods={'enabled': True},
            )
            
            # Create local payment intent record
            payment_intent = PaymentIntent.objects.create(
                stripe_payment_intent_id=intent.id,
                user=user_profile,
                course=course,
                amount=amount,
                currency=currency,
                status=PaymentStatus.PENDING,
                client_secret=intent.client_secret,
                stripe_customer_id=stripe_customer.stripe_customer_id,
                metadata=metadata
            )
            
            logger.info(f"Created payment intent {intent.id} for user {user_profile.email} and course {course.title}")
            return payment_intent, intent.client_secret
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {str(e)}")
            raise

    @staticmethod
    def confirm_payment_intent(payment_intent_id: str) -> Optional[PaymentIntent]:
        """Confirm a payment intent and update local record"""
        try:
            # Get Stripe payment intent
            stripe_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Get local payment intent
            payment_intent = PaymentIntent.objects.get(
                stripe_payment_intent_id=payment_intent_id
            )
            print(stripe_intent.status)
            
            # Update status based on Stripe status
            if stripe_intent.status == 'succeeded':
                payment_intent.status = PaymentStatus.COMPLETED
                payment_intent.paid_at = timezone.now()
                
                print(stripe_intent.latest_charge)
                # Create transaction record  
                if stripe_intent.latest_charge:
                    charge = stripe.Charge.retrieve(stripe_intent.latest_charge)
                    
                    transaction = PaymentTransaction.objects.create(
                        payment_intent=payment_intent,
                        stripe_charge_id=charge.id,
                        amount=Decimal(str(charge.amount / 100)),
                        currency=charge.currency,
                        net_amount=Decimal(str(charge.amount / 100)) - Decimal(str(charge.application_fee_amount / 100 if charge.application_fee_amount else 0)),
                        stripe_fee=Decimal(str(charge.application_fee_amount / 100 if charge.application_fee_amount else 0)),
                        payment_method_details=charge.payment_method_details,
                        receipt_url=charge.receipt_url,
                        status=PaymentStatus.COMPLETED
                    )
                    
                    # Create enrollment
                    enrollment, created = Enrollment.objects.get_or_create(
                        user=payment_intent.user,
                        course=payment_intent.course,
                        defaults={
                            'status': 'active',
                            'enrolled_at': timezone.now(),
                        }
                    )
                    
                    transaction.enrollment = enrollment
                    transaction.enrollment_created = created
                    transaction.save()
                    
                    logger.info(f"Payment succeeded for {payment_intent.user.email} - course {payment_intent.course.title}")
                
            elif stripe_intent.status in ['requires_payment_method', 'canceled']:
                payment_intent.status = PaymentStatus.FAILED
            elif stripe_intent.status in ['processing']:
                payment_intent.status = PaymentStatus.PROCESSING
            
            payment_intent.save()
            return payment_intent
            
        except PaymentIntent.DoesNotExist:
            logger.error(f"Payment intent {payment_intent_id} not found in database")
            return None
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment intent {payment_intent_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error confirming payment intent {payment_intent_id}: {str(e)}")
            return None

    @staticmethod
    def create_refund(transaction_id: str, amount: Optional[Decimal] = None, reason: str = '') -> Optional[Dict]:
        """Create a refund for a transaction"""
        try:
            transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
            
            refund_amount = amount or transaction.amount
            
            # Create Stripe refund
            refund = stripe.Refund.create(
                charge=transaction.stripe_charge_id,
                amount=int(refund_amount * 100),  # Convert to cents
                reason='requested_by_customer' if not reason else 'duplicate',
                metadata={
                    'transaction_id': str(transaction.transaction_id),
                    'user_id': str(transaction.payment_intent.user.supabase_user_id),
                    'course_id': str(transaction.payment_intent.course.id),
                }
            )
            
            # Create local refund record
            from .models import PaymentRefund
            payment_refund = PaymentRefund.objects.create(
                transaction=transaction,
                stripe_refund_id=refund.id,
                amount=refund_amount,
                currency=transaction.currency,
                reason=reason,
                status='succeeded' if refund.status == 'succeeded' else 'pending'
            )
            
            # Update enrollment if full refund
            if refund_amount == transaction.amount and transaction.enrollment:
                transaction.enrollment.status = 'cancelled'
                transaction.enrollment.save()
            
            logger.info(f"Created refund {refund.id} for transaction {transaction_id}")
            return {
                'refund_id': payment_refund.refund_id,
                'stripe_refund_id': refund.id,
                'amount': refund_amount,
                'status': payment_refund.status
            }
            
        except PaymentTransaction.DoesNotExist:
            logger.error(f"Transaction {transaction_id} not found")
            return None
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund for transaction {transaction_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating refund for transaction {transaction_id}: {str(e)}")
            return None

    @staticmethod
    def handle_webhook_event(event_data: Dict) -> bool:
        """Handle Stripe webhook events"""
        event_id = event_data.get('id')
        event_type = event_data.get('type')
        
        if not event_id or not event_type:
            logger.error("Invalid webhook event data")
            return False
        
        
        # Check if event already processed
        webhook_event, created = WebhookEvent.objects.get_or_create(
            stripe_event_id=event_id,
            defaults={
                'event_type': event_type,
                'event_data': event_data,
                'processed': False
            }
        )
        
        print("Hello world")
        
        if not created and webhook_event.processed:
            logger.info(f"Webhook event {event_id} already processed")
            return True
        
        
        try:
            # Process different event types
            if event_type == 'payment_intent.succeeded':
                payment_intent_id = event_data['data']['object']['id']
                print(payment_intent_id)
                StripePaymentService.confirm_payment_intent(payment_intent_id)
            
            elif event_type == 'payment_intent.payment_failed':
                payment_intent_id = event_data['data']['object']['id']
                try:
                    payment_intent = PaymentIntent.objects.get(
                        stripe_payment_intent_id=payment_intent_id
                    )
                    payment_intent.status = PaymentStatus.FAILED
                    payment_intent.save()
                    logger.info(f"Payment failed for intent {payment_intent_id}")
                except PaymentIntent.DoesNotExist:
                    logger.warning(f"Payment intent {payment_intent_id} not found for failed payment")
            
            elif event_type == 'charge.dispute.created':
                logger.warning(f"Dispute created for event {event_id}")
                # Handle dispute logic here
                
            # Mark webhook as processed
            webhook_event.processed = True
            webhook_event.processed_at = timezone.now()
            webhook_event.save()
            
            logger.info(f"Successfully processed webhook event {event_id} of type {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing webhook event {event_id}: {str(e)}")
            webhook_event.processing_error = str(e)
            webhook_event.retry_count += 1
            webhook_event.save()
            return False


class PaymentValidationService:
    """Service for validating payments and course access"""
    
    @staticmethod
    def validate_course_enrollment(user_profile, course) -> Dict:
        """Validate if user can enroll in a course (both free and paid)"""
        
        # Check if course exists and is published
        if not course.is_published:
            return {
                'valid': False,
                'error': 'Course is not available for enrollment'
            }
        
        # Check if user is already enrolled
        existing_enrollment = Enrollment.objects.filter(
            user=user_profile,
            course=course,
            status='active'
        ).exists()
        
        if existing_enrollment:
            return {
                'valid': False,
                'error': 'You are already enrolled in this course'
            }
        
        # For paid courses, check for pending payments
        if not course.is_free and course.price > 0:
            pending_payment = PaymentIntent.objects.filter(
                user=user_profile,
                course=course,
                status__in=[PaymentStatus.PENDING, PaymentStatus.PROCESSING]
            ).exists()
            
            if pending_payment:
                return {
                    'valid': False,
                    'error': 'You have a pending payment for this course'
                }
        
        return {
            'valid': True,
            'is_free': course.is_free or course.price == 0,
            'amount': course.discount_price or course.price,
            'currency': course.currency
        }

    @staticmethod
    def validate_course_purchase(user_profile, course) -> Dict:
        """Validate if user can purchase a course (paid courses only)"""
        
        # First run general enrollment validation
        enrollment_validation = PaymentValidationService.validate_course_enrollment(user_profile, course)
        if not enrollment_validation['valid']:
            return enrollment_validation
        
        # Check if course is free (shouldn't create payment intent for free courses)
        if course.is_free or course.price == 0:
            return {
                'valid': False,
                'error': 'This course is free and does not require payment'
            }
        
        return {
            'valid': True,
            'amount': course.discount_price or course.price,
            'currency': course.currency
        }

    @staticmethod
    def get_user_payment_history(user_profile) -> Dict:
        """Get user's payment history"""
        
        payment_intents = PaymentIntent.objects.filter(
            user=user_profile
        ).select_related('course').order_by('-created_at')
        
        transactions = PaymentTransaction.objects.filter(
            payment_intent__user=user_profile
        ).select_related('payment_intent__course', 'enrollment').order_by('-created_at')
        
        return {
            'payment_intents': payment_intents,
            'transactions': transactions,
            'total_spent': sum(t.amount for t in transactions if t.status == PaymentStatus.COMPLETED)
        }