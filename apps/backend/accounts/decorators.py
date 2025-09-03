"""
Optimized permission decorators using pre-loaded permissions from middleware.
"""
from functools import wraps
from django.http import JsonResponse
from .permissions import PermissionConstants


def require_permissions(required_permissions, require_all=True):
    """
    Decorator that checks if user has required permissions using pre-loaded data.
    
    Args:
        required_permissions: Single permission string or list of permissions
        require_all: If True, user must have ALL permissions. If False, user needs ANY permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Ensure user is authenticated
            if not hasattr(request, 'user_id') or not request.user_id:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            # Handle single permission as list
            perms = required_permissions if isinstance(required_permissions, list) else [required_permissions]
            
            # Check if middleware pre-loaded permissions (optimized path)
            if hasattr(request, 'has_permission'):
                if require_all:
                    has_access = all(request.has_permission(perm) for perm in perms)
                else:
                    has_access = any(request.has_permission(perm) for perm in perms)
            else:
                # Fallback to PermissionService (slower but still works)
                from .permissions import PermissionService
                if require_all:
                    has_access = PermissionService.has_all_permissions(request.user_id, perms)
                else:
                    has_access = PermissionService.has_any_permission(request.user_id, perms)
            
            if not has_access:
                return JsonResponse({
                    'error': 'Permission denied',
                    'required_permissions': perms,
                    'require_all': require_all
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(required_role):
    """
    Decorator that checks if user has required role using pre-loaded data.
    
    Args:
        required_role: Role name string
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Ensure user is authenticated
            if not hasattr(request, 'user_id') or not request.user_id:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            # Check if middleware pre-loaded roles (optimized path)
            if hasattr(request, 'has_role'):
                has_access = request.has_role(required_role)
            else:
                # Fallback to PermissionService
                from .permissions import PermissionService
                user_roles = PermissionService.get_user_roles(request.user_id)
                has_access = required_role in user_roles
            
            if not has_access:
                return JsonResponse({
                    'error': 'Role required',
                    'required_role': required_role
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Convenience decorators for common permission checks
def require_instructor_permissions(view_func):
    """Require instructor-level permissions"""
    return require_permissions([
        PermissionConstants.COURSE_CREATE,
        PermissionConstants.COURSE_UPDATE,
        PermissionConstants.MEDIA_UPLOAD
    ], require_all=False)(view_func)


def require_admin_permissions(view_func):
    """Require admin-level permissions"""  
    return require_permissions([PermissionConstants.SYSTEM_ADMIN])(view_func)


def require_course_management_permissions(view_func):
    """Require course management permissions"""
    return require_permissions([
        PermissionConstants.COURSE_CREATE,
        PermissionConstants.COURSE_UPDATE,
        PermissionConstants.COURSE_DELETE
    ], require_all=False)(view_func)