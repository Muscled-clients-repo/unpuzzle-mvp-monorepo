"""
Signal handlers for automatic cache invalidation when user roles/permissions change.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import UserRole, Role
from .permissions import PermissionService

logger = logging.getLogger(__name__)

@receiver(post_save, sender=UserRole)
def clear_user_cache_on_role_change(sender, instance, created, **kwargs):
    """Clear user permissions cache when a role is assigned or updated"""
    user_id = str(instance.user.supabase_user_id)
    PermissionService.clear_user_permissions_cache(user_id)
    
    action = "assigned" if created else "updated"
    logger.info(f"Role {instance.role.name} {action} to user {user_id} - cache cleared")

@receiver(post_delete, sender=UserRole)
def clear_user_cache_on_role_removal(sender, instance, **kwargs):
    """Clear user permissions cache when a role is removed"""
    user_id = str(instance.user.supabase_user_id)
    PermissionService.clear_user_permissions_cache(user_id)
    
    logger.info(f"Role {instance.role.name} removed from user {user_id} - cache cleared")

@receiver(post_save, sender=Role)
def clear_affected_users_cache_on_role_update(sender, instance, created, **kwargs):
    """Clear cache for all users with this role when role permissions change"""
    if not created:  # Only for updates, not new role creation
        try:
            # Get all users with this role
            affected_user_roles = UserRole.objects.filter(role=instance).select_related('user')
            affected_user_ids = [str(ur.user.supabase_user_id) for ur in affected_user_roles]
            
            # Clear cache for all affected users
            for user_id in affected_user_ids:
                PermissionService.clear_user_permissions_cache(user_id)
            
            logger.info(f"Role {instance.name} permissions updated - cleared cache for {len(affected_user_ids)} users")
            
        except Exception as e:
            logger.error(f"Failed to clear cache for role {instance.name} update: {e}")

# Optional: Clear entire permission cache on role deletion (rare but comprehensive)
@receiver(post_delete, sender=Role)
def clear_all_cache_on_role_deletion(sender, instance, **kwargs):
    """Clear all permission caches when a role is deleted"""
    try:
        # This is a nuclear option - clears all permission caches
        # Could be optimized to only clear affected users, but role deletion is rare
        cache_keys = cache.keys("user_permissions:*")
        role_keys = cache.keys("user_roles:*")
        
        if cache_keys:
            cache.delete_many(cache_keys)
        if role_keys:
            cache.delete_many(role_keys)
            
        logger.warning(f"Role {instance.name} deleted - cleared all permission caches")
        
    except Exception as e:
        logger.error(f"Failed to clear caches on role deletion: {e}")