# Course Management API Documentation

## Overview
This document outlines all API endpoints required for the course management system. All endpoints should follow RESTful conventions and return JSON responses.

## Base Configuration
- **Base URL**: `http://localhost:5000` (development)
- **API Version**: `/api/v1`
- **Authentication**: Cookie-based session with CSRF token protection
- **Content-Type**: `application/json`

## Authentication Headers
```
Content-Type: application/json
Accept: application/json
X-CSRF-Token: <csrf-token> (when required)
Cookie: <session-cookie>
```

---

## 📚 Public Course Endpoints (No Authentication Required)

### 1. Get All Courses
**Endpoint**: `GET /api/v1/courses`

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search | string | No | Search term for course title/description |
| difficulty | string | No | Filter by difficulty: `all`, `beginner`, `intermediate`, `advanced` |
| category | string | No | Filter by category |
| priceRange | string | No | Filter by price: `all`, `free`, `paid` |
| minRating | number | No | Minimum rating filter (1-5) |
| instructor | string | No | Filter by instructor name |
| sortBy | string | No | Sort options: `popular`, `newest`, `price-asc`, `price-desc`, `rating` |

**Response**: `200 OK`
```json
[
  {
    "id": "course-123",
    "title": "Advanced React Development",
    "description": "Master React with advanced patterns",
    "thumbnailUrl": "https://example.com/thumb.jpg",
    "instructor": {
      "id": "inst-456",
      "name": "John Doe",
      "email": "john@example.com",
      "avatar": "https://example.com/avatar.jpg",
      "bio": "Senior React Developer",
      "expertise": ["React", "TypeScript"],
      "coursesCount": 5,
      "studentsCount": 1200
    },
    "price": 99.99,
    "duration": 3600,
    "difficulty": "advanced",
    "tags": ["react", "javascript", "frontend"],
    "videos": [],
    "enrollmentCount": 234,
    "rating": 4.8,
    "isPublished": true,
    "isFree": false,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-15T00:00:00Z"
  }
]
```

### 2. Get Course by ID
**Endpoint**: `GET /api/v1/courses/{courseId}`

**Response**: `200 OK`
```json
{
  "id": "course-123",
  "title": "Advanced React Development",
  "description": "Master React with advanced patterns",
  "thumbnailUrl": "https://example.com/thumb.jpg",
  "instructor": {
    "id": "inst-456",
    "name": "John Doe",
    "email": "john@example.com",
    "avatar": "https://example.com/avatar.jpg"
  },
  "price": 99.99,
  "duration": 3600,
  "difficulty": "advanced",
  "tags": ["react", "javascript"],
  "videos": [
    {
      "id": "video-789",
      "courseId": "course-123",
      "title": "Introduction to Advanced Patterns",
      "description": "Learn about advanced React patterns",
      "duration": 600,
      "order": 1,
      "videoUrl": "https://example.com/video.mp4",
      "thumbnailUrl": "https://example.com/video-thumb.jpg",
      "transcript": [],
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ],
  "enrollmentCount": 234,
  "rating": 4.8,
  "isPublished": true,
  "isFree": false,
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-15T00:00:00Z"
}
```

### 3. Get Course Reviews
**Endpoint**: `GET /api/v1/courses/{courseId}/reviews`

**Response**: `200 OK`
```json
[
  {
    "id": "review-123",
    "userId": "user-456",
    "userName": "Jane Smith",
    "userAvatar": "https://example.com/avatar.jpg",
    "courseId": "course-123",
    "rating": 5,
    "comment": "Excellent course! Very comprehensive.",
    "createdAt": "2024-01-10T00:00:00Z",
    "helpful": 42,
    "verified": true
  }
]
```

---

## 🎓 Student Endpoints (Authentication Required - Student Role)

### 4. Get Enrolled Courses
**Endpoint**: `GET /api/v1/student/courses`

**Headers**: Requires authentication cookie

