from django.contrib import admin
from .models import UserProfile, Role, UserRole, Session, SubscriptionPlan, UserSubscription, SubscriptionHistory

# Simple admin registrations
admin.site.register(UserProfile)
admin.site.register(Role)  
admin.site.register(UserRole)
admin.site.register(Session)
admin.site.register(SubscriptionPlan)
admin.site.register(UserSubscription)
admin.site.register(SubscriptionHistory)
