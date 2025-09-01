"""
Example views showing how to use the permission system.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

from .permissions import (
    HasPermission,
    HasAnyPermission,
    IsAdmin,
    IsInstructor,
    IsStudent,
    PermissionConstants,
    PermissionService,
    permission_required
)
from .models import UserProfile


# Example 1: Using permission classes with DRF decorators
@api_view(['GET'])
@permission_classes([HasPermission(PermissionConstants.USER_LIST)])
def list_users(request):
    """List users - requires USER_LIST permission"""
    users = UserProfile.objects.all()
    user_data = [
        {
            'id': str(user.supabase_user_id),
            'email': user.email,
            'full_name': user.full_name,
            'status': user.status
        }
        for user in users
    ]
    return Response({'users': user_data})


# Example 2: Using convenience permission classes
@api_view(['DELETE'])
@permission_classes([IsAdmin])
def delete_user(request, user_id):
    """Delete user - admin only"""
    try:
        user = UserProfile.objects.get(supabase_user_id=user_id)
        user.status = 'inactive'
        user.save()
        return Response({'message': 'User deactivated successfully'})
    except UserProfile.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)


# Example 3: Using multiple permission options
@api_view(['POST'])
@permission_classes([HasAnyPermission([
    PermissionConstants.COURSE_CREATE,
    PermissionConstants.SYSTEM_ADMIN
])])
def create_course(request):
    """Create course - instructors or admins can create courses"""
    # Course creation logic would go here
    return Response({
        'message': 'Course created successfully',
        'user_id': request.user_id,
        'permissions': PermissionService.get_user_permissions(request.user_id)
    })


# Example 4: Using function decorator
@api_view(['GET'])
@permission_required(PermissionConstants.ANALYTICS_VIEW)
def view_analytics(request):
    """View analytics - requires specific permission"""
    return Response({
        'analytics_data': 'Sample analytics data',
        'user_permissions': PermissionService.get_user_permissions(request.user_id)
    })


# Example 5: Manual permission checking in view
@api_view(['PUT'])
def update_course(request, course_id):
    """Update course - manual permission check"""
    user_id = getattr(request, 'user_id', None)
    
    if not user_id:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Check if user has permission to update courses
    if not PermissionService.has_permission(user_id, PermissionConstants.COURSE_UPDATE):
        return Response({
            'error': 'Permission denied',
            'required_permission': PermissionConstants.COURSE_UPDATE
        }, status=403)
    
    # Course update logic would go here
    return Response({'message': f'Course {course_id} updated successfully'})


# Example 6: Role-specific endpoints
@api_view(['GET'])
@permission_classes([IsStudent])
def student_dashboard(request):
    """Student dashboard - student role required"""
    user_id = request.user_id
    
    # Get user's enrollments, progress, etc.
    return Response({
        'dashboard_type': 'student',
        'user_id': user_id,
        'permissions': PermissionService.get_user_permissions(user_id)
    })


@api_view(['GET'])
@permission_classes([IsInstructor])
def instructor_dashboard(request):
    """Instructor dashboard - instructor role required"""
    user_id = request.user_id
    
    # Get instructor's courses, analytics, etc.
    return Response({
        'dashboard_type': 'instructor',
        'user_id': user_id,
        'permissions': PermissionService.get_user_permissions(user_id)
    })


# Utility endpoints for managing permissions
@api_view(['GET'])
def my_permissions(request):
    """Get current user's permissions"""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return Response({'error': 'Authentication required'}, status=401)
    
    try:
        user_profile = UserProfile.objects.get(supabase_user_id=user_id)
        permissions = PermissionService.get_user_permissions(user_id)
        
        # Get user's roles
        user_roles = user_profile.user_roles.filter(role__is_active=True)
        roles = [
            {
                'name': ur.role.name,
                'description': ur.role.description,
                'assigned_at': ur.created_at
            }
            for ur in user_roles
        ]
        
        return Response({
            'user_id': user_id,
            'email': user_profile.email,
            'roles': roles,
            'permissions': sorted(permissions),
            'permission_count': len(permissions)
        })
    except UserProfile.DoesNotExist:
        return Response({'error': 'User profile not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAdmin])
def assign_role_to_user(request):
    """Assign role to user - admin only"""
    user_email = request.data.get('user_email')
    role_name = request.data.get('role_name')
    
    if not user_email or not role_name:
        return Response({
            'error': 'user_email and role_name are required'
        }, status=400)
    
    try:
        user_profile = UserProfile.objects.get(email=user_email)
        success = PermissionService.assign_role_to_user(
            str(user_profile.supabase_user_id),
            role_name,
            request.user_id
        )
        
        if success:
            return Response({
                'message': f'Role "{role_name}" assigned to "{user_email}" successfully'
            })
        else:
            return Response({
                'error': 'Failed to assign role. Role may not exist or user may already have this role.'
            }, status=400)
            
    except UserProfile.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)