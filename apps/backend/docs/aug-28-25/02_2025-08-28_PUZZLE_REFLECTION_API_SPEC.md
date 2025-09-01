# Puzzle Reflection API Specification

**Date:** 2025-08-28  
**Purpose:** Detailed API specification for puzzle reflection endpoints  
**Version:** 1.0

---

## 🌐 **Base Configuration**

**Base URL:** `/api/v1/reflections/`  
**Authentication:** Required (Bearer Token)  
**Content-Type:** `multipart/form-data` for file uploads, `application/json` for other operations

---

## 📋 **Model Structure**

### **PuzzleReflection Model**
```python
{
    "id": "integer (auto-generated)",
    "user": "foreign_key (User)",
    "video_id": "string (max 255 chars)",
    "reflection_type": "choice ['completion', 'learning', 'challenge', 'summary', 'other']",
    "reflection_file": "file_field (video/audio/document)",
    "loom_link": "url_field (nullable)",
    "text_content": "text_field (nullable)",
    "title": "string (max 255 chars, optional)",
    "description": "text_field (optional)",
    "created_at": "datetime (auto)",
    "updated_at": "datetime (auto)"
}
```

---

## 🔌 **API Endpoints**

### **1. Create Reflection**
**POST** `/api/v1/reflections/`

#### Request (multipart/form-data)
```json
{
    "video_id": "css-flexbox-101",
    "reflection_type": "completion",
    "title": "My Learning Reflection",
    "description": "Completed all flexbox puzzles",
    "reflection_file": "file_object",
    "loom_link": "https://loom.com/share/abc123",
    "text_content": "Today I learned about flexbox..."
}
```

#### Response (201 Created)
```json
{
    "id": 123,
    "video_id": "css-flexbox-101",
    "reflection_type": "completion",
    "title": "My Learning Reflection",
    "description": "Completed all flexbox puzzles",
    "reflection_file": "reflections/2025/08/28/user123_reflection.mp4",
    "reflection_file_url": "https://yourdomain.com/media/reflections/2025/08/28/user123_reflection.mp4",
    "file_size": 15728640,
    "file_type": "mp4",
    "loom_link": "https://loom.com/share/abc123",
    "text_content": "Today I learned about flexbox...",
    "created_at": "2025-08-28T10:30:00Z",
    "updated_at": "2025-08-28T10:30:00Z"
}
```

#### Validation Rules
- At least one of `reflection_file`, `loom_link`, or `text_content` must be provided
- `video_id` is required
- File size limit: 100MB
- Supported file types: `.mp4`, `.mov`, `.avi`, `.mp3`, `.wav`, `.m4a`, `.pdf`, `.docx`, `.txt`

---

### **2. List User Reflections**
**GET** `/api/v1/reflections/`

#### Query Parameters
- `video_id`: Filter by specific video (optional)
- `reflection_type`: Filter by reflection type (optional)
- `page`: Page number for pagination (default: 1)
- `page_size`: Items per page (default: 10, max: 50)

#### Request
```
GET /api/v1/reflections/?video_id=css-flexbox-101&reflection_type=completion&page=1&page_size=20
```

#### Response (200 OK)
```json
{
    "count": 45,
    "next": "https://api.example.com/api/v1/reflections/?page=2",
    "previous": null,
    "results": [
        {
            "id": 123,
            "video_id": "css-flexbox-101",
            "reflection_type": "completion",
            "title": "My Learning Reflection",
            "description": "Completed all flexbox puzzles",
            "reflection_file": "reflections/2025/08/28/user123_reflection.mp4",
            "reflection_file_url": "https://yourdomain.com/media/reflections/2025/08/28/user123_reflection.mp4",
            "file_size": 15728640,
            "file_type": "mp4",
            "loom_link": "https://loom.com/share/abc123",
            "text_content": "Today I learned about flexbox...",
            "created_at": "2025-08-28T10:30:00Z",
            "updated_at": "2025-08-28T10:30:00Z"
        }
    ]
}
```

---

### **3. Get Specific Reflection**
**GET** `/api/v1/reflections/{id}/`

#### Response (200 OK)
```json
{
    "id": 123,
    "video_id": "css-flexbox-101",
    "reflection_type": "completion",
    "title": "My Learning Reflection",
    "description": "Completed all flexbox puzzles",
    "reflection_file": "reflections/2025/08/28/user123_reflection.mp4",
    "reflection_file_url": "https://yourdomain.com/media/reflections/2025/08/28/user123_reflection.mp4",
    "file_size": 15728640,
    "file_type": "mp4",
    "loom_link": "https://loom.com/share/abc123",
    "text_content": "Today I learned about flexbox...",
    "created_at": "2025-08-28T10:30:00Z",
    "updated_at": "2025-08-28T10:30:00Z"
}
```

#### Error Response (404 Not Found)
```json
{
    "error": "reflection_not_found",
    "message": "Reflection not found or you don't have permission to access it",
    "code": 404
}
```

---

### **4. Update Reflection**
**PUT/PATCH** `/api/v1/reflections/{id}/`

#### Request (PATCH - partial update)
```json
{
    "title": "Updated Reflection Title",
    "loom_link": "https://loom.com/share/xyz789"
}
```

