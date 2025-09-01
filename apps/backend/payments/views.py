"""
Payment views for handling Stripe payment operations.
"""
import json
import logging
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from accounts.models import UserProfile
from courses.models import Course
from .models import PaymentIntent, PaymentTransaction, PaymentRefund
from .serializers import (
    CreatePaymentIntentSerializer,
    PaymentIntentSerializer,
    PaymentTransactionSerializer,
    PaymentHistorySerializer,
    PaymentSuccessResponseSerializer,
    PaymentStatusResponseSerializer,
    RefundRequestSerializer,
    WebhookEventSerializer
)
from .services import StripePaymentService, PaymentValidationService

logger = logging.getLogger(__name__)


def get_user_profile(request):
    """Helper to get user profile from request"""
    if not hasattr(request, 'user_id') or not request.user_id:
        return None
    try:
        return UserProfile.objects.get(supabase_user_id=request.user_id)
    except UserProfile.DoesNotExist:
        return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll_in_course(request):
    """Smart enrollment: create payment intent for paid courses, direct enrollment for free courses"""
    
    # Get user profile
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Validate request data
    serializer = CreatePaymentIntentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    course_id = serializer.validated_data['course_id']
    currency = serializer.validated_data.get('currency', 'usd')
    metadata = serializer.validated_data.get('metadata', {})
    
    try:
        # Get course
        course = get_object_or_404(Course, id=course_id)
        
        # Validate enrollment
        validation = PaymentValidationService.validate_course_enrollment(user_profile, course)
        if not validation['valid']:
            return Response({'error': validation['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        # Debug: Log course price
        logger.error(f"DEBUG: Course price = {course.price}, type = {type(course.price)}")
        
        # Check if course is free (only check price)
        if course.price == 0:
            # Direct enrollment for free courses
            from enrollments.models import Enrollment
            enrollment, created = Enrollment.objects.get_or_create(
                user=user_profile,
                course=course,
                defaults={
                    'status': 'active',
                    'enrolled_at': timezone.now(),
                }
            )
            
            return Response({
                'enrollment_id': enrollment.id,
                'course_id': course.id,
                'course_title': course.title,
                'status': 'enrolled',
                'is_free': True,
                'message': 'Successfully enrolled in free course'
            }, status=status.HTTP_201_CREATED)
        
        else:
            # Create payment intent for paid courses
            payment_intent, client_secret = StripePaymentService.create_payment_intent(
                user_profile=user_profile,
                course=course,
                amount=validation['amount'],
                currency=currency,
                metadata=metadata
            )
            
            # Return payment response
            response_data = PaymentSuccessResponseSerializer({
                'payment_id': payment_intent.payment_id,
                'client_secret': client_secret,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'status': payment_intent.status
            }).data
            
            response_data.update({
                'course_id': course.id,
                'course_title': course.title,
                'is_free': False,
                'message': 'Payment intent created. Complete payment to enroll.'
            })
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating payment intent: {str(e)}")
        return Response({'error': 'Payment processing error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error in course enrollment: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """Create a payment intent for course purchase (legacy endpoint)"""
    
    # This endpoint now redirects to the smart enrollment endpoint
    return enroll_in_course(request)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_status(request, payment_id):
    """Get payment status by payment ID"""
    
    # Get user profile
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        # Get payment intent
        payment_intent = get_object_or_404(
            PaymentIntent, 
            payment_id=payment_id, 
            user=user_profile
        )
        
        # Check if there's a transaction
        transaction = None
        enrollment_created = False
        
        try:
            transaction = PaymentTransaction.objects.get(payment_intent=payment_intent)
            enrollment_created = transaction.enrollment_created
        except PaymentTransaction.DoesNotExist:
            pass
        
        # Return status
        response_data = PaymentStatusResponseSerializer({
            'payment_id': payment_intent.payment_id,
            'status': payment_intent.status,
            'amount': payment_intent.amount,
            'currency': payment_intent.currency,
            'paid_at': payment_intent.paid_at,
            'course_title': payment_intent.course.title,
            'enrollment_created': enrollment_created
        }).data
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except PaymentIntent.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_history(request):
    """Get user's payment history"""
    
    # Get user profile
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        # Get payment history
        history = PaymentValidationService.get_user_payment_history(user_profile)
        
        # Serialize response
        serializer = PaymentHistorySerializer(history)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching payment history: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request, payment_id):
    """Manually confirm a payment (for testing)"""
    
    # Get user profile
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        # Get payment intent
        payment_intent = get_object_or_404(
            PaymentIntent, 
            payment_id=payment_id, 
            user=user_profile
        )
        
        # Confirm payment
        updated_payment = StripePaymentService.confirm_payment_intent(
            payment_intent.stripe_payment_intent_id
        )
        
        if updated_payment:
            serializer = PaymentIntentSerializer(updated_payment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Payment confirmation failed'}, status=status.HTTP_400_BAD_REQUEST)
        
    except PaymentIntent.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error confirming payment: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Only admins should be able to create refunds
def create_refund(request):
    """Create a refund for a transaction"""
    
    # Get user profile
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if user has admin role
    if not hasattr(user_profile, 'role') or user_profile.role.name != 'admin':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    # Validate request data
    serializer = RefundRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    transaction_id = serializer.validated_data['transaction_id']
    amount = serializer.validated_data.get('amount')
    reason = serializer.validated_data.get('reason', '')
    
    try:
        # Create refund
        refund_result = StripePaymentService.create_refund(
            transaction_id=str(transaction_id),
            amount=amount,
            reason=reason
        )
        
        if refund_result:
            return Response(refund_result, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Refund creation failed'}, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error creating refund: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload in webhook: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature in webhook: {e}")
        return HttpResponse(status=400)
    
    try:
        # Handle the event
        success = StripePaymentService.handle_webhook_event(event)
        
        if success:
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=500)
            
    except Exception as e:
        logger.error(f"Error handling webhook event: {str(e)}")
        return HttpResponse(status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_stripe_publishable_key(request):
    """Get Stripe publishable key for frontend"""
    
    return Response({
        'publishable_key': settings.STRIPE_PUBLISHABLE_KEY
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])  # No authentication for testing
def test_enroll_in_course(request):
    """Test enrollment endpoint without authentication - FOR TESTING ONLY"""
    
    return Response({
        'status': 'success',
        'message': 'Test endpoint working - authentication bypassed',
        'request_data': request.data,
        'content_type': request.content_type,
        'method': request.method,
        'cookies': dict(request.COOKIES),
        'auth_header': request.META.get('HTTP_AUTHORIZATION', 'Not provided'),
    }, status=status.HTTP_200_OK)


# Admin views for payment management

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_get_all_transactions(request):
    """Get all payment transactions (admin only)"""
    
    # Get user profile
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if user has admin role
    if not hasattr(user_profile, 'role') or user_profile.role.name != 'admin':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Get all transactions with pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        transactions = PaymentTransaction.objects.select_related(
            'payment_intent__user', 
            'payment_intent__course'
        ).order_by('-created_at')[start:end]
        
        total_count = PaymentTransaction.objects.count()
        
        serializer = PaymentTransactionSerializer(transactions, many=True)
        
        return Response({
            'transactions': serializer.data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'has_next': end < total_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching admin transactions: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_get_payment_stats(request):
    """Get payment statistics (admin only)"""
    
    # Get user profile
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if user has admin role
    if not hasattr(user_profile, 'role') or user_profile.role.name != 'admin':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from django.db.models import Count, Sum
        from .models import PaymentStatus
        
        # Get basic stats
        total_transactions = PaymentTransaction.objects.count()
        successful_payments = PaymentTransaction.objects.filter(
            status=PaymentStatus.COMPLETED
        ).count()
        total_revenue = PaymentTransaction.objects.filter(
            status=PaymentStatus.COMPLETED
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Payment status breakdown
        status_breakdown = PaymentIntent.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        return Response({
            'total_transactions': total_transactions,
            'successful_payments': successful_payments,
            'total_revenue': total_revenue,
            'success_rate': (successful_payments / total_transactions * 100) if total_transactions > 0 else 0,
            'status_breakdown': list(status_breakdown)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching payment stats: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
