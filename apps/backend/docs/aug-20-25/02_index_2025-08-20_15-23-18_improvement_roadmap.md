# Unpuzzle MVP Backend - Architecture Improvement Roadmap

**Date**: August 20, 2025  
**Time**: 15:23:18  
**Version**: 1.0  
**Status**: Implementation Plan

---

## Executive Summary

This document provides a detailed, actionable roadmap to address all issues identified in the project analysis and transform the Unpuzzle MVP backend into a production-grade, scalable application. The plan is organized by priority and includes specific implementation steps, code examples, and file modifications.

---

## Phase 1: Critical Improvements (Week 1-2)

### 1.1 Comprehensive Testing Framework 🔴 **HIGHEST PRIORITY**

#### Current State
- Only 4 test files exist
- No test coverage reporting
- Missing CI/CD integration

#### Implementation Plan

##### Step 1: Set Up Testing Infrastructure

**File**: `requirements-dev.txt` (CREATE)
```txt
# Testing Framework
pytest==7.4.3
pytest-cov==4.1.0
pytest-flask==1.3.0
pytest-mock==3.12.0
pytest-asyncio==0.21.1
factory-boy==3.3.0
faker==20.1.0

# Code Quality
black==23.12.1
isort==5.13.2
flake8==6.1.0
mypy==1.8.0
pylint==3.0.3
pre-commit==3.6.0

# Documentation
sphinx==7.2.6
sphinx-rtd-theme==2.0.0
```

**File**: `pytest.ini` (CREATE)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
    --cov-fail-under=80
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

##### Step 2: Create Test Structure

**Directory Structure** (CREATE):
```
tests/
├── conftest.py           # Shared fixtures
├── unit/
│   ├── test_models/
│   │   ├── test_user.py
│   │   ├── test_course.py
│   │   └── test_enrollment.py
│   ├── test_repositories/
│   │   ├── test_user_repository.py
│   │   └── test_course_repository.py
│   ├── test_services/
│   │   ├── test_auth_service.py
│   │   ├── test_course_service.py
│   │   └── test_ai_service.py
│   └── test_utils/
├── integration/
│   ├── test_api/
│   │   ├── test_auth_endpoints.py
│   │   ├── test_course_endpoints.py
│   │   └── test_student_endpoints.py
│   └── test_database/
└── e2e/
    └── test_user_flows.py
```

**File**: `tests/conftest.py` (UPDATE)
```python
import pytest
from app import create_app
from app.core.database import db as _db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.services.auth_service import AuthService
from datetime import datetime, timedelta
import jwt

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app, _ = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    return app

@pytest.fixture(scope='session')
def db(app):
    """Create database for testing."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """Create a clean database session for each test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    session = db.session
    session.begin_nested()
    
    yield session
    
    session.rollback()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def auth_headers(session):
    """Create authenticated headers for testing."""
    user = User(
        email='test@example.com',
        username='testuser',
        full_name='Test User'
    )
    user.set_password('password123')
    session.add(user)
    session.commit()
    
    token = jwt.encode({
        'user_id': str(user.id),
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, 'test-secret-key', algorithm='HS256')
    
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
```

