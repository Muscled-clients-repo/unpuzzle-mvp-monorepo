# Django REST Framework API Implementation
**Date**: 2025-08-23  
**Time**: 10:45:00  
**Component**: RESTful API Layer

## Overview

Complete implementation of all API endpoints using Django REST Framework, maintaining 100% compatibility with existing Flask endpoints while adding enhanced features.

## API Configuration

### DRF Settings
```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.CustomPageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'core.throttling.BurstRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'burst': '60/minute',
        'auth': '5/minute',
        'upload': '10/hour',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('JWT_SECRET_KEY'),
    'VERIFYING_KEY': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    'TOKEN_USER_CLASS': 'apps.accounts.models.User',
}
```

## Authentication API

### Serializers
```python
# apps/accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Role, UserSession

class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    role = serializers.CharField(write_only=True, required=False, default='student')
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm', 'full_name',
            'username', 'role'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        role_name = validated_data.pop('role', 'student')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            username=validated_data.get('username')
        )
        
        # Assign role
        role = Role.objects.get(name=role_name)
        user.custom_roles.add(role)
        
        return user

class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('Account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Email and password required')
        
        return attrs

class UserSerializer(serializers.ModelSerializer):
    """User detail serializer"""
    roles = serializers.StringRelatedField(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'display_name',
            'avatar', 'bio', 'phone', 'status', 'email_verified',
            'roles', 'permissions', 'created_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'last_login']
    
    def get_permissions(self, obj):
        return obj.get_all_permissions()

class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect')
        return value
```

### Views
```python
# apps/accounts/views.py
from rest_framework import status, generics, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import login, logout
from .serializers import *
from .models import User, UserSession
from services.auth_service import AuthService

class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = ['auth']
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Create session
        AuthService.create_session(
            user=user,
            request=request,
            access_token=str(refresh.access_token),
            refresh_token=str(refresh)
        )
        
        return Response({
            'success': True,
            'data': {
                'user': UserSerializer(user).data,
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh)
            }
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    """User login endpoint"""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = ['auth']
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Create session
        AuthService.create_session(
            user=user,
            request=request,
            access_token=str(refresh.access_token),
            refresh_token=str(refresh)
        )
        
        # Update last login
        user.save_last_login(request)
        
        return Response({
            'success': True,
            'data': {
                'user': UserSerializer(user).data,
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh)
            }
        })

class LogoutView(generics.GenericAPIView):
    """User logout endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Blacklist refresh token
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Invalidate session
            AuthService.invalidate_session(request.user)
            
            return Response({
                'success': True,
                'message': 'Successfully logged out'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    """User management viewset"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter based on user permissions"""
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Invalidate all sessions except current
        AuthService.invalidate_other_sessions(user, request)
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        })
    
    @action(detail=False, methods=['post'])
    def upload_avatar(self, request):
        """Upload user avatar"""
        file = request.FILES.get('avatar')
        if not file:
            return Response({
                'success': False,
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.avatar = file
        request.user.save()
        
        return Response({
            'success': True,
            'data': {
                'avatar_url': request.user.avatar.url
            }
        })
```

## Course Management API

### Serializers
```python
# apps/courses/serializers.py
from rest_framework import serializers
from .models import Course, CourseSection, CourseCategory
from apps.accounts.serializers import UserSerializer

class CourseCategorySerializer(serializers.ModelSerializer):
    """Course category serializer"""
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'slug', 'description', 'parent', 'icon']

class CourseSectionSerializer(serializers.ModelSerializer):
    """Course section serializer"""
    media_files = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseSection
        fields = [
            'id', 'title', 'description', 'order',
            'is_published', 'is_preview', 'media_files'
        ]
    
    def get_media_files(self, obj):
        from apps.media_library.serializers import MediaFileSerializer
        return MediaFileSerializer(
            obj.media_files.filter(is_deleted=False),
            many=True
        ).data

class CourseListSerializer(serializers.ModelSerializer):
    """Course list serializer (lightweight)"""
    instructor = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'thumbnail',
            'price', 'is_free', 'duration', 'difficulty', 'instructor',
            'category', 'rating_average', 'rating_count', 'enrollment_count'
        ]

class CourseDetailSerializer(serializers.ModelSerializer):
    """Course detail serializer (full data)"""
    instructor = UserSerializer(read_only=True)
    category = CourseCategorySerializer(read_only=True)
    sections = CourseSectionSerializer(many=True, read_only=True)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'thumbnail', 'preview_video_url', 'instructor', 'price',
            'currency', 'discount_price', 'is_free', 'duration',
            'difficulty', 'language', 'category', 'tags',
            'prerequisites', 'learning_outcomes', 'target_audience',
            'sections', 'enrollment_count', 'completion_count',
            'rating_average', 'rating_count', 'status', 'is_published',
            'published_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'slug', 'enrollment_count', 'completion_count',
            'rating_average', 'rating_count', 'published_at'
        ]

class CourseCreateSerializer(serializers.ModelSerializer):
    """Course creation serializer"""
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'short_description', 'thumbnail',
            'preview_video_url', 'price', 'currency', 'discount_price',
            'is_free', 'difficulty', 'language', 'category', 'tags',
            'prerequisites', 'learning_outcomes', 'target_audience'
        ]
    
    def create(self, validated_data):
        validated_data['instructor'] = self.context['request'].user
        return super().create(validated_data)
```

