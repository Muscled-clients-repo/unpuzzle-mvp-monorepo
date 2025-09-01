from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .websocket_service import notify_user, broadcast_to_room, system_alert


@csrf_exempt
@require_http_methods(["POST"])
def send_event_to_room(request):
    """
    API endpoint to send events to a WebSocket room.
    
    POST /api/v1/websocket/send-event/
    {
        "room_name": "general",
        "event_type": "message",
        "message": "Hello everyone!",
        "data": {"extra": "info"}
    }
    """
    try:
        data = json.loads(request.body)
        room_name = data.get('room_name')
        event_type = data.get('event_type', 'message')
        message = data.get('message')
        extra_data = data.get('data', {})
        
        if not room_name or not message:
            return JsonResponse({
                'error': 'room_name and message are required'
            }, status=400)
        
        broadcast_to_room(room_name, event_type, message, extra_data)
        
        return JsonResponse({
            'success': True,
            'message': f'Event sent to room {room_name}'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_notification_to_user(request):
    """
    API endpoint to send notifications to a specific user.
    
    POST /api/v1/websocket/send-notification/
    {
        "user_id": "user123",
        "message": "You have a new message!",
        "data": {"type": "chat", "count": 1}
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        message = data.get('message')
        extra_data = data.get('data', {})
        
        if not user_id or not message:
            return JsonResponse({
                'error': 'user_id and message are required'
            }, status=400)
        
        notify_user(user_id, message, extra_data)
        
        return JsonResponse({
            'success': True,
            'message': f'Notification sent to user {user_id}'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_system_message(request):
    """
    API endpoint to send system messages to a user.
    
    POST /api/v1/websocket/send-system-message/
    {
        "user_id": "user123",
        "message": "System maintenance in 5 minutes",
        "level": "warning",
        "data": {"maintenance_duration": "30 minutes"}
    }
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        message = data.get('message')
        level = data.get('level', 'info')  # info, warning, error, success
        extra_data = data.get('data', {})
        
        if not user_id or not message:
            return JsonResponse({
                'error': 'user_id and message are required'
            }, status=400)
        
        system_alert(user_id, message, level, extra_data)
        
        return JsonResponse({
            'success': True,
            'message': f'System message sent to user {user_id}'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def websocket_info(request):
    """
    Information endpoint about available WebSocket connections.
    """
    return JsonResponse({
        'websocket_endpoints': {
            'events': {
                'url': 'ws://localhost:8000/ws/events/{room_name}/',
                'description': 'Real-time events for specific rooms',
                'example': 'ws://localhost:8000/ws/events/general/'
            },
            'notifications': {
                'url': 'ws://localhost:8000/ws/notifications/{user_id}/',
                'description': 'User-specific notifications',
                'example': 'ws://localhost:8000/ws/notifications/user123/'
            }
        },
        'api_endpoints': {
            'send_event': '/api/v1/websocket/send-event/',
            'send_notification': '/api/v1/websocket/send-notification/',
            'send_system_message': '/api/v1/websocket/send-system-message/'
        }
    })