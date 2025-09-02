import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from app.middleware.websocket_auth import WebSocketAuthMiddlewareStack
from app.consumers.sse_consumer import SSEConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

django_asgi_app = get_asgi_application()

websocket_urlpatterns = [
    # Single WebSocket endpoint for all server-sent events
    re_path(r'ws/sse/$', SSEConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": WebSocketAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
