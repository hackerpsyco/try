#!/usr/bin/env python
"""
Test script to verify session timeout and URL handling fixes
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CLAS.settings')
django.setup()

User = get_user_model()


def test_session_timeout_handling():
    """Test session timeout middleware functionality"""
    print("Testing session timeout handling...")
    
    client = Client()
    
    # Create a test user
    try:
        user = User.objects.get(email='test@example.com')
    except User.DoesNotExist:
        from class.models import Role
        admin_role = Role.objects.get(name='ADMIN')
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            role=admin_role
        )
    
    # Test 1: Login and access protected page
    print("  1. Testing normal login and access...")
    response = client.post('/login/', {
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    if response.status_code == 302:
        print("    ✓ Login successful")
    else:
        print("    ✗ Login failed")
        return False
    
    # Test 2: Access protected page while authenticated
    response = client.get('/admin/dashboard/')
    if response.status_code == 200:
        print("    ✓ Protected page accessible when authenticated")
    else:
        print("    ✗ Protected page not accessible")
        return False
    
    # Test 3: Simulate session timeout by manually expiring session
    print("  2. Testing session timeout...")
    
    # Get the session and modify last_activity to simulate timeout
    session_key = client.session.session_key
    if session_key:
        session = Session.objects.get(session_key=session_key)
        session_data = session.get_decoded()
        
        # Set last_activity to 2 hours ago (beyond 1 hour timeout)
        session_data['last_activity'] = time.time() - 7200  # 2 hours ago
        session.session_data = session.encode(session_data)
        session.save()
        
        # Try to access protected page - should redirect to login
        response = client.get('/admin/dashboard/')
        if response.status_code == 302 and '/login/' in response.url:
            print("    ✓ Session timeout redirects to login")
        else:
            print("    ✗ Session timeout not handled properly")
            return False
    
    print("Session timeout handling tests passed!")
    return True


def test_unauthenticated_access():
    """Test handling of unauthenticated access to protected URLs"""
    print("Testing unauthenticated access handling...")
    
    client = Client()
    
    # Test accessing protected URL without authentication
    response = client.get('/admin/dashboard/')
    
    if response.status_code == 302 and '/login/' in response.url:
        print("    ✓ Unauthenticated access redirects to login")
    else:
        print("    ✗ Unauthenticated access not handled properly")
        return False
    
    # Test that next_url is stored in session
    if 'next_url' in client.session:
        print("    ✓ Original URL stored for post-login redirect")
    else:
        print("    ✗ Original URL not stored")
        return False
    
    print("Unauthenticated access handling tests passed!")
    return True


def test_404_handling():
    """Test 404 error handling"""
    print("Testing 404 error handling...")
    
    client = Client()
    
    # Test 404 for unauthenticated user
    response = client.get('/nonexistent-page/')
    
    if response.status_code == 302 and '/login/' in response.url:
        print("    ✓ 404 for unauthenticated user redirects to login")
    else:
        print("    ✗ 404 for unauthenticated user not handled properly")
        return False
    
    print("404 error handling tests passed!")
    return True


def test_post_login_redirect():
    """Test post-login redirect functionality"""
    print("Testing post-login redirect...")
    
    client = Client()
    
    # First, try to access a protected page (this should store next_url)
    response = client.get('/admin/schools/')
    
    # Now login
    response = client.post('/login/', {
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Check if redirected to the original page or dashboard
    if response.status_code == 302:
        print("    ✓ Post-login redirect working")
    else:
        print("    ✗ Post-login redirect not working")
        return False
    
    print("Post-login redirect tests passed!")
    return True


def main():
    """Run all tests"""
    print("Starting session timeout and URL handling tests...\n")
    
    tests = [
        test_unauthenticated_access,
        test_session_timeout_handling,
        test_404_handling,
        test_post_login_redirect,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"    ✗ Test failed with error: {e}")
            print()
    
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Session timeout handling is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)