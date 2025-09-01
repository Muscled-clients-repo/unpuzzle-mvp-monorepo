"""
Courses app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

app_name = 'courses'

urlpatterns = [
    # ============================================================================
    # PUBLIC COURSE ENDPOINTS (No Authentication Required)
    # ============================================================================
    
    # Course listing and details
    path('courses/', views.get_courses, name='get_courses'),
    path('courses/<uuid:course_id>/', views.get_course_detail, name='get_course_detail'),
    path('courses/<uuid:course_id>/reviews/', views.get_course_reviews, name='get_course_reviews'),
    path('courses/recommended/', views.get_recommended_courses, name='get_recommended_courses'),
    
    # ============================================================================
    # STUDENT ENDPOINTS (Authentication Required)
    # ============================================================================
    
    # Student course management  
    path('student/courses/', views.get_enrolled_courses, name='get_enrolled_courses'),
    path('courses/<uuid:course_id>/enroll/', views.enroll_in_course, name='enroll_in_course'),
    path('courses/<uuid:course_id>/unenroll/', views.unenroll_from_course, name='unenroll_from_course'),
    
    # Alternative student-prefixed enrollment routes (for frontend compatibility)
    path('student/courses/<uuid:course_id>/enroll/', views.enroll_in_course, name='student_enroll_in_course'),
    path('student/courses/<uuid:course_id>/unenroll/', views.unenroll_from_course, name='student_unenroll_from_course'),
    
    # Progress tracking
    path('student/courses/<uuid:course_id>/progress/', views.get_course_progress, name='get_course_progress'),
    path('videos/<int:lesson_id>/progress/', views.get_lesson_progress, name='get_lesson_progress'),
    path('videos/<int:lesson_id>/progress/update/', views.update_lesson_progress, name='update_lesson_progress'),
    path('student/videos/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    
    # Student Learning Routes
    path('student/courses/<uuid:course_id>/learn/', views.get_course_for_learning, name='course_learning'),
    path('student/courses/<uuid:course_id>/sections/<uuid:section_id>/content/', views.get_section_content, name='section_content'),
    path('sections/<uuid:section_id>/media/', views.get_section_media_for_students, name='section_media_list'),
    
    # Quiz and reviews
    path('student/videos/<int:lesson_id>/quiz/<int:quiz_id>/answer/', views.submit_quiz_answer, name='submit_quiz_answer'),
    path('student/courses/<uuid:course_id>/review/', views.submit_course_review, name='submit_course_review'),
    
    # ============================================================================
    # INSTRUCTOR ENDPOINTS (Authentication Required + Instructor Role)
    # ============================================================================
    
    # Course management
    path('instructor/courses/', views.get_instructor_courses, name='get_instructor_courses'),
    path('instructor/courses/create/', views.create_course, name='create_course'),
    path('instructor/courses/<uuid:course_id>/', views.get_instructor_course_detail, name='get_instructor_course_detail'),
    path('instructor/courses/<uuid:course_id>/update/', views.update_course, name='update_course'),
    path('instructor/courses/<uuid:course_id>/delete/', views.delete_course, name='delete_course'),
    
    # Course publishing
    path('instructor/courses/<uuid:course_id>/publish/', views.publish_course, name='publish_course'),
    path('instructor/courses/<uuid:course_id>/unpublish/', views.unpublish_course, name='unpublish_course'),
    path('instructor/courses/<uuid:course_id>/duplicate/', views.duplicate_course, name='duplicate_course'),
    
    # Include the router URLs
    path('', include(router.urls)),
]