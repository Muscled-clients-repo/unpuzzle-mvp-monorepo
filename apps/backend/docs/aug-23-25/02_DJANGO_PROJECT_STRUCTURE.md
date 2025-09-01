# Django Project Structure - Enterprise Architecture
**Date**: 2025-08-23  
**Time**: 10:15:00  
**Component**: Project Organization

## Project Structure Overview

The Django implementation follows enterprise best practices with a modular, scalable architecture designed for maintainability and growth.

## Complete Directory Structure

```
unpuzzle_django/                    # Root Django project
├── manage.py                        # Django management script
├── requirements/                    # Environment-specific requirements
│   ├── base.txt                    # Common dependencies
│   ├── development.txt              # Development dependencies
│   ├── production.txt               # Production dependencies
│   └── testing.txt                  # Testing dependencies
│
├── config/                          # Project configuration
│   ├── __init__.py
│   ├── settings/                    # Settings module
│   │   ├── __init__.py
│   │   ├── base.py                 # Base settings
│   │   ├── development.py          # Development settings
│   │   ├── production.py           # Production settings
│   │   └── testing.py              # Testing settings
│   ├── urls.py                      # Main URL configuration
│   ├── wsgi.py                      # WSGI configuration
│   ├── asgi.py                      # ASGI configuration (WebSocket)
│   └── celery.py                    # Celery configuration
│
├── apps/                            # Django applications
│   ├── __init__.py
│   │
│   ├── accounts/                    # User management app
│   │   ├── __init__.py
│   │   ├── models.py               # User, Role, Permission models
│   │   ├── serializers.py          # DRF serializers
│   │   ├── views.py                # API views
│   │   ├── urls.py                 # URL patterns
│   │   ├── managers.py             # Custom model managers
│   │   ├── permissions.py          # Custom permissions
│   │   ├── authentication.py       # Custom authentication
│   │   ├── signals.py              # Django signals
│   │   ├── tasks.py                # Celery tasks
│   │   ├── admin.py                # Admin configuration
│   │   ├── apps.py                 # App configuration
│   │   ├── migrations/             # Database migrations
│   │   └── tests/                  # Test suite
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_serializers.py
│   │
│   ├── courses/                     # Course management app
│   │   ├── __init__.py
│   │   ├── models.py               # Course, Section, Quiz models
│   │   ├── serializers.py          # Course serializers
│   │   ├── views.py                # Course API views
│   │   ├── urls.py                 # Course URLs
│   │   ├── filters.py              # Query filters
│   │   ├── pagination.py           # Custom pagination
│   │   ├── validators.py           # Custom validators
│   │   ├── signals.py              # Course signals
│   │   ├── tasks.py                # Background tasks
│   │   ├── admin.py                # Course admin
│   │   └── tests/
│   │
│   ├── enrollments/                 # Enrollment & Progress app
│   │   ├── __init__.py
│   │   ├── models.py               # Enrollment, Progress models
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py             # Business logic
│   │   ├── signals.py
│   │   └── tests/
│   │
│   ├── media_library/              # Media management app
│   │   ├── __init__.py
│   │   ├── models.py               # MediaFile model
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── storage.py              # Custom storage backends
│   │   ├── processors.py           # Media processors
│   │   ├── tasks.py                # Video processing tasks
│   │   └── tests/
│   │
│   ├── analytics/                   # Analytics app
│   │   ├── __init__.py
│   │   ├── models.py               # Analytics models
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── aggregators.py          # Data aggregation
│   │   ├── reports.py              # Report generation
│   │   └── tests/
│   │
│   ├── notifications/               # Notification app
│   │   ├── __init__.py
│   │   ├── models.py               # Notification models
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── handlers.py             # Notification handlers
│   │   ├── consumers.py            # WebSocket consumers
│   │   └── tests/
│   │
│   └── ai_assistant/               # AI Chat app
│       ├── __init__.py
│       ├── models.py               # Chat models
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       ├── services.py             # AI service integration
│       └── tests/
│
├── core/                            # Core functionality
│   ├── __init__.py
│   ├── models.py                   # Abstract base models
│   ├── mixins.py                   # Reusable mixins
│   ├── exceptions.py               # Custom exceptions
│   ├── validators.py               # Common validators
│   ├── permissions.py              # Base permissions
│   ├── pagination.py               # Base pagination
│   ├── throttling.py               # Rate limiting
│   ├── cache.py                    # Cache utilities
│   ├── storage.py                  # Storage utilities
│   └── utils.py                    # Common utilities
│
├── services/                        # Business logic services
│   ├── __init__.py
│   ├── auth_service.py             # Authentication service
│   ├── course_service.py           # Course management service
│   ├── enrollment_service.py       # Enrollment service
│   ├── media_service.py            # Media processing service
│   ├── analytics_service.py        # Analytics service
│   ├── notification_service.py     # Notification service
│   ├── email_service.py            # Email service
│   └── payment_service.py          # Payment processing
│
├── api/                             # API configuration
│   ├── __init__.py
│   ├── v1/                         # API version 1
│   │   ├── __init__.py
│   │   ├── urls.py                 # API v1 URLs
│   │   ├── serializers.py          # Common serializers
│   │   └── views.py                # Common views
│   └── v2/                         # API version 2 (future)
│
├── middleware/                      # Custom middleware
│   ├── __init__.py
│   ├── authentication.py           # Auth middleware
│   ├── cors.py                     # CORS middleware
│   ├── logging.py                  # Request logging
│   ├── security.py                 # Security headers
│   └── performance.py              # Performance monitoring
│
├── management/                      # Management commands
│   └── commands/
│       ├── __init__.py
│       ├── migrate_data.py         # Data migration
│       ├── cleanup_media.py        # Media cleanup
│       ├── generate_reports.py     # Report generation
│       └── seed_database.py        # Database seeding
│
├── static/                          # Static files
│   ├── css/
│   ├── js/
│   ├── img/
│   └── admin/                      # Admin customization
│
├── media/                           # User uploaded files
│   ├── avatars/
│   ├── thumbnails/
│   ├── documents/
│   └── temp/
│
├── templates/                       # Django templates
│   ├── base.html
│   ├── admin/                      # Admin templates
│   ├── email/                      # Email templates
│   └── errors/                     # Error pages
│
├── locale/                          # Internationalization
│   ├── en/
│   ├── es/
│   └── fr/
│
├── logs/                            # Application logs
│   ├── django.log
│   ├── celery.log
│   └── error.log
│
├── scripts/                         # Utility scripts
│   ├── deploy.sh
│   ├── backup.sh
│   └── migrate.sh
│
├── tests/                           # Integration tests
│   ├── __init__.py
│   ├── fixtures/                   # Test fixtures
│   ├── integration/                # Integration tests
│   └── e2e/                        # End-to-end tests
│
├── docs/                            # Documentation
│   ├── api/                        # API documentation
│   ├── deployment/                 # Deployment guides
│   └── development/                # Development guides
│
├── .env.example                     # Environment variables example
├── .gitignore                       # Git ignore file
├── .dockerignore                    # Docker ignore file
├── Dockerfile                       # Docker configuration
├── docker-compose.yml               # Docker Compose configuration
├── pytest.ini                       # Pytest configuration
├── setup.cfg                        # Project setup configuration
└── README.md                        # Project documentation
```

