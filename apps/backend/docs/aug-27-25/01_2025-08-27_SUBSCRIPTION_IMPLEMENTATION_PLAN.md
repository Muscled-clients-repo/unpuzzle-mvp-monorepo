# AI Subscription System Implementation Plan

**Date:** 2025-08-27  
**Purpose:** Complete development roadmap for implementing subscription functionality for AI services  
**Phase:** Backend Subscription System & Stripe Integration

---

## 📋 **Implementation Overview**

This plan addresses the critical missing subscription functionality needed to monetize AI services and enforce usage limits. Currently, all users default to the 'free' tier despite having sophisticated rate limiting logic in place.

### **Current State Analysis**
- ✅ AI usage rate limiting logic implemented
- ✅ Usage tracking and metrics collection
- ✅ Subscription tier checking in all AI endpoints
- ✅ Stripe integration for one-time payments
- ✅ Redis caching for performance
- ❌ No subscription database models
- ❌ No subscription_plan field in UserProfile
- ❌ No Stripe subscription integration
- ❌ No subscription management endpoints
- ❌ No upgrade/downgrade functionality

---

## 🏗️ **Implementation Phases**

### **Phase 1: Database Models & Schema (Day 1)**

#### **1.1 Subscription Models Implementation**
**File:** `accounts/models.py` (additions)

```python
class SubscriptionPlan(TimeStampedModel):
    """Define available subscription plans"""
    id = models.CharField(max_length=50, primary_key=True)  # 'free', 'premium', 'enterprise'
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_price_monthly_id = models.CharField(max_length=255, blank=True)
    stripe_price_yearly_id = models.CharField(max_length=255, blank=True)
    
    # AI Limits
    ai_daily_limit = models.IntegerField()
    ai_monthly_limit = models.IntegerField()
    
    # Features
    features = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
class UserSubscription(TimeStampedModel):
    """Track user subscription status"""
    user = models.OneToOneField(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT
    )
    status = models.CharField(
        max_length=30,
        choices=[
            ('active', 'Active'),
            ('canceled', 'Canceled'),
            ('past_due', 'Past Due'),
            ('trialing', 'Trialing'),
            ('expired', 'Expired'),
            ('paused', 'Paused')
        ],
        default='active'
    )
    billing_period = models.CharField(
        max_length=10,
        choices=[
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly')
        ],
        default='monthly'
    )
    
    # Stripe fields
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    
    # Important dates
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    ai_usage_this_period = models.IntegerField(default=0)
    last_reset_date = models.DateTimeField(auto_now_add=True)
    
class SubscriptionHistory(TimeStampedModel):
    """Track subscription changes for auditing"""
    user = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='subscription_history'
    )
    from_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name='history_from'
    )
    to_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name='history_to'
    )
    action = models.CharField(
        max_length=30,
        choices=[
            ('upgrade', 'Upgrade'),
            ('downgrade', 'Downgrade'),
            ('cancel', 'Cancel'),
            ('resume', 'Resume'),
            ('trial_start', 'Trial Start'),
            ('trial_end', 'Trial End')
        ]
    )
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
```

#### **1.2 UserProfile Model Updates**
**File:** `accounts/models.py` (modifications)

```python
class UserProfile(TimeStampedModel):
    # ... existing fields ...
    
    # Add subscription reference (backward compatible)
    @property
    def subscription_plan(self):
        """Get current subscription plan ID"""
        if hasattr(self, 'subscription') and self.subscription.status == 'active':
            return self.subscription.plan_id
        return 'free'
    
    @property
    def subscription_status(self):
        """Get current subscription status"""
        if hasattr(self, 'subscription'):
            return self.subscription.status
        return 'free'
    
    @property
    def ai_daily_limit(self):
        """Get daily AI usage limit based on subscription"""
        if hasattr(self, 'subscription') and self.subscription.status == 'active':
            return self.subscription.plan.ai_daily_limit
        return settings.AI_RATE_LIMIT_FREE
    
    @property
    def ai_monthly_limit(self):
        """Get monthly AI usage limit based on subscription"""
        if hasattr(self, 'subscription') and self.subscription.status == 'active':
            return self.subscription.plan.ai_monthly_limit
        return 50  # Free tier monthly limit
```

