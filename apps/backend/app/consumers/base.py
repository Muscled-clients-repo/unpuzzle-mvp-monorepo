"""
Base WebSocket consumer with authentication support.
"""
import json
import logging
from typing import Optional, Dict, Any
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from accounts.models import UserProfile

logger = logging.getLogger(__name__)


class AuthenticatedConsumer(AsyncJsonWebsocketConsumer):
    """
    Base WebSocket consumer that handles authentication and provides
    common functionality for all WebSocket connections.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: Optional[UserProfile] = None
        self.user_id: Optional[str] = None
        self.groups: list = []
    
    async def connect(self):
        """
        Handle WebSocket connection.
        Checks authentication before accepting connection.
        """
        # Get user from scope (set by middleware)
        self.user = self.scope.get('user', AnonymousUser())
        self.user_id = self.scope.get('user_id')
        
        # Check if user is authenticated
        if isinstance(self.user, AnonymousUser) or not self.user_id:
            logger.warning(f"Unauthenticated WebSocket connection attempt from {self.scope.get('client')}")
            await self.close(code=4001)  # Custom close code for authentication failure
            return
        
        # Accept connection for authenticated users
        await self.accept()
        logger.info(f"WebSocket connected: user_id={self.user_id}, path={self.scope.get('path')}")
        
        # Send connection confirmation
        await self.send_json({
            'type': 'connection',
            'status': 'connected',
            'user_id': self.user_id,
            'email': self.user.email if self.user else None
        })
        
        # Call subclass connection handler
        await self.on_connect()
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        Removes user from all groups.
        """
        # Leave all groups
        for group in self.groups:
            await self.channel_layer.group_discard(group, self.channel_name)
        
        logger.info(f"WebSocket disconnected: user_id={self.user_id}, code={close_code}")
        
        # Call subclass disconnection handler
        await self.on_disconnect(close_code)
    
    async def receive_json(self, content: Dict[str, Any], **kwargs):
        """
        Handle incoming JSON messages.
        Routes messages based on type.
        """
        message_type = content.get('type', 'unknown')
        
        # Handle ping/pong for connection keepalive
        if message_type == 'ping':
            await self.send_json({'type': 'pong', 'timestamp': content.get('timestamp')})
            return
        
        # Call subclass message handler
        await self.on_receive(message_type, content)
    
    async def join_group(self, group_name: str):
        """
        Add channel to a group.
        """
        if group_name not in self.groups:
            self.groups.append(group_name)
            await self.channel_layer.group_add(group_name, self.channel_name)
            logger.debug(f"User {self.user_id} joined group {group_name}")
    
    async def leave_group(self, group_name: str):
        """
        Remove channel from a group.
        """
        if group_name in self.groups:
            self.groups.remove(group_name)
            await self.channel_layer.group_discard(group_name, self.channel_name)
            logger.debug(f"User {self.user_id} left group {group_name}")
    
    async def broadcast_to_group(self, group_name: str, message: Dict[str, Any]):
        """
        Send message to all members of a group.
        """
        await self.channel_layer.group_send(
            group_name,
            {
                'type': 'group_message',
                **message
            }
        )
    
    async def group_message(self, event: Dict[str, Any]):
        """
        Handle messages sent to the group.
        """
        # Remove the 'type' field used for routing
        event.pop('type', None)
        await self.send_json(event)
    
    @database_sync_to_async
    def get_user_role(self) -> Optional[str]:
        """
        Get the user's role from the database.
        """
        if self.user and hasattr(self.user, 'role'):
            return self.user.role
        return None
    
    @database_sync_to_async
    def has_permission(self, resource_type: str, resource_id: str, action: str = 'view') -> bool:
        """
        Check if user has permission for a specific resource.
        Override in subclasses for specific permission logic.
        """
        # Default implementation - check if user is authenticated
        return self.user_id is not None
    
    # Methods to be implemented by subclasses
    async def on_connect(self):
        """
        Called after successful authentication and connection.
        Override in subclasses.
        """
        pass
    
    async def on_disconnect(self, close_code):
        """
        Called before disconnection.
        Override in subclasses.
        """
        pass
    
    async def on_receive(self, message_type: str, content: Dict[str, Any]):
        """
        Handle incoming messages.
        Override in subclasses.
        """
        pass