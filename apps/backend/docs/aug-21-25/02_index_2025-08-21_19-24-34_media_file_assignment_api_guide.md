# Media File Assignment API Guide for Frontend Developers

**Date:** August 21, 2025  
**Document Version:** 1.0  
**API Base URL:** `/api/v1/content`

## Overview

The Media File Assignment API provides endpoints for managing the assignment of media files (videos, documents, etc.) to course sections. This allows instructors to organize course content by adding, removing, and reordering media files within course sections.

## Authentication

All endpoints require user authentication. The user must be authenticated and own the media files or have instructor privileges for the course to manage media assignments.

**Required Headers:**
- Authentication via cookies (session, access_token, refresh_token) or Authorization header

## Endpoints

### 1. Assign Media File to Section

**POST** `/sections/{section_id}/media`

Assigns an existing media file to a specific course section.

**URL Parameters:**
- `section_id` (string, required): The unique identifier of the section

**Request Body:**
```json
{
  "mediaFileId": "media-file-uuid",
  "title": "Custom Video Title",
  "description": "Optional description for this video",
  "order": 1,
  "isPreview": false,
  "isPublished": true
}
```

**Request Body Fields:**
- `mediaFileId` (string, required): The unique identifier of the media file to assign
- `title` (string, optional): Custom title for the media file within this section (defaults to filename)
- `description` (string, optional): Custom description for the media file
- `order` (integer, optional): Position within the section (auto-assigned if not provided)
- `isPreview` (boolean, optional): Whether this media is available as preview content (default: false)
- `isPublished` (boolean, optional): Whether this media is published to students (default: true)

