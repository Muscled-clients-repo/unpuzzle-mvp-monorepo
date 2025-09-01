# Puzzle Reflection System - Comprehensive Implementation Plan

**Date:** 2025-08-28  
**Purpose:** Complete implementation roadmap adapted to current project architecture  
**Integration Type:** New Django App with Media Library Integration

---

## 📋 **Documentation Analysis Summary**

Based on analysis of all documentation and current project structure:

### **Key Insights:**
1. **Media Integration Approach**: Use MediaFile foreign key instead of FileField
2. **Architecture Pattern**: Follow existing app structure with AuditableModel base
3. **Authentication**: Leverage Supabase auth middleware
4. **API Pattern**: Follow DRF ViewSet pattern like other apps
5. **File Handling**: Reuse professional Backblaze B2 + CDN infrastructure


---

## 🏗️ **Architecture Integration Points**

### **Current System Integration:**
- **Authentication**: Supabase auth middleware (already implemented)
- **Media Storage**: Backblaze B2 with chunked uploads (media_library app)
- **Base Models**: AuditableModel with UUID, timestamps, soft delete
- **API Structure**: DRF with consistent patterns across apps
- **URL Routing**: Centralized v1 API routing
- **RLS Support**: Row Level Security for data isolation

---

## 🚀 **Implementation Plan**

### **Phase 1: Django App Setup (30 minutes)**

#### **1.1 Create Puzzle Reflections App**
```bash
python manage.py startapp puzzle_reflections
```

#### **1.2 Add to INSTALLED_APPS**
Update `app/settings.py`:
```python
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_filters',
    'accounts',
    'courses',
    'enrollments', 
    'media_library',
    'payments',
    'analytics',
    'notifications',
    'ai_assistant',
    'puzzle_reflections',  # ADD THIS
]
```

#### **1.3 Add URL Routing**
Update `app/urls.py`:
```python
urlpatterns = [
    # ... existing patterns ...
    path('api/v1/reflections/', include('puzzle_reflections.urls')),  # ADD THIS
]
```

---

### **Phase 2: Model Implementation (45 minutes)**

#### **2.1 Create Model in `puzzle_reflections/models.py`**
```python
"""
Puzzle reflection models following project architecture patterns.
"""
from django.db import models
from app.models import AuditableModel, RLSModelMixin


class ReflectionType(models.TextChoices):
    """Reflection type choices"""
    COMPLETION = 'completion', 'Puzzle Completion'
    LEARNING = 'learning', 'Learning Reflection'
    CHALLENGE = 'challenge', 'Challenge Response'
    SUMMARY = 'summary', 'Summary'
    OTHER = 'other', 'Other'


class PuzzleReflection(AuditableModel, RLSModelMixin):
    """
    Model for storing user puzzle reflections with media integration.
    Follows the project's AuditableModel pattern with RLS support.
    """
    
    # Core relationships (using proper FK references)
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='puzzle_reflections',
        help_text="User who created this reflection"
    )
    
    # Content association
    video_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="ID of the video this reflection is for"
    )
    
    # Reflection categorization
    reflection_type = models.CharField(
        max_length=20,
        choices=ReflectionType.choices,
        default=ReflectionType.COMPLETION,
        db_index=True
    )
    
    # Media file integration (KEY ARCHITECTURAL DECISION)
    media_file = models.ForeignKey(
        'media_library.MediaFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puzzle_reflections',
        help_text="Uploaded reflection media file (video/audio/document)"
    )
    
    # Alternative content options
    loom_link = models.URLField(
        null=True,
        blank=True,
        help_text="Optional Loom video link"
    )
    
    text_content = models.TextField(
        blank=True,
        null=True,
        help_text="Optional text reflection content"
    )
    
    # Metadata
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    # Optional course association for analytics
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='puzzle_reflections'
    )
    
    class Meta:
        db_table = 'puzzle_reflections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'video_id']),
            models.Index(fields=['reflection_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['media_file']),
            models.Index(fields=['course', 'user']),
        ]
        # RLS permissions
        permissions = (
            ('puzzle_reflections_rls', 'Row Level Security for puzzle reflections'),
        )
    
    def __str__(self):
        return f"Reflection by {self.user.full_name or self.user.email} for video {self.video_id}"
    
    @property
    def has_media(self):
        """Check if reflection has any media content"""
        return bool(self.media_file or self.loom_link)
    
    @property
    def media_url(self):
        """Get the primary media URL (MediaFile CDN or Loom)"""
        if self.media_file and self.media_file.cdn_url:
            return self.media_file.cdn_url
        elif self.media_file and self.media_file.storage_url:
            return self.media_file.storage_url
        elif self.loom_link:
            return self.loom_link
        return None
    
    @property
    def media_thumbnail(self):
        """Get thumbnail URL if available"""
        if self.media_file and self.media_file.thumbnail_url:
            return self.media_file.thumbnail_url
        return None
    
    # RLS Implementation
    @classmethod
    def get_rls_policies(cls):
        """Define RLS policies for user data isolation"""
        return [
            {
                'name': 'puzzle_reflections_user_isolation',
                'operation': 'ALL',
                'role': 'authenticated',
                'using': 'user_id = (auth.jwt() ->> \'sub\')::uuid',
                'with_check': 'user_id = (auth.jwt() ->> \'sub\')::uuid'
            }
        ]
```

