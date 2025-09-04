"""
URLs for platform statistics endpoints.
"""
from django.urls import path
from . import views_stats

app_name = 'stats'

urlpatterns = [
    # Platform statistics (public endpoints)
    path('platform/', views_stats.get_platform_stats, name='platform_stats'),
    path('featured-courses/', views_stats.get_featured_courses, name='featured_courses'),
]