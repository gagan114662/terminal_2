#!/usr/bin/env python3
"""
Simple test script for the blog application.
Run this to verify basic functionality.
"""

import json
from time import sleep

import requests

BASE_URL = "http://localhost:5000"


def test_homepage():
    """Test if homepage loads"""
    try:
        response = requests.get(BASE_URL)
        assert response.status_code == 200
        print("✓ Homepage loads successfully")
        return True
    except Exception as e:
        print(f"✗ Homepage test failed: {e}")
        return False


def test_registration():
    """Test user registration"""
    try:
        # Note: This will fail if user already exists
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        }
        response = requests.post(f"{BASE_URL}/register", data=data)
        print("✓ Registration endpoint accessible")
        return True
    except Exception as e:
        print(f"✗ Registration test failed: {e}")
        return False


def test_login():
    """Test user login"""
    try:
        data = {"username": "testuser", "password": "testpass123"}
        response = requests.post(f"{BASE_URL}/login", data=data)
        print("✓ Login endpoint accessible")
        return True
    except Exception as e:
        print(f"✗ Login test failed: {e}")
        return False


def main():
    print("Testing Blog Application...")
    print("-" * 40)

    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=2)
    except:
        print("⚠ Server not running. Start the blog app with: python blog_app.py")
        return

    # Run tests
    test_homepage()
    test_registration()
    test_login()

    print("-" * 40)
    print("Basic tests completed!")
    print("\nTo fully test the application:")
    print("1. Run: python blog_app.py")
    print("2. Open: http://localhost:5000")
    print("3. Register a new user")
    print("4. Create and edit posts")
    print("5. Test all features manually")


if __name__ == "__main__":
    main()
