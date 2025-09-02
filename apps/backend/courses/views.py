"""
Course management views.
"""
import logging
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Avg, Count, F, Sum
from django.db import transaction, IntegrityError
from accounts.models import UserProfile, UserRole, Role
from accounts.permissions import PermissionService, PermissionConstants
from decimal import Decimal

logger = logging.getLogger(__name__)

from .models import (
    Course, CourseSection, CourseCategory
)
from enrollments.models import Enrollment, CourseReview
from accounts.models import Session
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseCreateUpdateSerializer,
    EnrollmentSerializer, EnrollmentCreateSerializer, CourseReviewSerializer, 
    CourseReviewCreateSerializer, SessionSerializer,
    CourseSectionCreateUpdateSerializer, CourseAnalyticsSerializer,
    CourseCategorySerializer, CourseLearningSerializer, SectionContentSerializer,
    EnrollmentProgressSerializer
)


class StandardResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100


def get_user_profile(request):
    """Helper to get user profile from request"""
    if not hasattr(request, 'user_id') or not request.user_id:
        return None
    try:
        return UserProfile.objects.get(supabase_user_id=request.user_id)
    except UserProfile.DoesNotExist:
        return None


# ============================================================================
# PUBLIC COURSE ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_courses(request):
    """Get all public courses with filtering and sorting"""
    
    # Base queryset - accept both 'active' and 'published' status
    queryset = Course.objects.filter(
        is_published=True, 
        status__in=['published', 'active']
    )
    
    # Filtering
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(tags__contains=[search])
        )
    
    difficulty = request.GET.get('difficulty', '').strip()
    if difficulty and difficulty != 'all':
        queryset = queryset.filter(difficulty=difficulty)
    
    category = request.GET.get('category', '').strip()
    if category:
        queryset = queryset.filter(category__slug=category)
    
    price_range = request.GET.get('priceRange', '').strip()
    if price_range == 'free':
        queryset = queryset.filter(is_free=True)
    elif price_range == 'paid':
        queryset = queryset.filter(is_free=False)
    
    min_rating = request.GET.get('minRating', '').strip()
    if min_rating:
        try:
            min_rating = float(min_rating)
            queryset = queryset.filter(rating_average__gte=min_rating)
        except ValueError:
            pass
    
    instructor = request.GET.get('instructor', '').strip()
    if instructor:
        queryset = queryset.filter(
            Q(instructor__full_name__icontains=instructor) |
            Q(instructor__display_name__icontains=instructor)
        )
    
    # Sorting
    sort_by = request.GET.get('sortBy', 'newest')
    if sort_by == 'popular':
        queryset = queryset.order_by('-enrollment_count', '-rating_average')
    elif sort_by == 'newest':
        queryset = queryset.order_by('-created_at')
    elif sort_by == 'price-asc':
        queryset = queryset.order_by('price')
    elif sort_by == 'price-desc':
        queryset = queryset.order_by('-price')
    elif sort_by == 'rating':
        queryset = queryset.order_by('-rating_average', '-rating_count')
    else:
        queryset = queryset.order_by('-created_at')
    
    # Pagination
    paginator = StandardResultsPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = CourseListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = CourseListSerializer(queryset, many=True, context={'request': request})
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_course_detail(request, course_id):
    """Get detailed course information"""
    course = get_object_or_404(Course, id=course_id, is_published=True, status__in=['published', 'active'])
    
    serializer = CourseDetailSerializer(course, context={'request': request})
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_course_reviews(request, course_id):
    """Get course reviews with pagination"""
    course = get_object_or_404(Course, id=course_id, is_published=True, status__in=['published', 'active'])
    
    reviews = CourseReview.objects.filter(
        enrollment__course=course,
    ).select_related('enrollment__user').order_by('-is_featured', '-created_at')
    
    # Pagination
    paginator = StandardResultsPagination()
    page = paginator.paginate_queryset(reviews, request)
    
    if page is not None:
        serializer = CourseReviewSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    serializer = CourseReviewSerializer(reviews, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['GET'])