**File**: `tests/unit/test_repositories/test_user_repository.py` (CREATE)
```python
import pytest
from app.repositories.user_repository import UserRepository
from app.models.user import User
from tests.factories import UserFactory

class TestUserRepository:
    
    @pytest.fixture(autouse=True)
    def setup(self, session):
        self.repo = UserRepository(session)
        self.session = session
    
    def test_create_user(self):
        """Test user creation."""
        user_data = {
            'email': 'new@example.com',
            'username': 'newuser',
            'full_name': 'New User'
        }
        user = self.repo.create(user_data)
        
        assert user.id is not None
        assert user.email == 'new@example.com'
        assert user.username == 'newuser'
    
    def test_get_by_email(self):
        """Test finding user by email."""
        user = UserFactory.create(email='test@example.com')
        self.session.add(user)
        self.session.commit()
        
        found_user = self.repo.get_by_email('test@example.com')
        assert found_user is not None
        assert found_user.email == 'test@example.com'
    
    def test_get_by_email_not_found(self):
        """Test finding non-existent user."""
        found_user = self.repo.get_by_email('notfound@example.com')
        assert found_user is None
    
    def test_update_user(self):
        """Test user update."""
        user = UserFactory.create()
        self.session.add(user)
        self.session.commit()
        
        updated_user = self.repo.update(user.id, {'full_name': 'Updated Name'})
        assert updated_user.full_name == 'Updated Name'
    
    def test_soft_delete(self):
        """Test soft delete functionality."""
        user = UserFactory.create()
        self.session.add(user)
        self.session.commit()
        
        self.repo.delete(user.id)
        
        # Should not find with normal query
        found_user = self.repo.get_by_id(user.id)
        assert found_user is None
        
        # Should find with include_deleted
        found_user = self.repo.get_by_id(user.id, include_deleted=True)
        assert found_user is not None
        assert found_user.is_deleted is True
```

**File**: `tests/factories.py` (CREATE)
```python
import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from app.models.user import User
from app.models.course import Course
from app.models.learning import Enrollment
from datetime import datetime

fake = Faker()

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = 'commit'
    
    id = factory.Faker('uuid4')
    email = factory.Faker('email')
    username = factory.Faker('user_name')
    full_name = factory.Faker('name')
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

class CourseFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Course
        sqlalchemy_session_persistence = 'commit'
    
    id = factory.Faker('uuid4')
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text')
    instructor_id = factory.SubFactory(UserFactory)
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    created_at = factory.LazyFunction(datetime.utcnow)
```

##### Step 3: Add Coverage Reports

**File**: `.coveragerc` (CREATE)
```ini
[run]
source = app
omit = 
    */tests/*
    */migrations/*
    */venv/*
    */__pycache__/*
    */config.py
    */run.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

### 1.2 API Documentation with OpenAPI

#### Implementation Plan

**File**: `requirements.txt` (UPDATE)
```txt
# Add to existing requirements
flask-restx==1.3.0
flasgger==0.9.7.1
marshmallow==3.20.1
apispec==6.3.1
```

**File**: `app/api/v1/__init__.py` (UPDATE)
```python
from flask import Blueprint
from flask_restx import Api

# Create versioned API with documentation
api_v1 = Api(
    title='Unpuzzle API',
    version='1.0',
    description='Educational Platform REST API',
    doc='/api/v1/docs',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Bearer token. Example: "Bearer {token}"'
        }
    },
    security='Bearer'
)

# Import namespaces
from app.api.v1.auth import auth_ns
from app.api.v1.courses import courses_ns
from app.api.v1.users import users_ns

# Register namespaces
api_v1.add_namespace(auth_ns, path='/auth')
api_v1.add_namespace(courses_ns, path='/courses')
api_v1.add_namespace(users_ns, path='/users')
```

**File**: `app/api/v1/courses.py` (UPDATE)
```python
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.course_service import CourseService
from app.core.responses import APIResponse

courses_ns = Namespace('courses', description='Course operations')