#### **2.2 Create Migration**
```bash
python manage.py makemigrations puzzle_reflections
python manage.py migrate
```

---

### **Phase 3: Serializers Implementation (30 minutes)**

#### **3.1 Create `puzzle_reflections/serializers.py`**
```python
"""
Serializers for puzzle reflections API.
"""
from rest_framework import serializers
from media_library.serializers import MediaFileSerializer
from .models import PuzzleReflection, ReflectionType


class PuzzleReflectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reflections"""
    
    media_url = serializers.ReadOnlyField()
    media_thumbnail = serializers.ReadOnlyField()
    has_media = serializers.ReadOnlyField()
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = PuzzleReflection
        fields = [
            'id', 'video_id', 'reflection_type', 'title',
            'media_url', 'media_thumbnail', 'has_media',
            'loom_link', 'user_name', 'created_at'
        ]


class PuzzleReflectionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with full media information"""
    
    # Include full media file details
    media_file_details = MediaFileSerializer(source='media_file', read_only=True)
    
    # Computed fields for easy frontend access
    media_url = serializers.ReadOnlyField()
    media_thumbnail = serializers.ReadOnlyField()
    has_media = serializers.ReadOnlyField()
    
    # Media metadata
    file_type = serializers.CharField(source='media_file.file_type', read_only=True)
    file_size = serializers.IntegerField(source='media_file.file_size', read_only=True)
    duration = serializers.IntegerField(source='media_file.duration', read_only=True)
    
    # User info
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = PuzzleReflection
        fields = [
            'id', 'video_id', 'reflection_type', 'title', 'description',
            'media_file', 'media_file_details', 'media_url', 'media_thumbnail',
            'has_media', 'file_type', 'file_size', 'duration',
            'loom_link', 'text_content', 'course', 'course_title',
            'user_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PuzzleReflectionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating reflections"""
    
    class Meta:
        model = PuzzleReflection
        fields = [
            'video_id', 'reflection_type', 'title', 'description',
            'media_file', 'loom_link', 'text_content', 'course'
        ]
    
    def validate(self, data):
        """Ensure at least one content type is provided"""
        content_fields = ['media_file', 'loom_link', 'text_content']
        if not any(data.get(field) for field in content_fields):
            raise serializers.ValidationError(
                "At least one of media_file, loom_link, or text_content must be provided."
            )
        return data


class ReflectionSummarySerializer(serializers.Serializer):
    """Serializer for reflection summaries by video"""
    video_id = serializers.CharField()
    total_reflections = serializers.IntegerField()
    reflection_types = serializers.ListField(
        child=serializers.DictField()
    )
    latest_reflection = PuzzleReflectionListSerializer()
```

---

### **Phase 4: Views Implementation (45 minutes)**