---

### **Phase 2: Subscription Service Layer (Day 2)**

#### **2.1 Subscription Service Architecture**
**New Directory:** `accounts/services/`

```
accounts/services/
├── __init__.py
├── subscription_service.py    # Core subscription logic
├── stripe_subscription.py     # Stripe subscription handling
├── usage_tracker.py          # Usage tracking and limits
└── billing_service.py        # Billing and invoice management
```

#### **2.2 Core Subscription Service**
**File:** `accounts/services/subscription_service.py`

```python
class SubscriptionService:
    """Handle subscription lifecycle management"""
    
    def create_subscription(self, user, plan_id, billing_period='monthly'):
        """Create new subscription"""
        
    def upgrade_subscription(self, user, new_plan_id):
        """Upgrade to higher tier"""
        
    def downgrade_subscription(self, user, new_plan_id):
        """Downgrade to lower tier"""
        
    def cancel_subscription(self, user, reason=''):
        """Cancel subscription at period end"""
        
    def resume_subscription(self, user):
        """Resume canceled subscription"""
        
    def check_subscription_status(self, user):
        """Verify subscription is active and valid"""
        
    def apply_trial(self, user, days=14):
        """Start trial period for new users"""
        
    def handle_payment_failed(self, subscription_id):
        """Handle failed payment scenarios"""
```

#### **2.3 Stripe Subscription Integration**
**File:** `accounts/services/stripe_subscription.py`

```python
class StripeSubscriptionService:
    """Integrate with Stripe for subscription billing"""
    
    def create_stripe_subscription(self, customer_id, price_id):
        """Create Stripe subscription"""
        
    def update_stripe_subscription(self, subscription_id, new_price_id):
        """Update existing subscription"""
        
    def cancel_stripe_subscription(self, subscription_id):
        """Cancel Stripe subscription"""
        
    def handle_webhook_event(self, event):
        """Process Stripe webhook events"""
        # Handle: subscription.created, subscription.updated, 
        # subscription.deleted, invoice.payment_failed, etc.
```

---

### **Phase 3: API Endpoints Implementation (Days 3-4)**

#### **3.1 Subscription Management Endpoints**
**File:** `accounts/views/subscriptions.py`

```python
# Endpoints to implement:
class SubscriptionPlansView(APIView):
    """GET /api/v1/subscriptions/plans/ - List available plans"""
    
class CurrentSubscriptionView(APIView):
    """GET /api/v1/subscriptions/current/ - Get user's subscription"""
    
class CreateSubscriptionView(APIView):
    """POST /api/v1/subscriptions/create/ - Create new subscription"""
    
class UpdateSubscriptionView(APIView):
    """PUT /api/v1/subscriptions/update/ - Change plan or billing period"""
    
class CancelSubscriptionView(APIView):
    """POST /api/v1/subscriptions/cancel/ - Cancel subscription"""
    
class ResumeSubscriptionView(APIView):
    """POST /api/v1/subscriptions/resume/ - Resume canceled subscription"""
    
class SubscriptionHistoryView(APIView):
    """GET /api/v1/subscriptions/history/ - Get subscription history"""
    
class UsageStatsView(APIView):
    """GET /api/v1/subscriptions/usage/ - Get current usage stats"""
```

#### **3.2 Billing & Payment Endpoints**
**File:** `accounts/views/billing.py`

```python
class PaymentMethodsView(APIView):
    """GET /api/v1/billing/payment-methods/ - List payment methods"""
    
class AddPaymentMethodView(APIView):
    """POST /api/v1/billing/add-payment-method/ - Add payment method"""
    
class SetDefaultPaymentMethodView(APIView):
    """POST /api/v1/billing/set-default/ - Set default payment method"""
    
class InvoicesView(APIView):
    """GET /api/v1/billing/invoices/ - Get billing history"""
    
class UpcomingInvoiceView(APIView):
    """GET /api/v1/billing/upcoming-invoice/ - Preview next invoice"""
```

