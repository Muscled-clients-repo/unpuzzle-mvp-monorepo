"""
URL configuration for payments app.
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # ============================================================================
    # PUBLIC ENDPOINTS
    # ============================================================================
    
    # Stripe configuration
    path('config/stripe/', views.get_stripe_publishable_key, name='stripe_config'),
    
    # Test endpoint (no auth required)
    path('test-enroll/', views.test_enroll_in_course, name='test_enroll'),
    
    # Webhook endpoint (must be accessible without authentication)
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
    
    # ============================================================================
    # AUTHENTICATED USER ENDPOINTS
    # ============================================================================
    
    # Course enrollment (smart - handles both free and paid)
    path('enroll/', views.enroll_in_course, name='enroll_in_course'),
    
    # Payment intents
    path('intents/', views.create_payment_intent, name='create_payment_intent'),
    path('intents/<uuid:payment_id>/', views.get_payment_status, name='get_payment_status'),
    path('intents/<uuid:payment_id>/confirm/', views.confirm_payment, name='confirm_payment'),
    
    # Payment history
    path('history/', views.get_payment_history, name='get_payment_history'),
    
    # ============================================================================
    # ADMIN ENDPOINTS
    # ============================================================================
    
    # Admin payment management
    path('admin/transactions/', views.admin_get_all_transactions, name='admin_transactions'),
    path('admin/stats/', views.admin_get_payment_stats, name='admin_payment_stats'),
    
    # Refund management
    path('admin/refunds/', views.create_refund, name='create_refund'),
]