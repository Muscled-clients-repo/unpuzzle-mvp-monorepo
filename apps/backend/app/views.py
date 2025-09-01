"""
Main application views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db import connection
import os


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return Response({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
        'environment': os.environ.get('ENVIRONMENT', 'development'),
        'services': {
            'database': db_status,
            'supabase': 'configured' if os.environ.get('SUPABASE_URL') else 'not_configured'
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """API information endpoint"""
    return Response({
        'api_name': 'Unpuzzle MVP Backend',
        'version': '1.0.0',
        'description': 'Django-based learning management system with Supabase authentication',
        'endpoints': {
            'authentication': '/api/v1/auth/',
            'user_management': '/api/v1/user/',
            'courses': '/api/v1/courses/',
            'student_apis': '/api/v1/student/',
            'instructor_apis': '/api/v1/instructor/',
            'health_check': '/health'
        },
        'documentation': 'Available in /docs/',
        'timestamp': timezone.now().isoformat()
    })