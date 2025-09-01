"""
User reference models for Supabase Auth integration.
This model references users managed by Supabase Auth.
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from decimal import Decimal
from app.models import TimeStampedModel


class UserStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    SUSPENDED = 'suspended', 'Suspended'
    PENDING = 'pending', 'Pending'


class UserProfile(TimeStampedModel):
    """
    Extended user profile that references Supabase Auth users.
    The actual authentication is handled by Supabase.
    """
    
    # Reference to Supabase Auth user
    supabase_user_id = models.UUIDField(
        primary_key=True,
        editable=False,
        verbose_name='Supabase User ID'
    )
    
    # Profile fields
    email = models.EmailField(
        unique=True,
        db_index=True,
        verbose_name='Email Address'
    )
    username = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )
    full_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Full Name'
    )
    display_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Display Name'
    )
    avatar_url = models.URLField(
        blank=True,
        verbose_name='Avatar URL'
    )
    bio = models.TextField(
        blank=True,
        verbose_name='Biography'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
        db_index=True
    )
    
    # Metadata
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Phone Number'
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        verbose_name='Timezone'
    )
    language = models.CharField(
        max_length=10,
        default='en',
        verbose_name='Language'
    )
    
    # Tracking
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Login'
    )
    email_verified = models.BooleanField(
        default=False,
        verbose_name='Email Verified'
    )
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['username', 'status']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.full_name or self.email
    
    def get_short_name(self):
        return self.display_name or self.email.split('@')[0]
    
    # Django compatibility properties for DRF
    @property
    def is_authenticated(self):
        """Always return True for UserProfile objects (they exist = authenticated)"""
        return True
    
    @property
    def is_anonymous(self):
        """UserProfile is never anonymous"""
        return False
    
    # Subscription-related properties
    @property
    def subscription_plan(self):
        """Get current subscription plan ID"""
        if hasattr(self, 'subscription') and self.subscription.is_active():
            return self.subscription.plan_id
        return 'free'
    
    @property
    def subscription_status(self):
        """Get current subscription status"""
        if hasattr(self, 'subscription'):
            return self.subscription.status
        return 'free'
    
    @property
    def subscription_display_name(self):
        """Get subscription plan display name"""
        if hasattr(self, 'subscription') and self.subscription.is_active():
            return self.subscription.plan.display_name
        return 'Free Plan'
    
    @property
    def ai_daily_limit(self):
        """Get daily AI usage limit based on subscription"""
        if hasattr(self, 'subscription') and self.subscription.is_active():
            return self.subscription.plan.ai_daily_limit
        return settings.AI_RATE_LIMIT_FREE
    
    @property
    def ai_monthly_limit(self):
        """Get monthly AI usage limit based on subscription"""
        if hasattr(self, 'subscription') and self.subscription.is_active():
            return self.subscription.plan.ai_monthly_limit
        return 50  # Free tier monthly limit
    
    @property
    def ai_usage_today(self):
        """Get today's AI usage count"""
        if hasattr(self, 'subscription'):
            self.subscription.reset_daily_usage()  # Ensure counter is reset if needed
            return self.subscription.ai_usage_today
        return 0
    
    @property
    def ai_usage_remaining_today(self):
        """Get remaining AI interactions for today"""
        return max(0, self.ai_daily_limit - self.ai_usage_today)
    
    @property
    def has_active_subscription(self):
        """Check if user has an active paid subscription"""
        if hasattr(self, 'subscription'):
            return self.subscription.is_active() and self.subscription.plan_id != 'free'
        return False
    
    @property
    def is_trial_user(self):
        """Check if user is on trial"""
        if hasattr(self, 'subscription'):
            return self.subscription.status == 'trialing'
        return False
    
    @property
    def subscription_features(self):
        """Get subscription plan features"""
        if hasattr(self, 'subscription') and self.subscription.is_active():
            return self.subscription.plan.features
        # Default free plan features
        return {
            'ai_chat': True,
            'ai_hints': False,
            'ai_quiz': False,
            'ai_reflection': False,
            'ai_path': False,
            'priority_support': False
        }