# Define models for documentation
course_model = courses_ns.model('Course', {
    'id': fields.String(required=True, description='Course ID'),
    'title': fields.String(required=True, description='Course title'),
    'description': fields.String(description='Course description'),
    'instructor_id': fields.String(description='Instructor ID'),
    'price': fields.Float(description='Course price'),
    'duration_hours': fields.Integer(description='Course duration'),
    'level': fields.String(description='Course level'),
    'category': fields.String(description='Course category'),
    'thumbnail_url': fields.String(description='Thumbnail URL'),
    'is_published': fields.Boolean(description='Publication status'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Update timestamp')
})

course_create_model = courses_ns.model('CourseCreate', {
    'title': fields.String(required=True, description='Course title'),
    'description': fields.String(required=True, description='Course description'),
    'price': fields.Float(required=True, description='Course price'),
    'duration_hours': fields.Integer(description='Course duration'),
    'level': fields.String(description='Course level'),
    'category': fields.String(description='Course category')
})

@courses_ns.route('')
class CourseList(Resource):
    @courses_ns.doc('list_courses')
    @courses_ns.marshal_list_with(course_model)
    @courses_ns.param('page', 'Page number', type='integer', default=1)
    @courses_ns.param('limit', 'Items per page', type='integer', default=20)
    @courses_ns.param('category', 'Filter by category', type='string')
    @courses_ns.param('level', 'Filter by level', type='string')
    def get(self):
        """List all courses with pagination and filters"""
        # Implementation
        pass
    
    @courses_ns.doc('create_course')
    @courses_ns.expect(course_create_model)
    @courses_ns.marshal_with(course_model, code=201)
    @jwt_required()
    def post(self):
        """Create a new course"""
        # Implementation
        pass
```

### 1.3 Security Hardening

#### Implementation Plan

**File**: `app/middleware/security.py` (CREATE)
```python
from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import re
from typing import List, Dict, Any
import bleach
from werkzeug.exceptions import BadRequest

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"],
    storage_uri="redis://localhost:6379"
)