### Views
```python
# apps/courses/views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, CourseSection
from .serializers import *
from .permissions import IsInstructorOrReadOnly, IsOwnerOrReadOnly
from .filters import CourseFilter
from services.course_service import CourseService

class CourseViewSet(viewsets.ModelViewSet):
    """Course management viewset"""
    queryset = Course.objects.select_related(
        'instructor', 'category'
    ).prefetch_related('sections', 'sections__media_files')
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'price', 'rating_average', 'enrollment_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        elif self.action == 'create':
            return CourseCreateSerializer
        return CourseDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated, IsInstructorOrReadOnly]
        else:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter published courses for non-staff users
        if not self.request.user.is_staff:
            if self.action in ['list', 'retrieve']:
                queryset = queryset.filter(is_published=True, status='published')
            else:
                queryset = queryset.filter(instructor=self.request.user)
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrReadOnly])
    def publish(self, request, pk=None):
        """Publish a course"""
        course = self.get_object()
        
        # Validate course is ready for publishing
        errors = CourseService.validate_for_publishing(course)
        if errors:
            return Response({
                'success': False,
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Publish course
        CourseService.publish_course(course)
        
        return Response({
            'success': True,
            'data': {
                'status': course.status,
                'published_at': course.published_at
            }
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrReadOnly])
    def unpublish(self, request, pk=None):
        """Unpublish a course"""
        course = self.get_object()
        CourseService.unpublish_course(course)
        
        return Response({
            'success': True,
            'message': 'Course unpublished successfully'
        })
    
    @action(detail=True, methods=['get'])
    def curriculum(self, request, pk=None):
        """Get course curriculum"""
        course = self.get_object()
        sections = course.sections.filter(is_deleted=False).order_by('order')
        serializer = CourseSectionSerializer(sections, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrReadOnly])
    def duplicate(self, request, pk=None):
        """Duplicate a course"""
        course = self.get_object()
        new_course = CourseService.duplicate_course(course)
        serializer = CourseDetailSerializer(new_course)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

class CourseSectionViewSet(viewsets.ModelViewSet):
    """Course section management"""
    queryset = CourseSection.objects.all()
    serializer_class = CourseSectionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return CourseSection.objects.filter(
            course_id=course_id,
            is_deleted=False
        ).order_by('order')
    
    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_id')
        course = Course.objects.get(id=course_id)
        
        # Check permission
        if course.instructor != self.request.user:
            raise PermissionDenied('You can only add sections to your own courses')
        
        serializer.save(course=course)
    
    @action(detail=False, methods=['post'])
    def reorder(self, request, course_id=None):
        """Reorder course sections"""
        course = Course.objects.get(id=course_id)
        
        if course.instructor != request.user:
            raise PermissionDenied('You can only reorder sections in your own courses')
        
        sections = request.data.get('sections', [])
        for section_data in sections:
            CourseSection.objects.filter(
                id=section_data['id'],
                course=course
            ).update(order=section_data['order'])
        
        return Response({
            'success': True,
            'message': 'Sections reordered successfully'
        })
```

## Student/Enrollment API

### Serializers
```python
# apps/enrollments/serializers.py
from rest_framework import serializers
from .models import Enrollment, CourseProgress, VideoProgress
from apps.courses.serializers import CourseListSerializer

class EnrollmentSerializer(serializers.ModelSerializer):
    """Enrollment serializer"""
    course = CourseListSerializer(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'enrolled_at', 'completed_at',
            'status', 'progress_percentage', 'last_accessed',
            'certificate_issued', 'certificate_url'
        ]
        read_only_fields = ['enrolled_at', 'completed_at', 'certificate_issued']

class CourseProgressSerializer(serializers.ModelSerializer):
    """Course progress serializer"""
    class Meta:
        model = CourseProgress
        fields = [
            'id', 'course', 'section', 'completed_videos',
            'last_video_id', 'total_watch_time', 'completion_percentage',
            'last_updated'
        ]

class VideoProgressSerializer(serializers.ModelSerializer):
    """Video progress serializer"""
    class Meta:
        model = VideoProgress
        fields = [
            'id', 'video', 'course', 'watch_time', 'last_position',
            'completed', 'completion_percentage'
        ]
```

