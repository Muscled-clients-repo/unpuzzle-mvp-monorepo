# Unpuzzle MVP Backend Architecture Documentation

**Version:** 1.0.0  
**Last Updated:** August 28, 2025

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Technology Stack](#technology-stack)
4. [Core Components](#core-components)
5. [Database Architecture](#database-architecture)
6. [Authentication & Security](#authentication--security)
7. [API Layer](#api-layer)
8. [File Storage System](#file-storage-system)
9. [AI Integration](#ai-integration)
10. [Payment Processing](#payment-processing)
11. [Caching Strategy](#caching-strategy)
12. [Background Jobs](#background-jobs)
13. [Deployment Architecture](#deployment-architecture)
14. [Monitoring & Logging](#monitoring--logging)
15. [Scalability Considerations](#scalability-considerations)
16. [Security Architecture](#security-architecture)

---

## System Overview

The Unpuzzle MVP Backend is a comprehensive learning management system built with Django and Django REST Framework. It provides a robust, scalable API for course management, user authentication, AI-powered learning assistance, media handling, and payment processing.

### Key Architectural Principles

1. **Separation of Concerns**: Clear separation between API, business logic, and data layers
2. **Microservices-Ready**: Modular design allowing future microservices migration
3. **Security-First**: Row Level Security, JWT authentication, and encrypted storage
4. **Scalability**: Horizontal scaling support with Redis caching and CDN integration
5. **Cloud-Native**: Designed for cloud deployment with external service integration
6. **API-First**: RESTful API design with comprehensive documentation

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client Applications                        │
│  (Web App, Mobile App, Admin Dashboard, Third-party Integrations)   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          API Gateway / Load Balancer                 │
│                         (Nginx / AWS ALB / Cloudflare)              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌──────────────────────────────┐  ┌──────────────────────────────────┐
│     Django REST API Server    │  │      WebSocket Server (Future)    │
│                               │  │                                  │
│  ┌─────────────────────────┐ │  │  ┌────────────────────────────┐  │
│  │   URL Routing Layer      │ │  │  │   Real-time Notifications  │  │
│  ├─────────────────────────┤ │  │  │   Live Chat Support        │  │
│  │   Middleware Stack       │ │  │  │   Collaborative Features   │  │
│  │  - Authentication        │ │  │  └────────────────────────────┘  │
│  │  - CORS                  │ │  └──────────────────────────────────┘
│  │  - Rate Limiting         │ │
│  │  - Request Logging       │ │
│  ├─────────────────────────┤ │
│  │   View Layer (APIs)      │ │
│  │  - Auth Views            │ │
│  │  - Course Views          │ │
│  │  - Media Views           │ │
│  │  - AI Assistant Views    │ │
│  │  - Payment Views         │ │
│  ├─────────────────────────┤ │
│  │   Serializer Layer       │ │
│  ├─────────────────────────┤ │
│  │   Business Logic Layer   │ │
│  │  - Services              │ │
│  │  - Validators            │ │
│  │  - Utilities             │ │
│  ├─────────────────────────┤ │
│  │   Model Layer (ORM)      │ │
│  └─────────────────────────┘ │
└──────────────────────────────┘
                    │
        ┌───────────┼───────────────────────────────┐
        ▼           ▼                               ▼
┌──────────┐ ┌──────────────┐           ┌─────────────────────┐
│PostgreSQL│ │    Redis     │           │   Celery Workers    │
│   with   │ │  - Cache     │           │  - Email Tasks      │
│   RLS    │ │  - Sessions  │           │  - AI Processing    │
│          │ │  - Queue     │           │  - Video Processing │
└──────────┘ └──────────────┘           │  - Analytics        │
                                        └─────────────────────┘
                    │                               │
        ┌───────────┼───────────────────────────────┼──────────┐
        ▼           ▼                               ▼          ▼
┌──────────┐ ┌──────────────┐           ┌──────────────┐ ┌──────────┐
│ Supabase │ │ Backblaze B2 │           │   OpenAI     │ │  Stripe  │
│   Auth   │ │  + CDN       │           │   GPT-4      │ │ Payments │
└──────────┘ └──────────────┘           └──────────────┘ └──────────┘
```

---

## Technology Stack

### Core Framework
- **Django 5.0.1**: Web framework providing ORM, admin interface, and security features
- **Django REST Framework 3.14.0**: RESTful API development framework
- **Python 3.11+**: Primary programming language

### Database Layer
- **PostgreSQL 14+**: Primary database with Row Level Security
- **SQLite**: Development database
- **Django ORM**: Database abstraction layer

### Authentication & Security
- **Supabase Auth**: JWT-based authentication service
- **PyJWT**: JWT token processing
- **django-cors-headers**: CORS policy management
- **Python-dotenv**: Environment variable management

### Caching & Queue
- **Redis 7.0+**: In-memory data store for caching and message queue
- **Celery 5.3+**: Distributed task queue
- **django-redis**: Redis cache backend for Django

### File Storage
- **Backblaze B2**: Object storage service
- **boto3**: AWS SDK for S3-compatible storage
- **CDN**: Content delivery network for media files

### AI Services
- **OpenAI API**: GPT-4 integration for AI assistant
- **LangChain**: AI application framework (future)

### Payment Processing
- **Stripe API**: Payment gateway integration
- **stripe-python**: Official Stripe Python library

### Monitoring & Logging
- **Sentry**: Error tracking and performance monitoring
- **Django Debug Toolbar**: Development debugging
- **Python logging**: Application logging

### Development Tools
- **Docker**: Containerization
- **docker-compose**: Multi-container orchestration
- **pytest**: Testing framework
- **Black**: Code formatting
- **Flake8**: Code linting

---

## Core Components

### 1. Authentication Module (`authentication/`)
```python
authentication/
├── views.py          # Auth endpoints (signup, signin, OAuth)
├── models.py         # UserProfile, Role, Session models
├── serializers.py    # Auth data serialization
├── permissions.py    # Custom permission classes
├── middleware.py     # Supabase JWT authentication
└── utils.py         # Auth helper functions
```

**Key Features:**
- JWT token validation and refresh
- OAuth integration (10+ providers)
- Role-based access control (RBAC)
- Session management
- Password reset flow

### 2. Course Management Module (`courses/`)
```python
courses/
├── views.py          # Course CRUD operations
├── models.py         # Course, Section, Category models
├── serializers.py    # Course data serialization
├── services.py       # Business logic for courses
└── permissions.py    # Course access permissions
```

**Key Features:**
- Course creation and management
- Section and lesson organization
- Progress tracking
- Review and rating system
- Enrollment management

### 3. Media Library Module (`media_library/`)
```python
media_library/
├── views.py          # Media upload and management
├── models.py         # MediaFile, UploadSession models
├── services.py       # File storage operations
├── validators.py     # File validation
└── utils.py         # CDN and storage helpers
```

**Key Features:**
- Chunked file upload
- Backblaze B2 integration
- CDN URL generation
- Media assignment to courses
- File type validation

### 4. AI Assistant Module (`ai_assistant/`)
```python
ai_assistant/
├── views.py          # AI chat and agent endpoints
├── models.py         # AISession, AIMessage models
├── services.py       # OpenAI integration
├── agents/           # Specialized AI agents
│   ├── hint_agent.py
│   ├── quiz_agent.py
│   ├── reflection_agent.py
│   └── path_agent.py
├── prompts.py        # AI prompt templates
└── usage_tracker.py  # Usage monitoring
```

**Key Features:**
- Conversational AI chat
- Context-aware responses
- Specialized learning agents
- Usage tracking and limits
- Transcript integration

### 5. Payment Module (`payments/`)
```python
payments/
├── views.py          # Payment endpoints
├── models.py         # Transaction, Subscription models
├── services.py       # Stripe integration
├── webhooks.py       # Webhook handlers
└── utils.py         # Payment helpers
```

**Key Features:**
- Stripe payment processing
- Subscription management
- Webhook handling
- Refund processing
- Payment history

---

## Database Architecture

### Database Design Principles
1. **Normalization**: 3NF for data integrity
2. **Row Level Security**: User data isolation
3. **Indexing**: Optimized query performance
4. **Soft Deletes**: Data recovery capability
5. **Audit Trails**: Change tracking

### Core Database Schema

#### User Management Tables
```sql
-- UserProfile (Extended user data)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    supabase_user_id UUID UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Roles and Permissions
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES user_profiles(id),
    role_id UUID REFERENCES roles(id),
    assigned_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (user_id, role_id)
);
```

#### Course Management Tables
```sql
-- Courses
CREATE TABLE courses (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    instructor_id UUID REFERENCES user_profiles(id),
    category_id UUID REFERENCES course_categories(id),
    price DECIMAL(10, 2),
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_courses_instructor (instructor_id),
    INDEX idx_courses_category (category_id),
    INDEX idx_courses_published (is_published)
);

-- Course Sections
CREATE TABLE course_sections (
    id UUID PRIMARY KEY,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_sections_course (course_id),
    UNIQUE (course_id, order_index)
);
```

#### Media Storage Tables
```sql
-- Media Files
CREATE TABLE media_files (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id),
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT,
    content_type VARCHAR(100),
    storage_path TEXT,
    cdn_url TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_media_user (user_id),
    INDEX idx_media_created (created_at)
);
```

#### AI Assistant Tables
```sql
-- AI Sessions
CREATE TABLE ai_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id),
    course_id UUID REFERENCES courses(id),
    session_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE,
    INDEX idx_ai_sessions_user (user_id),
    INDEX idx_ai_sessions_course (course_id)
);

-- AI Messages
CREATE TABLE ai_messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES ai_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_ai_messages_session (session_id)
);

-- AI Usage Metrics
CREATE TABLE ai_usage_metrics (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id),
    date DATE NOT NULL,
    total_tokens INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 4),
    UNIQUE (user_id, date),
    INDEX idx_ai_usage_user_date (user_id, date)
);
```

### Database Optimization Strategies

1. **Connection Pooling**: Using Django's connection pooling with pgbouncer
2. **Query Optimization**: 
   - Selective field retrieval with `only()` and `defer()`
   - Prefetch related data with `select_related()` and `prefetch_related()`
   - Database views for complex queries
3. **Indexing Strategy**:
   - B-tree indexes for equality and range queries
   - GIN indexes for JSONB fields
   - Partial indexes for filtered queries
4. **Partitioning**: Time-based partitioning for large tables (future)

---

## Authentication & Security

### Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│   API    │────▶│ Supabase │────▶│   User   │
│          │     │ Gateway  │     │   Auth   │     │ Database │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                 │                 │
     │   1. Login    │                 │                 │
     │   Request     │                 │                 │
     ├──────────────▶│                 │                 │
     │               │  2. Forward     │                 │
     │               │  Credentials    │                 │
     │               ├────────────────▶│                 │
     │               │                 │  3. Validate    │
     │               │                 │  Credentials    │
     │               │                 ├────────────────▶│
     │               │                 │                 │
     │               │                 │◀────────────────┤
     │               │                 │  4. User Data   │
     │               │  5. JWT Token   │                 │
     │               │◀────────────────┤                 │
     │  6. Token +   │                 │                 │
     │◀──────────────┤                 │                 │
     │   User Data   │                 │                 │
     │               │                 │                 │
```

### JWT Token Structure
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_uuid",
    "email": "user@example.com",
    "role": "student",
    "exp": 1706400000,
    "iat": 1706396400,
    "aud": "authenticated",
    "app_metadata": {
      "provider": "email",
      "providers": ["email", "google"]
    }
  },
  "signature": "..."
}
```

### Security Middleware Stack
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'authentication.middleware.SupabaseAuthMiddleware',
    'ratelimit.middleware.RateLimitMiddleware',
    'audit.middleware.AuditLogMiddleware',
]
```

### Row Level Security (RLS) Policies
```sql
-- User can only see their own data
CREATE POLICY user_isolation ON user_profiles
    FOR ALL
    USING (auth.uid() = supabase_user_id);

-- Students can only see published courses
CREATE POLICY course_visibility ON courses
    FOR SELECT
    USING (
        is_published = true 
        OR instructor_id = auth.uid()
        OR EXISTS (
            SELECT 1 FROM enrollments 
            WHERE course_id = courses.id 
            AND user_id = auth.uid()
        )
    );
```

---

## API Layer

### API Design Principles
1. **RESTful Design**: Resource-based URLs, HTTP verbs
2. **Consistent Naming**: Plural nouns for collections
3. **Versioning**: URL-based versioning (/api/v1/)
4. **HATEOAS**: Hypermedia links in responses
5. **Idempotency**: Safe retries for POST/PUT operations

### API Request Flow
```
Client Request
     │
     ▼
┌─────────────────────┐
│   Rate Limiting     │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│   CORS Validation   │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│   Authentication    │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│   Authorization     │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│   Input Validation  │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│   Business Logic    │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│   Data Access       │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│   Response Format   │
└─────────────────────┘
     │
     ▼
Client Response
```

### API Serialization Strategy
```python
class CourseSerializer(serializers.ModelSerializer):
    # Nested serialization for related objects
    instructor = UserProfileSerializer(read_only=True)
    sections = CourseSectionSerializer(many=True, read_only=True)
    
    # Computed fields
    total_duration = serializers.SerializerMethodField()
    enrollment_count = serializers.SerializerMethodField()
    
    # Field-level validation
    def validate_price(self, value):
        if value < 0:
            raise ValidationError("Price cannot be negative")
        return value
    
    # Object-level validation
    def validate(self, data):
        # Complex validation logic
        return data
    
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
```

---

## File Storage System

### Storage Architecture
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client     │────▶│   Django     │────▶│ Backblaze B2 │
│   Upload     │     │   Server     │     │   Storage    │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                     │
        │                    ▼                     ▼
        │            ┌──────────────┐     ┌──────────────┐
        └───────────▶│     CDN      │────▶│   Client     │
                     │  (Delivery)  │     │   Download   │
                     └──────────────┘     └──────────────┘
```

### Chunked Upload Process
```python
# 1. Initiate upload session
def initiate_upload(request):
    session = UploadSession.objects.create(
        user=request.user,
        filename=request.data['filename'],
        file_size=request.data['file_size'],
        chunk_size=5 * 1024 * 1024  # 5MB chunks
    )
    return {
        'upload_id': session.id,
        'upload_url': generate_presigned_url(session),
        'chunk_size': session.chunk_size
    }

# 2. Upload chunks
def upload_chunk(request, upload_id):
    session = UploadSession.objects.get(id=upload_id)
    chunk_number = request.data['chunk_number']
    chunk_data = request.FILES['chunk']
    
    # Upload to B2
    b2_client.upload_part(
        bucket=settings.B2_BUCKET,
        key=f"{session.id}/chunk_{chunk_number}",
        data=chunk_data
    )
    
    session.uploaded_chunks.append(chunk_number)
    session.save()

# 3. Complete upload
def complete_upload(request, upload_id):
    session = UploadSession.objects.get(id=upload_id)
    
    # Combine chunks in B2
    file_id = b2_client.complete_multipart_upload(session)
    
    # Create MediaFile record
    media_file = MediaFile.objects.create(
        user=request.user,
        filename=session.filename,
        b2_file_id=file_id,
        cdn_url=generate_cdn_url(file_id)
    )
    
    session.delete()
    return MediaFileSerializer(media_file).data
```

### CDN Configuration
```python
CDN_CONFIG = {
    'provider': 'cloudflare',
    'base_url': 'https://cdn.unpuzzle.com',
    'cache_control': 'public, max-age=31536000',
    'image_optimization': {
        'formats': ['webp', 'avif'],
        'sizes': [320, 640, 1280, 1920],
        'quality': 85
    },
    'video_optimization': {
        'formats': ['mp4', 'webm'],
        'resolutions': ['480p', '720p', '1080p'],
        'adaptive_streaming': True
    }
}
```

---

## AI Integration

### AI Service Architecture
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   User       │────▶│   AI         │────▶│   OpenAI     │
│   Request    │     │   Service    │     │   GPT-4      │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                     │
        ▼                    ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Context    │────▶│   Prompt     │────▶│   Response   │
│   Builder    │     │   Engine     │     │   Parser     │
└──────────────┘     └──────────────┘     └──────────────┘
```

### AI Agent System
```python
class BaseAgent(ABC):
    """Abstract base class for AI agents"""
    
    @abstractmethod
    def generate_prompt(self, context: dict) -> str:
        pass
    
    @abstractmethod
    def process_response(self, response: str) -> dict:
        pass
    
    def execute(self, context: dict) -> dict:
        # Build prompt
        prompt = self.generate_prompt(context)
        
        # Call OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # Process response
        return self.process_response(response.choices[0].message.content)

class HintAgent(BaseAgent):
    """Agent for generating learning hints"""
    system_prompt = "You are a helpful tutor providing hints..."
    temperature = 0.7
    max_tokens = 200
    
    def generate_prompt(self, context):
        return f"Generate a hint for: {context['concept']}"
    
    def process_response(self, response):
        return {"hint": response, "level": "basic"}
```

### AI Usage Tracking
```python
class AIUsageTracker:
    def track_usage(self, user_id, tokens_used, cost):
        # Update daily metrics
        metric, created = AIUsageMetric.objects.get_or_create(
            user_id=user_id,
            date=timezone.now().date()
        )
        metric.total_tokens += tokens_used
        metric.total_requests += 1
        metric.cost_usd += cost
        metric.save()
        
        # Check limits
        subscription = UserSubscription.objects.get(user_id=user_id)
        if metric.total_requests >= subscription.daily_limit:
            raise AILimitExceeded("Daily AI limit reached")
        
        return {
            'requests_remaining': subscription.daily_limit - metric.total_requests,
            'reset_time': timezone.now().replace(hour=0, minute=0) + timedelta(days=1)
        }
```

---

## Payment Processing

### Payment Flow
```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│   API    │────▶│  Stripe  │────▶│ Payment  │
│          │     │          │     │          │     │ Complete │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                 │                 │
     │  1. Create    │                 │                 │
     │  Payment      │                 │                 │
     ├──────────────▶│                 │                 │
     │               │  2. Create      │                 │
     │               │  Intent         │                 │
     │               ├────────────────▶│                 │
     │               │                 │                 │
     │               │◀────────────────┤                 │
     │  3. Client    │  Intent Secret  │                 │
     │◀──────────────┤                 │                 │
     │               │                 │                 │
     │  4. Confirm   │                 │                 │
     │  Payment      │                 │                 │
     ├───────────────────────────────▶│                 │
     │               │                 │                 │
     │               │                 │  5. Webhook     │
     │               │◀────────────────┤                 │
     │               │                 │                 │
     │               │  6. Update      │                 │
     │               │  Database       │                 │
     │               ├────────────────────────────────▶│
     │  7. Success   │                 │                 │
     │◀──────────────┤                 │                 │
```

### Webhook Processing
```python
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=401)
    
    # Handle events
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        # Update payment record
        payment = Payment.objects.get(
            stripe_payment_intent=payment_intent['id']
        )
        payment.status = 'completed'
        payment.save()
        
        # Create enrollment
        Enrollment.objects.create(
            user_id=payment.user_id,
            course_id=payment.metadata['course_id'],
            payment=payment
        )
        
        # Send confirmation email
        send_enrollment_confirmation.delay(payment.user_id, payment.id)
    
    return HttpResponse(status=200)
```

---

## Caching Strategy

### Multi-Level Caching
```
┌──────────────────────────────────────┐
│         Application Cache            │
│                                      │
│  ┌────────────┐  ┌────────────┐    │
│  │   Local    │  │   Redis    │    │
│  │   Memory   │  │   Cache    │    │
│  └────────────┘  └────────────┘    │
│         │              │            │
│         ▼              ▼            │
│  ┌──────────────────────────┐      │
│  │     Cache Manager        │      │
│  └──────────────────────────┘      │
└──────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│         Database Cache               │
│  ┌────────────┐  ┌────────────┐    │
│  │  Query     │  │  Object    │    │
│  │  Cache     │  │  Cache     │    │
│  └────────────┘  └────────────┘    │
└──────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│           CDN Cache                  │
│  ┌────────────┐  ┌────────────┐    │
│  │   Static   │  │   Media    │    │
│  │   Assets   │  │   Files    │    │
│  └────────────┘  └────────────┘    │
└──────────────────────────────────────┘
```

### Cache Implementation
```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

class CacheManager:
    # Cache keys
    COURSE_LIST_KEY = "courses:list:{filters}"
    COURSE_DETAIL_KEY = "courses:detail:{course_id}"
    USER_PROFILE_KEY = "users:profile:{user_id}"
    
    # Cache durations
    SHORT_CACHE = 300  # 5 minutes
    MEDIUM_CACHE = 3600  # 1 hour
    LONG_CACHE = 86400  # 24 hours
    
    @staticmethod
    def get_or_set(key, callable, timeout=MEDIUM_CACHE):
        """Get from cache or compute and cache"""
        value = cache.get(key)
        if value is None:
            value = callable()
            cache.set(key, value, timeout)
        return value
    
    @staticmethod
    def invalidate_pattern(pattern):
        """Invalidate all keys matching pattern"""
        keys = cache.keys(pattern)
        if keys:
            cache.delete_many(keys)

# View-level caching
@cache_page(60 * 15)  # Cache for 15 minutes
def course_list(request):
    # View implementation
    pass

# Query caching
def get_popular_courses():
    return CacheManager.get_or_set(
        "courses:popular",
        lambda: Course.objects.filter(
            is_published=True
        ).order_by('-enrollment_count')[:10],
        timeout=CacheManager.LONG_CACHE
    )
```

---

## Background Jobs

### Celery Task Architecture
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Django     │────▶│    Redis     │────▶│   Celery     │
│   Process    │     │    Queue     │     │   Workers    │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                     │
        ▼                    ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Task       │     │   Task       │     │   Task       │
│   Created    │     │   Queued     │     │   Executed   │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Task Implementation
```python
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3)
def process_video_upload(self, media_file_id):
    """Process uploaded video file"""
    try:
        media_file = MediaFile.objects.get(id=media_file_id)
        
        # Generate thumbnails
        thumbnail_url = generate_video_thumbnail(media_file.cdn_url)
        
        # Extract metadata
        metadata = extract_video_metadata(media_file.cdn_url)
        
        # Generate transcripts
        transcript = generate_transcript(media_file.cdn_url)
        
        # Update media file
        media_file.thumbnail_url = thumbnail_url
        media_file.metadata = metadata
        media_file.transcript = transcript
        media_file.processing_status = 'completed'
        media_file.save()
        
        logger.info(f"Video {media_file_id} processed successfully")
        
    except Exception as exc:
        logger.error(f"Video processing failed: {exc}")
        raise self.retry(exc=exc, countdown=60)

@shared_task
def send_enrollment_confirmation(user_id, enrollment_id):
    """Send enrollment confirmation email"""
    enrollment = Enrollment.objects.get(id=enrollment_id)
    user = UserProfile.objects.get(id=user_id)
    
    send_email(
        to=user.email,
        subject="Course Enrollment Confirmation",
        template="enrollment_confirmation.html",
        context={
            'user': user,
            'enrollment': enrollment,
            'course': enrollment.course
        }
    )

# Periodic tasks
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-sessions': {
        'task': 'authentication.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'generate-analytics-reports': {
        'task': 'analytics.tasks.generate_daily_reports',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'check-subscription-expiry': {
        'task': 'payments.tasks.check_subscription_expiry',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    }
}
```

---

## Deployment Architecture

### Production Deployment
```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                        │
│                    (AWS ALB / Nginx)                     │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Django     │    │   Django     │    │   Django     │
│   Server 1   │    │   Server 2   │    │   Server 3   │
│  (Gunicorn)  │    │  (Gunicorn)  │    │  (Gunicorn)  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                ┌──────────────────────┐
                │   Shared Services    │
                │  - PostgreSQL (RDS)  │
                │  - Redis (ElastiCache)│
                │  - Celery Workers    │
                └──────────────────────┘
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "unpuzzle.wsgi:application"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/unpuzzle
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./media:/app/media
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=unpuzzle
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  celery:
    build: .
    command: celery -A unpuzzle worker -l info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/unpuzzle
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  celery-beat:
    build: .
    command: celery -A unpuzzle beat -l info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/unpuzzle
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## Monitoring & Logging

### Monitoring Stack
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Application │────▶│   Metrics    │────▶│   Grafana    │
│              │     │  Collector   │     │  Dashboard   │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                     │
        ▼                    ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Logs      │────▶│     ELK      │────▶│   Kibana     │
│              │     │    Stack     │     │  Dashboard   │
└──────────────┘     └──────────────┘     └──────────────┘
        │                    │                     │
        ▼                    ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Errors     │────▶│    Sentry    │────▶│   Alerts     │
│              │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Logging Configuration
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/unpuzzle/app.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 10,
            'formatter': 'json'
        },
        'sentry': {
            'class': 'sentry_sdk.integrations.logging.EventHandler',
            'level': 'ERROR'
        }
    },
    'root': {
        'handlers': ['console', 'file', 'sentry'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'unpuzzle': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}
```

### Performance Monitoring
```python
# Middleware for request tracking
class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > 1.0:
            logger.warning(
                f"Slow request: {request.path} took {duration:.2f}s",
                extra={
                    'path': request.path,
                    'method': request.method,
                    'duration': duration,
                    'user_id': getattr(request.user, 'id', None)
                }
            )
        
        # Send metrics
        statsd.timing('request.duration', duration * 1000)
        statsd.incr(f'request.status.{response.status_code}')
        
        return response
```

---

## Scalability Considerations

### Horizontal Scaling Strategy
1. **Stateless Application Servers**: No server-side sessions
2. **Database Connection Pooling**: PgBouncer for connection management
3. **Read Replicas**: Separate read/write database connections
4. **Caching Layer**: Redis cluster for distributed caching
5. **CDN**: Global content delivery for static assets
6. **Load Balancing**: Round-robin with health checks

### Vertical Scaling Optimization
```python
# Database query optimization
class OptimizedCourseQuerySet(models.QuerySet):
    def with_related(self):
        """Prefetch all related data"""
        return self.select_related(
            'instructor',
            'category'
        ).prefetch_related(
            'sections',
            'sections__media_files',
            'enrollments',
            'reviews'
        )
    
    def published(self):
        """Filter published courses"""
        return self.filter(is_published=True)
    
    def for_user(self, user):
        """Get courses accessible by user"""
        if user.is_anonymous:
            return self.published()
        
        return self.filter(
            Q(is_published=True) |
            Q(instructor=user) |
            Q(enrollments__user=user)
        ).distinct()

# Usage
courses = Course.objects.with_related().for_user(request.user)
```

### Microservices Migration Path
```
Current Monolith                    Future Microservices
┌──────────────┐                   ┌──────────────┐
│              │                   │   Gateway    │
│    Django    │                   └──────────────┘
│   Monolith   │                           │
│              │          ┌────────────────┼────────────────┐
└──────────────┘          ▼                ▼                ▼
                   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                   │    Auth      │ │   Course     │ │   Payment    │
                   │   Service    │ │   Service    │ │   Service    │
                   └──────────────┘ └──────────────┘ └──────────────┘
                          ▼                ▼                ▼
                   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                   │   Media      │ │      AI      │ │  Analytics   │
                   │   Service    │ │   Service    │ │   Service    │
                   └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Security Architecture

### Security Layers
```
┌─────────────────────────────────────────────────────────┐
│                   WAF (Web Application Firewall)         │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   DDoS Protection                        │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   SSL/TLS Termination                    │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Rate Limiting                          │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Authentication                         │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Authorization                          │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Input Validation                       │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Data Encryption                        │
└─────────────────────────────────────────────────────────┘
```

### Security Best Practices Implementation
```python
# Input sanitization
from django.utils.html import escape
from bleach import clean

def sanitize_user_input(text):
    """Sanitize user input to prevent XSS"""
    # Remove dangerous HTML
    cleaned = clean(
        text,
        tags=['p', 'br', 'strong', 'em', 'u'],
        attributes={},
        strip=True
    )
    return cleaned

# SQL injection prevention (using ORM)
def get_user_courses(user_id):
    # Safe: Uses parameterized queries
    return Course.objects.filter(
        enrollments__user_id=user_id
    )
    
    # Unsafe: Direct SQL (avoided)
    # cursor.execute(f"SELECT * FROM courses WHERE user_id = {user_id}")

# CSRF protection
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def update_profile(request):
    # CSRF token validated automatically
    pass

# Rate limiting
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='10/m', method='POST')
def create_course(request):
    # Limited to 10 course creations per minute per user
    pass

# Secrets management
from django.conf import settings
import boto3

def get_secret(secret_name):
    """Retrieve secrets from AWS Secrets Manager"""
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# Data encryption
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext):
        return self.cipher.encrypt(plaintext.encode())
    
    def decrypt(self, ciphertext):
        return self.cipher.decrypt(ciphertext).decode()
```

---

## Conclusion

The Unpuzzle MVP Backend architecture provides a robust, scalable, and secure foundation for a modern learning management system. Key architectural highlights include:

1. **Modular Design**: Clean separation of concerns enabling future microservices migration
2. **Security-First**: Multiple layers of security from WAF to data encryption
3. **Scalability**: Horizontal and vertical scaling capabilities with caching and CDN
4. **External Service Integration**: Seamless integration with Supabase, Stripe, OpenAI, and Backblaze
5. **Performance Optimization**: Multi-level caching, query optimization, and async processing
6. **Monitoring & Observability**: Comprehensive logging, metrics, and error tracking
7. **Developer Experience**: Well-documented APIs, consistent patterns, and automated testing

The architecture is designed to support the current MVP requirements while providing a clear path for future growth and feature expansion.