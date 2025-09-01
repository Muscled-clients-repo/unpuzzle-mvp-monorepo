"""
URL configuration for puzzle reflections app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PuzzleReflectionViewSet

app_name = 'puzzle_reflections'

router = DefaultRouter()
router.register(r'', PuzzleReflectionViewSet, basename='puzzle-reflection')

urlpatterns = [
    path('', include(router.urls)),
]