# Student Learning API - Frontend Implementation Guide
**Date**: 2025-08-25  
**Time**: 12:45:00  
**Component**: Frontend Integration for Student Learning Routes

## Overview

This guide provides comprehensive documentation for frontend developers to integrate the new Student Learning API endpoints. These routes enable students to access course content and track their learning progress with proper enrollment verification.

## Quick Start

### Base URL
```
https://your-api-domain.com/api/v1
```

### Authentication
All learning endpoints require JWT authentication via:
- **Authorization Header**: `Bearer <JWT_TOKEN>`
- **Cookie**: `auth_token=<JWT_TOKEN>`

## API Endpoints

### 1. Get Course for Learning

**Endpoint**: `GET /student/courses/{courseId}/learn/`

**Purpose**: Retrieve course overview with sections for the student learning dashboard

**Parameters**:
- `courseId` (UUID): The course identifier

**Headers**:
```javascript
{
  'Authorization': 'Bearer your_jwt_token_here',
  'Content-Type': 'application/json'
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "course": {
      "id": "ccc6067e-1afc-4d71-8194-27fce62e834d",
      "title": "Complete React Development",
      "description": "Learn React from basics to advanced concepts",
      "short_description": "Master React in 30 days",
      "thumbnail": "https://example.com/course-image.jpg",
      "instructor": {
        "supabase_user_id": "instructor-uuid",
        "full_name": "John Doe",
        "display_name": "John",
        "avatar_url": "https://example.com/avatar.jpg",
        "bio": "Senior React Developer"
      },
      "category": {
        "id": "category-uuid",
        "name": "Web Development",
        "slug": "web-development"
      },
      "difficulty": "intermediate",
      "duration": 7200,
      "sections": [
        {
          "id": "section-uuid-1",
          "title": "Getting Started",
          "description": "Introduction to React",
          "order": 1,
          "is_published": true,
          "is_preview": false,
          "media_count": 5
        },
        {
          "id": "section-uuid-2", 
          "title": "Components",
          "description": "Working with React components",
          "order": 2,
          "is_published": true,
          "is_preview": false,
          "media_count": 8
        }
      ]
    },
    "enrollment": {
      "enrolled_at": "2025-08-20T10:30:00Z",
      "progress_percentage": 45.5,
      "lessons_completed": 6,
      "total_lessons": 13,
      "last_accessed_at": "2025-08-25T09:15:00Z",
      "started_at": "2025-08-20T10:30:00Z"
    }
  }
}
```

**Error Responses**:

*401 Unauthorized*:
```json
{
  "error": "No authorization token provided"
}
```

*403 Forbidden (Not Enrolled)*:
```json
{
  "error": "Access denied - Please enroll first to start learning",
  "success": false
}
```

*404 Not Found*:
```json
{
  "error": "Course not found or not published"
}
```

### 2. Get Section Content

**Endpoint**: `GET /student/courses/{courseId}/sections/{sectionId}/content/`

**Purpose**: Retrieve detailed section content with media files for enrolled students

**Parameters**:
- `courseId` (UUID): The course identifier
- `sectionId` (UUID): The section identifier

**Headers**:
```javascript
{
  'Authorization': 'Bearer your_jwt_token_here',
  'Content-Type': 'application/json'
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "section": {
      "id": "section-uuid-1",
      "title": "Getting Started",
      "description": "Introduction to React basics",
      "order": 1,
      "course": "ccc6067e-1afc-4d71-8194-27fce62e834d",
      "media_files": [
        {
          "id": "media-uuid-1",
          "title": "Introduction Video",
          "original_filename": "intro.mp4",
          "file_type": "video",
          "file_size": 52428800,
          "duration": 300,
          "file_url": "https://storage.example.com/videos/intro.mp4",
          "thumbnail_url": "https://storage.example.com/thumbnails/intro.jpg",
          "processing_status": "completed",
          "metadata": {
            "resolution": "1080p",
            "codec": "h264"
          },
          "order": 1,
          "created_at": "2025-08-20T10:00:00Z"
        },
        {
          "id": "media-uuid-2",
          "title": "Setup Instructions",
          "original_filename": "setup.pdf",
          "file_type": "document",
          "file_size": 2048000,
          "file_url": "https://storage.example.com/docs/setup.pdf",
          "processing_status": "completed",
          "order": 2,
          "created_at": "2025-08-20T10:05:00Z"
        }
      ]
    },
    "progress": {
      "section_progress_percentage": 60.0,
      "completed_media": 1,
      "total_media": 2
    }
  }
}
```

**Same Error Responses as Course Learning endpoint**

## Frontend Implementation Examples

### React/JavaScript Integration

#### 1. Course Learning Page Component