#### **3.3 Stripe Webhook Endpoint**
**File:** `payments/views.py` (update existing)

```python
class StripeSubscriptionWebhookView(APIView):
    """POST /api/v1/payments/stripe/subscription-webhook/"""
    
    def handle_subscription_created(self, subscription):
        """New subscription created"""
        
    def handle_subscription_updated(self, subscription):
        """Subscription modified"""
        
    def handle_subscription_deleted(self, subscription):
        """Subscription canceled"""
        
    def handle_invoice_payment_failed(self, invoice):
        """Payment failed, may need to pause access"""
        
    def handle_customer_subscription_trial_will_end(self, subscription):
        """Trial ending soon notification"""
```

---

### **Phase 4: AI Service Integration Updates (Day 5)**

#### **4.1 Update AI Usage Service**
**File:** `ai_assistant/services/usage_service.py` (modifications)

```python
class AIUsageService:
    def get_user_subscription_limits(self, user):
        """Get limits from actual subscription instead of hardcoded"""
        if hasattr(user, 'subscription') and user.subscription.status == 'active':
            plan = user.subscription.plan
            return {
                'daily': plan.ai_daily_limit,
                'monthly': plan.ai_monthly_limit,
                'plan_name': plan.display_name,
                'features': plan.features
            }
        return self.get_free_tier_limits()
    
    def check_usage_limits(self, user, agent_type, estimated_tokens):
        """Updated to use real subscription data"""
        subscription = getattr(user, 'subscription', None)
        
        if not subscription or subscription.status != 'active':
            # Free tier or expired subscription
            return self.check_free_tier_limits(user)
        
        # Check against actual subscription limits
        return self.check_subscription_limits(user, subscription, agent_type)
```

#### **4.2 Add Subscription Context to AI Responses**
**File:** `ai_assistant/views/ai_agents.py` (modifications)

```python
# Update all AI views to include subscription context
class ChatSendView(APIView):
    def post(self, request):
        # ... existing code ...
        
        # Add subscription info to response
        subscription_info = {
            'plan': user.subscription_plan,
            'usage_today': usage_service.get_daily_usage(user),
            'limit_today': user.ai_daily_limit,
            'usage_this_month': usage_service.get_monthly_usage(user),
            'limit_this_month': user.ai_monthly_limit
        }
        
        return Response({
            'message': ai_response,
            'subscription': subscription_info,
            # ... other fields ...
        })
```

---

### **Phase 5: Frontend Integration Requirements (Day 6)**

#### **5.1 Required Frontend Components**

1. **Subscription Management Dashboard**
   - Current plan display
   - Usage statistics visualization
   - Upgrade/downgrade buttons
   - Billing history

2. **Plan Selection Component**
   - Plan comparison table
   - Feature highlights
   - Pricing toggle (monthly/yearly)
   - Trial offer display

3. **Payment Method Management**
   - Add/remove cards
   - Set default payment method
   - Security badges

4. **Usage Tracker Widget**
   - Real-time usage display
   - Progress bars for limits
   - Upgrade prompts at 80% usage

5. **Billing & Invoices Section**
   - Invoice history
   - Download receipts
   - Upcoming charges

---

### **Phase 6: Data Migration & Seeding (Day 7)**

#### **6.1 Create Default Subscription Plans**
**File:** `accounts/management/commands/seed_subscription_plans.py`