#### **4.1 Create `puzzle_reflections/views.py`**
```python
"""
API views for puzzle reflections.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from accounts.models import UserProfile
from .models import PuzzleReflection, ReflectionType
from .serializers import (
    PuzzleReflectionListSerializer,
    PuzzleReflectionDetailSerializer, 
    PuzzleReflectionCreateUpdateSerializer,
    ReflectionSummarySerializer
)
from .filters import PuzzleReflectionFilter


class PuzzleReflectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing puzzle reflections.
    Provides CRUD operations with proper user isolation.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PuzzleReflectionFilter
    
    def get_queryset(self):
        """Return reflections for the authenticated user only"""
        if not hasattr(self.request, 'user_profile'):
            return PuzzleReflection.objects.none()
        
        return PuzzleReflection.objects.filter(
            user=self.request.user_profile,
            is_deleted=False
        ).select_related(
            'user', 'course', 'media_file'
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PuzzleReflectionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PuzzleReflectionCreateUpdateSerializer
        else:
            return PuzzleReflectionDetailSerializer
    
    def perform_create(self, serializer):
        """Set user when creating reflection"""
        serializer.save(
            user=self.request.user_profile,
            created_by=self.request.user_id
        )
    
    def perform_update(self, serializer):
        """Set updated_by when updating"""
        serializer.save(updated_by=self.request.user_id)
    
    def perform_destroy(self, instance):
        """Soft delete instead of hard delete"""
        instance.soft_delete(user_id=self.request.user_id)
    
    @action(detail=False, methods=['get'])
    def by_video(self, request):
        """Get reflections for a specific video"""
        video_id = request.query_params.get('video_id')
        if not video_id:
            return Response(
                {'error': 'video_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reflections = self.get_queryset().filter(video_id=video_id)
        serializer = PuzzleReflectionListSerializer(reflections, many=True)
        
        return Response({
            'video_id': video_id,
            'total_reflections': reflections.count(),
            'reflections': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get reflection summary statistics"""
        queryset = self.get_queryset()
        
        # Overall stats
        total_reflections = queryset.count()
        
        # By type
        type_stats = queryset.values('reflection_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # By video
        video_stats = queryset.values('video_id').annotate(
            count=Count('id')
        ).order_by('-count')[:10]  # Top 10 videos
        
        # Recent activity
        recent_reflections = queryset[:5]
        recent_serializer = PuzzleReflectionListSerializer(recent_reflections, many=True)
        
        return Response({
            'total_reflections': total_reflections,
            'by_type': type_stats,
            'top_videos': video_stats,
            'recent_reflections': recent_serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status (future enhancement)"""
        # Placeholder for future favorite functionality
        return Response({'message': 'Feature coming soon'})
```

#### **4.2 Create `puzzle_reflections/filters.py`**
```python
"""
Filters for puzzle reflection API.
"""
import django_filters
from .models import PuzzleReflection, ReflectionType


class PuzzleReflectionFilter(django_filters.FilterSet):
    """Filter set for puzzle reflections"""
    
    video_id = django_filters.CharFilter(lookup_expr='icontains')
    reflection_type = django_filters.ChoiceFilter(choices=ReflectionType.choices)
    has_media_file = django_filters.BooleanFilter(method='filter_has_media_file')
    has_loom_link = django_filters.BooleanFilter(method='filter_has_loom_link')
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = PuzzleReflection
        fields = ['video_id', 'reflection_type', 'course']
    
    def filter_has_media_file(self, queryset, name, value):
        """Filter by presence of media file"""
        if value:
            return queryset.filter(media_file__isnull=False)
        return queryset.filter(media_file__isnull=True)
    
    def filter_has_loom_link(self, queryset, name, value):
        """Filter by presence of loom link"""
        if value:
            return queryset.exclude(loom_link__in=['', None])
        return queryset.filter(Q(loom_link='') | Q(loom_link__isnull=True))
    
    def filter_search(self, queryset, name, value):
        """Search across title, description, and text content"""
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(text_content__icontains=value)
        )
```

---

### **Phase 5: URL Configuration (15 minutes)**

#### **5.1 Create `puzzle_reflections/urls.py`**
```python
"""
URL configuration for puzzle reflections app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PuzzleReflectionViewSet

app_name = 'puzzle_reflections'

router = DefaultRouter()
router.register(r'', PuzzleReflectionViewSet, basename='puzzle-reflection')

urlpatterns = [
    path('', include(router.urls)),
]
```

---

### **Phase 6: Database Migration & RLS Setup (15 minutes)**

#### **6.1 Create and Apply Migration**
```bash
python manage.py makemigrations puzzle_reflections
python manage.py migrate
```

