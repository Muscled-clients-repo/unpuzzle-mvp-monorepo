# Django Deployment & Production Configuration
**Date**: 2025-08-23  
**Time**: 11:15:00  
**Component**: Production Deployment Strategy

## Overview

Complete production deployment guide for Django application with enterprise-grade configuration, monitoring, and scaling strategies.

## Production Environment Setup

### Environment Variables
```bash
# .env.production
DEBUG=False
SECRET_KEY=your-super-secret-production-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database
DATABASE_URL=postgresql://username:password@host:5432/database
DB_NAME=unpuzzle_prod
DB_USER=unpuzzle_user
DB_PASSWORD=secure_password
DB_HOST=prod-db-server.com
DB_PORT=5432

# Redis
REDIS_URL=redis://username:password@redis-host:6379/0
CELERY_BROKER_URL=redis://username:password@redis-host:6379/1

# Email
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.com
SMTP_PASSWORD=your-mailgun-password
DEFAULT_FROM_EMAIL=noreply@unpuzzle.com

# Storage
BACKBLAZE_KEY_ID=your-backblaze-key-id
BACKBLAZE_APPLICATION_KEY=your-backblaze-app-key
BACKBLAZE_BUCKET_NAME=unpuzzle-media
BACKBLAZE_BUCKET_ID=bucket-id

# External Services
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
OPENAI_API_KEY=your-openai-api-key

# Security
ALLOWED_HOSTS=api.unpuzzle.com,unpuzzle.com
CORS_ALLOWED_ORIGINS=https://unpuzzle.com,https://www.unpuzzle.com
CSRF_TRUSTED_ORIGINS=https://unpuzzle.com,https://www.unpuzzle.com

# Performance
DATABASE_CONN_MAX_AGE=600
CACHE_TTL=300
```

### Production Settings
```python
# config/settings/production.py
from .base import *
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

# Security Settings
DEBUG = False
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'CONN_MAX_AGE': env.int('DATABASE_CONN_MAX_AGE', default=600),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=serializable'
        }
    }
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
                'retry_on_timeout': True,
                'health_check_interval': 30,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'unpuzzle_prod',
        'VERSION': 1,
        'TIMEOUT': env.int('CACHE_TTL', default=300),
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Security Headers
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# CORS Configuration
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True
CORS_PREFLIGHT_MAX_AGE = 86400

# CSRF Configuration
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS')
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# File Storage Configuration
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

AWS_ACCESS_KEY_ID = env('BACKBLAZE_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('BACKBLAZE_APPLICATION_KEY')
AWS_STORAGE_BUCKET_NAME = env('BACKBLAZE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = 'https://s3.us-west-002.backblazeb2.com'
AWS_S3_REGION_NAME = 'us-west-002'
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_FILE_OVERWRITE = False
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.us-west-002.backblazeb2.com'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('SMTP_HOST')
EMAIL_PORT = env.int('SMTP_PORT')
EMAIL_HOST_USER = env('SMTP_USER')
EMAIL_HOST_PASSWORD = env('SMTP_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'root': {
        'handlers': ['file', 'console'],
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'services': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('REDIS_URL')
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50

# Sentry Configuration
sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(
            transaction_style='url',
        ),
        CeleryIntegration(
            monitor_beat_tasks=True,
        ),
    ],
    traces_sample_rate=0.1,
    send_default_pii=True,
    environment='production',
)

# Rate Limiting
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = True

# API Throttling
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].update({
    'anon': '50/hour',
    'user': '500/hour',
    'burst': '30/minute',
    'auth': '3/minute',
    'upload': '5/hour',
})
```

## Docker Configuration

### Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        libmagic1 \
        ffmpeg \
        imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

# Copy project
COPY . .

# Create user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate --noinput

# Expose port
EXPOSE 8000