def get_recommended_courses(request):
    """Get personalized course recommendations"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Simple recommendation based on user's enrolled courses and ratings
    # In a real system, this would use ML algorithms
    
    enrolled_courses = Course.objects.filter(
        enrollments__user=user_profile,
        enrollments__status='active'
    ).values_list('id', flat=True)
    
    # Get courses with similar tags or categories
    recommendations = Course.objects.filter(
        is_published=True,
        status__in=['published', 'active']
    ).exclude(id__in=enrolled_courses).order_by(
        '-rating_average', '-enrollment_count'
    )[:10]
    
    serializer = CourseListSerializer(recommendations, many=True, context={'request': request})
    return Response({
        'success': True,
        'data': serializer.data
    })


# ============================================================================
# STUDENT ENDPOINTS
# ============================================================================

@api_view(['GET'])
def get_enrolled_courses(request):
    """Get courses the student is enrolled in"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    enrollments = Enrollment.objects.filter(
        user=user_profile,
        status='active'
    ).select_related('course', 'course__instructor').order_by('-enrolled_at')
    
    courses = [enrollment.course for enrollment in enrollments]
    serializer = CourseListSerializer(courses, many=True, context={'request': request})
    
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['POST'])
def enroll_in_course(request, course_id):
    """Enroll in a course"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    # Check if already enrolled (including all statuses)
    existing_enrollment = Enrollment.objects.filter(
        user=user_profile,
        course=course
    ).first()
    
    if existing_enrollment:
        # Check the status and handle accordingly
        if existing_enrollment.status == 'active':
            return Response({
                'error': 'You are already enrolled in this course',
                'success': False,
                'enrollment_id': existing_enrollment.id
            }, status=400)
        elif existing_enrollment.status in ['cancelled', 'expired', 'suspended']:
            # Reactivate enrollment
            existing_enrollment.status = 'active'
            existing_enrollment.enrolled_at = timezone.now()
            existing_enrollment.save()
            
            return Response({
                'success': True,
                'enrollment_id': existing_enrollment.id,
                'message': 'Successfully re-enrolled in course'
            })
        elif existing_enrollment.status == 'completed':
            return Response({
                'error': 'You have already completed this course',
                'success': False,
                'enrollment_id': existing_enrollment.id
            }, status=400)
    
    # Debug: Log course price
    logger.error(f"DEBUG COURSES: Course '{course.title}' price = {course.price}, type = {type(course.price)}")
    
    # Check if course requires payment
    if course.price > 0:
        # Import payment services
        from payments.services import StripePaymentService, PaymentValidationService
        
        # Validate enrollment
        validation = PaymentValidationService.validate_course_enrollment(user_profile, course)
        if not validation['valid']:
            return Response({'error': validation['error'], 'success': False}, status=400)
        
        # Create payment intent for paid courses
        try:
            payment_intent, client_secret = StripePaymentService.create_payment_intent(
                user_profile=user_profile,
                course=course,
                amount=validation['amount'],
                currency=course.currency,
                metadata={}
            )
            
            return Response({
                'success': True,
                'requires_payment': True,
                'payment_id': payment_intent.payment_id,
                'client_secret': client_secret,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'course_id': str(course.id),
                'course_title': course.title,
                'message': 'Payment intent created. Complete payment to enroll.'
            })
            
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            return Response({
                'error': 'Failed to create payment intent',
                'success': False
            }, status=500)
    
    serializer = EnrollmentCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': serializer.errors, 'success': False}, status=400)
    
    validated_data = serializer.validated_data
    
    # Calculate total lessons for progress tracking
    # Since lessons model doesn't exist, we'll use sections count for now
    total_sections = course.sections.filter(is_published=True).count()
    
    try:
        with transaction.atomic():
            # Create enrollment (only for free courses)
            enrollment = Enrollment.objects.create(
                user=user_profile,
                course=course,
                payment_method='free',
                payment_amount=Decimal('0.00'),
                payment_currency=course.currency,
                total_lessons=total_sections,  # Using sections count as lessons for now
                enrolled_at=timezone.now(),
                started_at=timezone.now()
            )
            
            # Update course enrollment count
            course.enrollment_count = F('enrollment_count') + 1
            course.save(update_fields=['enrollment_count'])
        
        return Response({
            'success': True,
            'enrollment_id': enrollment.id,
            'message': 'Successfully enrolled in course'
        })
    except IntegrityError:
        # This handles the rare case where another enrollment was created between our check and create
        # (race condition in concurrent requests)
        existing_enrollment = Enrollment.objects.filter(
            user=user_profile,
            course=course
        ).first()
        
        if existing_enrollment and existing_enrollment.status == 'active':
            return Response({
                'error': 'You are already enrolled in this course',
                'success': False,
                'enrollment_id': existing_enrollment.id
            }, status=400)
        else:
            return Response({
                'error': 'Failed to enroll in course. Please try again.',
                'success': False
            }, status=500)


@api_view(['POST'])
def unenroll_from_course(request, course_id):
    """Unenroll from a course"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    enrollment = get_object_or_404(
        Enrollment,
        user=user_profile,
        course_id=course_id,
        status='active'
    )
    
    enrollment.status = 'cancelled'
    enrollment.save()
    
    return Response({
        'success': True,
        'message': 'Successfully unenrolled from course'
    })


