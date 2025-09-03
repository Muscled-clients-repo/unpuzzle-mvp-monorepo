"""
Permission system for Supabase-based authentication.
Handles role-based access control (RBAC) for the application.
"""
from typing import List, Dict, Any, Optional
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView
from django.core.cache import cache
from .models import UserProfile, Role, UserRole


class PermissionConstants:
    """Define all available permissions in the system"""
    
    # User management
    USER_CREATE = 'user:create'
    USER_READ = 'user:read'
    USER_UPDATE = 'user:update'
    USER_DELETE = 'user:delete'
    USER_LIST = 'user:list'
    
    # Course management
    COURSE_CREATE = 'course:create'
    COURSE_READ = 'course:read'
    COURSE_UPDATE = 'course:update'
    COURSE_DELETE = 'course:delete'
    COURSE_LIST = 'course:list'
    COURSE_PUBLISH = 'course:publish'
    
    # Enrollment management
    ENROLLMENT_CREATE = 'enrollment:create'
    ENROLLMENT_READ = 'enrollment:read'
    ENROLLMENT_UPDATE = 'enrollment:update'
    ENROLLMENT_DELETE = 'enrollment:delete'
    ENROLLMENT_LIST = 'enrollment:list'
    
    # Media management
    MEDIA_UPLOAD = 'media:upload'
    MEDIA_READ = 'media:read'
    MEDIA_UPDATE = 'media:update'
    MEDIA_DELETE = 'media:delete'
    MEDIA_LIST = 'media:list'
    
    # Analytics
    ANALYTICS_VIEW = 'analytics:view'
    ANALYTICS_EXPORT = 'analytics:export'
    
    # Admin permissions
    ROLE_MANAGE = 'role:manage'
    SYSTEM_ADMIN = 'system:admin'
    
    @classmethod
    def get_all_permissions(cls) -> List[str]:
        """Get all available permissions"""
        return [
            value for name, value in cls.__dict__.items()
            if not name.startswith('_') and isinstance(value, str) and ':' in value
        ]


class RoleConstants:
    """Define default system roles"""
    
    SUPER_ADMIN = 'super_admin'
    ADMIN = 'admin'
    INSTRUCTOR = 'instructor'
    STUDENT = 'student'
    VIEWER = 'viewer'
    
    @classmethod
    def get_default_roles(cls) -> Dict[str, Dict[str, Any]]:
        """Get default role configurations"""
        return {
            cls.SUPER_ADMIN: {
                'description': 'Full system access',
                'permissions': PermissionConstants.get_all_permissions()
            },
            cls.ADMIN: {
                'description': 'Administrative access',
                'permissions': [
                    PermissionConstants.USER_CREATE,
                    PermissionConstants.USER_READ,
                    PermissionConstants.USER_UPDATE,
                    PermissionConstants.USER_LIST,
                    PermissionConstants.COURSE_CREATE,
                    PermissionConstants.COURSE_READ,
                    PermissionConstants.COURSE_UPDATE,
                    PermissionConstants.COURSE_DELETE,
                    PermissionConstants.COURSE_LIST,
                    PermissionConstants.COURSE_PUBLISH,
                    PermissionConstants.ENROLLMENT_CREATE,
                    PermissionConstants.ENROLLMENT_READ,
                    PermissionConstants.ENROLLMENT_UPDATE,
                    PermissionConstants.ENROLLMENT_DELETE,
                    PermissionConstants.ENROLLMENT_LIST,
                    PermissionConstants.MEDIA_UPLOAD,
                    PermissionConstants.MEDIA_READ,
                    PermissionConstants.MEDIA_UPDATE,
                    PermissionConstants.MEDIA_DELETE,
                    PermissionConstants.MEDIA_LIST,
                    PermissionConstants.ANALYTICS_VIEW,
                    PermissionConstants.ANALYTICS_EXPORT,
                ]
            },
            cls.INSTRUCTOR: {
                'description': 'Course instructor access',
                'permissions': [
                    PermissionConstants.USER_READ,
                    PermissionConstants.COURSE_CREATE,
                    PermissionConstants.COURSE_READ,
                    PermissionConstants.COURSE_UPDATE,
                    PermissionConstants.COURSE_LIST,
                    PermissionConstants.COURSE_PUBLISH,
                    PermissionConstants.ENROLLMENT_READ,
                    PermissionConstants.ENROLLMENT_LIST,
                    PermissionConstants.MEDIA_UPLOAD,
                    PermissionConstants.MEDIA_READ,
                    PermissionConstants.MEDIA_UPDATE,
                    PermissionConstants.MEDIA_LIST,
                    PermissionConstants.ANALYTICS_VIEW,
                ]
            },
            cls.STUDENT: {
                'description': 'Student access',
                'permissions': [
                    PermissionConstants.COURSE_READ,
                    PermissionConstants.COURSE_LIST,
                    PermissionConstants.ENROLLMENT_CREATE,
                    PermissionConstants.ENROLLMENT_READ,
                    PermissionConstants.MEDIA_READ,
                ]
            },
            cls.VIEWER: {
                'description': 'Read-only access',
                'permissions': [
                    PermissionConstants.COURSE_READ,
                    PermissionConstants.COURSE_LIST,
                    PermissionConstants.MEDIA_READ,
                ]
            }
        }


