"""
Management command to seed subscription plans into the database.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Seed database with default subscription plans'
    
    def handle(self, *args, **options):
        """Execute the command to create subscription plans"""
        
        plans = [
            {
                'id': 'free',
                'name': 'Free',
                'display_name': 'Free Plan',
                'description': 'Get started with basic AI features',
                'price_monthly': Decimal('0.00'),
                'price_yearly': Decimal('0.00'),
                'ai_daily_limit': 3,
                'ai_monthly_limit': 50,
                'trial_days': 0,
                'sort_order': 1,
                'features': {
                    'ai_chat': True,
                    'ai_hints': False,
                    'ai_quiz': False,
                    'ai_reflection': False,
                    'ai_path': False,
                    'priority_support': False,
                    'custom_models': False,
                    'api_access': False,
                    'unlimited_courses': False,
                    'advanced_analytics': False
                }
            },
            {
                'id': 'premium',
                'name': 'Premium',
                'display_name': 'Premium Plan',
                'description': 'Unlock advanced AI features and higher limits',
                'price_monthly': Decimal('19.99'),
                'price_yearly': Decimal('199.99'),
                'ai_daily_limit': 50,
                'ai_monthly_limit': 1000,
                'trial_days': 14,
                'sort_order': 2,
                'is_featured': True,
                'stripe_product_id': '',  # To be filled with actual Stripe IDs
                'stripe_price_monthly_id': '',
                'stripe_price_yearly_id': '',
                'features': {
                    'ai_chat': True,
                    'ai_hints': True,
                    'ai_quiz': True,
                    'ai_reflection': True,
                    'ai_path': False,
                    'priority_support': True,
                    'custom_models': False,
                    'api_access': False,
                    'unlimited_courses': True,
                    'advanced_analytics': True
                }
            },
            {
                'id': 'enterprise',
                'name': 'Enterprise',
                'display_name': 'Enterprise Plan',
                'description': 'Maximum AI capabilities with custom features',
                'price_monthly': Decimal('49.99'),
                'price_yearly': Decimal('499.99'),
                'ai_daily_limit': 200,
                'ai_monthly_limit': 5000,
                'trial_days': 14,
                'sort_order': 3,
                'stripe_product_id': '',  # To be filled with actual Stripe IDs
                'stripe_price_monthly_id': '',
                'stripe_price_yearly_id': '',
                'features': {
                    'ai_chat': True,
                    'ai_hints': True,
                    'ai_quiz': True,
                    'ai_reflection': True,
                    'ai_path': True,
                    'priority_support': True,
                    'custom_models': True,
                    'api_access': True,
                    'unlimited_courses': True,
                    'advanced_analytics': True,
                    'white_label': True,
                    'dedicated_support': True
                }
            }
        ]
        
        with transaction.atomic():
            created_count = 0
            updated_count = 0
            
            for plan_data in plans:
                plan_id = plan_data.pop('id')
                
                plan, created = SubscriptionPlan.objects.update_or_create(
                    id=plan_id,
                    defaults=plan_data
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created subscription plan: {plan.display_name}'
                        )
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Updated subscription plan: {plan.display_name}'
                        )
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSubscription plans seeded successfully!\n'
                    f'Created: {created_count} plans\n'
                    f'Updated: {updated_count} plans'
                )
            )
            
            # Display plan summary
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write('SUBSCRIPTION PLANS SUMMARY')
            self.stdout.write('=' * 60)
            
            for plan in SubscriptionPlan.objects.all().order_by('sort_order'):
                self.stdout.write(
                    f'\n{plan.display_name}:'
                    f'\n  Price: ${plan.price_monthly}/month or ${plan.price_yearly}/year'
                    f'\n  AI Limits: {plan.ai_daily_limit}/day, {plan.ai_monthly_limit}/month'
                    f'\n  Trial: {plan.trial_days} days'
                    f'\n  Features: {", ".join([k for k, v in plan.features.items() if v])}'
                )
            
            self.stdout.write('\n' + '=' * 60)
            
            # Instructions for next steps
            self.stdout.write(
                self.style.WARNING(
                    '\nNEXT STEPS:\n'
                    '1. Create Stripe products and prices in your Stripe dashboard\n'
                    '2. Update the plan records with actual Stripe IDs:\n'
                    '   - stripe_product_id\n'
                    '   - stripe_price_monthly_id\n'
                    '   - stripe_price_yearly_id\n'
                    '3. Run migrations to ensure all users have free subscriptions\n'
                    '4. Test subscription endpoints with API client'
                )
            )