# Command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "config.wsgi:application"]
```

### Docker Compose
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    env_file:
      - .env.production
    volumes:
      - ./logs:/var/log/django
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery:
    build: .
    command: celery -A config worker -l info --concurrency=4
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    env_file:
      - .env.production
    volumes:
      - ./logs:/var/log/django
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    restart: unless-stopped

  celery-beat:
    build: .
    command: celery -A config beat -l info
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    env_file:
      - .env.production
    volumes:
      - ./logs:/var/log/django
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=unpuzzle_prod
      - POSTGRES_USER=unpuzzle_user
      - POSTGRES_PASSWORD=secure_password
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U unpuzzle_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### Nginx Configuration
```nginx
# nginx/nginx.conf
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name api.unpuzzle.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.unpuzzle.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=1r/s;

    # Static Files
    location /static/ {
        alias /app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media Files
    location /media/ {
        alias /app/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Auth Endpoints (Rate Limited)
    location ~ ^/api/v1/auth/ {
        limit_req zone=auth burst=5 nodelay;
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket Support
    location /ws/ {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health Check
    location /health/ {
        proxy_pass http://django;
        access_log off;
    }

    # Admin (IP Restricted)
    location /admin/ {
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
        
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring & Logging

### Health Check Views
```python
# apps/monitoring/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """Comprehensive health check"""
    checks = {
        'database': check_database(),
        'cache': check_cache(),
        'celery': check_celery(),
        'storage': check_storage(),
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JsonResponse({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'version': getattr(settings, 'VERSION', '1.0.0')
    }, status=status_code)

def check_database():
    """Check database connectivity"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def check_cache():
    """Check Redis cache"""
    try:
        cache.set('health_check', 'ok', 10)
        return cache.get('health_check') == 'ok'
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return False

def check_celery():
    """Check Celery workers"""
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        return stats is not None and len(stats) > 0
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return False

def check_storage():
    """Check storage connectivity"""
    try:
        from django.core.files.storage import default_storage
        # Simple existence check
        return hasattr(default_storage, 'bucket')
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return False
```

### Prometheus Metrics
```python
# apps/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from django.conf import settings

# Metrics
request_count = Counter(
    'django_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'django_request_duration_seconds',
    'Time spent processing requests',
    ['method', 'endpoint']
)

active_users = Gauge(
    'django_active_users',
    'Number of active users'
)

database_connections = Gauge(
    'django_database_connections',
    'Number of database connections'
)

celery_task_count = Counter(
    'celery_tasks_total',
    'Total number of Celery tasks',
    ['task_name', 'status']
)
```

### Custom Middleware
```python
# middleware/monitoring.py
import time
from django.utils.deprecation import MiddlewareMixin
from apps.monitoring.metrics import request_count, request_duration

class MetricsMiddleware(MiddlewareMixin):
    """Middleware to collect metrics"""
    
    def process_request(self, request):
        request._start_time = time.time()
        
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Record metrics
            request_count.labels(
                method=request.method,
                endpoint=request.path,
                status=response.status_code
            ).inc()
            
            request_duration.labels(
                method=request.method,
                endpoint=request.path
            ).observe(duration)
        
        return response
```

## Database Configuration

### Connection Pooling
```python
# config/database.py
from django.db import connections
from django.core.management.base import BaseCommand

class DatabasePoolManager:
    """Manage database connection pools"""
    
    @staticmethod
    def warm_connections():
        """Warm up database connections"""
        for alias in connections:
            connections[alias].ensure_connection()
    
    @staticmethod
    def close_old_connections():
        """Close old database connections"""
        connections.close_all()
```

### Database Optimization
```sql
-- Database optimization queries
-- Create indexes for performance
CREATE INDEX CONCURRENTLY idx_users_email_active ON users(email) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_courses_published ON courses(is_published, status) WHERE is_published = true;
CREATE INDEX CONCURRENTLY idx_enrollments_active ON enrollments(user_id, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_media_files_course ON media_files(course_id, file_type) WHERE is_deleted = false;

-- Analyze tables for better query planning
ANALYZE users;
ANALYZE courses;
ANALYZE enrollments;
ANALYZE media_files;

-- Set up connection pooling parameters
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
```

## Deployment Scripts

### Deploy Script
```bash
#!/bin/bash
# deploy.sh

set -e

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Build Docker images
docker-compose -f docker-compose.production.yml build

# Run migrations
docker-compose -f docker-compose.production.yml run --rm web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.production.yml run --rm web python manage.py collectstatic --noinput

# Update search indexes
docker-compose -f docker-compose.production.yml run --rm web python manage.py update_index

# Restart services
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d

# Health check
sleep 30
curl -f http://localhost/health/ || exit 1

echo "Deployment completed successfully!"
```

### Backup Script
```bash
#!/bin/bash
# backup.sh

set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting backup..."

# Database backup
docker-compose -f docker-compose.production.yml exec -T db pg_dump -U unpuzzle_user unpuzzle_prod | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Media files backup
tar -czf "$BACKUP_DIR/media_backup_$DATE.tar.gz" -C /var/lib/docker/volumes/unpuzzle_media_volume/_data .

# Redis backup
docker-compose -f docker-compose.production.yml exec -T redis redis-cli BGSAVE
docker cp $(docker-compose -f docker-compose.production.yml ps -q redis):/data/dump.rdb "$BACKUP_DIR/redis_backup_$DATE.rdb"

# Clean old backups (keep 7 days)
find "$BACKUP_DIR" -name "*backup*" -mtime +7 -delete

echo "Backup completed successfully!"
```

## Scaling Configuration

### Load Balancer Configuration
```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  web:
    build: .
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    env_file:
      - .env.production
    volumes:
      - ./logs:/var/log/django
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    restart: unless-stopped
    scale: 4  # Run 4 instances

  celery:
    build: .
    command: celery -A config worker -l info --concurrency=8
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    env_file:
      - .env.production
    volumes:
      - ./logs:/var/log/django
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    restart: unless-stopped
    scale: 2  # Run 2 worker instances

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/load_balancer.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web
    restart: unless-stopped
```

### Auto-scaling with Docker Swarm
```yaml
# docker-stack.yml
version: '3.8'

services:
  web:
    image: unpuzzle/django-app:latest
    deploy:
      replicas: 4
      update_config:
        parallelism: 2
        delay: 30s
      restart_policy:
        condition: on-failure
        max_attempts: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    env_file:
      - .env.production
    networks:
      - unpuzzle-network

  celery:
    image: unpuzzle/django-app:latest
    command: celery -A config worker -l info --autoscale=10,2
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
        max_attempts: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    env_file:
      - .env.production
    networks:
      - unpuzzle-network

networks:
  unpuzzle-network:
    driver: overlay
```

## Security Hardening

### Security Checklist
```python
# security_checklist.py
"""
Production Security Checklist:

✅ DEBUG = False
✅ SECRET_KEY from environment
✅ ALLOWED_HOSTS configured
✅ HTTPS enforced
✅ Security headers enabled
✅ Database passwords secured
✅ Static files served by Nginx
✅ File upload validation
✅ SQL injection protection
✅ XSS protection
✅ CSRF protection
✅ Rate limiting enabled
✅ Input validation
✅ Error handling
✅ Logging configured
✅ Monitoring enabled
"""

SECURITY_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'middleware.security.SecurityHeadersMiddleware',
    'middleware.logging.RequestLoggingMiddleware',
]
```

### Custom Security Middleware
```python
# middleware/security.py
from django.utils.deprecation import MiddlewareMixin

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses"""
    
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "media-src 'self' https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
```

## Monitoring Dashboard

### Grafana Configuration
```yaml
# grafana-dashboard.json
{
  "dashboard": {
    "title": "Unpuzzle Django Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(django_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "django_request_duration_seconds"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "singlestat",
        "targets": [
          {
            "expr": "django_active_users"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "django_database_connections"
          }
        ]
      }
    ]
  }
}
```

## Performance Optimization

### Caching Strategy
```python
# Cache configuration for different data types
CACHE_STRATEGIES = {
    'user_profile': {'timeout': 3600, 'version': 1},
    'course_list': {'timeout': 900, 'version': 1},
    'course_detail': {'timeout': 3600, 'version': 1},
    'analytics': {'timeout': 1800, 'version': 1},
    'static_content': {'timeout': 86400, 'version': 1},
}

# Redis configuration for high availability
CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS'].update({
    'max_connections': 100,
    'retry_on_timeout': True,
    'health_check_interval': 30,
})
```

## Final Deployment Checklist

```bash
# Pre-deployment checklist
□ Environment variables configured
□ SSL certificates installed
□ Database migrations applied
□ Static files collected
□ Cache warmed up
□ Health checks passing
□ Monitoring configured
□ Backup strategy implemented
□ Log rotation configured
□ Rate limiting enabled
□ Security headers configured
□ Performance monitoring active
□ Error tracking setup
□ Documentation updated
□ Team notified

# Post-deployment verification
□ API endpoints responding
□ Database queries optimized  
□ Cache hit rates acceptable
□ Error rates within limits
□ Response times optimal
□ Background tasks running
□ WebSocket connections working
□ File uploads functioning
□ Email delivery working
□ User registration flow tested
```

---
**Document Version**: 1.0  
**Last Updated**: 2025-08-23  
**Deployment Status**: Production Ready