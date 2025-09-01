# Puzzle Reflection API - Frontend Integration Guide

**Date:** 2025-08-28  
**Purpose:** API documentation for puzzle reflection endpoints  
**API Base URL:** `https://yourdomain.com/api/v1/reflections/`

---

## 🔐 **Authentication**

All endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer your-jwt-token-here
```

---

## 📋 **API Endpoints**

### **1. List Reflections**

**Endpoint:** `GET /api/v1/reflections/`  
**Description:** Retrieve a paginated list of user's reflections

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `video_id` | String | Filter by video ID |
| `reflection_type` | String | Filter by type (voice, image, loom_link) |
| `search` | String | Search in title, description, and text_content |
| `date_from` | Date | Filter reflections created after this date (YYYY-MM-DD) |
| `date_to` | Date | Filter reflections created before this date (YYYY-MM-DD) |
| `has_media_file` | Boolean | Filter reflections with/without media files |
| `page` | Integer | Page number for pagination |
| `page_size` | Integer | Number of items per page (default: 20) |

**Response (200 OK):**
```json
{
  "count": 15,
  "next": "https://yourdomain.com/api/v1/reflections/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "video_id": "css-flexbox-101",
      "reflection_type": "voice",
      "title": "My CSS Learning Journey",
      "media_url": "https://cdn.yourdomain.com/reflections/video.mp4",
      "media_thumbnail": "https://cdn.yourdomain.com/reflections/thumbnail.jpg",
      "has_media": true,
      "loom_link": null,
      "user_name": "John Doe",
      "created_at": "2025-08-28T10:30:00Z"
    }
  ]
}
```

---

### **2. Create Reflection**

**Endpoint:** `POST /api/v1/reflections/`  
**Description:** Create a new reflection with optional file upload

#### **Option A: JSON Request (with existing MediaFile UUID)**

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "video_id": "string (required)",
  "reflection_type": "voice|image|loom_link",
  "title": "string (optional)",
  "description": "string (optional)",
  "media_file": "UUID of existing MediaFile (optional)",
  "loom_link": "URL string (optional)",
  "text_content": "string (optional)",
  "course": "UUID (optional)"
}
```

#### **Option B: Multipart Form Data (with direct file upload)**

**Content-Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | No | Binary file data (video/audio/document) |
| `video_id` | String | Yes | Video identifier |
| `reflection_type` | String | No | Default: "voice" |
| `title` | String | No | Reflection title |
| `description` | String | No | Reflection description |
| `loom_link` | String | No | Loom video URL |
| `text_content` | String | No | Text reflection content |
| `course` | UUID | No | Associated course ID |

**Validation Rules:**
- At least one of `file`, `media_file`, `loom_link`, or `text_content` must be provided
- File size limits: Video (100MB), Audio (50MB), Image (10MB), Document (10MB)
- Supported file types:
  - Video: mp4, mov, avi, webm
  - Audio: mp3, wav, m4a, ogg
  - Image: jpg, jpeg, png, gif
  - Document: pdf, doc, docx, txt

**cURL Example:**
```bash
curl -X POST https://yourdomain.com/api/v1/reflections/ \
  -H "Authorization: Bearer your-jwt-token" \
  -F "file=@/path/to/video.mp4" \
  -F "video_id=css-flexbox-101" \
  -F "reflection_type=voice" \
  -F "title=My Reflection Title"
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "video_id": "css-flexbox-101",
  "reflection_type": "voice",
  "title": "My Reflection Title",
  "description": "Completed all flexbox puzzles",
  "media_file": "media-file-uuid",
  "media_url": "https://cdn.yourdomain.com/reflections/video.mp4",
  "media_thumbnail": "https://cdn.yourdomain.com/reflections/thumbnail.jpg",
  "has_media": true,
  "loom_link": null,
  "text_content": "Additional notes",
  "course": null,
  "created_at": "2025-08-28T10:30:00Z",
  "updated_at": "2025-08-28T10:30:00Z"
}
```

**Error Responses:**
- **400 Bad Request:** Missing required fields or validation errors
- **401 Unauthorized:** Invalid or missing authentication token
- **413 Payload Too Large:** File size exceeds limit
- **500 Internal Server Error:** File upload or processing failed

---

### **3. Get Reflection Details**

**Endpoint:** `GET /api/v1/reflections/{id}/`  
**Description:** Retrieve detailed information about a specific reflection