**Response**: `200 OK`
```json
[
  {
    "id": "course-123",
    "title": "Advanced React Development",
    "description": "Master React with advanced patterns",
    "thumbnailUrl": "https://example.com/thumb.jpg",
    "instructor": {
      "id": "inst-456",
      "name": "John Doe",
      "email": "john@example.com",
      "avatar": "https://example.com/avatar.jpg"
    },
    "price": 99.99,
    "duration": 3600,
    "difficulty": "advanced",
    "tags": ["react", "javascript"],
    "videos": [],
    "enrollmentCount": 234,
    "rating": 4.8,
    "isPublished": true,
    "isFree": false,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-15T00:00:00Z"
  }
]
```

### 5. Enroll in Course
**Endpoint**: `POST /api/v1/courses/{courseId}/enroll`

**Request Body**:
```json
{
  "paymentMethod": "credit_card",
  "couponCode": "DISCOUNT20"
}
```

**Response**: `200 OK`
```json
{
  "success": true,
  "enrollmentId": "enroll-123",
  "message": "Successfully enrolled in course"
}
```

### 6. Unenroll from Course
**Endpoint**: `POST /api/v1/courses/{courseId}/unenroll`

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Successfully unenrolled from course"
}
```

### 7. Get Course Progress
**Endpoint**: `GET /api/v1/student/courses/{courseId}/progress`

**Response**: `200 OK`
```json
{
  "userId": "user-123",
  "courseId": "course-456",
  "videosCompleted": 5,
  "totalVideos": 12,
  "percentComplete": 41.67,
  "lastAccessedAt": "2024-01-20T10:30:00Z",
  "certificateEarnedAt": null
}
```

### 8. Get Video Progress
**Endpoint**: `GET /api/v1/videos/{videoId}/progress`

**Response**: `200 OK`
```json
{
  "userId": "user-123",
  "videoId": "video-789",
  "watchedSeconds": 450,
  "totalSeconds": 600,
  "percentComplete": 75,
  "lastWatchedAt": "2024-01-20T10:30:00Z",
  "completedAt": null,
  "quizAttempts": [],
  "reflectionCount": 2
}
```

### 9. Update Video Progress
**Endpoint**: `PUT /api/v1/videos/{videoId}/progress`

**Request Body**:
```json
{
  "watchedSeconds": 450
}
```

**Response**: `200 OK`
```json
{
  "success": true,
  "percentComplete": 75
}
```

### 10. Mark Video Complete
**Endpoint**: `POST /api/v1/videos/{videoId}/complete`

**Response**: `200 OK`
```json
{
  "success": true,
  "completedAt": "2024-01-20T10:30:00Z"
}
```

### 11. Submit Quiz Answer
**Endpoint**: `POST /api/v1/videos/{videoId}/quiz/{quizId}/answer`

**Request Body**:
```json
{
  "answer": 2
}
```

**Response**: `200 OK`
```json
{
  "correct": true,
  "explanation": "Correct! React hooks must be called at the top level."
}
```

### 12. Get Recommended Courses
**Endpoint**: `GET /api/v1/courses/recommended`

**Response**: `200 OK`
```json
[
  {
    "id": "course-789",
    "title": "TypeScript Masterclass",
    "description": "Complete TypeScript guide",
    "thumbnailUrl": "https://example.com/thumb.jpg",
    "price": 79.99,
    "rating": 4.9,
    "matchScore": 0.92,
    "reason": "Based on your React course progress"
  }
]
```

### 13. Submit Course Review
**Endpoint**: `POST /api/v1/courses/{courseId}/review`

**Request Body**:
```json
{
  "rating": 5,
  "comment": "Excellent course! Very comprehensive and well-structured."
}
```

**Response**: `201 Created`
```json
{
  "id": "review-456",
  "success": true
}
```

---

## 👩‍🏫 Instructor Endpoints (Authentication Required - Instructor Role)

### 14. Get Instructor's Courses
**Endpoint**: `GET /api/v1/instructor/courses`

**Response**: `200 OK`
```json
[
  {
    "id": "course-123",
    "title": "Advanced React Development",
    "description": "Master React with advanced patterns",
    "thumbnailUrl": "https://example.com/thumb.jpg",
    "instructor": {
      "id": "inst-456",
      "name": "John Doe",
      "email": "john@example.com",
      "avatar": "https://example.com/avatar.jpg"
    },
    "price": 99.99,
    "duration": 3600,
    "difficulty": "advanced",
    "tags": ["react", "javascript"],
    "videos": [],
    "enrollmentCount": 234,
    "rating": 4.8,
    "isPublished": true,
    "isFree": false,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-15T00:00:00Z"
  }
]
```

### 15. Create Course
**Endpoint**: `POST /api/v1/instructor/courses`

**Request Body**:
```json
{
  "title": "Advanced React Development",
  "description": "Master React with advanced patterns and best practices",
  "thumbnailUrl": "https://example.com/thumb.jpg",
  "price": 99.99,
  "duration": 3600,
  "difficulty": "advanced",
  "tags": ["react", "javascript", "frontend"],
  "isFree": false
}
```

**Response**: `201 Created`
```json
{
  "id": "course-new-123",
  "title": "Advanced React Development",
  "description": "Master React with advanced patterns and best practices",
  "thumbnailUrl": "https://example.com/thumb.jpg",
  "instructor": {
    "id": "inst-456",
    "name": "John Doe",
    "email": "john@example.com",
    "avatar": "https://example.com/avatar.jpg"
  },
  "price": 99.99,
  "duration": 3600,
  "difficulty": "advanced",
  "tags": ["react", "javascript", "frontend"],
  "videos": [],
  "enrollmentCount": 0,
  "rating": 0,
  "isPublished": false,
  "isFree": false,
  "createdAt": "2024-01-20T00:00:00Z",
  "updatedAt": "2024-01-20T00:00:00Z"
}
```

### 16. Update Course
**Endpoint**: `PUT /api/v1/instructor/courses/{courseId}`

**Request Body**:
```json
{
  "title": "Updated Course Title",
  "description": "Updated description",
  "price": 89.99,
  "tags": ["react", "typescript", "advanced"]
}
```

**Response**: `200 OK`
```json
{
  "id": "course-123",
  "title": "Updated Course Title",
  "description": "Updated description",
  "price": 89.99,
  "tags": ["react", "typescript", "advanced"],
  "updatedAt": "2024-01-20T00:00:00Z"
}
```

### 17. Delete Course
**Endpoint**: `DELETE /api/v1/instructor/courses/{courseId}`

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Course deleted successfully"
}
```

### 18. Publish Course
**Endpoint**: `POST /api/v1/instructor/courses/{courseId}/publish`

**Response**: `200 OK`
```json
{
  "success": true,
  "isPublished": true,
  "publishedAt": "2024-01-20T00:00:00Z"
}
```

### 19. Unpublish Course
**Endpoint**: `POST /api/v1/instructor/courses/{courseId}/unpublish`

**Response**: `200 OK`
```json
{
  "success": true,
  "isPublished": false
}
```

### 20. Duplicate Course
**Endpoint**: `POST /api/v1/instructor/courses/{courseId}/duplicate`

**Response**: `201 Created`
```json
{
  "id": "course-copy-789",
  "title": "Advanced React Development (Copy)",
  "description": "Master React with advanced patterns and best practices",
  "isPublished": false,
  "createdAt": "2024-01-20T00:00:00Z"
}
```

### 21. Add Video to Course
**Endpoint**: `POST /api/v1/instructor/courses/{courseId}/videos`

**Request Body**:
```json
{
  "title": "Introduction to Hooks",
  "description": "Learn about React Hooks",
  "videoUrl": "https://example.com/video.mp4",
  "thumbnailUrl": "https://example.com/thumb.jpg",
  "duration": 600,
  "order": 1,
  "quizPoints": [
    {
      "timestamp": 300,
      "question": "What is the purpose of useEffect?",
      "options": [
        "To manage state",
        "To handle side effects",
        "To create components",
        "To style components"
      ],
      "correctAnswer": 1
    }
  ]
}
```

**Response**: `201 Created`
```json
{
  "id": "video-new-456",
  "courseId": "course-123",
  "title": "Introduction to Hooks",
  "description": "Learn about React Hooks",
  "duration": 600,
  "order": 1,
  "videoUrl": "https://example.com/video.mp4",
  "thumbnailUrl": "https://example.com/thumb.jpg",
  "transcript": [],
  "createdAt": "2024-01-20T00:00:00Z",
  "updatedAt": "2024-01-20T00:00:00Z"
}
```

