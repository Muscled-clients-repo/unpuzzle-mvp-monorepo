"""
URL configuration for Unpuzzle MVP project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views, websocket_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # System endpoints
    path('health/', views.health_check, name='health_check'),
    path('api/', views.api_info, name='api_info'),
    
    # WebSocket API endpoints
    path('api/v1/websocket/info/', websocket_views.websocket_info, name='websocket_info'),
    path('api/v1/websocket/send-event/', websocket_views.send_event_to_room, name='send_event'),
    path('api/v1/websocket/send-notification/', websocket_views.send_notification_to_user, name='send_notification'),
    path('api/v1/websocket/send-system-message/', websocket_views.send_system_message, name='send_system_message'),
    
    # API endpoints
    path('api/v1/auth/', include('accounts.urls', namespace='auth')),
    path('api/v1/user/', include('accounts.urls', namespace='user')),  # Alias for frontend compatibility
    path('api/v1/stats/', include('courses.urls_stats')),  # Platform statistics (public)
    path('api/v1/media/', include('media_library.urls')),  # Media upload and management
    path('api/v1/content/', include('courses.urls_content')),  # Content management endpoints
    path('api/v1/payments/', include('payments.urls')),  # Payment and Stripe integration
    path('api/v1/', include('courses.urls')),  # Course management endpoints
    path('api/v1/ai-assistant/', include('ai_assistant.urls')),  # AI Assistant endpoints
    path('api/v1/enrollments/', include('enrollments.urls')),  # Enrollment endpoints
    path('api/v1/analytics/', include('analytics.urls')),  # Analytics endpoints
    path('api/v1/notifications/', include('notifications.urls')),  # Notification endpoints
    path('api/v1/reflections/', include('puzzle_reflections.urls')),  # Puzzle reflections endpoints
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