**Path Parameters:**
- `id`: UUID of the reflection

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "video_id": "css-flexbox-101",
  "reflection_type": "voice",
  "title": "My CSS Learning Journey",
  "description": "Reflection on completing all flexbox puzzles",
  "media_file": "media-file-uuid",
  "media_file_details": {
    "id": "media-file-uuid",
    "filename": "reflection_video.mp4",
    "file_type": "video",
    "file_size": 15728640,
    "storage_url": "https://storage-url.com/file.mp4",
    "cdn_url": "https://cdn-url.com/file.mp4",
    "thumbnail_url": "https://cdn-url.com/thumbnail.jpg",
    "duration": 180,
    "width": 1920,
    "height": 1080,
    "processing_status": "completed"
  },
  "media_url": "https://cdn-url.com/file.mp4",
  "media_thumbnail": "https://cdn-url.com/thumbnail.jpg",
  "has_media": true,
  "file_type": "video",
  "file_size": 15728640,
  "duration": 180,
  "loom_link": null,
  "text_content": "Detailed reflection text...",
  "course": "course-uuid",
  "course_title": "CSS Mastery Course",
  "user_name": "John Doe",
  "created_at": "2025-08-28T10:30:00Z",
  "updated_at": "2025-08-28T10:30:00Z"
}
```

**Error Responses:**
- **404 Not Found:** Reflection does not exist or user doesn't have access
- **401 Unauthorized:** Invalid or missing authentication token

---

### **4. Update Reflection**

**Endpoint:** `PUT /api/v1/reflections/{id}/`  
**Description:** Completely update a reflection

**Endpoint:** `PATCH /api/v1/reflections/{id}/`  
**Description:** Partially update a reflection

**Path Parameters:**
- `id`: UUID of the reflection

**Request Body (same as create, all fields optional for PATCH):**
```json
{
  "video_id": "string",
  "reflection_type": "voice|image|loom_link",
  "title": "string",
  "description": "string",
  "media_file": "UUID",
  "loom_link": "URL string",
  "text_content": "string",
  "course": "UUID"
}
```

**Response (200 OK):**
Returns the updated reflection object (same format as Get Reflection Details)

**Error Responses:**
- **400 Bad Request:** Validation errors
- **404 Not Found:** Reflection does not exist
- **401 Unauthorized:** Invalid or missing authentication token

---

### **5. Delete Reflection**

**Endpoint:** `DELETE /api/v1/reflections/{id}/`  
**Description:** Soft delete a reflection (can be recovered)

**Path Parameters:**
- `id`: UUID of the reflection

**Response (204 No Content):**
No response body on successful deletion

**Error Responses:**
- **404 Not Found:** Reflection does not exist
- **401 Unauthorized:** Invalid or missing authentication token

---

### **6. Get Reflections by Video**

**Endpoint:** `GET /api/v1/reflections/by_video/`  
**Description:** Retrieve all reflections for a specific video

**Query Parameters:**
- `video_id`: String (required) - The video identifier

**Response (200 OK):**
```json
{
  "video_id": "css-flexbox-101",
  "total_reflections": 3,
  "reflections": [
    {
      "id": "reflection-uuid-1",
      "video_id": "css-flexbox-101",
      "reflection_type": "voice",
      "title": "Puzzle Completion",
      "media_url": "https://cdn.yourdomain.com/reflection.mp4",
      "media_thumbnail": "https://cdn.yourdomain.com/thumbnail.jpg",
      "has_media": true,
      "loom_link": null,
      "user_name": "John Doe",
      "created_at": "2025-08-28T10:30:00Z"
    }
  ]
}
```

**Error Responses:**
- **400 Bad Request:** Missing video_id parameter
- **401 Unauthorized:** Invalid or missing authentication token

---

### **7. Get Reflection Summary**

**Endpoint:** `GET /api/v1/reflections/summary/`  
**Description:** Get statistics and summary of user's reflections

**Response (200 OK):**
```json
{
  "total_reflections": 25,
  "by_type": [
    { "reflection_type": "voice", "count": 10 },
    { "reflection_type": "image", "count": 8 },
    { "reflection_type": "loom_link", "count": 7 }
  ],
  "top_videos": [
    { "video_id": "css-flexbox-101", "count": 5 },
    { "video_id": "js-basics-202", "count": 3 }
  ],
  "recent_reflections": [
    {
      "id": "recent-reflection-uuid",
      "video_id": "css-grid-301",
      "reflection_type": "loom_link",
      "title": "Latest Reflection",
      "media_url": null,
      "media_thumbnail": null,
      "has_media": false,
      "loom_link": "https://loom.com/share/abc123",
      "user_name": "John Doe",
      "created_at": "2025-08-28T15:30:00Z"
    }
  ]
}
```

**Error Responses:**
- **401 Unauthorized:** Invalid or missing authentication token

---

## 🔍 **Common Response Codes**

| Code | Description |
|------|-------------|
| 200 | Success - Request completed successfully |
| 201 | Created - Resource created successfully |
| 204 | No Content - Successful deletion |
| 400 | Bad Request - Invalid request parameters or validation errors |
| 401 | Unauthorized - Authentication required or invalid token |
| 403 | Forbidden - User doesn't have permission |
| 404 | Not Found - Resource doesn't exist |
| 413 | Payload Too Large - File size exceeds limit |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error occurred |

---

## 📝 **Notes for Frontend Developers**

1. **File Upload**: When uploading files, use `multipart/form-data` content type
2. **Pagination**: List endpoints return paginated results with `next` and `previous` URLs
3. **Filtering**: Use query parameters to filter and search reflections
4. **Media URLs**: The `media_url` and `media_thumbnail` fields provide direct CDN links
5. **Soft Delete**: Deleted reflections are not permanently removed and can be recovered
6. **User Isolation**: Each user can only access their own reflections
7. **Required Fields**: Always provide `video_id` and at least one content field
8. **Date Format**: Use ISO 8601 format for dates (YYYY-MM-DDTHH:MM:SSZ)

---

This documentation provides all necessary information for integrating the puzzle reflection API into your frontend application.