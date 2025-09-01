import json
import asyncio
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


class WebSocketService:
    """
    Service for sending WebSocket messages from anywhere in the application.
    Supports both sync and async contexts.
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_event_to_room(self, room_name: str, event_type: str, message: str, data: dict = None):
        """
        Send an event to all clients in a specific room.
        Can be called from synchronous code.
        """
        if not self.channel_layer:
            logger.warning("Channel layer not configured. WebSocket message not sent.")
            return
        
        async_to_sync(self.channel_layer.group_send)(
            f'events_{room_name}',
            {
                'type': 'event_message',
                'event_type': event_type,
                'message': message,
                'data': data or {},
                'timestamp': datetime.now().isoformat()
            }
        )
        logger.info(f"Event sent to room {room_name}: {event_type}")
    
    def send_notification_to_user(self, user_id: str, message: str, data: dict = None):
        """
        Send a notification to a specific user.
        Can be called from synchronous code.
        """
        if not self.channel_layer:
            logger.warning("Channel layer not configured. WebSocket notification not sent.")
            return
        
        async_to_sync(self.channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'notification_message',
                'message': message,
                'data': data or {},
                'timestamp': datetime.now().isoformat()
            }
        )
        logger.info(f"Notification sent to user {user_id}: {message}")
    
    def send_system_message_to_user(self, user_id: str, message: str, level: str = 'info', data: dict = None):
        """
        Send a system message to a specific user.
        Can be called from synchronous code.
        """
        if not self.channel_layer:
            logger.warning("Channel layer not configured. WebSocket system message not sent.")
            return
        
        async_to_sync(self.channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'system_message',
                'message': message,
                'level': level,  # 'info', 'warning', 'error', 'success'
                'data': data or {},
                'timestamp': datetime.now().isoformat()
            }
        )
        logger.info(f"System message sent to user {user_id}: {message}")
    
    async def async_send_event_to_room(self, room_name: str, event_type: str, message: str, data: dict = None):
        """
        Send an event to all clients in a specific room.
        For use in async contexts.
        """
        if not self.channel_layer:
            logger.warning("Channel layer not configured. WebSocket message not sent.")
            return
        
        await self.channel_layer.group_send(
            f'events_{room_name}',
            {
                'type': 'event_message',
                'event_type': event_type,
                'message': message,
                'data': data or {},
                'timestamp': datetime.now().isoformat()
            }
        )
        logger.info(f"Event sent to room {room_name}: {event_type}")
    
    async def async_send_notification_to_user(self, user_id: str, message: str, data: dict = None):
        """
        Send a notification to a specific user.
        For use in async contexts.
        """
        if not self.channel_layer:
            logger.warning("Channel layer not configured. WebSocket notification not sent.")
            return
        
        await self.channel_layer.group_send(
            f'notifications_{user_id}',
            {
                'type': 'notification_message',
                'message': message,
                'data': data or {},
                'timestamp': datetime.now().isoformat()
            }
        )
        logger.info(f"Notification sent to user {user_id}: {message}")


# Global instance for easy importing
websocket_service = WebSocketService()


# Convenience functions for common use cases
def notify_user(user_id: str, message: str, data: dict = None):
    """Send notification to a specific user"""
    websocket_service.send_notification_to_user(user_id, message, data)


def broadcast_to_room(room_name: str, event_type: str, message: str, data: dict = None):
    """Broadcast event to all clients in a room"""
    websocket_service.send_event_to_room(room_name, event_type, message, data)


def system_alert(user_id: str, message: str, level: str = 'info', data: dict = None):
    """Send system message to a user"""
    websocket_service.send_system_message_to_user(user_id, message, level, data)