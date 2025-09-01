import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class EventConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time events.
    Supports room-based messaging for different event types.
    """
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'events_{self.room_name}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected to room: {self.room_name}")
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': f'Connected to {self.room_name} events',
            'room': self.room_name
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected from room: {self.room_name}")

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            event_type = text_data_json.get('type', 'message')
            message = text_data_json.get('message', '')
            
            # Broadcast message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'event_message',
                    'event_type': event_type,
                    'message': message,
                    'sender_channel': self.channel_name
                }
            )
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in WebSocket")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def event_message(self, event):
        """Send message to WebSocket"""
        # Don't send message back to sender
        if event.get('sender_channel') != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': event['event_type'],
                'message': event['message'],
                'room': self.room_name
            }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for user-specific notifications.
    Each user has their own notification channel.
    """
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user_group_name = f'notifications_{self.user_id}'
        
        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Notification WebSocket connected for user: {self.user_id}")
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': f'Connected to notifications for user {self.user_id}',
            'user_id': self.user_id
        }))

    async def disconnect(self, close_code):
        # Leave user group
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
        logger.info(f"Notification WebSocket disconnected for user: {self.user_id}")

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'ping')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': 'Connection alive'
                }))
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in notification WebSocket")

    async def notification_message(self, event):
        """Send notification to user"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp')
        }))

    async def system_message(self, event):
        """Send system message to user"""
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': event['message'],
            'level': event.get('level', 'info'),
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp')
        }))