### Views
```python
# apps/enrollments/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Enrollment, CourseProgress, VideoProgress
from .serializers import *
from services.enrollment_service import EnrollmentService

class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    """Student enrollment management"""
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Enrollment.objects.filter(
            user=self.request.user
        ).select_related('course', 'course__instructor')
    
    @action(detail=False, methods=['post'])
    def enroll(self, request):
        """Enroll in a course"""
        course_id = request.data.get('course_id')
        
        if not course_id:
            return Response({
                'success': False,
                'error': 'Course ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            enrollment = EnrollmentService.enroll_student(
                user=request.user,
                course_id=course_id
            )
            serializer = self.get_serializer(enrollment)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Successfully enrolled in course'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def drop(self, request, pk=None):
        """Drop a course"""
        enrollment = self.get_object()
        EnrollmentService.drop_course(enrollment)
        
        return Response({
            'success': True,
            'message': 'Course dropped successfully'
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active enrollments"""
        enrollments = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(enrollments, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get completed courses"""
        enrollments = self.get_queryset().filter(status='completed')
        serializer = self.get_serializer(enrollments, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })

class ProgressViewSet(viewsets.GenericViewSet):
    """Progress tracking viewset"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def course(self, request):
        """Get course progress"""
        course_id = request.query_params.get('course_id')
        
        if not course_id:
            return Response({
                'success': False,
                'error': 'Course ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        progress = CourseProgress.objects.filter(
            user=request.user,
            course_id=course_id
        ).first()
        
        if not progress:
            return Response({
                'success': True,
                'data': {
                    'completion_percentage': 0,
                    'completed_videos': [],
                    'total_watch_time': 0
                }
            })
        
        serializer = CourseProgressSerializer(progress)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def update_video(self, request):
        """Update video progress"""
        data = request.data
        video_id = data.get('video_id')
        course_id = data.get('course_id')
        watch_time = data.get('watch_time', 0)
        last_position = data.get('last_position', 0)
        completed = data.get('completed', False)
        
        try:
            video_progress, course_progress = EnrollmentService.update_progress(
                user=request.user,
                video_id=video_id,
                course_id=course_id,
                watch_time=watch_time,
                last_position=last_position,
                completed=completed
            )
            
            return Response({
                'success': True,
                'data': {
                    'video_progress': VideoProgressSerializer(video_progress).data,
                    'course_progress': CourseProgressSerializer(course_progress).data
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
```

## Media Upload API

### Serializers
```python
# apps/media_library/serializers.py
from rest_framework import serializers
from .models import MediaFile

class MediaFileSerializer(serializers.ModelSerializer):
    """Media file serializer"""
    class Meta:
        model = MediaFile
        fields = [
            'id', 'file_name', 'file_type', 'mime_type', 'file_size',
            'public_url', 'thumbnail_url', 'duration', 'resolution',
            'processing_status', 'is_public', 'is_downloadable',
            'order_index', 'created_at'
        ]
        read_only_fields = [
            'public_url', 'thumbnail_url', 'processing_status'
        ]

class MediaUploadInitSerializer(serializers.Serializer):
    """Media upload initialization serializer"""
    file_name = serializers.CharField(max_length=255)
    file_size = serializers.IntegerField()
    mime_type = serializers.CharField(max_length=100)
    course_id = serializers.UUIDField(required=False)
    section_id = serializers.UUIDField(required=False)

class MediaUploadCompleteSerializer(serializers.Serializer):
    """Media upload completion serializer"""
    upload_id = serializers.UUIDField()
    file_id = serializers.CharField()
```

### Views
```python
# apps/media_library/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from .models import MediaFile
from .serializers import *
from services.media_service import MediaService

class MediaUploadViewSet(viewsets.ModelViewSet):
    """Media file management"""
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    
    def get_queryset(self):
        return MediaFile.objects.filter(
            user=self.request.user,
            is_deleted=False
        )
    
    @action(detail=False, methods=['post'])
    def init(self, request):
        """Initialize media upload"""
        serializer = MediaUploadInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            upload_data = MediaService.initialize_upload(
                user=request.user,
                **serializer.validated_data
            )
            
            return Response({
                'success': True,
                'data': upload_data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def complete(self, request):
        """Complete media upload"""
        serializer = MediaUploadCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            media_file = MediaService.complete_upload(
                user=request.user,
                **serializer.validated_data
            )
            
            return Response({
                'success': True,
                'data': MediaFileSerializer(media_file).data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def direct(self, request):
        """Direct file upload"""
        file = request.FILES.get('file')
        if not file:
            return Response({
                'success': False,
                'error': 'No file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        course_id = request.data.get('course_id')
        section_id = request.data.get('section_id')
        
        try:
            media_file = MediaService.direct_upload(
                user=request.user,
                file=file,
                course_id=course_id,
                section_id=section_id
            )
            
            return Response({
                'success': True,
                'data': MediaFileSerializer(media_file).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
```