**Success Response (200):**
```json
{
  "ok": true,
  "data": {
    "mediaFile": {
      "id": "media-file-uuid",
      "userId": "user-uuid",
      "courseId": "course-uuid",
      "courseSectionId": "section-uuid",
      "title": "Custom Video Title",
      "description": "Optional description for this video",
      "orderInSection": 1,
      "isPreview": false,
      "isPublished": true,
      "filename": "video.mp4",
      "originalFilename": "my-video.mp4",
      "fileType": "video",
      "mimeType": "video/mp4",
      "fileSize": 15728640,
      "fileSizeFormatted": "15.00 MB",
      "durationSeconds": 300,
      "durationFormatted": "05:00",
      "width": 1920,
      "height": 1080,
      "resolution": "1920x1080",
      "processingStatus": "completed",
      "storageUrl": "https://storage.example.com/video.mp4",
      "cdnUrl": "https://cdn.example.com/video.mp4",
      "bestUrl": "https://cdn.example.com/video.mp4",
      "thumbnailUrl": "https://cdn.example.com/thumb.jpg",
      "createdAt": "2025-08-21T19:00:00Z",
      "updatedAt": "2025-08-21T19:20:00Z"
    },
    "message": "Media file assigned to section successfully"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing mediaFileId or invalid request body
- `403 Forbidden`: User doesn't own the media file or can't manage the course
- `404 Not Found`: Section or media file not found

**Rate Limit:** 30 requests per minute

---

### 2. Remove Media File from Section

**POST** `/media/{media_file_id}/unassign`

Removes a media file from its current course section, making it unassigned.

**URL Parameters:**
- `media_file_id` (string, required): The unique identifier of the media file

**No Request Body Required**

**Success Response (200):**
```json
{
  "ok": true,
  "data": {
    "message": "Media file unassigned successfully",
    "mediaFile": {
      "id": "media-file-uuid",
      "userId": "user-uuid",
      "courseId": null,
      "courseSectionId": null,
      "title": "my-video.mp4",
      "description": null,
      "orderInSection": null,
      "isPreview": false,
      "isPublished": true,
      "filename": "video.mp4",
      "originalFilename": "my-video.mp4",
      "fileType": "video",
      "mimeType": "video/mp4",
      "fileSize": 15728640,
      "fileSizeFormatted": "15.00 MB",
      "durationSeconds": 300,
      "durationFormatted": "05:00",
      "processingStatus": "completed",
      "storageUrl": "https://storage.example.com/video.mp4",
      "cdnUrl": "https://cdn.example.com/video.mp4",
      "bestUrl": "https://cdn.example.com/video.mp4",
      "createdAt": "2025-08-21T19:00:00Z",
      "updatedAt": "2025-08-21T19:25:00Z"
    }
  }
}
```

**Error Responses:**
- `403 Forbidden`: User doesn't own the media file
- `404 Not Found`: Media file not found

**Rate Limit:** 30 requests per minute

**Important Notes:**
- This removes the media file from the course/section but doesn't delete the file itself
- The media file becomes unassigned and can be reassigned to other sections
- Custom title and description are reset; the file will use its original filename as title

---

### 3. Reorder Media Files in Section

**PUT** `/sections/{section_id}/media/reorder`

Updates the order of media files within a section.

**URL Parameters:**
- `section_id` (string, required): The unique identifier of the section

**Request Body:**
```json
{
  "mediaOrder": [
    "media-file-uuid-1",
    "media-file-uuid-2", 
    "media-file-uuid-3"
  ]
}
```

**Request Body Fields:**
- `mediaOrder` (array, required): Array of media file IDs in the desired order

**Success Response (200):**
```json
{
  "ok": true,
  "data": {
    "mediaFiles": [
      {
        "id": "media-file-uuid-1",
        "title": "Introduction Video",
        "orderInSection": 1,
        "filename": "intro.mp4",
        "durationSeconds": 180
      },
      {
        "id": "media-file-uuid-2", 
        "title": "Main Content",
        "orderInSection": 2,
        "filename": "main.mp4",
        "durationSeconds": 600
      },
      {
        "id": "media-file-uuid-3",
        "title": "Summary",
        "orderInSection": 3,
        "filename": "summary.mp4",
        "durationSeconds": 120
      }
    ],
    "message": "Media files reordered successfully"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing or invalid mediaOrder array
- `403 Forbidden`: User doesn't have permission to manage the course
- `404 Not Found`: Section not found

**Rate Limit:** 30 requests per minute

**Important Notes:**
- Only media files currently assigned to the section will be reordered
- Media files not included in the mediaOrder array will keep their current positions
- Order numbers start from 1

---

### 4. Get Course Media Files

**GET** `/courses/{course_id}/media`

Retrieves all media files for a course, organized by section.

**URL Parameters:**
- `course_id` (string, required): The unique identifier of the course

**Success Response (200):**
```json
{
  "ok": true,
  "data": {
    "courseId": "course-uuid",
    "courseTitle": "Introduction to Programming",
    "sections": [
      {
        "sectionId": "section-uuid-1",
        "sectionTitle": "Getting Started",
        "order": 1,
        "mediaFiles": [
          {
            "id": "media-file-uuid-1",
            "title": "Welcome Video",
            "orderInSection": 1,
            "filename": "welcome.mp4",
            "fileType": "video",
            "durationSeconds": 300,
            "durationFormatted": "05:00",
            "isPreview": true,
            "isPublished": true
          }
        ]
      },
      {
        "sectionId": "section-uuid-2",
        "sectionTitle": "Advanced Topics",
        "order": 2,
        "mediaFiles": [
          {
            "id": "media-file-uuid-2",
            "title": "Advanced Concepts",
            "orderInSection": 1,
            "filename": "advanced.mp4",
            "fileType": "video",
            "durationSeconds": 900,
            "durationFormatted": "15:00",
            "isPreview": false,
            "isPublished": true
          }
        ]
      }
    ],
    "unsectionedMedia": [
      {
        "id": "media-file-uuid-3",
        "title": "Bonus Content",
        "filename": "bonus.mp4",
        "fileType": "video",
        "durationSeconds": 180,
        "courseId": "course-uuid",
        "courseSectionId": null,
        "isPublished": false
      }
    ]
  }
}
```

**Response Structure:**
- `courseId`: The course identifier
- `courseTitle`: The course title
- `sections`: Array of sections with their media files
- `unsectionedMedia`: Media files assigned to the course but not to any specific section

**Error Responses:**
- `404 Not Found`: Course not found

**Rate Limit:** 100 requests per minute

---

## Media File Object Properties

When media files are returned in API responses, they include the following key properties:

### Basic Properties
- `id`: Unique identifier
- `title`: Display title (custom title or filename)
- `description`: Optional description
- `filename`: Storage filename
- `originalFilename`: Original uploaded filename
- `fileType`: Type of file (video, audio, document, image)
- `mimeType`: MIME type of the file

### Course/Section Assignment
- `courseId`: Associated course ID (null if unassigned)
- `courseSectionId`: Associated section ID (null if unassigned)
- `orderInSection`: Position within the section
- `isPreview`: Whether available as preview content
- `isPublished`: Whether published to students

### File Details
- `fileSize`: Size in bytes
- `fileSizeFormatted`: Human-readable file size
- `durationSeconds`: Duration for video/audio files
- `durationFormatted`: Human-readable duration (HH:MM or MM:SS)
- `width`, `height`: Dimensions for video/image files
- `resolution`: Resolution string (e.g., "1920x1080")

### URLs and Storage
- `storageUrl`: Direct storage URL
- `cdnUrl`: CDN URL for optimized delivery
- `bestUrl`: Recommended URL for playback
- `thumbnailUrl`: Thumbnail image URL

### Processing Status
- `processingStatus`: Current processing status (pending, processing, completed, failed)
- `uploadProgress`: Upload progress percentage
- `processingError`: Error message if processing failed

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
- `400 Bad Request`: Invalid request data
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Best Practices for Frontend Implementation

1. **Media File Ownership**: Ensure users can only assign media files they own
2. **Section Management**: Check that users have instructor privileges before showing management UI
3. **Order Management**: When reordering, include all media files you want to maintain in the section
4. **Progress Indicators**: Use `processingStatus` to show processing progress for newly uploaded files
5. **Preview Content**: Use `isPreview` flag to identify content available to non-enrolled users
6. **URL Selection**: Use `bestUrl` for media playback, which prioritizes CDN over direct storage URLs
7. **File Size Display**: Use `fileSizeFormatted` for user-friendly file size display
8. **Duration Display**: Use `durationFormatted` for user-friendly duration display

## Workflow Example

1. **Upload Media**: First upload media files using the media upload API
2. **Create Section**: Create course sections using the sections API
3. **Assign Media**: Assign uploaded media files to sections using this API
4. **Reorder Content**: Use reorder endpoint to arrange content within sections
5. **Publish**: Set `isPublished: true` when content is ready for students

## Additional Endpoints

### 5. Get User's Media Files

**GET** `/user/media`

Retrieves all media files owned by the current user, including both assigned and unassigned files.

**Base URL:** `/api/v1/media` (Note: Different base URL)

**Query Parameters:**
- `page` (integer, optional): Page number for pagination (default: 1)
- `limit` (integer, optional): Number of items per page (default: 20)
- `type` (string, optional): Filter by file type (video, audio, document, image)

**Success Response (200):**
```json
{
  "ok": true,
  "data": {
    "mediaFiles": [
      {
        "id": "media-file-uuid",
        "title": "My Video",
        "filename": "video.mp4",
        "originalFilename": "my-video.mp4",
        "fileType": "video",
        "courseId": null,
        "courseSectionId": null,
        "durationSeconds": 300,
        "fileSize": 15728640,
        "fileSizeFormatted": "15.00 MB",
        "processingStatus": "completed",
        "createdAt": "2025-08-21T19:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

**Rate Limit:** 50 requests per minute

---

### 6. Get Unassigned Video Files

**GET** `/user/unassigned-videos`

Retrieves only video files that are not assigned to any course or section.

**Base URL:** `/api/v1/media` (Note: Different base URL)

**Query Parameters:**
- `page` (integer, optional): Page number for pagination (default: 1)
- `limit` (integer, optional): Number of items per page (default: 20)

**Success Response (200):**
```json
{
  "ok": true,
  "data": {
    "videos": [
      {
        "id": "media-file-uuid",
        "title": "Unassigned Video",
        "filename": "video.mp4",
        "originalFilename": "my-unassigned-video.mp4",
        "fileType": "video",
        "courseId": null,
        "courseSectionId": null,
        "durationSeconds": 450,
        "fileSize": 25165824,
        "fileSizeFormatted": "24.00 MB",
        "processingStatus": "completed",
        "isProcessed": true,
        "isReady": true,
        "createdAt": "2025-08-21T18:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 12,
      "pages": 1
    }
  }
}
```

**Response includes:**
- `isProcessed`: Whether video processing is complete
- `isReady`: Whether the video is ready to be assigned (processing completed or pending)

**Rate Limit:** 50 requests per minute

**Use Case:** Perfect for showing a library of available videos when assigning content to course sections.

---

## Related APIs

- **Course Sections**: Use `/courses/{course_id}/sections` endpoints for section management
- **Media Upload**: Use `/media/upload` endpoints to upload files before assignment
- **Course Management**: Use `/instructor/courses` endpoints for overall course management