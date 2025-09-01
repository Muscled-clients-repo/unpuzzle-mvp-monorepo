# WebSocket API Documentation

## Overview

The WebSocket API provides real-time updates for course activities, student progress, and interactive features. It uses Socket.IO for bidirectional communication.

## Connection

### URL
```
ws://localhost:5000/socket.io/
```

### Authentication
Pass the JWT token as a query parameter or in the connection headers:

```javascript
// JavaScript client example
const socket = io('http://localhost:5000', {
  auth: {
    token: 'your-jwt-token'
  }
});
```

## Events

### Client -> Server Events

#### `connect`
Establishes connection with the server.

#### `join_course`
Join a course room for real-time updates.
```json
{
  "course_id": "course-uuid"
}
```

#### `leave_course`
Leave a course room.
```json
{
  "course_id": "course-uuid"
}
```

#### `join_video`
Join a video room for collaborative features.
```json
{
  "video_id": "video-uuid"
}
```

#### `video_progress`
Send video watching progress.
```json
{
  "video_id": "video-uuid",
  "course_id": "course-uuid",
  "progress": 75,
  "timestamp": 450
}
```

#### `send_chat_message`
Send a chat message in video room.
```json
{
  "video_id": "video-uuid",
  "message": "Question about the content",
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### Server -> Client Events

#### `connected`
Confirmation of successful connection.
```json
{
  "status": "Connected successfully"
}
```

#### `error`
Error message from server.
```json
{
  "message": "Error description"
}
```

#### `joined_course`
Confirmation of joining course room.
```json
{
  "course_id": "course-uuid",
  "status": "Joined successfully"
}
```

#### `joined_video`
Confirmation of joining video room.
```json
{
  "video_id": "video-uuid",
  "status": "Joined successfully"
}
```

#### `user_joined_video`
Notification when another user joins the video.
```json
{
  "user_id": "user-uuid",
  "user_email": "user@example.com"
}
```

#### `new_enrollment`
New student enrolled in course (broadcasted to course room).
```json
{
  "user_id": "user-uuid",
  "user_email": "student@example.com",
  "message": "student@example.com enrolled in the course"
}
```

#### `progress_update`
Student progress update (sent to instructor).
```json
{
  "user_id": "user-uuid",
  "video_id": "video-uuid",
  "watched_seconds": 300,
  "percent_complete": 75.5
}
```

#### `new_review`
New review posted for the course.
```json
{
  "user_email": "reviewer@example.com",
  "rating": 5,
  "comment": "Excellent course..."
}
```

#### `new_chat_message`
Chat message in video room.
```json
{
  "user_id": "user-uuid",
  "user_email": "user@example.com",
  "message": "Message content",
  "timestamp": "2024-01-20T10:30:00Z"
}
```

#### `student_progress`
Real-time progress tracking for instructors.
```json
{
  "user_id": "user-uuid",
  "video_id": "video-uuid",
  "progress": 45,
  "timestamp": 270
}
```

#### `quiz_submission`
Notification of quiz submission.
```json
{
  "user_id": "user-uuid",
  "quiz_id": "quiz-uuid",
  "score": 85,
  "passed": true
}
```

## Room Structure

### Course Rooms
- **Room Name**: `course_{course_id}`
- **Purpose**: Broadcasts updates to all students in a course
- **Events**: new_enrollment, new_review, course_updated

### Video Rooms
- **Room Name**: `video_{video_id}`
- **Purpose**: Collaborative features while watching video
- **Events**: user_joined_video, new_chat_message

### Instructor Rooms
- **Room Name**: `instructor_{course_id}`
- **Purpose**: Real-time dashboard for course instructors
- **Events**: new_enrollment, progress_update, quiz_submission

## Usage Examples

### JavaScript/TypeScript Client

```javascript
import io from 'socket.io-client';

// Connect with authentication
const socket = io('http://localhost:5000', {
  auth: {
    token: localStorage.getItem('auth_token')
  }
});

// Handle connection
socket.on('connect', () => {
  console.log('Connected to WebSocket server');
  
  // Join a course room
  socket.emit('join_course', { course_id: 'abc123' });
});

// Listen for new enrollments
socket.on('new_enrollment', (data) => {
  console.log('New student enrolled:', data.user_email);
});

// Send video progress
socket.emit('video_progress', {
  video_id: 'video123',
  course_id: 'course123',
  progress: 50,
  timestamp: 300
});

// Handle disconnection
socket.on('disconnect', () => {
  console.log('Disconnected from server');
});
```

### Python Client

```python
import socketio

# Create client
sio = socketio.Client()

# Define event handlers
@sio.event
def connect():
    print('Connected')
    sio.emit('join_course', {'course_id': 'abc123'})

@sio.event
def new_enrollment(data):
    print(f"New enrollment: {data}")

# Connect with token
sio.connect('http://localhost:5000', 
            auth={'token': 'your-jwt-token'})

# Keep connection alive
sio.wait()
```

## Error Handling

### Connection Errors
- **Invalid Token**: Connection will be refused, client disconnected
- **Expired Token**: Connection terminated with error message
- **Network Issues**: Client should implement reconnection logic

### Event Errors
- **Missing Parameters**: Error event emitted with details
- **Permission Denied**: Error event with forbidden message
- **Invalid Room**: Error event with not found message

## Best Practices

1. **Connection Management**
   - Implement automatic reconnection on disconnect
   - Clean up listeners when components unmount
   - Use connection state indicators in UI

2. **Event Handling**
   - Always validate data before emitting events
   - Implement error handlers for all events
   - Use typed events in TypeScript

3. **Performance**
   - Throttle frequent updates (like progress tracking)
   - Batch multiple updates when possible
   - Leave rooms when no longer needed

4. **Security**
   - Never expose sensitive data in events
   - Validate permissions server-side
   - Use secure WebSocket (wss://) in production

## Testing

Use the provided test client:
```bash
python app/utils/websocket_client_example.py <jwt_token>
```

Or test with curl:
```bash
# Get auth token first
TOKEN=$(curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.data.access_token')

# Use token with test client
python app/utils/websocket_client_example.py $TOKEN
```