class Role(TimeStampedModel):
    """Role model for role-based access control"""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Role Name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    permissions = models.JSONField(
        default=list,
        verbose_name='Permissions'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserRole(TimeStampedModel):
    """Many-to-many relationship between users and roles"""
    
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_users'
    )
    assigned_by = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='Assigned By User ID'
    )
    
    class Meta:
        db_table = 'user_roles'
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
        unique_together = [['user', 'role']]
    
    def __str__(self):
        return f"{self.user.email} - {self.role.name}"


class Session(TimeStampedModel):
    """Session tracking for user activity"""
    
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_token = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Session Token'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Address'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    expires_at = models.DateTimeField(
        verbose_name='Expires At'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )
    
    class Meta:
        db_table = 'sessions'
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
        indexes = [
            models.Index(fields=['session_token']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.created_at}"


class SubscriptionPlan(TimeStampedModel):
    """Define available subscription plans for AI services"""
    
    PLAN_IDS = [
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise')
    ]
    
    id = models.CharField(
        max_length=50,
        primary_key=True,
        choices=PLAN_IDS,
        verbose_name='Plan ID'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Plan Name'
    )
    display_name = models.CharField(
        max_length=100,
        verbose_name='Display Name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Plan Description'
    )
    
    # Pricing
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monthly Price'
    )
    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Yearly Price'
    )
    
    # Stripe IDs
    stripe_product_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Stripe Product ID'
    )
    stripe_price_monthly_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Stripe Monthly Price ID'
    )
    stripe_price_yearly_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Stripe Yearly Price ID'
    )
    
    # AI Limits
    ai_daily_limit = models.IntegerField(
        default=0,
        verbose_name='Daily AI Interactions Limit'
    )
    ai_monthly_limit = models.IntegerField(
        default=0,
        verbose_name='Monthly AI Interactions Limit'
    )
    
    # Features (stored as JSON)
    features = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Plan Features',
        help_text='JSON object with feature flags'
    )
    
    # Display settings
    is_active = models.BooleanField(
        default=True,
        verbose_name='Is Active'
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Is Featured Plan'
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name='Display Sort Order'
    )
    
    # Trial settings
    trial_days = models.IntegerField(
        default=0,
        verbose_name='Trial Period (days)'
    )
    
    class Meta:
        db_table = 'subscription_plans'
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
        ordering = ['sort_order', 'price_monthly']
    
    def __str__(self):
        return f"{self.display_name} (${self.price_monthly}/mo)"
    
    def get_stripe_price_id(self, billing_period='monthly'):
        """Get the appropriate Stripe price ID based on billing period"""
        if billing_period == 'yearly':
            return self.stripe_price_yearly_id
        return self.stripe_price_monthly_id


class SubscriptionStatus(models.TextChoices):
    """Subscription status choices"""
    ACTIVE = 'active', 'Active'
    CANCELED = 'canceled', 'Canceled'
    PAST_DUE = 'past_due', 'Past Due'
    TRIALING = 'trialing', 'Trialing'
    EXPIRED = 'expired', 'Expired'
    PAUSED = 'paused', 'Paused'
    INCOMPLETE = 'incomplete', 'Incomplete'


class BillingPeriod(models.TextChoices):
    """Billing period choices"""
    MONTHLY = 'monthly', 'Monthly'
    YEARLY = 'yearly', 'Yearly'


