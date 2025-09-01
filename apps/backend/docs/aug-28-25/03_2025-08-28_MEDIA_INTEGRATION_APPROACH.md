# Puzzle Reflection Media Integration Approach

**Date:** 2025-08-28  
**Purpose:** Define how puzzle reflections integrate with existing media library system  
**Integration Type:** MediaFile Reference Pattern

---

## 🎯 **Integration Strategy**

Instead of creating a separate file upload system, we'll leverage the existing robust media library infrastructure that already handles:

- ✅ **Backblaze B2 Cloud Storage** with CDN delivery
- ✅ **Chunked uploads** for large files with progress tracking
- ✅ **File type validation** and security scanning
- ✅ **Metadata extraction** (duration, resolution, thumbnails)
- ✅ **Professional upload flow** with error handling

---

## 🏗️ **Updated Model Structure**

### **PuzzleReflection Model (Revised)**
```python
from django.db import models
from app.models import AuditableModel

class PuzzleReflection(AuditableModel):
    """Model for storing user puzzle reflections with media integration"""
    
    # Core relationships
    user = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        related_name='puzzle_reflections'
    )
    
    # Content association
    video_id = models.CharField(
        max_length=255,
        help_text="ID of the video this reflection is for"
    )
    
    # Reflection categorization
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
    
    # Media file integration (MAIN CHANGE)
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
    
    class Meta:
        db_table = 'puzzle_reflections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'video_id']),
            models.Index(fields=['reflection_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['media_file']),  # Index for media lookups
        ]
    
    def __str__(self):
        return f"Reflection by {self.user.email} for video {self.video_id}"
    
    @property
    def has_media(self):
        """Check if reflection has any media content"""
        return bool(self.media_file or self.loom_link)
    
    @property
    def media_url(self):
        """Get the primary media URL (MediaFile CDN or Loom)"""
        if self.media_file and self.media_file.cdn_url:
            return self.media_file.cdn_url
        elif self.loom_link:
            return self.loom_link
        return None
```

---

## 🔄 **Upload Flow Integration**

### **Two-Step Process:**

#### **Step 1: Upload Media File**
Use existing media library endpoints:

```javascript
// Frontend: Upload reflection file using existing media API
const uploadResponse = await fetch('/api/v1/media/upload/initiate/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    filename: 'my-reflection-video.mp4',
    file_size: 15728640,
    file_type: 'video',
    mime_type: 'video/mp4'
  })
});

// Complete the chunked upload process...
const mediaFile = await completeUpload(uploadId, chunks);
```

#### **Step 2: Create Puzzle Reflection**
Reference the uploaded MediaFile:

```javascript
// Frontend: Create puzzle reflection with MediaFile reference
const reflection = await fetch('/api/v1/reflections/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    video_id: 'css-flexbox-101',
    reflection_type: 'completion',
    media_file: mediaFile.id,  // Reference the uploaded MediaFile UUID
    title: 'My CSS Flexbox Learning Journey',
    description: 'Reflection on completing all flexbox puzzles',
    text_content: 'I learned so much about flexbox today...'
  })
});
```

---

## 📊 **Updated API Specification**

### **Serializers**

```python
class PuzzleReflectionSerializer(serializers.ModelSerializer):
    """Serializer for puzzle reflections with media integration"""
    
    # Include full media file details
    media_file_details = MediaFileSerializer(source='media_file', read_only=True)
    
    # Computed fields for easy frontend access
    media_url = serializers.ReadOnlyField()
    has_media = serializers.ReadOnlyField()
    file_type = serializers.CharField(source='media_file.file_type', read_only=True)
    file_size = serializers.IntegerField(source='media_file.file_size', read_only=True)
    duration = serializers.IntegerField(source='media_file.duration', read_only=True)
    thumbnail_url = serializers.URLField(source='media_file.thumbnail_url', read_only=True)
    
    class Meta:
        model = PuzzleReflection
        fields = [
            'id', 'video_id', 'reflection_type', 'title', 'description',
            'media_file', 'media_file_details', 'media_url', 'has_media',
            'file_type', 'file_size', 'duration', 'thumbnail_url',
            'loom_link', 'text_content', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Ensure at least one content type is provided"""
        if not any([
            data.get('media_file'),
            data.get('loom_link'),
            data.get('text_content')
        ]):
            raise serializers.ValidationError(
                "At least one of media_file, loom_link, or text_content must be provided."
            )
        return data
```

### **Response Format**

```json
{
  "id": 123,
  "video_id": "css-flexbox-101",
  "reflection_type": "completion",
  "title": "My CSS Learning Journey",
  "description": "Reflection on completing flexbox puzzles",
  "media_file": "550e8400-e29b-41d4-a716-446655440000",
  "media_file_details": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "reflection_20250828.mp4",
    "original_filename": "my-reflection-video.mp4",
    "file_type": "video",
    "file_size": 15728640,
    "storage_url": "https://backblaze-url.com/file.mp4",
    "cdn_url": "https://cdn-url.com/file.mp4",
    "thumbnail_url": "https://cdn-url.com/thumbnail.jpg",
    "duration": 180,
    "width": 1920,
    "height": 1080,
    "processing_status": "completed"
  },
  "media_url": "https://cdn-url.com/file.mp4",
  "has_media": true,
  "file_type": "video",
  "file_size": 15728640,
  "duration": 180,
  "thumbnail_url": "https://cdn-url.com/thumbnail.jpg",
  "loom_link": null,
  "text_content": "I learned so much about flexbox today...",
  "created_at": "2025-08-28T10:30:00Z",
  "updated_at": "2025-08-28T10:30:00Z"
}
```

---

## 🎯 **Benefits of Media Integration**

### **1. Reuse Existing Infrastructure**
- No duplicate file upload logic
- Leverages proven Backblaze B2 + CDN setup
- Inherits security and validation features

### **2. Professional File Handling**
- Chunked uploads for large files
- Progress tracking during upload
- Automatic thumbnail generation for videos
- Metadata extraction (duration, resolution)
- File type validation and security scanning

### **3. Consistent User Experience**
- Same upload flow as course video uploads
- Familiar progress indicators
- Consistent error handling

### **4. Advanced Features Out-of-Box**
- CDN delivery for fast loading
- Multiple file format support
- Cloud storage scalability
- Built-in file management APIs

### **5. Cost Effective**
- No additional storage infrastructure needed
- Shared CDN bandwidth costs
- Single point of file management

---

## 🔧 **Implementation Steps**

### **Phase 1: Model Updates**
1. Create PuzzleReflection model with MediaFile foreign key
2. Run database migrations
3. Add indexes for performance

### **Phase 2: API Integration**
1. Create PuzzleReflection CRUD endpoints
2. Update serializers to include MediaFile details
3. Add validation for content requirements

### **Phase 3: Frontend Integration**
1. Use existing media upload components
2. Create two-step upload flow
3. Display media content in reflection UI

### **Phase 4: Testing & Optimization**
1. Test large file uploads
2. Verify CDN delivery performance
3. Test across different file types

---

## 🚀 **Migration Strategy**

Since this is a new feature, no data migration is needed. The implementation follows these patterns:

1. **Create new tables** without affecting existing media system
2. **Reference existing MediaFile records** via foreign key
3. **Extend current upload flow** without breaking existing functionality
4. **Add new endpoints** while maintaining backward compatibility

---

**Note:** This approach maximizes code reuse while providing a professional, scalable solution for puzzle reflection file uploads.