"""
Notifications app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

app_name = 'notifications'

urlpatterns = [
    path('', include(router.urls)),
]