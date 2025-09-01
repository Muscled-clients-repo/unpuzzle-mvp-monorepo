# Course Sections API Guide for Frontend Developers

**Date:** August 21, 2025  
**Document Version:** 1.0  
**API Base URL:** `/api/v1/content`

## Overview

The Course Sections API provides endpoints for creating, managing, and organizing course sections within the learning platform. Course sections help structure course content into logical chapters or modules, with each section containing multiple media files (videos, documents, etc.).

## Authentication

All endpoints require user authentication. The user must be authenticated and have instructor privileges for the course to manage sections.

**Required Headers:**
- Authentication via cookies (session, access_token, refresh_token) or Authorization header

## Endpoints

### 1. Get Course Sections

**GET** `/courses/{course_id}/sections`

Retrieves all sections for a specific course, including associated media files.

**URL Parameters:**
- `course_id` (string, required): The unique identifier of the course

**Response Format:**
```json
{
  "ok": true,
  "data": {
    "sections": [
      {
        "id": "section-uuid",
        "courseId": "course-uuid",
        "title": "Introduction to Programming",
        "description": "Basic concepts and fundamentals",
        "order": 1,
        "isPublished": true,
        "isPreview": false,
        "mediaFiles": [
          {
            "id": "media-uuid",
            "title": "Welcome Video",
            "originalFilename": "intro.mp4",
            "fileType": "video",
            "durationSeconds": 300,
            "orderInSection": 1,
            "isPreview": false
          }
        ],
        "mediaCount": 1,
        "createdAt": "2025-08-21T18:30:00Z",
        "updatedAt": "2025-08-21T18:30:00Z"
      }
    ],
    "totalSections": 1
  }
}
```

**Rate Limit:** 100 requests per minute

---

### 2. Create Course Section

**POST** `/courses/{course_id}/sections`

Creates a new section within a course.

**URL Parameters:**
- `course_id` (string, required): The unique identifier of the course

**Request Body:**
```json
{
  "title": "Advanced Programming Concepts",
  "description": "Deep dive into advanced topics",
  "order": 2,
  "isPublished": true,
  "isPreview": false
}
```

**Request Body Fields:**
- `title` (string, required): The section title (1-255 characters)
- `description` (string, optional): Detailed description of the section content
- `order` (integer, optional): Position of the section within the course (auto-assigned if not provided)
- `isPublished` (boolean, optional): Whether the section is published to students (default: true)
- `isPreview` (boolean, optional): Whether the section is available as preview content (default: false)

**Success Response (201):**
```json
{
  "ok": true,
  "data": {
    "id": "new-section-uuid",
    "courseId": "course-uuid",
    "title": "Advanced Programming Concepts",
    "description": "Deep dive into advanced topics",
    "order": 2,
    "isPublished": true,
    "isPreview": false,
    "createdAt": "2025-08-21T18:45:00Z",
    "updatedAt": "2025-08-21T18:45:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing required fields or invalid data
- `403 Forbidden`: User doesn't have permission to manage the course
- `404 Not Found`: Course not found

**Rate Limit:** 20 requests per minute

---

### 3. Update Course Section

**PUT** `/sections/{section_id}`

Updates an existing course section.

**URL Parameters:**
- `section_id` (string, required): The unique identifier of the section

**Request Body:**
```json
{
  "title": "Updated Section Title",
  "description": "Updated description",
  "order": 3,
  "isPublished": false,
  "isPreview": true
}
```

**Request Body Fields:**
All fields are optional. Only provided fields will be updated:
- `title` (string): Updated section title
- `description` (string): Updated section description
- `order` (integer): New position within the course
- `isPublished` (boolean): Publication status
- `isPreview` (boolean): Preview availability

**Success Response (200):**
```json
{
  "ok": true,
  "data": {
    "id": "section-uuid",
    "courseId": "course-uuid",
    "title": "Updated Section Title",
    "description": "Updated description",
    "order": 3,
    "isPublished": false,
    "isPreview": true,
    "createdAt": "2025-08-21T18:30:00Z",
    "updatedAt": "2025-08-21T18:50:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request body
- `403 Forbidden`: User doesn't have permission to manage the course
- `404 Not Found`: Section not found

**Rate Limit:** 30 requests per minute

---

### 4. Delete Course Section

**DELETE** `/sections/{section_id}`

Soft-deletes a course section. The section will be marked as deleted but not permanently removed.

**URL Parameters:**
- `section_id` (string, required): The unique identifier of the section

**No Request Body Required**

**Success Response (200):**
```json
{
  "ok": true,
  "data": {
    "message": "Section deleted successfully"
  }
}
```

**Error Responses:**
- `403 Forbidden`: User doesn't have permission to manage the course
- `404 Not Found`: Section not found

**Rate Limit:** 20 requests per minute

**Important Notes:**
- This is a soft delete operation - the section is marked as deleted but data is preserved
- Media files associated with the section will have their course_section_id set to NULL
- Deleted sections won't appear in course content but can potentially be restored by administrators

---

## Error Response Format

All error responses follow this format:
```json
{
  "ok": false,
  "error": "Error message describing what went wrong"
}
```

## Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Best Practices for Frontend Implementation

1. **Order Management**: When creating sections, consider the order field to maintain logical course flow
2. **Preview Content**: Use `isPreview: true` for sections that should be accessible to non-enrolled users
3. **Publishing Control**: Use `isPublished: false` for sections still under development
4. **Error Handling**: Always check the `ok` field in responses before accessing `data`
5. **Rate Limiting**: Implement proper rate limiting awareness to avoid hitting API limits
6. **Permission Checks**: Ensure users have instructor privileges before showing section management UI

## Related APIs

- **Media File Assignment**: Use `/sections/{section_id}/media` endpoints to assign media files to sections
- **Course Management**: Use `/instructor/courses` endpoints for overall course management
- **Media Upload**: Use `/media/upload` endpoints to upload content before assigning to sections