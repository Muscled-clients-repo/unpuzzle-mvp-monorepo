"""
Supabase webhook handlers for auth events.
"""
import json
import hmac
import hashlib
import os
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import transaction
from .models import UserProfile


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature from Supabase"""
    secret = os.environ.get('SUPABASE_WEBHOOK_SECRET', '')
    if not secret:
        return True  # Skip verification if no secret is set
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@csrf_exempt
@require_http_methods(["POST"])
def supabase_auth_webhook(request):
    """
    Handle Supabase auth webhooks.
    
    This webhook receives notifications when users are created, updated, or deleted
    in Supabase Auth and syncs the changes to our UserProfile model.
    """
    # Verify signature
    signature = request.headers.get('X-Webhook-Signature', '')
    if not verify_webhook_signature(request.body, signature):
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    try:
        payload = json.loads(request.body)
        event_type = payload.get('type')
        user_data = payload.get('record', {})
        
        if not user_data or 'id' not in user_data:
            return JsonResponse({'error': 'Invalid payload'}, status=400)
        
        user_id = user_data['id']
        email = user_data.get('email', '')
        
        if event_type == 'INSERT':
            # New user created
            handle_user_created(user_id, user_data)
            
        elif event_type == 'UPDATE':
            # User updated
            handle_user_updated(user_id, user_data)
            
        elif event_type == 'DELETE':
            # User deleted
            handle_user_deleted(user_id)
        
        return JsonResponse({'status': 'success'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def handle_user_created(user_id: str, user_data: dict):
    """Handle new user creation from Supabase Auth"""
    try:
        with transaction.atomic():
            raw_user_meta_data = user_data.get('raw_user_meta_data', {})
            
            profile, created = UserProfile.objects.get_or_create(
                supabase_user_id=user_id,
                defaults={
                    'email': user_data.get('email', ''),
                    'full_name': raw_user_meta_data.get('full_name', ''),
                    'email_verified': user_data.get('email_confirmed_at') is not None,
                }
            )
            
            if created:
                print(f"Created UserProfile for user {user_id}")
            else:
                print(f"UserProfile already exists for user {user_id}")
                
    except Exception as e:
        print(f"Error creating user profile: {e}")
        raise


def handle_user_updated(user_id: str, user_data: dict):
    """Handle user update from Supabase Auth"""
    try:
        profile = UserProfile.objects.filter(supabase_user_id=user_id).first()
        if not profile:
            # User doesn't exist, create it
            handle_user_created(user_id, user_data)
            return
        
        # Update profile with new data
        profile.email = user_data.get('email', profile.email)
        profile.email_verified = user_data.get('email_confirmed_at') is not None
        
        # Update metadata if provided
        raw_user_meta_data = user_data.get('raw_user_meta_data', {})
        if 'full_name' in raw_user_meta_data:
            profile.full_name = raw_user_meta_data['full_name']
        
        profile.save()
        print(f"Updated UserProfile for user {user_id}")
        
    except Exception as e:
        print(f"Error updating user profile: {e}")
        raise


def handle_user_deleted(user_id: str):
    """Handle user deletion from Supabase Auth"""
    try:
        profile = UserProfile.objects.filter(supabase_user_id=user_id).first()
        if profile:
            # Soft delete the profile
            profile.status = 'inactive'
            profile.is_deleted = True
            profile.deleted_at = timezone.now()
            profile.deleted_by = user_id
            profile.save()
            print(f"Soft deleted UserProfile for user {user_id}")
        
    except Exception as e:
        print(f"Error deleting user profile: {e}")
        raise


@csrf_exempt 
@require_http_methods(["GET"])
def webhook_health(request):
    """Health check endpoint for webhooks"""
    return JsonResponse({'status': 'healthy', 'service': 'supabase-auth-webhook'})