@api_view(['GET'])
def get_course_progress(request, course_id):
    """Get detailed course progress"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    enrollment = get_object_or_404(
        Enrollment,
        user=user_profile,
        course_id=course_id,
        status='active'
    )
    
    return Response({
        'success': True,
        'data': {
            'user_id': user_profile.supabase_user_id,
            'course_id': course_id,
            'lessons_completed': enrollment.lessons_completed,
            'total_lessons': enrollment.total_lessons,
            'progress_percentage': enrollment.progress_percentage,
            'last_accessed_at': enrollment.last_accessed_at,
            'certificate_earned_at': enrollment.completed_at
        }
    })


@api_view(['GET'])
def get_lesson_progress(request, lesson_id):
    """Get detailed lesson progress"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    try:
        progress = LessonProgress.objects.get(user=user_profile, lesson=lesson)
        serializer = LessonProgressSerializer(progress)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except LessonProgress.DoesNotExist:
        return Response({
            'success': True,
            'data': {
                'user_id': user_profile.supabase_user_id,
                'lesson_id': lesson_id,
                'watched_seconds': 0,
                'total_seconds': lesson.video_duration,
                'progress_percentage': 0,
                'last_watched_at': None,
                'completed_at': None,
                'quiz_attempts': [],
                'bookmarks': []
            }
        })


@api_view(['PUT'])
def update_lesson_progress(request, lesson_id):
    """Update lesson progress"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Get or create enrollment
    enrollment = Enrollment.objects.filter(
        user=user_profile,
        course=lesson.section.course,
        status='active'
    ).first()
    
    if not enrollment:
        return Response({'error': 'Not enrolled in this course'}, status=403)
    
    # Get or create progress
    progress, created = LessonProgress.objects.get_or_create(
        user=user_profile,
        lesson=lesson,
        enrollment=enrollment,
        defaults={
            'total_seconds': lesson.video_duration,
            'watched_seconds': 0,
            'last_position': 0
        }
    )
    
    serializer = LessonProgressUpdateSerializer(progress, data=request.data)
    if not serializer.is_valid():
        return Response({'error': serializer.errors, 'success': False}, status=400)
    
    progress = serializer.save()
    
    # Update enrollment last accessed time
    enrollment.last_accessed_at = timezone.now()
    enrollment.save(update_fields=['last_accessed_at'])
    
    return Response({
        'success': True,
        'progress_percentage': progress.progress_percentage
    })


@api_view(['POST'])
def mark_lesson_complete(request, lesson_id):
    """Mark a lesson as completed"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Get enrollment
    enrollment = get_object_or_404(
        Enrollment,
        user=user_profile,
        course=lesson.section.course,
        status='active'
    )
    
    # Get or create progress
    progress, created = LessonProgress.objects.get_or_create(
        user=user_profile,
        lesson=lesson,
        enrollment=enrollment,
        defaults={
            'total_seconds': lesson.video_duration,
            'watched_seconds': lesson.video_duration
        }
    )
    
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.watched_seconds = progress.total_seconds
        progress.save()
        
        # Update enrollment progress
        completed_lessons = enrollment.lesson_progress.filter(is_completed=True).count()
        enrollment.lessons_completed = completed_lessons
        enrollment.progress_percentage = (completed_lessons / enrollment.total_lessons) * 100 if enrollment.total_lessons > 0 else 0
        enrollment.save(update_fields=['lessons_completed', 'progress_percentage'])
    
    return Response({
        'success': True,
        'completed_at': progress.completed_at
    })


