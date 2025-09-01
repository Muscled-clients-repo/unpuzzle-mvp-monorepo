#!/usr/bin/env python
"""
Test script for OAuth authentication endpoints.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:3001/api/v1/auth"

def test_get_providers():
    """Test getting list of supported OAuth providers"""
    print("\n" + "="*50)
    print("Testing: Get Supported OAuth Providers")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/oauth/providers/")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Providers: {len(data.get('providers', []))} providers found")
        for provider in data.get('providers', []):
            print(f"  - {provider['name']} ({provider['id']})")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def test_oauth_signin():
    """Test initiating OAuth sign in"""
    print("\n" + "="*50)
    print("Testing: Initiate OAuth Sign In (Google)")
    print("="*50)
    
    payload = {
        "provider": "google",
        "redirect_url": "http://localhost:3000/auth/callback"
    }
    
    response = requests.post(
        f"{BASE_URL}/oauth/signin/",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Provider: {data.get('provider')}")
        print(f"OAuth URL: {data.get('url')[:100]}..." if data.get('url') else "No URL")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200


def test_invalid_provider():
    """Test with invalid provider"""
    print("\n" + "="*50)
    print("Testing: Invalid Provider")
    print("="*50)
    
    payload = {
        "provider": "invalid_provider"
    }
    
    response = requests.post(
        f"{BASE_URL}/oauth/signin/",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 400:
        data = response.json()
        print(f"Expected error: {data.get('error')}")
        print(f"Supported providers: {data.get('supported_providers')}")
        return True
    else:
        print(f"Unexpected response: {response.text}")
        return False


def test_oauth_callback_without_code():
    """Test OAuth callback without code"""
    print("\n" + "="*50)
    print("Testing: OAuth Callback without Code")
    print("="*50)
    
    response = requests.post(
        f"{BASE_URL}/oauth/callback/",
        json={},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 400:
        data = response.json()
        print(f"Expected error: {data.get('error')}")
        return True
    else:
        print(f"Unexpected response: {response.text}")
        return False


def main():
    """Run all OAuth tests"""
    print("\n" + "#"*50)
    print("# OAuth Authentication Tests")
    print("#"*50)
    
    tests = [
        ("Get Providers", test_get_providers),
        ("OAuth Sign In", test_oauth_signin),
        ("Invalid Provider", test_invalid_provider),
        ("Callback without Code", test_oauth_callback_without_code)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\nError running {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Note about Supabase configuration
    print("\n" + "="*50)
    print("IMPORTANT NOTES:")
    print("="*50)
    print("1. For OAuth to work, you need to configure providers in Supabase Dashboard:")
    print("   - Go to Authentication > Providers")
    print("   - Enable desired providers (Google, LinkedIn, GitHub, etc.)")
    print("   - Add OAuth credentials from each provider")
    print("\n2. OAuth callback URL format:")
    print("   - Supabase: https://[PROJECT_ID].supabase.co/auth/v1/callback")
    print("   - Add to provider's authorized redirect URIs")
    print("\n3. Frontend integration:")
    print("   - POST to /api/accounts/oauth/signin/ with provider")
    print("   - Redirect user to returned OAuth URL")
    print("   - Handle callback at /api/accounts/oauth/callback/")
    

if __name__ == "__main__":
    main()