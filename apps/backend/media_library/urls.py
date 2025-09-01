"""
URL configuration for media library - Django equivalent of Flask media upload routes
"""
from django.urls import path
from . import views

app_name = 'media_library'

urlpatterns = [
    # Upload endpoints (equivalent to Flask media_upload routes)
    path('upload/initiate/', views.initiate_upload, name='initiate_upload'),
    path('upload/complete/', views.complete_upload, name='complete_upload'),
    path('upload/proxy/', views.proxy_upload, name='proxy_upload'),
    
    # Video management
    path('videos/', views.list_videos, name='list_videos'),
    path('videos/assign/', views.assign_video, name='assign_video'),
    
    # User media endpoints (for frontend compatibility)
    path('user/media/', views.user_media, name='user_media'),
    path('user/unassigned-videos/', views.list_unassigned_videos, name='unassigned_videos'),
    
    # Media file management
    path('media/<uuid:media_id>/', views.get_media_info, name='get_media_info'),
    path('media/<uuid:media_id>', views.get_media_info, name='get_media_info_no_slash'),
    path('media/<uuid:media_id>/delete/', views.delete_media, name='delete_media'),
    path('media/<uuid:media_id>/delete', views.delete_media, name='delete_media_no_slash'),
]