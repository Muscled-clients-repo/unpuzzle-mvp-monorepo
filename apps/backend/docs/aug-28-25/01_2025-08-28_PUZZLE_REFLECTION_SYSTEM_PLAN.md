# Puzzle Reflection System Implementation Plan

**Date:** 2025-08-28  
**Purpose:** Complete development roadmap for implementing puzzle reflection functionality with file upload capabilities  
**Phase:** Media Upload & Storage System for Puzzle Reflections

---

## 📋 **Implementation Overview**

This plan addresses the need for a simple puzzle reflection system that allows users to upload reflection files (video/audio/documents) without requiring AI processing. The system will store user reflections linked to specific videos with optional Loom integration.

### **Current State Analysis**
- ✅ AI reflection agent implemented (but not needed for this use case)
- ✅ Media library system for file uploads
- ✅ User authentication and video tracking
- ✅ Course and enrollment system
- ❌ No puzzle reflection model
- ❌ No file-based reflection endpoints
- ❌ No Loom link integration
- ❌ No reflection type categorization

---

## 🏗️ **Implementation Phases**

### **Phase 1: Database Models & Schema (Day 1)**

#### **1.1 Create PuzzleReflection Model**
```python
class PuzzleReflection(models.Model):
    """Model for storing user puzzle reflections with file uploads"""
    
    # Core fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='puzzle_reflections')
    video_id = models.CharField(max_length=255, help_text="ID of the video this reflection is for")
    reflection_type = models.CharField(
        max_length=50,
        choices=[
            ('completion', 'Puzzle Completion'),
            ('learning', 'Learning Reflection'),
            ('challenge', 'Challenge Response'),
            ('summary', 'Summary'),
            ('other', 'Other')
        ],
        default='completion'
    )
    
    # File storage
    reflection_file = models.FileField(
        upload_to='reflections/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Uploaded reflection file (video, audio, document)"
    )
    
    # Optional external links
    loom_link = models.URLField(
        null=True,
        blank=True,
        help_text="Optional Loom video link"
    )
    
    # Optional text content
    text_content = models.TextField(
        blank=True,
        null=True,
        help_text="Optional text reflection content"
    )
    
    # Metadata
    title = models.CharField(max_length=255, blank=True, help_text="Optional reflection title")
    description = models.TextField(blank=True, help_text="Optional reflection description")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'puzzle_reflections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'video_id']),
            models.Index(fields=['reflection_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Reflection by {self.user.email} for video {self.video_id}"
```

#### **1.2 Database Migration**
- Create migration for PuzzleReflection model
- Add appropriate indexes for performance
- Set up file storage configurations

### **Phase 2: API Endpoints (Day 1)**

#### **2.1 Reflection CRUD Endpoints**