```python
def create_subscription_plans():
    """Seed database with subscription plans"""
    
    plans = [
        {
            'id': 'free',
            'name': 'Free',
            'display_name': 'Free Plan',
            'price_monthly': 0,
            'price_yearly': 0,
            'ai_daily_limit': 3,
            'ai_monthly_limit': 50,
            'features': {
                'ai_chat': True,
                'ai_hints': False,
                'ai_quiz': False,
                'ai_reflection': False,
                'ai_path': False,
                'priority_support': False
            }
        },
        {
            'id': 'premium',
            'name': 'Premium',
            'display_name': 'Premium Plan',
            'price_monthly': 19.99,
            'price_yearly': 199.99,
            'ai_daily_limit': 50,
            'ai_monthly_limit': 1000,
            'stripe_price_monthly_id': 'price_premium_monthly',
            'stripe_price_yearly_id': 'price_premium_yearly',
            'features': {
                'ai_chat': True,
                'ai_hints': True,
                'ai_quiz': True,
                'ai_reflection': True,
                'ai_path': False,
                'priority_support': True
            }
        },
        {
            'id': 'enterprise',
            'name': 'Enterprise',
            'display_name': 'Enterprise Plan',
            'price_monthly': 49.99,
            'price_yearly': 499.99,
            'ai_daily_limit': 200,
            'ai_monthly_limit': 5000,
            'stripe_price_monthly_id': 'price_enterprise_monthly',
            'stripe_price_yearly_id': 'price_enterprise_yearly',
            'features': {
                'ai_chat': True,
                'ai_hints': True,
                'ai_quiz': True,
                'ai_reflection': True,
                'ai_path': True,
                'priority_support': True,
                'custom_models': True,
                'api_access': True
            }
        }
    ]
```

#### **6.2 Migrate Existing Users**
**File:** `accounts/migrations/00XX_add_subscription_support.py`

```python
def migrate_existing_users(apps, schema_editor):
    """Create free subscriptions for existing users"""
    UserProfile = apps.get_model('accounts', 'UserProfile')
    UserSubscription = apps.get_model('accounts', 'UserSubscription')
    SubscriptionPlan = apps.get_model('accounts', 'SubscriptionPlan')
    
    free_plan = SubscriptionPlan.objects.get(id='free')
    
    for user in UserProfile.objects.all():
        UserSubscription.objects.get_or_create(
            user=user,
            defaults={
                'plan': free_plan,
                'status': 'active',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timedelta(days=30)
            }
        )
```

---

### **Phase 7: Testing & Monitoring (Day 8)**

#### **7.1 Test Coverage Requirements**

1. **Unit Tests**
   - Subscription creation/update/cancel
   - Usage limit enforcement
   - Billing calculations
   - Plan transitions

2. **Integration Tests**
   - Stripe webhook handling
   - Payment method management
   - Invoice generation
   - AI usage with subscriptions

3. **End-to-End Tests**
   - Complete subscription lifecycle
   - Upgrade/downgrade flows
   - Payment failure handling
   - Trial to paid conversion

#### **7.2 Monitoring & Analytics**

1. **Key Metrics to Track**
   - Subscription conversion rate
   - Churn rate by plan
   - Average revenue per user (ARPU)
   - AI usage by subscription tier
   - Payment failure rate

2. **Alerts to Configure**
   - High payment failure rate
   - Unusual subscription cancellations
   - AI usage spikes
   - Stripe webhook failures

---

## 🔧 **Technical Implementation Details**

### **Environment Variables**
**Add to:** `.env`
```bash
# Stripe Subscription Products
STRIPE_PRODUCT_PREMIUM_ID=prod_xxxxx
STRIPE_PRODUCT_ENTERPRISE_ID=prod_xxxxx

# Stripe Price IDs
STRIPE_PRICE_PREMIUM_MONTHLY=price_xxxxx
STRIPE_PRICE_PREMIUM_YEARLY=price_xxxxx
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_xxxxx
STRIPE_PRICE_ENTERPRISE_YEARLY=price_xxxxx

# Trial Configuration
TRIAL_PERIOD_DAYS=14
AUTO_RENEW_DEFAULT=true

# Subscription Features
ENABLE_TRIALS=true
ENABLE_PRORATION=true
ENABLE_MULTIPLE_SUBSCRIPTIONS=false
```