#### **6.2 Set up RLS Policies**
Create SQL file `sql/setup_puzzle_reflections_rls.sql`:
```sql
-- Enable RLS for puzzle_reflections table
ALTER TABLE puzzle_reflections ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own reflections
CREATE POLICY puzzle_reflections_user_isolation ON puzzle_reflections
    FOR ALL TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub')::uuid)
    WITH CHECK (user_id = (auth.jwt() ->> 'sub')::uuid);

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON puzzle_reflections TO authenticated;
```

---

### **Phase 7: Testing & Validation (30 minutes)**

#### **7.1 API Endpoint Testing**
```bash
# Test endpoints with curl
curl -X GET "http://localhost:3001/api/v1/reflections/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

curl -X POST "http://localhost:3001/api/v1/reflections/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "css-flexbox-101",
    "reflection_type": "completion",
    "title": "My Test Reflection",
    "text_content": "This is a test reflection."
  }'
```

#### **7.2 Media Integration Testing**
```javascript
// Frontend: Two-step upload process
// Step 1: Upload media file
const mediaFile = await uploadMediaFile(videoFile);

// Step 2: Create reflection
const reflection = await createReflection({
  video_id: 'css-flexbox-101',
  reflection_type: 'completion', 
  media_file: mediaFile.id,
  title: 'My Video Reflection'
});
```

---

## 📊 **API Endpoints Summary**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/reflections/` | List user's reflections |
| `POST` | `/api/v1/reflections/` | Create new reflection |
| `GET` | `/api/v1/reflections/{id}/` | Get specific reflection |
| `PUT/PATCH` | `/api/v1/reflections/{id}/` | Update reflection |
| `DELETE` | `/api/v1/reflections/{id}/` | Soft delete reflection |
| `GET` | `/api/v1/reflections/by_video/?video_id=X` | Get reflections for video |
| `GET` | `/api/v1/reflections/summary/` | Get user's reflection statistics |

---

## 🔧 **Integration Benefits**

### **Architectural Consistency:**
✅ **Follows Project Patterns**: AuditableModel, RLS, UUID primary keys  
✅ **Reuses Infrastructure**: Supabase auth, Backblaze storage, DRF patterns  
✅ **Maintains Security**: User isolation, file validation, secure storage  
✅ **Professional Quality**: Proper error handling, pagination, filtering  

### **Media Integration Advantages:**
✅ **Enterprise Storage**: Backblaze B2 cloud storage with CDN  
✅ **Large File Support**: Chunked uploads with progress tracking  
✅ **Rich Metadata**: Automatic thumbnails, duration, resolution detection  
✅ **Cost Effective**: Shared infrastructure, no duplicate upload systems  

---

## ⏱️ **Implementation Timeline**

| Phase | Time | Description |
|-------|------|-------------|
| **Phase 1** | 30 min | Django app setup, INSTALLED_APPS, URL routing |
| **Phase 2** | 45 min | Model implementation with proper FK relationships |
| **Phase 3** | 30 min | Serializers for list/detail/create operations |
| **Phase 4** | 45 min | ViewSet implementation with filtering/search |
| **Phase 5** | 15 min | URL configuration and routing |
| **Phase 6** | 15 min | Database migration and RLS setup |
| **Phase 7** | 30 min | Testing and validation |
| **TOTAL** | **3.5 hours** | Complete implementation |

---

## 🎯 **Success Criteria Checklist**

### **Functional Requirements:**
- [ ] Users can create reflections with MediaFile references
- [ ] Support for Loom links and text content
- [ ] CRUD operations with proper user isolation
- [ ] Filter by video_id, reflection_type, date range
- [ ] Search across title, description, text content
- [ ] Integration with existing media upload system

### **Technical Requirements:**
- [ ] Follows AuditableModel pattern with soft delete
- [ ] Implements RLS for user data isolation  
- [ ] Uses MediaFile FK instead of FileField
- [ ] Proper error handling and validation
- [ ] API documentation and testing
- [ ] Database indexes for performance

---

## 🚀 **Ready to Implement**

This plan provides a complete, production-ready implementation that:

1. **Integrates seamlessly** with your current Django architecture
2. **Reuses existing infrastructure** (media library, auth, patterns)
3. **Follows established conventions** throughout the codebase
4. **Provides professional-grade features** out of the box
5. **Can be implemented in ~3.5 hours** total

The system will handle file uploads through the proven media library system while providing a clean, dedicated API for puzzle reflections with proper user isolation and security.