class SecurityMiddleware:
    """Security middleware for request validation and sanitization."""
    
    # SQL Injection patterns
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\bOR\b\s*\d+\s*=\s*\d+)",
        r"(\bAND\b\s*\d+\s*=\s*\d+)"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>"
    ]
    
    @staticmethod
    def sanitize_input(data: Any) -> Any:
        """Recursively sanitize input data."""
        if isinstance(data, str):
            # Remove HTML tags
            data = bleach.clean(data, tags=[], strip=True)
            
            # Check for SQL injection patterns
            for pattern in SecurityMiddleware.SQL_PATTERNS:
                if re.search(pattern, data, re.IGNORECASE):
                    raise BadRequest("Potentially malicious input detected")
            
            # Check for XSS patterns
            for pattern in SecurityMiddleware.XSS_PATTERNS:
                if re.search(pattern, data, re.IGNORECASE):
                    raise BadRequest("Potentially malicious input detected")
            
            return data
        
        elif isinstance(data, dict):
            return {k: SecurityMiddleware.sanitize_input(v) for k, v in data.items()}
        
        elif isinstance(data, list):
            return [SecurityMiddleware.sanitize_input(item) for item in data]
        
        return data
    
    @staticmethod
    def validate_request():
        """Decorator to validate and sanitize requests."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Sanitize JSON body
                if request.is_json:
                    request.json = SecurityMiddleware.sanitize_input(request.get_json())
                
                # Sanitize query parameters
                if request.args:
                    sanitized_args = {}
                    for key, value in request.args.items():
                        sanitized_args[key] = SecurityMiddleware.sanitize_input(value)
                    request.args = sanitized_args
                
                # Add security headers
                response = f(*args, **kwargs)
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Content-Security-Policy'] = "default-src 'self'"
                
                return response
            
            return decorated_function
        return decorator

def apply_rate_limits(app):
    """Apply rate limits to specific endpoints."""
    
    # Auth endpoints - stricter limits
    limiter.limit("5 per minute")(app.view_functions['auth.login'])
    limiter.limit("3 per hour")(app.view_functions['auth.register'])
    limiter.limit("3 per hour")(app.view_functions['auth.forgot_password'])
    
    # API endpoints - standard limits
    limiter.limit("100 per minute")(app.view_functions['api.courses'])
    limiter.limit("50 per minute")(app.view_functions['api.enrollments'])
    
    return app
```

**File**: `app/core/config.py` (UPDATE)
```python
import os
from datetime import timedelta
from typing import Optional

class Config:
    """Base configuration."""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.urandom(32)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_HEADERS = ['Content-Type', 'Authorization']
    CORS_SUPPORTS_CREDENTIALS = True
    
    # Session
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_DEFAULT = '1000 per hour'
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4', 'webm'}
    
    # Password Policy
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL = True

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5173']

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    CORS_ORIGINS = ['https://unpuzzle.com', 'https://app.unpuzzle.com']

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': Config
}
```

---

## Phase 2: Performance Optimization (Week 3-4)

### 2.1 Query Optimization

**File**: `app/repositories/optimized_base.py` (CREATE)
```python
from typing import Optional, List, Dict, Any, TypeVar, Generic
from sqlalchemy.orm import Session, selectinload, joinedload, Query
from sqlalchemy import and_, or_, func
from functools import lru_cache
from app.core.cache import cache
import hashlib
import json

T = TypeVar('T')

class OptimizedRepository(Generic[T]):
    """Base repository with query optimization."""
    
    def __init__(self, model: T, session: Session):
        self.model = model
        self.session = session
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """Generate cache key for query results."""
        key_data = f"{self.model.__name__}:{method}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @cache.memoize(timeout=300)
    def get_by_id(self, id: str, relations: List[str] = None) -> Optional[T]:
        """Get entity by ID with optional eager loading."""
        query = self.session.query(self.model)
        
        # Add eager loading for relationships
        if relations:
            for relation in relations:
                query = query.options(selectinload(getattr(self.model, relation)))
        
        return query.filter(self.model.id == id).first()
    
    def get_many(
        self,
        filters: Dict[str, Any] = None,
        relations: List[str] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> List[T]:
        """Get multiple entities with optimization."""
        query = self.session.query(self.model)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        # Eager load relationships
        if relations:
            for relation in relations:
                query = query.options(selectinload(getattr(self.model, relation)))
        
        # Apply ordering
        if order_by:
            query = query.order_by(order_by)
        
        # Apply pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def bulk_create(self, entities: List[Dict[str, Any]]) -> List[T]:
        """Bulk create entities for better performance."""
        instances = [self.model(**entity) for entity in entities]
        self.session.bulk_save_objects(instances, return_defaults=True)
        self.session.commit()
        return instances
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """Bulk update entities."""
        self.session.bulk_update_mappings(self.model, updates)
        self.session.commit()
        return len(updates)
```

### 2.2 Async Support with Celery

**File**: `app/tasks/__init__.py` (CREATE)
```python
from celery import Celery
from app.core.config import Config

def create_celery(app=None):
    """Create Celery instance."""
    celery = Celery(
        'unpuzzle',
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND
    )
    
    if app:
        celery.conf.update(app.config)
        
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery

celery = create_celery()
```

**File**: `app/tasks/email_tasks.py` (CREATE)
```python
from app.tasks import celery
from app.services.email_service import EmailService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3)
def send_email_async(self, to: str, subject: str, template: str, data: Dict[str, Any]):
    """Send email asynchronously."""
    try:
        email_service = EmailService()
        email_service.send_email(to, subject, template, data)
        logger.info(f"Email sent to {to}")
        return {'status': 'success', 'recipient': to}
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise self.retry(exc=e, countdown=60)

@celery.task
def process_video_upload(video_id: str):
    """Process uploaded video in background."""
    from app.services.video_service import VideoService
    
    video_service = VideoService()
    video_service.process_video(video_id)
    return {'status': 'completed', 'video_id': video_id}

@celery.task
def generate_course_analytics(course_id: str):
    """Generate course analytics in background."""
    from app.services.analytics_service import AnalyticsService
    
    analytics_service = AnalyticsService()
    analytics = analytics_service.generate_course_analytics(course_id)
    return analytics
```

### 2.3 Caching Strategy

**File**: `app/core/cache_config.py` (CREATE)
```python
from flask_caching import Cache
from typing import Optional, Any, Callable
from functools import wraps
import hashlib
import json

cache = Cache()

class CacheManager:
    """Advanced cache management."""
    
    CACHE_TIMES = {
        'short': 60,      # 1 minute
        'medium': 300,    # 5 minutes
        'long': 3600,     # 1 hour
        'day': 86400      # 1 day
    }
    
    @staticmethod
    def key_builder(prefix: str, **kwargs) -> str:
        """Build cache key from prefix and arguments."""
        key_data = {k: str(v) for k, v in kwargs.items()}
        key_str = f"{prefix}:{json.dumps(key_data, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @staticmethod
    def cached(duration: str = 'medium', key_prefix: Optional[str] = None):
        """Decorator for caching function results."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Build cache key
                prefix = key_prefix or f"{f.__module__}.{f.__name__}"
                cache_key = CacheManager.key_builder(prefix, args=str(args), kwargs=str(kwargs))
                
                # Try to get from cache
                result = cache.get(cache_key)
                if result is not None:
                    return result
                
                # Execute function and cache result
                result = f(*args, **kwargs)
                timeout = CacheManager.CACHE_TIMES.get(duration, 300)
                cache.set(cache_key, result, timeout=timeout)
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def invalidate_pattern(pattern: str):
        """Invalidate all cache keys matching pattern."""
        # This requires Redis cache backend
        if hasattr(cache.cache, 'delete_many'):
            keys = cache.cache.keys(pattern)
            if keys:
                cache.cache.delete_many(*keys)
