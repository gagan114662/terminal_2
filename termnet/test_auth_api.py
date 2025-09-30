import json
import time

import requests

BASE_URL = "http://localhost:5001"


def test_register():
    print("Testing Registration...")
    url = f"{BASE_URL}/api/auth/register"

    test_user = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "password123",
    }

    response = requests.post(url, json=test_user)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 201:
        print("✓ Registration successful")
        return response.json()
    else:
        print("✗ Registration failed")
        return None


def test_login(username, password):
    print("\nTesting Login...")
    url = f"{BASE_URL}/api/auth/login"

    credentials = {"username": username, "password": password}

    response = requests.post(url, json=credentials)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✓ Login successful")
        return response.json()
    else:
        print("✗ Login failed")
        return None


def test_profile(access_token):
    print("\nTesting Get Profile...")
    url = f"{BASE_URL}/api/auth/profile"

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✓ Get profile successful")
    else:
        print("✗ Get profile failed")


def test_update_profile(access_token, new_email):
    print("\nTesting Update Profile...")
    url = f"{BASE_URL}/api/auth/profile"

    headers = {"Authorization": f"Bearer {access_token}"}

    data = {"email": new_email}

    response = requests.put(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✓ Update profile successful")
    else:
        print("✗ Update profile failed")


def test_change_password(access_token, current_password, new_password):
    print("\nTesting Change Password...")
    url = f"{BASE_URL}/api/auth/change-password"

    headers = {"Authorization": f"Bearer {access_token}"}

    data = {"current_password": current_password, "new_password": new_password}

    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✓ Change password successful")
        return True
    else:
        print("✗ Change password failed")
        return False


def test_logout(access_token):
    print("\nTesting Logout...")
    url = f"{BASE_URL}/api/auth/logout"

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.post(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✓ Logout successful")
    else:
        print("✗ Logout failed")


def test_verify_token(access_token):
    print("\nTesting Token Verification...")
    url = f"{BASE_URL}/api/auth/verify"

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✓ Token verification successful")
    else:
        print("✗ Token verification failed")


def test_refresh_token(refresh_token):
    print("\nTesting Token Refresh...")
    url = f"{BASE_URL}/api/auth/refresh"

    headers = {"Authorization": f"Bearer {refresh_token}"}

    response = requests.post(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("✓ Token refresh successful")
        return response.json()
    else:
        print("✗ Token refresh failed")
        return None


def run_all_tests():
    print("=" * 50)
    print("AUTHENTICATION API TEST SUITE")
    print("=" * 50)

    reg_result = test_register()
    if not reg_result:
        print("\nTests stopped: Registration failed")
        return

    username = reg_result["user"]["username"]
    access_token = reg_result["access_token"]
    refresh_token = reg_result["refresh_token"]

    test_profile(access_token)

    new_email = f"updated_{int(time.time())}@example.com"
    test_update_profile(access_token, new_email)

    password_changed = test_change_password(
        access_token, "password123", "newpassword123"
    )

    test_verify_token(access_token)

    refresh_result = test_refresh_token(refresh_token)
    if refresh_result:
        new_access_token = refresh_result["access_token"]
        test_verify_token(new_access_token)

    test_logout(access_token)

    print("\nTesting After Logout (should fail)...")
    test_verify_token(access_token)

    if password_changed:
        print("\nTesting Login with New Password...")
        test_login(username, "newpassword123")

    print("\n" + "=" * 50)
    print("TEST SUITE COMPLETED")
    print("=" * 50)


if __name__ == "__main__":
    print("Make sure the authentication API is running on port 5001")
    print("Starting tests...")
    run_all_tests()