### 22. Update Video
**Endpoint**: `PUT /api/v1/instructor/videos/{videoId}`

**Request Body**:
```json
{
  "title": "Updated Video Title",
  "description": "Updated description",
  "order": 2
}
```

**Response**: `200 OK`
```json
{
  "id": "video-456",
  "title": "Updated Video Title",
  "description": "Updated description",
  "order": 2,
  "updatedAt": "2024-01-20T00:00:00Z"
}
```

### 23. Delete Video
**Endpoint**: `DELETE /api/v1/instructor/videos/{videoId}`

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Video deleted successfully"
}
```

### 24. Reorder Videos
**Endpoint**: `PUT /api/v1/instructor/courses/{courseId}/videos/reorder`

**Request Body**:
```json
{
  "videoIds": ["video-3", "video-1", "video-2", "video-4"]
}
```

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Videos reordered successfully"
}
```

### 25. Upload Video File
**Endpoint**: `POST /api/v1/instructor/videos/upload`

**Request**: `multipart/form-data`
```
Content-Type: multipart/form-data
File field name: video
```

**Response**: `200 OK`
```json
{
  "url": "https://cdn.example.com/videos/uploaded-video-123.mp4",
  "duration": 600,
  "size": 104857600
}
```

---

## 📊 Analytics Endpoints (Instructor Only)

### 26. Get Course Analytics
**Endpoint**: `GET /api/v1/instructor/courses/{courseId}/analytics`

**Response**: `200 OK`
```json
{
  "enrollments": 234,
  "completionRate": 0.68,
  "avgProgress": 0.45,
  "revenueTotal": 23400,
  "revenueThisMonth": 3200,
  "totalStudents": 234,
  "studentEngagement": {
    "active": 156,
    "inactive": 45,
    "struggling": 33
  },
  "topPerformers": [
    {
      "studentId": "user-123",
      "studentName": "Jane Smith",
      "progress": 0.92
    }
  ],
  "strugglingStudents": [
    {
      "studentId": "user-456",
      "studentName": "Bob Johnson",
      "progress": 0.15,
      "lastActive": "2024-01-10T00:00:00Z"
    }
  ],
  "videoAnalytics": [
    {
      "videoId": "video-123",
      "title": "Introduction",
      "avgWatchTime": 480,
      "completionRate": 0.80,
      "dropOffPoints": [120, 240, 360]
    }
  ]
}
```

### 27. Get Student Progress (Instructor View)
**Endpoint**: `GET /api/v1/instructor/courses/{courseId}/students/{studentId}/progress`

**Response**: `200 OK`
```json
{
  "userId": "user-123",
  "courseId": "course-456",
  "videosCompleted": 8,
  "totalVideos": 12,
  "percentComplete": 66.67,
  "lastAccessedAt": "2024-01-20T10:30:00Z",
  "certificateEarnedAt": null,
  "videoDetails": [
    {
      "videoId": "video-123",
      "title": "Introduction",
      "watchedSeconds": 600,
      "totalSeconds": 600,
      "completed": true,
      "quizScore": 100
    }
  ]
}
```

### 28. Export Analytics
**Endpoint**: `GET /api/v1/instructor/courses/{courseId}/analytics/export`

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| format | string | Yes | Export format: `csv` or `pdf` |

**Response**: `200 OK`
```json
{
  "url": "https://cdn.example.com/exports/analytics-course-123-20240120.csv",
  "expiresAt": "2024-01-21T00:00:00Z"
}
```

---

## 🤖 AI-Powered Endpoints

### 29. Get AI Course Recommendations
**Endpoint**: `GET /api/v1/ai/courses/{courseId}/recommendations`

**Response**: `200 OK`
```json
{
  "recommendations": [
    "Consider adding more practical exercises in Module 3",
    "Students struggle with the Redux section - add more examples",
    "Break down the authentication video into smaller segments",
    "Add a summary video at the end of each module"
  ]
}
```

