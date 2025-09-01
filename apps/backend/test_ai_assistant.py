#!/usr/bin/env python
"""
Test script for AI Assistant API endpoints.
This shows how to properly authenticate and call the AI endpoints.
"""
import os
import json
import requests
from supabase import create_client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

# API base URL
API_BASE_URL = 'http://localhost:8000/api/v1'

def test_ai_assistant():
    """Test AI Assistant endpoints with proper authentication"""
    
    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    print("1. Authenticating with Supabase...")
    # Sign in with test user (you need to create this user first)
    # OR use your existing test credentials
    try:
        auth_response = supabase.auth.sign_in_with_password({
            'email': 'test@example.com',  # Replace with your test user
            'password': 'testpassword123'  # Replace with your test password
        })
        
        if not auth_response.session:
            print("❌ Failed to authenticate. Please check credentials.")
            print("   You may need to create a test user first:")
            print("   - Sign up through your frontend")
            print("   - OR use Supabase dashboard to create a user")
            return
            
        access_token = auth_response.session.access_token
        print(f"✅ Authenticated successfully!")
        print(f"   Token (first 20 chars): {access_token[:20]}...")
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\nTo create a test user, you can:")
        print("1. Use Supabase dashboard")
        print("2. Use the signup endpoint")
        print("3. Run: python manage.py shell")
        print("   >>> from accounts.models import UserProfile")
        print("   >>> # Create user in Supabase first, then create profile")
        return
    
    # Headers with authentication
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print("\n2. Testing AI Assistant Chat endpoint...")
    chat_data = {
        'message': 'Hello, can you help me understand Python functions?',
        'context': {
            'course_id': 'test-course-123',
            'video_id': 'test-video-456'
        }
    }
    
    try:
        response = requests.post(
            f'{API_BASE_URL}/ai-assistant/chat/send/',
            json=chat_data,
            headers=headers
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI Response: {data.get('message', 'No message')[:100]}...")
            print(f"   Session ID: {data.get('session_id')}")
            print(f"   Usage: {data.get('subscription', {})}")
            
        elif response.status_code == 403:
            print("❌ 403 Forbidden - Authentication issue")
            print(f"   Response: {response.text}")
            
        elif response.status_code == 429:
            data = response.json()
            print("⚠️  Rate limit exceeded!")
            print(f"   Message: {data.get('message')}")
            print(f"   Daily limit: {data.get('details', {}).get('daily_limit')}")
            print(f"   Current usage: {data.get('details', {}).get('current_usage')}")
            
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n3. Testing usage check endpoint...")
    try:
        response = requests.post(
            f'{API_BASE_URL}/ai-assistant/user/check-limits/',
            json={'agent_type': 'chat', 'estimated_tokens': 100},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Usage Check:")
            print(f"   Can use AI: {data.get('can_use_ai')}")
            print(f"   Daily limit: {data.get('daily_limit')}")
            print(f"   Remaining today: {data.get('remaining_interactions')}")
            print(f"   Subscription plan: {data.get('subscription_plan')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n4. Testing AI Stats endpoint...")
    try:
        response = requests.get(
            f'{API_BASE_URL}/ai-assistant/user/ai-stats/',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI Stats:")
            print(f"   Subscription: {data.get('subscription_plan')}")
            print(f"   Usage today: {data.get('usage_today')}/{data.get('daily_limit')}")
            print(f"   Usage this month: {data.get('usage_this_period')}/{data.get('monthly_limit')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_without_auth():
    """Test what happens without authentication"""
    print("\n" + "="*60)
    print("Testing WITHOUT Authentication")
    print("="*60)
    
    response = requests.post(
        f'{API_BASE_URL}/ai-assistant/chat/send/',
        json={'message': 'Hello'},
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly returns 401 Unauthorized")
    elif response.status_code == 403:
        print("✅ Returns 403 Forbidden (authentication required)")
    else:
        print(f"Response: {response.text}")

if __name__ == '__main__':
    print("="*60)
    print("AI Assistant API Test")
    print("="*60)
    
    # Test without auth first
    test_without_auth()
    
    # Test with auth
    print("\n" + "="*60)
    print("Testing WITH Authentication")
    print("="*60)
    test_ai_assistant()
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("\nNOTE: If you're getting 403 errors with valid token:")
    print("1. Check that UserProfile exists for the authenticated user")
    print("2. Ensure OPENAI_API_KEY is set in .env")
    print("3. Check that subscription plans are seeded (run: python manage.py seed_subscription_plans)")
    print("4. Verify Redis is running for caching")