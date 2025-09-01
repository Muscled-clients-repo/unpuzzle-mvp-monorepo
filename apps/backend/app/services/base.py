from typing import Any, Dict, Optional, List
from django.db import transaction
from django.core.cache import cache
import logging


class BaseService:
    """Base service class with common functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cache = cache
    
    @transaction.atomic
    def execute_in_transaction(self, func, *args, **kwargs):
        """Execute function in database transaction"""
        return func(*args, **kwargs)
    
    def get_cached_or_compute(self, cache_key: str, compute_func, timeout: int = 300):
        """Get from cache or compute and cache"""
        result = self.cache.get(cache_key)
        if result is None:
            result = compute_func()
            self.cache.set(cache_key, result, timeout)
        return result
    
    def invalidate_cache(self, keys: Optional[List[str]] = None, prefix: Optional[str] = None):
        """Invalidate cache by keys or prefix"""
        if keys:
            # Delete specific keys
            self.cache.delete_many(keys)
        elif prefix:
            # Pattern-based deletion requires Redis backend with django-redis
            # For standard Django cache backends, this isn't supported
            self.logger.warning(
                f"Pattern-based deletion not available. "
                f"Consider using django-redis for advanced cache operations."
            )
        else:
            # Clear all cache as last resort
            self.cache.clear()
    
    def log_action(self, action: str, user=None, **kwargs):
        """Log service action"""
        self.logger.info(
            f"Action: {action}",
            extra={
                'user': user.id if user else None,
                **kwargs
            }
        )