### 30. Generate Course Outline
**Endpoint**: `POST /api/v1/ai/courses/generate-outline`

**Request Body**:
```json
{
  "topic": "Advanced TypeScript for Enterprise Applications"
}
```

**Response**: `200 OK`
```json
{
  "title": "Advanced TypeScript for Enterprise Applications",
  "description": "Master TypeScript patterns and architectures for large-scale applications",
  "objectives": [
    "Understand advanced TypeScript type system",
    "Implement design patterns in TypeScript",
    "Build scalable enterprise architectures",
    "Master testing strategies for TypeScript applications"
  ],
  "modules": [
    {
      "title": "Advanced Type System",
      "description": "Deep dive into TypeScript's type system",
      "lessons": [
        {
          "title": "Conditional Types and Infer",
          "duration": 45,
          "topics": ["Conditional types", "Type inference", "Utility types"]
        },
        {
          "title": "Template Literal Types",
          "duration": 30,
          "topics": ["String manipulation", "Type-safe APIs", "Branded types"]
        }
      ]
    },
    {
      "title": "Design Patterns",
      "description": "Implementing GoF patterns in TypeScript",
      "lessons": [
        {
          "title": "Creational Patterns",
          "duration": 60,
          "topics": ["Factory", "Builder", "Singleton"]
        }
      ]
    }
  ],
  "prerequisites": [
    "Intermediate TypeScript knowledge",
    "Understanding of OOP concepts",
    "Basic design patterns knowledge"
  ],
  "targetAudience": [
    "Senior developers",
    "Technical leads",
    "Software architects"
  ],
  "estimatedDuration": 720
}
```

### 31. Get AI Chat History
**Endpoint**: `GET /api/v1/ai/videos/{videoId}/chat`

**Response**: `200 OK`
```json
{
  "id": "chat-123",
  "userId": "user-456",
  "videoId": "video-789",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "Can you explain the useEffect cleanup function?",
      "timestamp": "2024-01-20T10:30:00Z",
      "videoContext": {
        "segmentId": "seg-123",
        "startTime": 240,
        "endTime": 300,
        "content": "useEffect cleanup explanation"
      },
      "intent": "conceptual"
    },
    {
      "id": "msg-2",
      "role": "assistant",
      "content": "The cleanup function in useEffect is used to perform cleanup operations...",
      "timestamp": "2024-01-20T10:30:15Z"
    }
  ],
  "contextSegments": [],
  "createdAt": "2024-01-20T10:30:00Z"
}
```

### 32. Send AI Chat Message
**Endpoint**: `POST /api/v1/ai/videos/{videoId}/chat`

**Request Body**:
```json
{
  "message": "Can you explain this concept in simpler terms?"
}
```

**Response**: `200 OK`
```json
{
  "id": "msg-3",
  "role": "assistant",
  "content": "Of course! Let me break this down into simpler terms...",
  "timestamp": "2024-01-20T10:31:00Z",
  "intent": "conceptual"
}
```

---

## Error Responses

All endpoints should return appropriate error responses:

### 400 Bad Request
```json
{
  "error": {
    "message": "Invalid request parameters",
    "code": "INVALID_REQUEST",
    "details": {
      "field": "price",
      "reason": "Price must be a positive number"
    }
  }
}
```

### 401 Unauthorized
```json
{
  "error": {
    "message": "Authentication required",
    "code": "AUTH_REQUIRED"
  }
}
```

### 403 Forbidden
```json
{
  "error": {
    "message": "Insufficient permissions",
    "code": "FORBIDDEN"
  }
}
```

### 404 Not Found
```json
{
  "error": {
    "message": "Course not found",
    "code": "NOT_FOUND"
  }
}
```

### 409 Conflict
```json
{
  "error": {
    "message": "Course title already exists",
    "code": "CONFLICT"
  }
}
```

### 500 Internal Server Error
```json
{
  "error": {
    "message": "An unexpected error occurred",
    "code": "INTERNAL_ERROR"
  }
}
```

---

## Rate Limiting