## Instructor Analytics API

```python
# apps/analytics/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from services.analytics_service import AnalyticsService
from apps.courses.permissions import IsInstructor

class InstructorAnalyticsViewSet(viewsets.GenericViewSet):
    """Instructor analytics viewset"""
    permission_classes = [IsAuthenticated, IsInstructor]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get instructor overview analytics"""
        data = AnalyticsService.get_instructor_overview(request.user)
        
        return Response({
            'success': True,
            'data': data
        })
    
    @action(detail=False, methods=['get'])
    def course(self, request):
        """Get course analytics"""
        course_id = request.query_params.get('course_id')
        
        if not course_id:
            return Response({
                'success': False,
                'error': 'Course ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = AnalyticsService.get_course_analytics(
            course_id=course_id,
            instructor=request.user
        )
        
        return Response({
            'success': True,
            'data': data
        })
    
    @action(detail=False, methods=['get'])
    def students(self, request):
        """Get student analytics for a course"""
        course_id = request.query_params.get('course_id')
        
        if not course_id:
            return Response({
                'success': False,
                'error': 'Course ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = AnalyticsService.get_student_analytics(
            course_id=course_id,
            instructor=request.user
        )
        
        return Response({
            'success': True,
            'data': data
        })
    
    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """Get revenue analytics"""
        period = request.query_params.get('period', 'month')
        data = AnalyticsService.get_revenue_analytics(
            instructor=request.user,
            period=period
        )
        
        return Response({
            'success': True,
            'data': data
        })
```

## Custom Permissions

```python
# apps/courses/permissions.py
from rest_framework import permissions

class IsInstructor(permissions.BasePermission):
    """Check if user is an instructor"""
    def has_permission(self, request, view):
        return request.user.custom_roles.filter(name='instructor').exists()

class IsInstructorOrReadOnly(permissions.BasePermission):
    """Allow instructors to write, everyone to read"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.custom_roles.filter(name='instructor').exists()

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow owners to edit, everyone to read"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if object has instructor field
        if hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        
        # Check if object has user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False

class IsAdminUser(permissions.BasePermission):
    """Check if user is an admin"""
    def has_permission(self, request, view):
        return request.user.is_staff or request.user.custom_roles.filter(name='admin').exists()
```

## API Filters

```python
# apps/courses/filters.py
import django_filters
from .models import Course

class CourseFilter(django_filters.FilterSet):
    """Course filtering"""
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    difficulty = django_filters.MultipleChoiceFilter(
        field_name='difficulty',
        choices=Course.DifficultyLevel.choices
    )
    category = django_filters.CharFilter(field_name='category__slug')
    is_free = django_filters.BooleanFilter(field_name='is_free')
    instructor = django_filters.CharFilter(field_name='instructor__username')
    rating = django_filters.NumberFilter(field_name='rating_average', lookup_expr='gte')
    
    class Meta:
        model = Course
        fields = [
            'difficulty', 'category', 'is_free', 'instructor',
            'language', 'status'
        ]
```

## Custom Pagination

```python
# core/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomPageNumberPagination(PageNumberPagination):
    """Custom pagination with metadata"""
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'data': {
                'results': data,
                'pagination': {
                    'page': self.page.number,
                    'limit': self.page.paginator.per_page,
                    'total': self.page.paginator.count,
                    'pages': self.page.paginator.num_pages,
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link()
                }
            }
        })
```

## Exception Handling

```python
# core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """Custom exception handler with logging"""
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error
        logger.error(
            f"API Error: {exc.__class__.__name__} - {str(exc)}",
            exc_info=True,
            extra={
                'request': context['request'],
                'view': context['view']
            }
        )
        
        # Format error response
        if isinstance(exc, ValidationError):
            errors = response.data
        else:
            errors = str(exc)
        
        custom_response_data = {
            'success': False,
            'error': {
                'code': exc.__class__.__name__,
                'message': str(exc),
                'details': errors if isinstance(exc, ValidationError) else None
            }
        }
        
        response.data = custom_response_data
    
    return response
```

## API Documentation

```python
# config/urls.py - Add API documentation
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

---
**Document Version**: 1.0  
**Last Updated**: 2025-08-23  
**Next Document**: Django Services Architecture