```

---

## Phase 3: DevOps & Infrastructure (Week 5-6)

### 3.1 Docker Configuration

**File**: `Dockerfile` (CREATE)
```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 unpuzzle && chown -R unpuzzle:unpuzzle /app
USER unpuzzle

# Environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "60", "run:app"]
```

**File**: `docker-compose.yml` (CREATE)
```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: unpuzzle-backend
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    depends_on:
      - redis
      - postgres
    volumes:
      - ./uploads:/app/uploads
    networks:
      - unpuzzle-network
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: unpuzzle-db
    environment:
      - POSTGRES_DB=unpuzzle
      - POSTGRES_USER=unpuzzle
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - unpuzzle-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: unpuzzle-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - unpuzzle-network
    restart: unless-stopped

  celery:
    build: .
    container_name: unpuzzle-celery
    command: celery -A app.tasks worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
      - CELERY_BROKER_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres
    networks:
      - unpuzzle-network
    restart: unless-stopped

  flower:
    build: .
    container_name: unpuzzle-flower
    command: celery -A app.tasks flower
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
    depends_on:
      - redis
      - celery
    networks:
      - unpuzzle-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  unpuzzle-network:
    driver: bridge
```

### 3.2 CI/CD Pipeline

**File**: `.github/workflows/ci.yml` (CREATE)
```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        black --check app/
        isort --check-only app/
        flake8 app/
    
    - name: Run type checking
      run: mypy app/
    
    - name: Run tests with coverage
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
        REDIS_URL: redis://localhost:6379
        JWT_SECRET_KEY: test-secret-key
      run: |
        pytest --cov=app --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
    
    - name: Build Docker image
      run: docker build -t unpuzzle-backend:test .
    
    - name: Run security scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: unpuzzle-backend:test
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      env:
        DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
      run: |
        # Add deployment script here
        echo "Deploying to production..."
```

### 3.3 Monitoring & Observability

**File**: `app/monitoring/__init__.py` (CREATE)
```python
from prometheus_flask_exporter import PrometheusMetrics
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
import logging
import structlog
from pythonjsonlogger import jsonlogger
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