```javascript
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

const CourseLearningPage = () => {
  const { courseId } = useParams();
  const [courseData, setCourseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCourseForLearning();
  }, [courseId]);

  const fetchCourseForLearning = async () => {
    try {
      const token = localStorage.getItem('jwt_token'); // or get from your auth context
      
      const response = await fetch(`/api/v1/student/courses/${courseId}/learn/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('You need to enroll in this course first');
        }
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setCourseData(data.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading course...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!courseData) return <div>No course data available</div>;

  return (
    <div className="course-learning-page">
      <header className="course-header">
        <h1>{courseData.course.title}</h1>
        <p>{courseData.course.description}</p>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${courseData.enrollment.progress_percentage}%` }}
          />
          <span>{courseData.enrollment.progress_percentage.toFixed(1)}% Complete</span>
        </div>
      </header>

      <div className="course-sections">
        {courseData.course.sections.map((section, index) => (
          <SectionCard 
            key={section.id}
            section={section}
            courseId={courseId}
            isUnlocked={index === 0 || courseData.enrollment.progress_percentage > (index * 20)}
          />
        ))}
      </div>
    </div>
  );
};

const SectionCard = ({ section, courseId, isUnlocked }) => {
  const handleSectionClick = () => {
    if (isUnlocked) {
      // Navigate to section content
      window.location.href = `/learn/${courseId}/section/${section.id}`;
    }
  };

  return (
    <div 
      className={`section-card ${isUnlocked ? 'unlocked' : 'locked'}`}
      onClick={handleSectionClick}
    >
      <h3>{section.title}</h3>
      <p>{section.description}</p>
      <div className="section-meta">
        <span>{section.media_count} lessons</span>
        {!isUnlocked && <span className="lock-icon">🔒</span>}
      </div>
    </div>
  );
};

export default CourseLearningPage;
```

#### 2. Section Content Component

```javascript
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

const SectionContentPage = () => {
  const { courseId, sectionId } = useParams();
  const [sectionData, setSectionData] = useState(null);
  const [currentMedia, setCurrentMedia] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSectionContent();
  }, [courseId, sectionId]);

  const fetchSectionContent = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      
      const response = await fetch(
        `/api/v1/student/courses/${courseId}/sections/${sectionId}/content/`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Access denied - Please enroll first');
        }
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setSectionData(data.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMediaComplete = () => {
    // Mark current media as completed
    // You might want to call another API to track progress
    if (currentMedia < sectionData.section.media_files.length - 1) {
      setCurrentMedia(currentMedia + 1);
    }
  };

  if (loading) return <div>Loading section...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!sectionData) return <div>No section data available</div>;

  const currentMediaFile = sectionData.section.media_files[currentMedia];

  return (
    <div className="section-content-page">
      <header className="section-header">
        <h1>{sectionData.section.title}</h1>
        <p>{sectionData.section.description}</p>
        <div className="section-progress">
          Progress: {sectionData.progress.section_progress_percentage.toFixed(1)}%
          ({sectionData.progress.completed_media}/{sectionData.progress.total_media} completed)
        </div>
      </header>

      <div className="media-player">
        {currentMediaFile && (
          <MediaPlayer 
            mediaFile={currentMediaFile}
            onComplete={handleMediaComplete}
          />
        )}
      </div>

      <div className="media-playlist">
        {sectionData.section.media_files.map((media, index) => (
          <div 
            key={media.id}
            className={`media-item ${index === currentMedia ? 'active' : ''}`}
            onClick={() => setCurrentMedia(index)}
          >
            <div className="media-thumbnail">
              {media.file_type === 'video' && media.thumbnail_url && (
                <img src={media.thumbnail_url} alt={media.title} />
              )}
              {media.file_type === 'document' && <div className="doc-icon">📄</div>}
            </div>
            <div className="media-info">
              <h4>{media.title}</h4>
              <span className="media-type">{media.file_type}</span>
              {media.duration && (
                <span className="duration">{formatDuration(media.duration)}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const MediaPlayer = ({ mediaFile, onComplete }) => {
  if (mediaFile.file_type === 'video') {
    return (
      <video 
        controls 
        src={mediaFile.file_url}
        onEnded={onComplete}
        className="video-player"
      >
        Your browser does not support video playback.
      </video>
    );
  }

  if (mediaFile.file_type === 'document') {
    return (
      <div className="document-viewer">
        <iframe 
          src={mediaFile.file_url} 
          className="pdf-viewer"
          title={mediaFile.title}
        />
        <button onClick={onComplete} className="mark-complete-btn">
          Mark as Complete
        </button>
      </div>
    );
  }

  return <div>Unsupported media type: {mediaFile.file_type}</div>;
};

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export default SectionContentPage;
```

#### 3. API Service Class

```javascript
class StudentLearningAPI {
  constructor(baseURL = '/api/v1') {
    this.baseURL = baseURL;
  }

  getAuthHeaders() {
    const token = localStorage.getItem('jwt_token') || 
                 this.getCookie('auth_token');
    
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  async handleResponse(response) {
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async getCourseForLearning(courseId) {
    const response = await fetch(
      `${this.baseURL}/student/courses/${courseId}/learn/`,
      {
        method: 'GET',
        headers: this.getAuthHeaders()
      }
    );
    
    return this.handleResponse(response);
  }

  async getSectionContent(courseId, sectionId) {
    const response = await fetch(
      `${this.baseURL}/student/courses/${courseId}/sections/${sectionId}/content/`,
      {
        method: 'GET', 
        headers: this.getAuthHeaders()
      }
    );
    
    return this.handleResponse(response);
  }

  // Helper method for enrollment check
  async checkEnrollment(courseId) {
    try {
      await this.getCourseForLearning(courseId);
      return { enrolled: true };
    } catch (error) {
      if (error.message.includes('Please enroll first')) {
        return { enrolled: false, message: error.message };
      }
      throw error;
    }
  }
}

export default new StudentLearningAPI();
```

## Error Handling Best Practices

### 1. Enrollment Verification

```javascript
const handleLearningAccess = async (courseId) => {
  try {
    const data = await studentAPI.getCourseForLearning(courseId);
    // Success - user is enrolled
    return data;
  } catch (error) {
    if (error.message.includes('Please enroll first')) {
      // Redirect to enrollment page
      window.location.href = `/courses/${courseId}`;
      return;
    }
    
    if (error.message.includes('No authorization token')) {
      // Redirect to login
      window.location.href = '/login';
      return;
    }
    
    // Other errors
    console.error('Learning access error:', error);
    throw error;
  }
};
```

### 2. Global Error Handler

```javascript
const globalErrorHandler = (error, context = '') => {
  console.error(`Error in ${context}:`, error);
  
  // Common error patterns
  const errorPatterns = {
    'No authorization token': () => {
      // Clear stored tokens and redirect to login
      localStorage.removeItem('jwt_token');
      window.location.href = '/login';
    },
    'Please enroll first': () => {
      // Show enrollment modal or redirect
      showEnrollmentModal();
    },
    'Course not found': () => {
      // Redirect to courses page
      window.location.href = '/courses';
    }
  };

  for (const [pattern, handler] of Object.entries(errorPatterns)) {
    if (error.message.includes(pattern)) {
      handler();
      return;
    }
  }

  // Default error handling
  showErrorToast(error.message);
};
```

## Integration Checklist

### Frontend Requirements
- [ ] JWT token management (localStorage or cookies)
- [ ] Error boundary components for graceful error handling
- [ ] Loading states for API calls
- [ ] Responsive design for mobile learning
- [ ] Video player with progress tracking
- [ ] Document viewer for PDF/text content

### Security Considerations
- [ ] Store JWT tokens securely (httpOnly cookies recommended)
- [ ] Implement token refresh mechanism
- [ ] Validate user enrollment before expensive operations
- [ ] Handle expired tokens gracefully
- [ ] Sanitize user-generated content

### Performance Optimization
- [ ] Implement lazy loading for media content
- [ ] Cache course structure data
- [ ] Preload next section content
- [ ] Optimize video streaming (adaptive bitrate)
- [ ] Implement offline viewing capabilities

### User Experience
- [ ] Progress indicators throughout the learning flow
- [ ] Bookmarking and note-taking features
- [ ] Continue where you left off functionality
- [ ] Mobile-friendly video controls
- [ ] Keyboard navigation support

## Testing

### Unit Tests Example
```javascript
// Jest test example
import { render, screen, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import CourseLearningPage from './CourseLearningPage';

const server = setupServer(
  rest.get('/api/v1/student/courses/:courseId/learn/', (req, res, ctx) => {
    return res(ctx.json({
      success: true,
      data: {
        course: { /* mock course data */ },
        enrollment: { /* mock enrollment data */ }
      }
    }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('displays course learning content for enrolled user', async () => {
  render(<CourseLearningPage />);
  
  await waitFor(() => {
    expect(screen.getByText('Complete React Development')).toBeInTheDocument();
  });
  
  expect(screen.getByText(/45.5% Complete/)).toBeInTheDocument();
});
```

## Support and Troubleshooting

### Common Issues

**1. 401 Unauthorized Errors**
- Verify JWT token is included in request headers
- Check token expiration
- Ensure user is logged in

**2. 403 Access Denied Errors**
- Confirm user is enrolled in the course
- Check course publication status
- Verify section belongs to the course

**3. Media Playback Issues**
- Check media file processing status
- Verify file URLs are accessible
- Implement fallback for unsupported formats

### Debug Mode
```javascript
// Enable debug logging
const DEBUG = process.env.NODE_ENV === 'development';

const apiCall = async (url, options) => {
  if (DEBUG) {
    console.log('API Call:', url, options);
  }
  
  const response = await fetch(url, options);
  
  if (DEBUG) {
    console.log('API Response:', response.status, await response.clone().json());
  }
  
  return response;
};
```

## Conclusion

This API provides a secure, scalable foundation for student learning experiences. The enrollment verification ensures proper access control while the rich response data enables engaging frontend interfaces.

For additional support or feature requests, please refer to the API documentation or contact the development team.

---

**Next Steps**: 
- Implement progress tracking endpoints
- Add quiz and assessment functionality  
- Integrate with video analytics
- Add social learning features