@api_view(['POST'])
def submit_quiz_answer(request, lesson_id, quiz_id):
    """Submit quiz answer"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    quiz = get_object_or_404(QuizQuestion, id=quiz_id, lesson_id=lesson_id)
    
    serializer = QuizAnswerSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': serializer.errors, 'success': False}, status=400)
    
    answer = serializer.validated_data['answer']
    time_spent = serializer.validated_data.get('time_spent', 0)
    
    is_correct = answer == quiz.correct_answer
    
    # Record attempt
    attempt_data = {
        'answer': answer,
        'correct': is_correct,
        'time_spent': time_spent,
        'timestamp': timezone.now().isoformat()
    }
    
    # Get or create progress to store quiz attempt
    progress, created = LessonProgress.objects.get_or_create(
        user=user_profile,
        lesson=quiz.lesson,
        defaults={'total_seconds': quiz.lesson.video_duration}
    )
    
    quiz_attempts = progress.quiz_attempts or []
    quiz_attempts.append({
        'quiz_id': quiz.id,
        **attempt_data
    })
    progress.quiz_attempts = quiz_attempts
    progress.save(update_fields=['quiz_attempts'])
    
    return Response({
        'success': True,
        'correct': is_correct,
        'explanation': quiz.explanation if is_correct else '',
        'correct_answer': quiz.correct_answer if not is_correct else None
    })


@api_view(['POST'])
def submit_course_review(request, course_id):
    """Submit or update course review"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    enrollment = Enrollment.objects.filter(
        user=user_profile,
        course=course,
        status='active'
    ).first()
    
    if not enrollment:
        return Response({'error': 'Must be enrolled to review'}, status=403)
    
    serializer = CourseReviewCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': serializer.errors, 'success': False}, status=400)
    
    # Update or create review
    review, created = CourseReview.objects.update_or_create(
        user=user_profile,
        course=course,
        enrollment=enrollment,
        defaults={
            **serializer.validated_data,
            'is_verified': True  # Since they're enrolled
        }
    )
    
    # Update course rating statistics
    with transaction.atomic():
        ratings = CourseReview.objects.filter(course=course, is_hidden=False)
        course.rating_average = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
        course.rating_count = ratings.count()
        course.save(update_fields=['rating_average', 'rating_count'])
    
    return Response({
        'success': True,
        'review_id': review.id,
        'message': 'Review submitted successfully'
    })


