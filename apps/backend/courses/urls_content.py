"""
URL configuration for course content management.
"""
from django.urls import path
from . import views_content

app_name = 'content'

urlpatterns = [
    # Section management
    path('courses/<uuid:course_id>/sections/', views_content.manage_course_sections, name='manage_sections'),
    path('courses/<uuid:course_id>/sections/<uuid:section_id>/', views_content.manage_section_detail, name='section_detail'),
    
    # Media management  
    path('courses/<uuid:course_id>/sections/<uuid:section_id>/media/', views_content.get_section_media, name='section_media'),
    path('courses/<uuid:course_id>/media/', views_content.get_course_media, name='course_media'),
    
    # Direct section media assignment (for frontend compatibility)
    path('sections/<uuid:section_id>/media/', views_content.assign_media_to_section, name='assign_media_to_section'),
    
    # Unassign media from section
    path('media/<uuid:media_id>/unassign/', views_content.unassign_media, name='unassign_media'),
]