def setup_monitoring(app):
    """Set up comprehensive monitoring."""
    
    # Prometheus metrics
    metrics = PrometheusMetrics(app)
    metrics.info('app_info', 'Application info', version='1.0.0')
    
    # Custom metrics
    metrics.register_default(
        metrics.counter(
            'api_requests_by_endpoint',
            'API requests by endpoint',
            labels={'endpoint': lambda: request.endpoint}
        )
    )
    
    # Jaeger tracing
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    jaeger_exporter = JaegerExporter(
        agent_host_name='localhost',
        agent_port=6831,
    )
    
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrument Flask and SQLAlchemy
    FlaskInstrumentor().instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    
    # Structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Sentry error tracking
    sentry_sdk.init(
        dsn=app.config.get('SENTRY_DSN'),
        integrations=[
            FlaskIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=app.config.get('ENVIRONMENT', 'development')
    )
    
    return app
```

**File**: `app/api/health.py` (CREATE)
```python
from flask import Blueprint, jsonify
from app.core.database import db
from app.core.cache import cache
import redis
import psutil
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Basic health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

@health_bp.route('/health/detailed')
def detailed_health():
    """Detailed health check with component status."""
    health_status = {
        'status': 'healthy',
        'components': {}
    }
    
    # Check database
    try:
        db.session.execute('SELECT 1')
        health_status['components']['database'] = 'healthy'
    except Exception as e:
        health_status['components']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check Redis
    try:
        r = redis.Redis.from_url(os.environ.get('REDIS_URL'))
        r.ping()
        health_status['components']['redis'] = 'healthy'
    except Exception as e:
        health_status['components']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
    
    # System metrics
    health_status['metrics'] = {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    }
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@health_bp.route('/ready')
def readiness_check():
    """Kubernetes readiness probe."""
    try:
        # Check if app can serve traffic
        db.session.execute('SELECT 1')
        return jsonify({'ready': True}), 200
    except:
        return jsonify({'ready': False}), 503

@health_bp.route('/live')
def liveness_check():
    """Kubernetes liveness probe."""
    return jsonify({'alive': True}), 200
```

---

## Phase 4: Code Quality & Standards (Week 7-8)

### 4.1 Pre-commit Hooks

**File**: `.pre-commit-config.yaml` (CREATE)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-json
      - id: detect-private-key
      - id: debug-statements
      - id: requirements-txt-fixer

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ["--max-line-length=100", "--ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-r", "app/"]
```

### 4.2 Code Standards

**File**: `pyproject.toml` (CREATE)
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | build
  | dist
  | migrations
)/
'''

[tool.isort]
profile = "black"
line_length = 100
known_first_party = ["app"]
skip_glob = ["*/migrations/*", "*/venv/*"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = true

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/migrations/*", "*/__pycache__/*"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
fail_under = 80
```

---

## Implementation Timeline

### Week 1-2: Foundation
- [ ] Set up testing framework
- [ ] Create test fixtures and factories
- [ ] Write unit tests for critical services
- [ ] Implement API documentation

### Week 3-4: Security & Performance
- [ ] Add security middleware
- [ ] Implement rate limiting
- [ ] Set up Celery for async tasks
- [ ] Optimize database queries

### Week 5-6: DevOps
- [ ] Create Docker configuration
- [ ] Set up CI/CD pipeline
- [ ] Implement monitoring
- [ ] Add health check endpoints

### Week 7-8: Quality & Polish
- [ ] Configure pre-commit hooks
- [ ] Add code quality tools
- [ ] Complete test coverage
- [ ] Update documentation

---

## Success Metrics

1. **Test Coverage**: Achieve 80%+ code coverage
2. **API Documentation**: 100% of endpoints documented
3. **Performance**: <200ms average response time
4. **Security**: Pass OWASP security scan
5. **Reliability**: 99.9% uptime
6. **Code Quality**: 0 critical issues in linting

---

## Conclusion

This comprehensive roadmap addresses all critical issues identified in the project analysis. Following this plan will transform the Unpuzzle MVP backend into a production-ready, scalable, and maintainable application that follows industry best practices.

The improvements are prioritized based on criticality, with testing and security taking precedence, followed by performance optimization and DevOps maturity. Each phase builds upon the previous one, ensuring a smooth transition and minimal disruption to ongoing development.

---

*Document Created: August 20, 2025, 15:23:18*  
*Version: 1.0*  
*Status: Ready for Implementation*