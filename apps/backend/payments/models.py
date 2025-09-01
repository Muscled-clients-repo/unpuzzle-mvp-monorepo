"""
Payment management models for Stripe integration.
"""
from django.db import models
from decimal import Decimal
from app.models import AuditableModel
import uuid


class PaymentStatus(models.TextChoices):
    """Payment status choices"""
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'
    PARTIALLY_REFUNDED = 'partially_refunded', 'Partially Refunded'
    CANCELLED = 'cancelled', 'Cancelled'


class PaymentMethod(models.TextChoices):
    """Payment method choices"""
    STRIPE = 'stripe', 'Stripe'
    PAYPAL = 'paypal', 'PayPal'
    FREE = 'free', 'Free'


class RefundStatus(models.TextChoices):
    """Refund status choices"""
    PENDING = 'pending', 'Pending'
    SUCCEEDED = 'succeeded', 'Succeeded'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class PaymentIntent(AuditableModel):
    """Payment intent model for tracking Stripe payment intents"""
    
    # Core fields
    payment_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # User and course relationship
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='payment_intents'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='payment_intents'
    )
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.STRIPE,
        db_index=True
    )
    
    # Stripe specific fields
    client_secret = models.CharField(max_length=500, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    # Payment metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    paid_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_intents'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['created_at', 'status']),
        ]
        # PostgreSQL RLS policies
        permissions = (
            ('payment_intents_rls', 'Row Level Security for payment intents'),
        )
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.user.email} - {self.course.title}"


class PaymentTransaction(AuditableModel):
    """Completed payment transaction record"""
    
    # Core fields
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    payment_intent = models.OneToOneField(
        PaymentIntent,
        on_delete=models.CASCADE,
        related_name='transaction'
    )
    
    # Transaction details
    stripe_charge_id = models.CharField(max_length=255, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount after fees")
    stripe_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Payment details
    payment_method_details = models.JSONField(default=dict, blank=True)
    receipt_url = models.URLField(blank=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.COMPLETED,
        db_index=True
    )
    
    # Enrollment tracking
    enrollment_created = models.BooleanField(default=False)
    enrollment = models.ForeignKey(
        'enrollments.Enrollment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_transaction'
    )
    
    class Meta:
        db_table = 'payment_transactions'
        indexes = [
            models.Index(fields=['payment_intent', 'status']),
            models.Index(fields=['stripe_charge_id']),
            models.Index(fields=['created_at', 'status']),
        ]
        # PostgreSQL RLS policies  
        permissions = (
            ('payment_transactions_rls', 'Row Level Security for payment transactions'),
        )
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.amount} {self.currency}"


class PaymentRefund(AuditableModel):
    """Payment refund tracking"""
    
    # Core fields
    refund_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    
    # Stripe refund details
    stripe_refund_id = models.CharField(max_length=255, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    
    # Refund details
    reason = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING,
        db_index=True
    )
    
    # Administrative fields
    requested_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_refunds'
    )
    processed_by = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds'
    )
    
    # Timestamps
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'payment_refunds'
        indexes = [
            models.Index(fields=['transaction', 'status']),
            models.Index(fields=['stripe_refund_id']),
            models.Index(fields=['created_at', 'status']),
        ]
        # PostgreSQL RLS policies
        permissions = (
            ('payment_refunds_rls', 'Row Level Security for payment refunds'),
        )
    
    def __str__(self):
        return f"Refund {self.refund_id} - {self.amount} {self.currency}"


class StripeCustomer(AuditableModel):
    """Stripe customer mapping"""
    
    user = models.OneToOneField(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='stripe_customer'
    )
    stripe_customer_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Customer details
    email = models.EmailField()
    name = models.CharField(max_length=255, blank=True)
    
    # Default payment method
    default_payment_method = models.CharField(max_length=255, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'stripe_customers'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['stripe_customer_id']),
        ]
        # PostgreSQL RLS policies
        permissions = (
            ('stripe_customers_rls', 'Row Level Security for stripe customers'),
        )
    
    def __str__(self):
        return f"Stripe Customer {self.stripe_customer_id} - {self.email}"


class WebhookEvent(AuditableModel):
    """Stripe webhook event tracking for idempotency"""
    
    # Stripe event details
    stripe_event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    
    # Processing status
    processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Event data
    event_data = models.JSONField(default=dict)
    
    # Error tracking
    processing_error = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'webhook_events'
        indexes = [
            models.Index(fields=['stripe_event_id']),
            models.Index(fields=['event_type', 'processed']),
            models.Index(fields=['created_at', 'processed']),
        ]
    
    def __str__(self):
        return f"Webhook {self.stripe_event_id} - {self.event_type}"
