# WebSocket Integration Examples

## Backend Examples

### Emitting Events from Django Views

```python
# courses/views.py
from app.websocket_events import ws_events, notify_new_enrollment, update_course_analytics

class EnrollmentViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # ... create enrollment logic
        enrollment = Enrollment.objects.create(...)
        
        # Emit WebSocket event to notify instructor
        notify_new_enrollment(
            course_id=enrollment.course.id,
            student_data={
                'id': enrollment.student.id,
                'name': enrollment.student.full_name,
                'email': enrollment.student.email,
                'enrolled_at': enrollment.created_at.isoformat()
            }
        )
        
        # Update course analytics in real-time
        analytics = self.calculate_course_analytics(enrollment.course.id)
        update_course_analytics(enrollment.course.id, analytics)
        
        return Response(serializer.data, status=201)
```

### Emitting Events from Django Signals

```python
# courses/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from app.websocket_events import notify_student_progress
from .models import LessonProgress

@receiver(post_save, sender=LessonProgress)
def lesson_progress_updated(sender, instance, created, **kwargs):
    """
    Emit WebSocket event when student progress is updated
    """
    notify_student_progress(
        student_id=instance.student_id,
        course_id=instance.lesson.course_id,
        progress_data={
            'lesson_id': instance.lesson_id,
            'progress': instance.progress_percentage,
            'completed_at': instance.completed_at.isoformat() if instance.completed_at else None,
            'time_spent': instance.time_spent_seconds
        }
    )
```

### Emitting Events from Celery Tasks

```python
# analytics/tasks.py
from celery import shared_task
from app.websocket_events import update_course_analytics

@shared_task
def update_course_analytics_task(course_id):
    """
    Background task to calculate and emit course analytics
    """
    # Calculate analytics
    analytics_data = calculate_course_analytics(course_id)
    
    # Emit to WebSocket
    update_course_analytics(course_id, analytics_data)
    
    return analytics_data
```

## Frontend Examples

### Using WebSocket in React Components

```typescript
// components/instructor/CourseAnalytics.tsx
import { useAppStore } from '@/stores/app-store';
import { useEffect } from 'react';

export function CourseAnalytics({ courseId }) {
  const { liveAnalytics, wsStatus } = useAppStore();
  
  // Analytics automatically update via WebSocket
  // No need for manual polling
  
  return (
    <div>
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${
          wsStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
        }`} />
        <span>Real-time {wsStatus}</span>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        <div>
          <h3>Active Students</h3>
          <p>{liveAnalytics.activeStudents}</p>
        </div>
        <div>
          <h3>Completion Rate</h3>
          <p>{liveAnalytics.completionRate}%</p>
        </div>
        <div>
          <h3>Avg Progress</h3>
          <p>{liveAnalytics.avgProgress}%</p>
        </div>
      </div>
    </div>
  );
}
```

### Listening to Specific Event Types

```typescript
// hooks/useInstructorNotifications.ts
import { useAppStore } from '@/stores/app-store';
import { useEffect } from 'react';
import { toast } from 'sonner';

export function useInstructorNotifications() {
  const { liveConfusions, recentEvents } = useAppStore();
  
  useEffect(() => {
    const latestConfusion = liveConfusions[0];
    if (latestConfusion && !latestConfusion.resolved) {
      toast.error(`New confusion from ${latestConfusion.studentName}`, {
        description: latestConfusion.message,
        action: {
          label: 'View Details',
          onClick: () => {
            // Navigate to confusion details
          }
        }
      });
    }
  }, [liveConfusions]);
  
  return { liveConfusions };
}
```

### App-wide WebSocket Provider Setup

```typescript
// app/layout.tsx
import { WebSocketProvider } from '@/components/providers/WebSocketProvider';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <WebSocketProvider>
          {children}
        </WebSocketProvider>
      </body>
    </html>
  );
}
```

## Common Use Cases

### 1. Student Confusion Alerts

**Backend (when confusion is reported):**
```python
# ai_assistant/views.py
from app.websocket_events import notify_confusion

def report_confusion(request):
    confusion = Confusion.objects.create(...)
    
    notify_confusion(
        course_id=confusion.lesson.course_id,
        lesson_id=confusion.lesson_id,
        confusion_data={
            'student_id': confusion.student_id,
            'student_name': confusion.student.full_name,
            'message': confusion.message,
            'video_timestamp': confusion.video_timestamp
        }
    )
```

**Frontend (instructor sees instant alert):**
```typescript
// Automatically handled by WebSocketProvider
// Shows toast notification and updates store
```

### 2. Real-time Analytics Updates

**Backend (periodic task):**
```python
# Run every 5 minutes
@shared_task
def update_all_course_analytics():
    for course in Course.objects.filter(status='published'):
        analytics = calculate_analytics(course.id)
        update_course_analytics(course.id, analytics)
```

**Frontend (live dashboard):**
```typescript
// LiveDashboard component automatically shows updated data
// No polling needed - updates arrive via WebSocket
```

### 3. New Enrollment Notifications

**Backend (on successful payment):**
```python
# payments/webhooks.py
def stripe_webhook_handler(request):
    # ... payment processing
    
    notify_new_enrollment(
        course_id=enrollment.course_id,
        student_data={
            'name': enrollment.student.full_name,
            'amount': payment_intent.amount / 100,
            'currency': payment_intent.currency
        }
    )
```

**Frontend (instructor notification):**
```typescript
// Automatic toast: "New student enrolled! John Doe - $99"
// Dashboard updates with new student count
```

## Testing WebSocket Events

### Backend Testing

```python
# tests/test_websocket_events.py
from channels.testing import WebsocketCommunicator
from app.consumers.sse_consumer import SSEConsumer

class TestWebSocketEvents(TestCase):
    async def test_confusion_event(self):
        communicator = WebsocketCommunicator(SSEConsumer.as_asgi(), "/ws/sse/")
        connected, subprotocol = await communicator.connect()
        
        # Emit event
        notify_confusion('course_1', 'lesson_1', {
            'student_name': 'Test Student',
            'message': 'I am confused'
        })
        
        # Check received message
        response = await communicator.receive_json_from()
        assert response['type'] == 'new_confusion'
        assert response['data']['student_name'] == 'Test Student'
```

### Frontend Testing

```typescript
// __tests__/websocket.test.tsx
import { renderHook } from '@testing-library/react';
import { useWebSocketSSE } from '@/hooks/useWebSocketSSE';

test('WebSocket connection and message handling', () => {
  const mockOnMessage = jest.fn();
  
  const { result } = renderHook(() =>
    useWebSocketSSE({ onMessage: mockOnMessage })
  );
  
  // Mock WebSocket message
  const mockMessage = {
    type: 'confusion',
    data: { student_name: 'Test Student' }
  };
  
  // Simulate message received
  // ... test WebSocket message handling
});
```

## Performance Considerations

1. **Connection Limits**: Monitor concurrent WebSocket connections
2. **Message Rate Limiting**: Prevent message spam
3. **Memory Usage**: Clean up old events from store
4. **Redis Memory**: Monitor Redis memory usage for channel layers
5. **Reconnection Logic**: Handle network interruptions gracefully

## Deployment Notes

1. **Heroku**: WebSocket connections work automatically
2. **Load Balancing**: Use sticky sessions for WebSocket connections
3. **SSL**: Always use WSS in production
4. **Monitoring**: Set up alerts for connection drops
5. **Scaling**: Consider using Redis Cluster for high-traffic applications