class UserSubscription(TimeStampedModel):
    """Track user subscription status and billing"""
    
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='User'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        verbose_name='Subscription Plan'
    )
    status = models.CharField(
        max_length=30,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
        db_index=True,
        verbose_name='Status'
    )
    billing_period = models.CharField(
        max_length=10,
        choices=BillingPeriod.choices,
        default=BillingPeriod.MONTHLY,
        verbose_name='Billing Period'
    )
    
    # Stripe fields
    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        unique=True,
        null=True,
        db_index=True,
        verbose_name='Stripe Subscription ID'
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        verbose_name='Stripe Customer ID'
    )
    
    # Important dates
    current_period_start = models.DateTimeField(
        verbose_name='Current Period Start'
    )
    current_period_end = models.DateTimeField(
        verbose_name='Current Period End'
    )
    cancel_at_period_end = models.BooleanField(
        default=False,
        verbose_name='Cancel at Period End'
    )
    canceled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Canceled At'
    )
    trial_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Trial Start Date'
    )
    trial_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Trial End Date'
    )
    
    # Usage tracking
    ai_usage_this_period = models.IntegerField(
        default=0,
        verbose_name='AI Usage This Period'
    )
    ai_usage_today = models.IntegerField(
        default=0,
        verbose_name='AI Usage Today'
    )
    last_usage_reset_date = models.DateField(
        auto_now_add=True,
        verbose_name='Last Usage Reset Date'
    )
    
    # Payment
    last_payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Last Payment Amount'
    )
    last_payment_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last Payment Date'
    )
    next_payment_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Next Payment Date'
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Additional Metadata'
    )
    
    class Meta:
        db_table = 'user_subscriptions'
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'
        indexes = [
            models.Index(fields=['status', 'current_period_end']),
            models.Index(fields=['stripe_subscription_id']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.display_name} ({self.status})"
    
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
    
    def is_expired(self):
        """Check if subscription has expired"""
        return self.current_period_end < timezone.now()
    
    def days_until_renewal(self):
        """Calculate days until next renewal"""
        if self.current_period_end:
            delta = self.current_period_end - timezone.now()
            return max(0, delta.days)
        return 0
    
    def reset_daily_usage(self):
        """Reset daily AI usage counter"""
        today = timezone.now().date()
        if self.last_usage_reset_date != today:
            self.ai_usage_today = 0
            self.last_usage_reset_date = today
            self.save(update_fields=['ai_usage_today', 'last_usage_reset_date'])
    
    def reset_period_usage(self):
        """Reset period AI usage counter"""
        self.ai_usage_this_period = 0
        self.save(update_fields=['ai_usage_this_period'])


class SubscriptionAction(models.TextChoices):
    """Subscription history action types"""
    CREATE = 'create', 'Create'
    UPGRADE = 'upgrade', 'Upgrade'
    DOWNGRADE = 'downgrade', 'Downgrade'
    CANCEL = 'cancel', 'Cancel'
    RESUME = 'resume', 'Resume'
    PAUSE = 'pause', 'Pause'
    EXPIRE = 'expire', 'Expire'
    TRIAL_START = 'trial_start', 'Trial Start'
    TRIAL_END = 'trial_end', 'Trial End'
    PAYMENT_FAILED = 'payment_failed', 'Payment Failed'
    PAYMENT_SUCCESS = 'payment_success', 'Payment Success'


class SubscriptionHistory(TimeStampedModel):
    """Track subscription changes for auditing and analytics"""
    
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='subscription_history',
        verbose_name='User'
    )
    from_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_from',
        verbose_name='From Plan'
    )
    to_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_to',
        verbose_name='To Plan'
    )
    action = models.CharField(
        max_length=30,
        choices=SubscriptionAction.choices,
        verbose_name='Action'
    )
    reason = models.TextField(
        blank=True,
        verbose_name='Reason for Change'
    )
    
    # Billing details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Amount'
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        verbose_name='Currency'
    )
    
    # Stripe references
    stripe_event_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Stripe Event ID'
    )
    stripe_invoice_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Stripe Invoice ID'
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Additional Metadata'
    )
    
    class Meta:
        db_table = 'subscription_history'
        verbose_name = 'Subscription History'
        verbose_name_plural = 'Subscription History'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['stripe_event_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.created_at}"