### **URL Routing**
**File:** `accounts/urls.py`
```python
urlpatterns = [
    # Subscription Management
    path('subscriptions/plans/', SubscriptionPlansView.as_view()),
    path('subscriptions/current/', CurrentSubscriptionView.as_view()),
    path('subscriptions/create/', CreateSubscriptionView.as_view()),
    path('subscriptions/update/', UpdateSubscriptionView.as_view()),
    path('subscriptions/cancel/', CancelSubscriptionView.as_view()),
    path('subscriptions/resume/', ResumeSubscriptionView.as_view()),
    path('subscriptions/history/', SubscriptionHistoryView.as_view()),
    path('subscriptions/usage/', UsageStatsView.as_view()),
    
    # Billing
    path('billing/payment-methods/', PaymentMethodsView.as_view()),
    path('billing/add-payment-method/', AddPaymentMethodView.as_view()),
    path('billing/set-default/', SetDefaultPaymentMethodView.as_view()),
    path('billing/invoices/', InvoicesView.as_view()),
    path('billing/upcoming-invoice/', UpcomingInvoiceView.as_view()),
]
```

---

## ✅ **Success Criteria**

### **Functional Requirements**
- ✅ Users can view available subscription plans
- ✅ Users can subscribe to premium/enterprise plans
- ✅ Users can upgrade/downgrade their subscription
- ✅ Users can cancel and resume subscriptions
- ✅ AI usage limits enforced based on subscription
- ✅ Automated billing through Stripe
- ✅ Trial periods for new users
- ✅ Grace period for failed payments

### **Technical Requirements**
- ✅ Stripe webhooks properly handled
- ✅ Subscription data synchronized with Stripe
- ✅ Usage tracking reset on billing cycle
- ✅ Proper error handling for payment failures
- ✅ Audit trail for subscription changes

### **Business Requirements**
- ✅ Multiple pricing tiers supported
- ✅ Monthly and yearly billing options
- ✅ Proration for plan changes
- ✅ Revenue tracking and reporting
- ✅ Churn prevention mechanisms

---

## 📊 **Risk Mitigation**

### **Technical Risks**
1. **Stripe API Failures**
   - Solution: Implement retry logic with exponential backoff
   - Fallback: Queue failed operations for manual processing

2. **Data Synchronization Issues**
   - Solution: Regular reconciliation jobs
   - Monitoring: Alert on subscription mismatches

3. **Usage Limit Bypassing**
   - Solution: Redis-based rate limiting
   - Backup: Database-level enforcement

### **Business Risks**
1. **High Churn Rate**
   - Solution: Implement win-back campaigns
   - Analytics: Track cancellation reasons

2. **Payment Failures**
   - Solution: Smart retry schedule
   - Grace period: 7 days before suspension

---

## 📅 **Timeline Summary**

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1** | Day 1 | Database models, migrations |
| **Phase 2** | Day 2 | Subscription service layer |
| **Phase 3** | Days 3-4 | API endpoints implementation |
| **Phase 4** | Day 5 | AI service integration |
| **Phase 5** | Day 6 | Frontend requirements spec |
| **Phase 6** | Day 7 | Data migration & seeding |
| **Phase 7** | Day 8 | Testing & monitoring setup |

**Total Estimated Duration:** 8 working days

---

## 🚀 **Next Steps**

1. **Immediate Actions:**
   - Review and approve this implementation plan
   - Set up Stripe subscription products
   - Create test Stripe account for development

2. **Phase 1 Kickoff:**
   - Create subscription models
   - Update UserProfile with subscription fields
   - Generate and run migrations

3. **Coordination Required:**
   - Frontend team alignment on UI/UX
   - DevOps for monitoring setup
   - Marketing for pricing strategy
   - Legal for terms of service updates

---

*This implementation plan provides a comprehensive roadmap for adding subscription functionality to monetize AI services, with proper Stripe integration, usage enforcement, and user management capabilities.*