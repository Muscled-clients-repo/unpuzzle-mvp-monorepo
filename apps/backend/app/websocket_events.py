"""
Utility functions for emitting WebSocket events from Django views, signals, or tasks.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class WebSocketEventEmitter:
    """
    Helper class for emitting WebSocket events to connected clients.
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def emit_to_user(self, user_id: str, event_type: str, data: Dict[str, Any]):
        """
        Send event to a specific user.
        """
        group_name = f'user_{user_id}'
        self._send_to_group(group_name, event_type, data)
        logger.info(f"Emitted {event_type} to user {user_id}")
    
    def emit_to_role(self, role: str, event_type: str, data: Dict[str, Any]):
        """
        Send event to all users with a specific role.
        """
        group_name = f'role_{role}'
        self._send_to_group(group_name, event_type, data)
        logger.info(f"Emitted {event_type} to role {role}")
    
    def emit_to_course_instructors(self, course_id: str, event_type: str, data: Dict[str, Any]):
        """
        Send event to all instructors of a course.
        """
        # This would typically query the database for course instructors
        # For now, we'll use a role-based approach
        self.emit_to_role('instructor', event_type, {
            'course_id': course_id,
            **data
        })
    
    def broadcast(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcast event to all connected clients.
        """
        self._send_to_group('broadcast', event_type, data)
        logger.info(f"Broadcasted {event_type} to all clients")
    
    def _send_to_group(self, group_name: str, event_type: str, data: Dict[str, Any]):
        """
        Internal method to send event to a channel group.
        """
        try:
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    'type': event_type.replace('.', '_'),  # Channels requires underscores
                    'data': data,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            )
        except Exception as e:
            logger.error(f"Error sending WebSocket event: {e}")


# Global event emitter instance
ws_events = WebSocketEventEmitter()


# Convenience functions for common events

def notify_new_enrollment(course_id: str, student_data: Dict[str, Any]):
    """
    Notify instructors about new enrollment.
    """
    ws_events.emit_to_course_instructors(
        course_id,
        'enrollment_update',
        {
            'action': 'new_enrollment',
            'student': student_data
        }
    )


def notify_confusion(course_id: str, lesson_id: str, confusion_data: Dict[str, Any]):
    """
    Notify instructors about student confusion.
    """
    ws_events.emit_to_course_instructors(
        course_id,
        'new_confusion',
        {
            'lesson_id': lesson_id,
            **confusion_data
        }
    )


def update_course_analytics(course_id: str, analytics_data: Dict[str, Any]):
    """
    Send updated course analytics to instructors.
    """
    ws_events.emit_to_course_instructors(
        course_id,
        'course_analytics_update',
        analytics_data
    )


def update_lesson_analytics(lesson_id: str, analytics_data: Dict[str, Any]):
    """
    Send updated lesson analytics.
    """
    ws_events.emit_to_role(
        'instructor',
        'lesson_analytics_update',
        {
            'lesson_id': lesson_id,
            **analytics_data
        }
    )


def notify_student_progress(student_id: str, course_id: str, progress_data: Dict[str, Any]):
    """
    Notify about student progress update.
    """
    # Notify the student
    ws_events.emit_to_user(
        student_id,
        'student_progress_update',
        progress_data
    )
    
    # Notify instructors
    ws_events.emit_to_course_instructors(
        course_id,
        'student_progress_update',
        {
            'student_id': student_id,
            **progress_data
        }
    )


def send_notification(user_id: str, message: str, level: str = 'info', data: Optional[Dict] = None):
    """
    Send a general notification to a user.
    """
    ws_events.emit_to_user(
        user_id,
        'notification',
        {
            'message': message,
            'level': level,
            'data': data or {}
        }
    )


def notify_payment_received(instructor_id: str, payment_data: Dict[str, Any]):
    """
    Notify instructor about payment received.
    """
    ws_events.emit_to_user(
        instructor_id,
        'payment_update',
        payment_data
    )