## App Structure Details

### 1. Accounts App
```python
# apps/accounts/models.py
class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with extended fields"""
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars/')
    bio = models.TextField(blank=True)
    status = models.CharField(choices=UserStatus.choices)
    email_verified = models.BooleanField(default=False)
    
class Role(models.Model):
    """Role model for RBAC"""
    name = models.CharField(max_length=50, unique=True)
    permissions = models.ManyToManyField(Permission)
    
class UserSession(models.Model):
    """Session management"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
```

### 2. Courses App
```python
# apps/courses/models.py
class Course(TimeStampedModel):
    """Course model with all features"""
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=CourseStatus.choices)
    
class CourseSection(models.Model):
    """Course sections for content organization"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    
class Quiz(models.Model):
    """Quiz model for assessments"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    passing_score = models.FloatField()
```

### 3. Core Module
```python
# core/models.py
class TimeStampedModel(models.Model):
    """Abstract base model with timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class SoftDeleteModel(models.Model):
    """Abstract model with soft delete"""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
```

## Configuration Structure

### Settings Organization
```python
# config/settings/base.py
"""Base settings for all environments"""

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'channels',
    'django_celery_beat',
    'django_filters',
    'storages',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.courses',
    'apps.enrollments',
    'apps.media_library',
    'apps.analytics',
    'apps.notifications',
    'apps.ai_assistant',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'middleware.logging.RequestLoggingMiddleware',
    'middleware.performance.PerformanceMiddleware',
]

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
        },
        'KEY_PREFIX': 'unpuzzle',
        'TIMEOUT': 300,
    }
}

# Celery configuration
CELERY_BROKER_URL = env('REDIS_URL')
CELERY_RESULT_BACKEND = env('REDIS_URL')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# Channels configuration for WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_URL')],
        },
    },
}
```

## URL Configuration

### Main URL Structure
```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.v1.urls')),
    path('api/v2/', include('api.v2.urls')),
    path('ws/', include('apps.notifications.routing')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
```

### API Version 1 URLs
```python
# api/v1/urls.py
from django.urls import path, include

app_name = 'v1'

urlpatterns = [
    path('auth/', include('apps.accounts.urls')),
    path('users/', include('apps.accounts.user_urls')),
    path('courses/', include('apps.courses.urls')),
    path('enrollments/', include('apps.enrollments.urls')),
    path('media/', include('apps.media_library.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('ai/', include('apps.ai_assistant.urls')),
]
```

## Development Workflow

### Local Development Setup
```bash
# Clone repository
git clone <repository>
cd unpuzzle_django

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data
python manage.py loaddata initial_data.json

# Run development server
python manage.py runserver

# In another terminal, run Celery
celery -A config worker -l info

# In another terminal, run Celery Beat
celery -A config beat -l info
```

### Testing Structure
```bash
# Run all tests
pytest

# Run specific app tests
pytest apps/courses/tests/

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test
pytest apps/courses/tests/test_models.py::TestCourseModel
```

## Best Practices

### 1. App Independence
- Each app should be self-contained
- Minimize inter-app dependencies
- Use services for cross-app communication

### 2. Settings Management
- Environment-specific settings files
- Use environment variables for secrets
- Never commit sensitive data

### 3. Code Organization
- Fat models, thin views
- Business logic in services
- Reusable components in core

### 4. Testing Strategy
- Unit tests for models and utilities
- Integration tests for views
- End-to-end tests for critical flows

---
**Document Version**: 1.0  
**Last Updated**: 2025-08-23  
**Next Document**: Django Models Implementation