# ============================================================================
# INSTRUCTOR ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
def get_instructor_courses(request):
    """Handle instructor courses - GET to list, POST to create"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has instructor role or higher
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_CREATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to access this endpoint'
        }, status=403)
    
    if request.method == 'GET':
        # List instructor's courses
        courses = Course.objects.filter(
            instructor=user_profile
        ).select_related('category').order_by('-created_at')
        
        # Add analytics data
        courses_data = []
        for course in courses:
            serializer = CourseDetailSerializer(course, context={'request': request})
            course_data = serializer.data
            
            # Add instructor-specific analytics
            course_data['analytics'] = {
                'total_revenue': course.enrollments.filter(status='active').aggregate(
                    Sum('payment_amount'))['payment_amount__sum'] or 0,
                'active_students': course.enrollments.filter(status='active').count(),
                'completion_rate': _calculate_completion_rate(course)
            }
            courses_data.append(course_data)
        
        return Response({
            'success': True,
            'data': courses_data
        })
    
    elif request.method == 'POST':
        # Create a new course
        serializer = CourseCreateUpdateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'error': serializer.errors, 'success': False}, status=400)
        
        course = serializer.save()
        
        # Return detailed course data
        response_serializer = CourseDetailSerializer(course, context={'request': request})
        return Response({
            'success': True,
            'data': response_serializer.data
        }, status=201)


@api_view(['GET', 'PUT', 'PATCH'])
def get_instructor_course_detail(request, course_id):
    """Get or update detailed course info for instructor"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has instructor role
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to access this endpoint'
        }, status=403)
    
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    
    if request.method == 'GET':
        serializer = CourseDetailSerializer(course, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method in ['PUT', 'PATCH']:
        # Update course
        partial = request.method == 'PATCH'
        serializer = CourseCreateUpdateSerializer(
            course, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({'error': serializer.errors, 'success': False}, status=400)
        
        course = serializer.save()
        
        response_serializer = CourseDetailSerializer(course, context={'request': request})
        return Response({
            'success': True,
            'data': response_serializer.data
        })


@api_view(['POST'])
def create_course(request):
    """Create a new course"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has instructor role
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_CREATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to create courses'
        }, status=403)
    
    serializer = CourseCreateUpdateSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response({'error': serializer.errors, 'success': False}, status=400)
    
    course = serializer.save()
    
    # Return detailed course data
    response_serializer = CourseDetailSerializer(course, context={'request': request})
    return Response({
        'success': True,
        'data': response_serializer.data
    }, status=201)


@api_view(['PUT'])
def update_course(request, course_id):
    """Update course details"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has instructor role
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to update courses'
        }, status=403)
    
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    
    serializer = CourseCreateUpdateSerializer(course, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response({'error': serializer.errors, 'success': False}, status=400)
    
    course = serializer.save()
    
    response_serializer = CourseDetailSerializer(course, context={'request': request})
    return Response({
        'success': True,
        'data': response_serializer.data
    })


@api_view(['DELETE'])
def delete_course(request, course_id):
    """Soft delete a course"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has instructor role
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_DELETE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to delete courses'
        }, status=403)
    
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    
    # Soft delete - set status to archived
    course.status = 'archived'
    course.is_published = False
    course.save(update_fields=['status', 'is_published'])
    
    return Response({
        'success': True,
        'message': 'Course deleted successfully'
    })


@api_view(['POST'])
def publish_course(request, course_id):
    """Publish a course"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has publish permission
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_PUBLISH):
        return Response({
            'error': 'Permission denied',
            'message': 'You need instructor permissions to publish courses'
        }, status=403)
    
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    
    # Check if course has at least one published section with content
    if not course.sections.filter(is_published=True).exists():
        return Response({
            'error': 'Course must have at least one published section to be published',
            'success': False
        }, status=400)
    
    course.status = 'published'
    course.is_published = True
    course.published_at = timezone.now()
    course.save(update_fields=['status', 'is_published', 'published_at'])
    
    return Response({
        'success': True,
        'is_published': True,
        'published_at': course.published_at
    })


