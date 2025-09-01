"""
API Version 1 URL configuration
"""
from django.urls import path, include

app_name = 'v1'

urlpatterns = [
    # Authentication routes (expected by frontend)
    path('auth/', include('accounts.urls')),
    path('user/', include('accounts.urls')),  # For /user/profile endpoint
    
    # App-specific routes
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
    path('enrollments/', include('enrollments.urls')),
    path('media/', include('media_library.urls')),
    path('analytics/', include('analytics.urls')),
    path('notifications/', include('notifications.urls')),
    path('ai-assistant/', include('ai_assistant.urls')),
]