#### Response (200 OK)
```json
{
    "id": 123,
    "video_id": "css-flexbox-101",
    "reflection_type": "completion",
    "title": "Updated Reflection Title",
    "description": "Completed all flexbox puzzles",
    "reflection_file": "reflections/2025/08/28/user123_reflection.mp4",
    "reflection_file_url": "https://yourdomain.com/media/reflections/2025/08/28/user123_reflection.mp4",
    "file_size": 15728640,
    "file_type": "mp4",
    "loom_link": "https://loom.com/share/xyz789",
    "text_content": "Today I learned about flexbox...",
    "created_at": "2025-08-28T10:30:00Z",
    "updated_at": "2025-08-28T14:45:00Z"
}
```

---

### **5. Delete Reflection**
**DELETE** `/api/v1/reflections/{id}/`

#### Response (204 No Content)
```
HTTP 204 No Content
```

#### Error Response (404 Not Found)
```json
{
    "error": "reflection_not_found", 
    "message": "Reflection not found or you don't have permission to delete it",
    "code": 404
}
```

---

### **6. Get Reflections by Video**
**GET** `/api/v1/reflections/video/{video_id}/`

#### Response (200 OK)
```json
{
    "video_id": "css-flexbox-101",
    "total_reflections": 3,
    "reflections": [
        {
            "id": 123,
            "reflection_type": "completion",
            "title": "Puzzle Completion",
            "created_at": "2025-08-28T10:30:00Z"
        },
        {
            "id": 124,
            "reflection_type": "learning",
            "title": "Key Learnings",
            "created_at": "2025-08-28T11:15:00Z"
        }
    ]
}
```

---

## 🔒 **Authentication & Permissions**

### **Authentication**
- All endpoints require user authentication
- Use Bearer token in Authorization header:
  ```
  Authorization: Bearer your-jwt-token-here
  ```

### **Permissions**
- Users can only access their own reflections
- No admin/superuser override for privacy
- 404 response for reflections belonging to other users

---

## 📁 **File Upload Specifications**

### **Supported File Types**
| Category | Extensions | Max Size |
|----------|------------|----------|
| Video | `.mp4`, `.mov`, `.avi`, `.webm` | 100MB |
| Audio | `.mp3`, `.wav`, `.m4a`, `.ogg` | 50MB |
| Document | `.pdf`, `.docx`, `.txt`, `.md` | 10MB |

### **Upload Path Structure**
```
media/
└── reflections/
    └── {year}/
        └── {month}/
            └── {day}/
                └── user{user_id}_reflection_{timestamp}.{ext}
```

### **File Security**
- Files are stored with unique names to prevent conflicts
- Access controlled through Django's media serving
- File type validation on upload
- Virus scanning recommended for production

---

## ⚡ **Error Handling**

### **Common Error Responses**

#### **Validation Error (400)**
```json
{
    "error": "validation_error",
    "message": "Invalid input data",
    "code": 400,
    "details": {
        "video_id": ["This field is required."],
        "reflection_file": ["File size too large. Maximum 100MB allowed."]
    }
}
```

#### **Authentication Error (401)**
```json
{
    "error": "authentication_required",
    "message": "Authentication credentials were not provided",
    "code": 401
}
```

#### **Permission Error (403)**
```json
{
    "error": "permission_denied",
    "message": "You do not have permission to perform this action",
    "code": 403
}
```

#### **File Upload Error (413)**
```json
{
    "error": "file_too_large",
    "message": "File size exceeds maximum allowed size",
    "code": 413
}
```

#### **Unsupported Media Type (415)**
```json
{
    "error": "unsupported_file_type",
    "message": "File type not supported. Supported formats: mp4, mov, avi, mp3, wav, pdf, docx, txt",
    "code": 415
}
```

---

## 🧪 **Testing Examples**

### **cURL Examples**

#### **Create Reflection with File Upload**
```bash
curl -X POST \
  -H "Authorization: Bearer your-token-here" \
  -F "video_id=css-flexbox-101" \
  -F "reflection_type=completion" \
  -F "title=My Reflection" \
  -F "reflection_file=@/path/to/reflection.mp4" \
  -F "text_content=I learned a lot today!" \
  http://localhost:3001/api/v1/reflections/
```

#### **Get User's Reflections**
```bash
curl -X GET \
  -H "Authorization: Bearer your-token-here" \
  -H "Accept: application/json" \
  "http://localhost:3001/api/v1/reflections/?video_id=css-flexbox-101"
```

#### **Update Reflection**
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title", "loom_link": "https://loom.com/share/new123"}' \
  http://localhost:3001/api/v1/reflections/123/
```

---

## 🔄 **Integration Notes**

### **Frontend Integration Points**
1. **File Upload Component**: Handle multipart form data
2. **Progress Tracking**: Show upload progress for large files
3. **File Preview**: Display uploaded files (video player, PDF viewer, etc.)
4. **Loom Integration**: Embed Loom videos when loom_link is provided
5. **Reflection Gallery**: Show user's reflections organized by video/date

### **Backend Dependencies**
- Django FileField for file handling
- Media library app for file security
- User authentication system
- Video/course management system

---

**Note:** This API is designed to be simple, secure, and efficient for handling puzzle reflections without AI processing overhead.