@api_view(['POST'])
def unpublish_course(request, course_id):
    """Unpublish a course"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has publish permission
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_PUBLISH):
        return Response({
            'error': 'Permission denied',
            'message': 'You need instructor permissions to unpublish courses'
        }, status=403)
    
    course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    
    course.is_published = False
    course.status = 'draft'  # Changed from 'unpublished' to 'draft' to match frontend expectation
    course.save(update_fields=['is_published', 'status'])
    
    return Response({
        'success': True,
        'is_published': False
    })


@api_view(['POST'])
def duplicate_course(request, course_id):
    """Create a duplicate of an existing course"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has instructor role
    if not PermissionService.has_permission(request.user_id, PermissionConstants.COURSE_CREATE):
        return Response({
            'error': 'Instructor role required',
            'message': 'You need instructor permissions to duplicate courses'
        }, status=403)
    
    original_course = get_object_or_404(Course, id=course_id, instructor=user_profile)
    
    with transaction.atomic():
        # Create course copy
        course_copy = Course.objects.create(
            title=f"{original_course.title} (Copy)",
            slug=f"{original_course.slug}-copy",
            description=original_course.description,
            short_description=original_course.short_description,
            instructor=user_profile,
            price=original_course.price,
            currency=original_course.currency,
            is_free=original_course.is_free,
            duration=original_course.duration,
            difficulty=original_course.difficulty,
            language=original_course.language,
            category=original_course.category,
            tags=original_course.tags,
            prerequisites=original_course.prerequisites,
            learning_outcomes=original_course.learning_outcomes,
            target_audience=original_course.target_audience,
            course_structure=original_course.course_structure,
            status='draft',
            is_published=False
        )
        
        # Copy sections and lessons
        for section in original_course.sections.all():
            section_copy = CourseSection.objects.create(
                course=course_copy,
                title=section.title,
                description=section.description,
                order=section.order,
                is_published=section.is_published,
                is_preview=section.is_preview
            )
            
            for lesson in section.lessons.all():
                lesson_copy = Lesson.objects.create(
                    section=section_copy,
                    title=lesson.title,
                    description=lesson.description,
                    content=lesson.content,
                    video_url=lesson.video_url,
                    video_duration=lesson.video_duration,
                    order=lesson.order,
                    is_published=lesson.is_published,
                    is_preview=lesson.is_preview,
                    is_downloadable=lesson.is_downloadable,
                    resources=lesson.resources
                )
                
                # Copy quiz questions
                for quiz in lesson.quiz_questions.all():
                    QuizQuestion.objects.create(
                        lesson=lesson_copy,
                        question=quiz.question,
                        options=quiz.options,
                        correct_answer=quiz.correct_answer,
                        explanation=quiz.explanation,
                        timestamp=quiz.timestamp,
                        time_limit=quiz.time_limit,
                        is_required=quiz.is_required,
                        points=quiz.points
                    )
    
    return Response({
        'success': True,
        'data': {
            'id': course_copy.id,
            'title': course_copy.title,
            'description': course_copy.description,
            'is_published': course_copy.is_published,
            'created_at': course_copy.created_at
        }
    }, status=201)


def _calculate_completion_rate(course):
    """Helper function to calculate course completion rate"""
    total_enrollments = course.enrollments.filter(status='active').count()
    if total_enrollments == 0:
        return 0
    
    completed_enrollments = course.enrollments.filter(
        status='active',
        progress_percentage__gte=100
    ).count()
    
    return (completed_enrollments / total_enrollments) * 100


# Additional helper functions can be added here for analytics, etc.


# ============================================================================
# STUDENT LEARNING ENDPOINTS
# ============================================================================