Implement rate limiting for all endpoints:
- **Public endpoints**: 100 requests per minute
- **Authenticated endpoints**: 500 requests per minute
- **Upload endpoints**: 10 requests per minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642680000
```

---

## Pagination

For list endpoints, implement pagination:

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | number | 1 | Page number |
| limit | number | 20 | Items per page |

**Response Headers**:
```
X-Total-Count: 156
X-Page: 1
X-Per-Page: 20
X-Total-Pages: 8
```

---

## WebSocket Events (Real-time Updates)

For real-time features, implement WebSocket connections:

### Connection
```
ws://localhost:5000/ws
```

### Events

**Course Update** (Instructor)
```json
{
  "event": "course.updated",
  "data": {
    "courseId": "course-123",
    "changes": ["title", "description"]
  }
}
```

**Progress Update** (Student)
```json
{
  "event": "progress.updated",
  "data": {
    "courseId": "course-123",
    "videoId": "video-456",
    "percentComplete": 75
  }
}
```

**New Enrollment** (Instructor)
```json
{
  "event": "course.enrolled",
  "data": {
    "courseId": "course-123",
    "studentId": "user-789",
    "studentName": "Alice Johnson"
  }
}
```

---

## Database Schema Requirements

### Tables Needed:
1. **courses** - Course information
2. **videos** - Course videos
3. **enrollments** - Student enrollments
4. **course_progress** - Overall course progress
5. **video_progress** - Individual video progress
6. **reviews** - Course reviews
7. **quiz_attempts** - Quiz attempt records
8. **ai_chats** - AI conversation history
9. **course_analytics** - Aggregated analytics data

### Indexes Recommended:
- courses.instructor_id
- courses.is_published
- enrollments.user_id
- enrollments.course_id
- video_progress.user_id + video_id (composite)
- reviews.course_id
- reviews.user_id

---

## Security Considerations

1. **Authentication**: All student/instructor endpoints require valid session
2. **Authorization**: Verify user roles before allowing access
3. **CSRF Protection**: Require CSRF token for state-changing operations
4. **Input Validation**: Validate all input data
5. **SQL Injection**: Use parameterized queries
6. **File Upload**: Validate file types and sizes, scan for malware
7. **Rate Limiting**: Implement per-user and per-IP rate limits
8. **Data Privacy**: Don't expose sensitive user data in responses

---

## Performance Recommendations

1. **Caching**:
   - Cache course listings (5 minutes)
   - Cache course details (2 minutes)
   - Cache analytics data (10 minutes)

2. **Database Optimization**:
   - Use database connection pooling
   - Implement query result caching
   - Use indexes for frequently queried fields

3. **CDN**:
   - Serve video content from CDN
   - Cache thumbnails and static assets

4. **Async Processing**:
   - Process video uploads asynchronously
   - Generate analytics in background jobs
   - Send emails via queue system

---

## Testing Checklist

- [ ] All endpoints return correct status codes
- [ ] Error responses follow consistent format
- [ ] Authentication/authorization works correctly
- [ ] Input validation prevents invalid data
- [ ] Rate limiting functions properly
- [ ] Pagination works for list endpoints
- [ ] File uploads handle edge cases
- [ ] WebSocket events fire correctly
- [ ] CSRF protection is active
- [ ] Performance meets requirements

---

## Notes for Backend Developer

1. **Mock Data**: The frontend currently uses mock data when `useMockData` is true. Ensure the real API matches these structures.

2. **Timestamps**: All timestamps should be in ISO 8601 format (e.g., "2024-01-20T10:30:00Z")

3. **IDs**: Use string IDs for all entities to support UUIDs or custom ID formats

4. **Null vs Undefined**: Use `null` for explicitly empty values, omit fields that are undefined

5. **Video Streaming**: Consider implementing video streaming with range requests for better performance

6. **Search**: Consider implementing full-text search using Elasticsearch or similar for course search

7. **Notifications**: Consider adding notification endpoints for course updates, new enrollments, etc.

8. **Versioning**: API is versioned at `/api/v1` - maintain backward compatibility or version endpoints

---

## Contact

For questions or clarifications about this API specification, please contact the frontend team.

Last Updated: 2024-01-20
Version: 1.0.0