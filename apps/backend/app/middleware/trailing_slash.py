"""
Custom middleware to handle trailing slashes for all HTTP methods.
This middleware allows POST, PUT, DELETE requests to work without trailing slashes
even when APPEND_SLASH is True.
"""
from django.shortcuts import redirect
from django.urls import resolve
from django.urls.exceptions import Resolver404


class SmartTrailingSlashMiddleware:
    """
    Middleware that intelligently handles trailing slashes for all HTTP methods.
    Unlike Django's APPEND_SLASH, this works with POST/PUT/DELETE by internally
    rewriting the path instead of redirecting.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if the path needs a trailing slash
        if not request.path.endswith('/'):
            try:
                # Try to resolve the current path
                resolve(request.path)
            except Resolver404:
                # Current path doesn't resolve, try with trailing slash
                path_with_slash = request.path + '/'
                try:
                    # Check if path with slash would resolve
                    resolve(path_with_slash)
                    
                    # For GET/HEAD requests, redirect (standard behavior)
                    if request.method in ('GET', 'HEAD'):
                        return redirect(path_with_slash, permanent=True)
                    
                    # For other methods (POST, PUT, DELETE, etc.), 
                    # internally rewrite the path without redirect
                    request.path = path_with_slash
                    request.path_info = path_with_slash
                    
                except Resolver404:
                    # Neither path resolves, continue with original
                    pass
        
        response = self.get_response(request)
        return response