@api_view(['GET'])
def get_course_for_learning(request, course_id):
    """Get course with sections for student learning page"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get course (must be published)
    course = get_object_or_404(Course, id=course_id, is_published=True, status__in=['published', 'active'])
    
    # Verify enrollment
    try:
        enrollment = Enrollment.objects.get(
            user=user_profile,
            course=course,
            status='active'
        )
    except Enrollment.DoesNotExist:
        return Response({
            'error': 'Access denied - Please enroll first to start learning',
            'success': False
        }, status=403)
    
    # Serialize course with sections
    course_serializer = CourseLearningSerializer(course, context={'request': request})
    enrollment_serializer = EnrollmentProgressSerializer(enrollment)
    
    return Response({
        'success': True,
        'data': {
            'course': course_serializer.data,
            'enrollment': enrollment_serializer.data
        }
    })


@api_view(['GET'])
def get_section_content(request, course_id, section_id):
    """Get section content with media files for enrolled students"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get course (must be published)
    course = get_object_or_404(Course, id=course_id, is_published=True, status__in=['published', 'active'])
    
    # Verify enrollment
    try:
        enrollment = Enrollment.objects.get(
            user=user_profile,
            course=course,
            status='active'
        )
    except Enrollment.DoesNotExist:
        return Response({
            'error': 'Access denied - Please enroll first to start learning',
            'success': False
        }, status=403)
    
    # Get section (must belong to course and be published)
    section = get_object_or_404(
        CourseSection,
        id=section_id,
        course=course,
        is_published=True
    )
    
    # Update last accessed time
    enrollment.last_accessed_at = timezone.now()
    enrollment.save(update_fields=['last_accessed_at'])
    
    # Serialize section with media files
    section_serializer = SectionContentSerializer(section, context={'request': request})
    
    # Calculate section progress (basic implementation)
    total_media = section.media_files.filter(processing_status='completed').count()
    # For now, assume no completion tracking per media file
    # This could be enhanced with actual progress tracking
    section_progress = {
        'section_progress_percentage': 0.0,
        'completed_media': 0,
        'total_media': total_media
    }
    
    return Response({
        'success': True,
        'data': {
            'section': section_serializer.data,
            'progress': section_progress
        }
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # We'll check enrollment inside
def get_section_media_for_students(request, section_id):
    """Get media files for a section with safe metadata (CDN URLs only for enrolled students)"""
    user_profile = get_user_profile(request)
    if not user_profile:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get section and verify it exists and is published
    section = get_object_or_404(CourseSection, id=section_id, is_published=True)
    
    # Check if user is enrolled in the course
    is_enrolled = False
    enrollment = None
    try:
        enrollment = Enrollment.objects.get(
            user=user_profile,
            course=section.course,
            status='active'
        )
        is_enrolled = True
    except Enrollment.DoesNotExist:
        # User not enrolled - they can see metadata but not CDN URLs
        is_enrolled = False
    
    # Get media files for this section
    media_files = section.media_files.filter(
        processing_status='completed'
    ).order_by('created_at')
    
    # Prepare media data - include CDN URL only for enrolled students
    media_data = []
    for media in media_files:
        media_item = {
            'id': media.id,
            'filename': media.filename,  # User-friendly name (e.g., "Introduction Video")
            'file_type': media.file_type,
            'file_size': media.file_size,
            'thumbnail': media.thumbnail_url if media.thumbnail_url else None,
            'duration': getattr(media, 'duration', None),
            'created_at': media.created_at,
            'updated_at': media.updated_at,
        }
        
        # Include CDN URL only for enrolled students
        if is_enrolled:
            media_item['cdn_url'] = media.cdn_url  # ✅ Enrolled students can access content
            # Never include storage_url - that's for internal use only
        else:
            media_item['cdn_url'] = None  # ❌ Non-enrolled users cannot access content
            media_item['access_message'] = 'Enroll in this course to access the content'
        
        media_data.append(media_item)
    
    # Update last accessed time only for enrolled users
    if is_enrolled and enrollment:
        enrollment.last_accessed_at = timezone.now()
        enrollment.save(update_fields=['last_accessed_at'])
    
    return Response({
        'success': True,
        'data': {
            'section': {
                'id': section.id,
                'title': section.title,
                'description': section.description,
                'order': section.order,
                'course_id': section.course.id,
                'course_title': section.course.title,
            },
            'media_files': media_data,
            'total_media': len(media_data),
            'is_enrolled': is_enrolled,
            'enrollment_status': 'active' if is_enrolled else 'not_enrolled'
        }
    })