**Base URL:** `/api/v1/reflections/`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/reflections/` | GET | List user's reflections |
| `/api/v1/reflections/` | POST | Create new reflection |
| `/api/v1/reflections/{id}/` | GET | Get specific reflection |
| `/api/v1/reflections/{id}/` | PUT/PATCH | Update reflection |
| `/api/v1/reflections/{id}/` | DELETE | Delete reflection |
| `/api/v1/reflections/video/{video_id}/` | GET | Get reflections for specific video |

#### **2.2 File Upload Integration**
- Integrate with existing media library system
- Support multiple file formats:
  - Video: `.mp4`, `.mov`, `.avi`
  - Audio: `.mp3`, `.wav`, `.m4a`
  - Documents: `.pdf`, `.docx`, `.txt`
- File size limits and validation
- Secure file storage with proper permissions

### **Phase 3: Serializers & Validation (Day 1)**

#### **3.1 Request/Response Serializers**
```python
class PuzzleReflectionSerializer(serializers.ModelSerializer):
    """Serializer for puzzle reflections"""
    
    reflection_file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    
    class Meta:
        model = PuzzleReflection
        fields = [
            'id', 'video_id', 'reflection_type', 'title', 'description',
            'reflection_file', 'reflection_file_url', 'file_size', 'file_type',
            'loom_link', 'text_content', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_reflection_file_url(self, obj):
        if obj.reflection_file:
            return obj.reflection_file.url
        return None
    
    def get_file_size(self, obj):
        if obj.reflection_file:
            return obj.reflection_file.size
        return None
    
    def get_file_type(self, obj):
        if obj.reflection_file:
            return obj.reflection_file.name.split('.')[-1].lower()
        return None
```

#### **3.2 Upload Serializer**
```python
class ReflectionUploadSerializer(serializers.Serializer):
    """Serializer for reflection file uploads"""
    
    video_id = serializers.CharField(max_length=255)
    reflection_type = serializers.ChoiceField(
        choices=PuzzleReflection.REFLECTION_TYPE_CHOICES,
        default='completion'
    )
    reflection_file = serializers.FileField(required=False)
    loom_link = serializers.URLField(required=False, allow_blank=True)
    text_content = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Ensure at least one content type is provided"""
        if not any([
            data.get('reflection_file'),
            data.get('loom_link'),
            data.get('text_content')
        ]):
            raise serializers.ValidationError(
                "At least one of reflection_file, loom_link, or text_content must be provided."
            )
        return data
```

### **Phase 4: Views & Business Logic (Day 2)**

#### **4.1 Reflection ViewSet**
- Full CRUD operations
- File upload handling
- Permissions and authentication
- Filtering by video_id, reflection_type
- Pagination for large lists

#### **4.2 Key Features**
- **Multi-format Support**: Handle video, audio, document uploads
- **Loom Integration**: Store and validate Loom links
- **User Isolation**: Users can only see their own reflections
- **Video Association**: Link reflections to specific video content
- **Search & Filter**: Find reflections by type, video, date

### **Phase 5: Frontend Integration Points (Day 2)**

#### **5.1 API Response Format**
```json
{
  "id": 123,
  "video_id": "css-flexbox-101",
  "reflection_type": "completion",
  "title": "My CSS Learning Journey",
  "description": "Reflection on completing the CSS flexbox puzzles",
  "reflection_file": "reflections/2025/08/28/user123_reflection.mp4",
  "reflection_file_url": "https://yourdomain.com/media/reflections/2025/08/28/user123_reflection.mp4",
  "file_size": 15728640,
  "file_type": "mp4",
  "loom_link": "https://loom.com/share/abc123",
  "text_content": "I learned a lot about flexbox today...",
  "created_at": "2025-08-28T10:30:00Z",
  "updated_at": "2025-08-28T10:30:00Z"
}
```

#### **5.2 Upload Flow**
1. User completes puzzle
2. Frontend presents reflection options:
   - Upload video/audio file
   - Provide Loom link
   - Write text reflection
   - Or combination of above
3. Submit to API endpoint
4. Display success/error feedback
5. Show reflection in user's profile/progress

---

## 🔧 **Technical Specifications**

### **File Storage**
- Use Django's FileField with proper upload paths
- Integrate with existing media library security
- Support cloud storage (S3) for production
- Implement file cleanup for deleted reflections

### **Security**
- User can only access their own reflections
- Validate file types and sizes
- Sanitize user input
- Secure file serving with permissions

### **Performance**
- Database indexing on common query fields
- Pagination for reflection lists
- Lazy loading of file metadata
- Caching for frequently accessed reflections

---

## 🎯 **Success Criteria**

### **Functional Requirements**
- [ ] Users can upload reflection files for specific videos
- [ ] Support for video, audio, and document file types
- [ ] Optional Loom link integration
- [ ] Text-based reflections as alternative
- [ ] CRUD operations for all reflections
- [ ] Filter reflections by video or type

### **Non-Functional Requirements**
- [ ] Secure file storage and access
- [ ] Responsive API endpoints (<500ms)
- [ ] Proper error handling and validation
- [ ] Clean, documented code
- [ ] Database migrations without data loss

---

## 📋 **Next Steps**

1. **Create the PuzzleReflection model** in appropriate Django app
2. **Implement serializers** with proper validation
3. **Build API endpoints** with file upload support
4. **Test file upload functionality** with different formats
5. **Add Loom link validation** and integration
6. **Document API endpoints** for frontend team
7. **Deploy and test** in staging environment

---

**Note:** This system is designed to be simple and focused on file storage rather than AI processing, making it more efficient and cost-effective for basic reflection capture.