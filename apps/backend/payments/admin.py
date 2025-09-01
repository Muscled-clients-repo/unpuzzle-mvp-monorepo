from django.contrib import admin
from .models import PaymentIntent, PaymentTransaction, PaymentRefund, StripeCustomer, WebhookEvent


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'user', 'course', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['user__email', 'course__title', 'stripe_payment_intent_id']
    readonly_fields = ['payment_id', 'stripe_payment_intent_id', 'client_secret', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user_email', 'course_title', 'amount', 'currency', 'status', 'enrollment_created', 'created_at']
    list_filter = ['status', 'currency', 'enrollment_created', 'created_at']
    search_fields = ['payment_intent__user__email', 'payment_intent__course__title', 'stripe_charge_id']
    readonly_fields = ['transaction_id', 'stripe_charge_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def user_email(self, obj):
        return obj.payment_intent.user.email
    user_email.short_description = 'User Email'
    
    def course_title(self, obj):
        return obj.payment_intent.course.title
    course_title.short_description = 'Course Title'


@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    list_display = ['refund_id', 'transaction', 'amount', 'currency', 'status', 'reason', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['stripe_refund_id', 'transaction__transaction_id']
    readonly_fields = ['refund_id', 'stripe_refund_id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ['stripe_customer_id', 'user', 'email', 'name', 'created_at']
    search_fields = ['user__email', 'stripe_customer_id', 'email', 'name']
    readonly_fields = ['stripe_customer_id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ['stripe_event_id', 'event_type', 'processed', 'retry_count', 'created_at']
    list_filter = ['processed', 'event_type', 'created_at']
    search_fields = ['stripe_event_id', 'event_type']
    readonly_fields = ['stripe_event_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
