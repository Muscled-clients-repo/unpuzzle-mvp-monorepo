"""
Serializers for payment-related models and API responses.
"""
from rest_framework import serializers
from .models import PaymentIntent, PaymentTransaction, PaymentRefund, StripeCustomer
from courses.serializers import CourseListSerializer
from accounts.serializers import UserProfileSerializer


class PaymentIntentSerializer(serializers.ModelSerializer):
    """Serializer for payment intents"""
    
    course = CourseListSerializer(read_only=True)
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = PaymentIntent
        fields = [
            'payment_id',
            'stripe_payment_intent_id',
            'user',
            'course',
            'amount',
            'currency',
            'status',
            'payment_method',
            'client_secret',
            'metadata',
            'paid_at',
            'expires_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'payment_id',
            'stripe_payment_intent_id',
            'user',
            'course',
            'client_secret',
            'created_at',
            'updated_at'
        ]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for payment transactions"""
    
    payment_intent = PaymentIntentSerializer(read_only=True)
    course_title = serializers.CharField(source='payment_intent.course.title', read_only=True)
    user_email = serializers.CharField(source='payment_intent.user.email', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'transaction_id',
            'payment_intent',
            'stripe_charge_id',
            'amount',
            'currency',
            'net_amount',
            'stripe_fee',
            'payment_method_details',
            'receipt_url',
            'status',
            'enrollment_created',
            'course_title',
            'user_email',
            'created_at',
            'updated_at'
        ]
        read_only_fields = '__all__'


class PaymentRefundSerializer(serializers.ModelSerializer):
    """Serializer for payment refunds"""
    
    transaction_id = serializers.CharField(source='transaction.transaction_id', read_only=True)
    course_title = serializers.CharField(source='transaction.payment_intent.course.title', read_only=True)
    
    class Meta:
        model = PaymentRefund
        fields = [
            'refund_id',
            'transaction_id',
            'stripe_refund_id',
            'amount',
            'currency',
            'reason',
            'status',
            'course_title',
            'processed_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = '__all__'


class CreatePaymentIntentSerializer(serializers.Serializer):
    """Serializer for creating payment intents"""
    
    course_id = serializers.UUIDField()
    currency = serializers.CharField(max_length=3, default='usd')
    metadata = serializers.JSONField(required=False)
    
    def validate_currency(self, value):
        """Validate currency code"""
        allowed_currencies = ['usd', 'eur', 'gbp']
        if value.lower() not in allowed_currencies:
            raise serializers.ValidationError(f"Currency must be one of: {allowed_currencies}")
        return value.lower()


class PaymentHistorySerializer(serializers.Serializer):
    """Serializer for user payment history"""
    
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_intents = PaymentIntentSerializer(many=True)
    transactions = PaymentTransactionSerializer(many=True)


class StripeCustomerSerializer(serializers.ModelSerializer):
    """Serializer for Stripe customers"""
    
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = StripeCustomer
        fields = [
            'stripe_customer_id',
            'user',
            'email',
            'name',
            'default_payment_method',
            'metadata',
            'created_at',
            'updated_at'
        ]
        read_only_fields = '__all__'


class WebhookEventSerializer(serializers.Serializer):
    """Serializer for webhook event processing"""
    
    id = serializers.CharField()
    type = serializers.CharField()
    data = serializers.JSONField()
    created = serializers.IntegerField()
    
    
class RefundRequestSerializer(serializers.Serializer):
    """Serializer for refund requests"""
    
    transaction_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    reason = serializers.CharField(max_length=100, required=False)


# Response serializers for API endpoints
class PaymentSuccessResponseSerializer(serializers.Serializer):
    """Response serializer for successful payment creation"""
    
    payment_id = serializers.UUIDField()
    client_secret = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    status = serializers.CharField()


class PaymentStatusResponseSerializer(serializers.Serializer):
    """Response serializer for payment status"""
    
    payment_id = serializers.UUIDField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    paid_at = serializers.DateTimeField()
    course_title = serializers.CharField()
    enrollment_created = serializers.BooleanField()