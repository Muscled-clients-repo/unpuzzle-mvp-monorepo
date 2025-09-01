from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG') == 'True'

# Build allowed hosts list
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    '0.0.0.0',
    'dev1.nazmulcodes.org'
]

# Add environment-based hosts if they exist
frontend_url = os.environ.get('FRONTEND_URL')
if frontend_url:
    # Extract domain from URL (remove https:// and http:// prefix)
    frontend_domain = frontend_url.replace('https://', '').replace('http://', '').rstrip('/')
    ALLOWED_HOSTS.append(frontend_domain)

host_url = os.environ.get('HOST')
if host_url:
    # Extract domain from URL (remove https:// and http:// prefix)
    host_domain = host_url.replace('https://', '').replace('http://', '').rstrip('/')
    ALLOWED_HOSTS.append(host_domain)

print(ALLOWED_HOSTS)

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',  # Required by Django/DRF but not used for authentication
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_filters',
    'channels',
    'accounts',
    'courses',
    'enrollments',
    'media_library',
    'payments',
    'analytics',
    'notifications',
    'ai_assistant',
    'puzzle_reflections',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'app.middleware.trailing_slash.SmartTrailingSlashMiddleware',  # Smart trailing slash handler
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Disabled for API
    'app.middleware.supabase_auth.SupabaseAuthMiddleware',  # Custom Supabase auth
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'
ASGI_APPLICATION = 'app.asgi.application'

# Database
# Use DATABASE_URL from environment if available, otherwise fall back to SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Custom user model - commented out since using Supabase Auth
# AUTH_USER_MODEL = 'accounts.User'

# Password validation - not needed with Supabase Auth
# AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# API Configuration
APPEND_SLASH = True  # Enable automatic slash appending - redirects URLs without trailing slashes

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'app.authentication.SupabaseAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS configuration
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://dev1.nazmulcodes.org',
    host_url,
    frontend_url
]

CORS_ALLOW_CREDENTIALS = True

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Backblaze B2 Configuration
BACKBLAZE_ENDPOINT = os.environ.get('BB_ENDPOINT', 's3.us-west-002.backblazeb2.com')
BACKBLAZE_KEY_ID = os.environ.get('BB_KEY_ID')
BACKBLAZE_APPLICATION_KEY = os.environ.get('BB_APPLICATION_KEY')
BACKBLAZE_BUCKET_NAME = os.environ.get('BB_BUCKET_NAME')
BACKBLAZE_BUCKET_ID = os.environ.get('BB_BUCKET_ID')

# CDN Configuration (Bunny CDN or similar)
CDN_BASE_URL = os.environ.get('CDN_URL')

# Media Upload Configuration
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks
UPLOAD_SESSION_EXPIRES_HOURS = 24

# Video Processing Configuration
MIN_VIDEO_WIDTH = 320
MIN_VIDEO_HEIGHT = 240
MAX_VIDEO_DURATION_SECONDS = 7200  # 2 hours

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'root': {
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'supabase_auth': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'courses_views': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'media_library.views': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.authentication': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'ai_assistant': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}


# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Default currency for payments
DEFAULT_CURRENCY = 'usd'

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4')
OPENAI_MAX_TOKENS = int(os.environ.get('OPENAI_MAX_TOKENS', '500'))

# AI Features Configuration
AI_RATE_LIMIT_FREE = int(os.environ.get('AI_RATE_LIMIT_FREE', '3'))
AI_RATE_LIMIT_PREMIUM = int(os.environ.get('AI_RATE_LIMIT_PREMIUM', '50'))
AI_RATE_LIMIT_ENTERPRISE = int(os.environ.get('AI_RATE_LIMIT_ENTERPRISE', '200'))
AI_CACHE_TTL_SECONDS = int(os.environ.get('AI_CACHE_TTL_SECONDS', '3600'))

# Transcript Context Configuration
TRANSCRIPT_CONTEXT_WINDOW_SECONDS = int(os.environ.get('TRANSCRIPT_CONTEXT_WINDOW_SECONDS', '30'))

# Redis Configuration
# Get Redis URL from environment (Heroku provides REDIS_URL)
HEROKU_REDIS_URL = os.environ.get('REDIS_URL')

# Redis Cache Configuration
CACHE_REDIS_URL = HEROKU_REDIS_URL if HEROKU_REDIS_URL else 'redis://127.0.0.1:6379'
# Heroku Redis only supports database 0, use database 2 for local development
CACHE_DB = '/0' if HEROKU_REDIS_URL else '/2'
CACHE_LOCATION = CACHE_REDIS_URL.rstrip('/') + CACHE_DB

# Redis connection options for Heroku (SSL)
REDIS_CONNECTION_KWARGS = {}
if HEROKU_REDIS_URL and 'rediss://' in HEROKU_REDIS_URL:
    import ssl
    # Heroku Redis uses SSL, configure SSL settings
    REDIS_CONNECTION_KWARGS = {
        'ssl_cert_reqs': ssl.CERT_NONE,  # Disable SSL certificate verification
        'ssl_check_hostname': False,
    }

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': CACHE_LOCATION,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                **REDIS_CONNECTION_KWARGS
            },
        },
        'KEY_PREFIX': 'unpuzzle_ai',
        'TIMEOUT': AI_CACHE_TTL_SECONDS,
    }
}

# Celery Configuration
# On Heroku, use REDIS_URL for both broker and backend
if HEROKU_REDIS_URL:
    # Heroku Redis only supports database 0, use same database for broker and backend
    CELERY_BROKER_URL = HEROKU_REDIS_URL.rstrip('/')
    CELERY_RESULT_BACKEND = HEROKU_REDIS_URL.rstrip('/')
    
    # Configure SSL settings for Celery if using rediss://
    if 'rediss://' in HEROKU_REDIS_URL:
        import ssl
        CELERY_REDIS_BACKEND_USE_SSL = {
            'ssl_cert_reqs': ssl.CERT_NONE,
            'ssl_check_hostname': False,
        }
        CELERY_BROKER_USE_SSL = CELERY_REDIS_BACKEND_USE_SSL
else:
    # Local development fallback
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/1')

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [CACHE_LOCATION],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}