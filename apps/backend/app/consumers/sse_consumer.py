"""
Simplified WebSocket consumer for Server-Sent Events (SSE).
Single endpoint that handles all real-time events from server to client.
"""
import json
import logging
from typing import Dict, Any, Set
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from accounts.models import UserProfile

logger = logging.getLogger(__name__)


class SSEConsumer(AsyncJsonWebsocketConsumer):
    """
    Single WebSocket consumer for all server-sent events.
    Clients connect and automatically receive relevant events based on their user context.
    """
    
    # Track active connections for broadcasting
    active_connections: Dict[str, Set[str]] = {}
    
    async def connect(self):
        """
        Handle WebSocket connection and set up user-specific channels.
        """
        # Get user from scope (set by auth middleware)
        self.user = self.scope.get('user', AnonymousUser())
        self.user_id = self.scope.get('user_id')
        
        # Accept all connections (even anonymous for public events)
        await self.accept()
        
        if self.user_id:
            # Add to user-specific group for personalized events
            self.user_group = f'user_{self.user_id}'
            await self.channel_layer.group_add(self.user_group, self.channel_name)
            
            # Get user role and add to role-based groups
            role = await self.get_user_role()
            if role:
                self.role_group = f'role_{role}'
                await self.channel_layer.group_add(self.role_group, self.channel_name)
            
            # Track active connection
            if self.user_id not in self.active_connections:
                self.active_connections[self.user_id] = set()
            self.active_connections[self.user_id].add(self.channel_name)
            
            logger.info(f"SSE WebSocket connected: user_id={self.user_id}, role={role}")
        else:
            logger.info("Anonymous SSE WebSocket connected")
        
        # Add to global broadcast group
        await self.channel_layer.group_add('broadcast', self.channel_name)
        
        # Send connection confirmation
        await self.send_json({
            'type': 'connected',
            'user_id': self.user_id,
            'timestamp': self.get_timestamp()
        })
    
    async def disconnect(self, close_code):
        """
        Clean up on disconnect.
        """
        # Remove from all groups
        await self.channel_layer.group_discard('broadcast', self.channel_name)
        
        if self.user_id:
            await self.channel_layer.group_discard(f'user_{self.user_id}', self.channel_name)
            
            # Remove from active connections
            if self.user_id in self.active_connections:
                self.active_connections[self.user_id].discard(self.channel_name)
                if not self.active_connections[self.user_id]:
                    del self.active_connections[self.user_id]
        
        logger.info(f"SSE WebSocket disconnected: user_id={self.user_id}")
    
    async def receive_json(self, content: Dict[str, Any]):
        """
        Handle incoming messages (mainly for ping/pong keepalive).
        """
        if content.get('type') == 'ping':
            await self.send_json({
                'type': 'pong',
                'timestamp': self.get_timestamp()
            })
    
    # Event handlers for different types of server-sent events
    
    async def course_analytics_update(self, event):
        """
        Send course analytics updates to instructors.
        """
        await self.send_json({
            'type': 'course_analytics',
            'data': event['data'],
            'timestamp': event.get('timestamp', self.get_timestamp())
        })
    
    async def student_progress_update(self, event):
        """
        Send student progress updates.
        """
        await self.send_json({
            'type': 'student_progress',
            'data': event['data'],
            'timestamp': event.get('timestamp', self.get_timestamp())
        })
    
    async def new_confusion(self, event):
        """
        Send new confusion notifications to instructors.
        """
        await self.send_json({
            'type': 'confusion',
            'data': event['data'],
            'timestamp': event.get('timestamp', self.get_timestamp())
        })
    
    async def notification(self, event):
        """
        Send general notifications.
        """
        await self.send_json({
            'type': 'notification',
            'message': event['message'],
            'level': event.get('level', 'info'),
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp', self.get_timestamp())
        })
    
    async def enrollment_update(self, event):
        """
        Send enrollment updates (new students, cancellations).
        """
        await self.send_json({
            'type': 'enrollment',
            'action': event['action'],
            'data': event['data'],
            'timestamp': event.get('timestamp', self.get_timestamp())
        })
    
    async def payment_update(self, event):
        """
        Send payment/revenue updates.
        """
        await self.send_json({
            'type': 'payment',
            'data': event['data'],
            'timestamp': event.get('timestamp', self.get_timestamp())
        })
    
    async def lesson_analytics_update(self, event):
        """
        Send lesson-specific analytics.
        """
        await self.send_json({
            'type': 'lesson_analytics',
            'data': event['data'],
            'timestamp': event.get('timestamp', self.get_timestamp())
        })
    
    async def broadcast_message(self, event):
        """
        Send broadcast messages to all connected clients.
        """
        await self.send_json({
            'type': 'broadcast',
            'message': event['message'],
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp', self.get_timestamp())
        })
    
    @database_sync_to_async
    def get_user_role(self):
        """
        Get user role from database.
        """
        if self.user and hasattr(self.user, 'role'):
            return self.user.role
        return None
    
    def get_timestamp(self):
        """
        Get current timestamp in ISO format.
        """
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'