class PermissionService:
    """Service for managing user permissions"""
    
    @staticmethod
    def get_user_permissions(user_id: str) -> List[str]:
        """Get all permissions for a user (cached with optimized database queries)"""
        import time
        start_time = time.time()
        
        cache_key = f"user_permissions:{user_id}"
        permissions = cache.get(cache_key)
        
        if permissions is None:
            print(f"[PERMISSION DEBUG] Cache MISS for user {user_id} - querying database")
            try:
                # Optimized query to fetch user with all roles and permissions in one go
                user_profile = UserProfile.objects.select_related().prefetch_related(
                    'user_roles__role'  # Prefetch roles to avoid N+1 queries
                ).get(supabase_user_id=user_id)
                
                # Get active roles with a single optimized query
                active_user_roles = user_profile.user_roles.filter(role__is_active=True)
                
                permissions = set()
                for user_role in active_user_roles:
                    role_permissions = user_role.role.permissions or []
                    permissions.update(role_permissions)
                
                permissions = list(permissions)
                # Cache for 10 minutes (increased from 5 minutes for better performance)
                cache.set(cache_key, permissions, 600)
                
            except UserProfile.DoesNotExist:
                permissions = []
                # Cache empty permissions for 2 minutes to avoid repeated DB queries
                cache.set(cache_key, permissions, 120)
        else:
            print(f"[PERMISSION DEBUG] Cache HIT for user {user_id}")
        
        elapsed_time = (time.time() - start_time) * 1000
        print(f"[PERMISSION DEBUG] get_user_permissions took {elapsed_time:.2f}ms")
                
        return permissions
    
    @staticmethod
    def get_user_roles(user_id: str) -> List[str]:
        """Get all active role names for a user (cached)"""
        import time
        start_time = time.time()
        
        cache_key = f"user_roles:{user_id}"
        roles = cache.get(cache_key)
        
        if roles is None:
            print(f"[ROLE DEBUG] Cache MISS for user {user_id} - querying database")
            try:
                user_profile = UserProfile.objects.prefetch_related(
                    'user_roles__role'
                ).get(supabase_user_id=user_id)
                
                active_user_roles = user_profile.user_roles.filter(role__is_active=True)
                roles = [user_role.role.name for user_role in active_user_roles]
                
                # Cache for 15 minutes (roles change less frequently than permissions)
                cache.set(cache_key, roles, 900)
                
            except UserProfile.DoesNotExist:
                roles = []
                cache.set(cache_key, roles, 120)
        else:
            print(f"[ROLE DEBUG] Cache HIT for user {user_id}")
        
        elapsed_time = (time.time() - start_time) * 1000
        print(f"[ROLE DEBUG] get_user_roles took {elapsed_time:.2f}ms")
                
        return roles

    @staticmethod
    def has_permission(user_id: str, permission: str) -> bool:
        """Check if user has a specific permission (optimized)"""
        user_permissions = PermissionService.get_user_permissions(user_id)
        return permission in user_permissions or PermissionConstants.SYSTEM_ADMIN in user_permissions
    
    @staticmethod
    def has_any_permission(user_id: str, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(PermissionService.has_permission(user_id, perm) for perm in permissions)
    
    @staticmethod
    def has_all_permissions(user_id: str, permissions: List[str]) -> bool:
        """Check if user has all specified permissions"""
        return all(PermissionService.has_permission(user_id, perm) for perm in permissions)
    
    @staticmethod
    def clear_user_permissions_cache(user_id: str):
        """Clear cached permissions and roles for a user"""
        permissions_cache_key = f"user_permissions:{user_id}"
        roles_cache_key = f"user_roles:{user_id}"
        
        # Delete both permissions and roles cache
        cache.delete_many([permissions_cache_key, roles_cache_key])
        
        # Also invalidate JWT cache if user permissions changed
        # This ensures immediate permission changes take effect
        try:
            from django.core.cache import cache as django_cache
            # Clear any JWT tokens for this user (they contain old permission context)
            # Note: This is a broad invalidation - in production, you might want more targeted approach
            import logging
            logger = logging.getLogger('supabase_auth')
            logger.info(f"Cleared permission cache for user {user_id}")
        except Exception as e:
            pass  # Don't break if logging fails
    
    @staticmethod
    def assign_role_to_user(user_id: str, role_name: str, assigned_by: str = None) -> bool:
        """Assign a role to a user"""
        try:
            user_profile = UserProfile.objects.get(supabase_user_id=user_id)
            role = Role.objects.get(name=role_name, is_active=True)
            
            user_role, created = UserRole.objects.get_or_create(
                user=user_profile,
                role=role,
                defaults={'assigned_by': assigned_by}
            )
            
            # Clear permission cache - user gets new permissions immediately
            PermissionService.clear_user_permissions_cache(user_id)
            return True
            
        except (UserProfile.DoesNotExist, Role.DoesNotExist):
            return False
    
    @staticmethod
    def remove_role_from_user(user_id: str, role_name: str) -> bool:
        """Remove a role from a user"""
        try:
            user_profile = UserProfile.objects.get(supabase_user_id=user_id)
            role = Role.objects.get(name=role_name)
            
            UserRole.objects.filter(user=user_profile, role=role).delete()
            
            # Clear cache
            PermissionService.clear_user_permissions_cache(user_id)
            return True
            
        except (UserProfile.DoesNotExist, Role.DoesNotExist):
            return False


class HasPermission(BasePermission):
    """DRF Permission class to check for specific permissions"""
    
    def __init__(self, permission: str):
        self.permission = permission
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        # Check if user is authenticated (has user_id from middleware)
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return False
        
        return PermissionService.has_permission(user_id, self.permission)


class HasAnyPermission(BasePermission):
    """DRF Permission class to check for any of specified permissions"""
    
    def __init__(self, permissions: List[str]):
        self.permissions = permissions
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return False
        
        return PermissionService.has_any_permission(user_id, self.permissions)


class HasAllPermissions(BasePermission):
    """DRF Permission class to check for all specified permissions"""
    
    def __init__(self, permissions: List[str]):
        self.permissions = permissions
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return False
        
        return PermissionService.has_all_permissions(user_id, self.permissions)


# Convenience permission classes for common use cases
class IsAdmin(HasPermission):
    def __init__(self):
        super().__init__(PermissionConstants.SYSTEM_ADMIN)


class IsInstructor(HasAnyPermission):
    def __init__(self):
        super().__init__([
            PermissionConstants.COURSE_CREATE,
            PermissionConstants.COURSE_UPDATE,
            PermissionConstants.SYSTEM_ADMIN
        ])


class IsStudent(HasAnyPermission):
    def __init__(self):
        super().__init__([
            PermissionConstants.ENROLLMENT_CREATE,
            PermissionConstants.COURSE_READ,
            PermissionConstants.SYSTEM_ADMIN
        ])


def permission_required(permission: str):
    """Decorator for view functions that require specific permissions"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_id = getattr(request, 'user_id', None)
            if not user_id or not PermissionService.has_permission(user_id, permission):
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Permission denied',
                    'required_permission': permission
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator