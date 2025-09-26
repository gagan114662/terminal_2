"""
Test script for the Simple Blog Platform
"""

import sys

import requests


def test_blog():
    """Test basic blog functionality"""
    base_url = "http://127.0.0.1:5000"

    print("Testing Simple Blog Platform...")
    print("-" * 40)

    # Test home page
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("✅ Home page is accessible")
        else:
            print(f"❌ Home page returned status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the blog. Make sure it's running on port 5000")
        return False

    # Test new post page
    response = requests.get(f"{base_url}/new")
    if response.status_code == 200:
        print("✅ New post page is accessible")
    else:
        print(f"❌ New post page returned status code: {response.status_code}")

    # Test creating a new post
    post_data = {
        "title": "Test Post from Script",
        "author": "Test Script",
        "content": "This is a test post created by the automated test script to verify blog functionality.",
    }

    response = requests.post(f"{base_url}/new", data=post_data, allow_redirects=False)
    if response.status_code in [302, 301]:  # Redirect after successful post
        print("✅ Successfully created a new post")

        # Get the post ID from redirect location
        location = response.headers.get("Location", "")
        if "/post/" in location:
            post_id = location.split("/post/")[-1]
            print(f"   Post ID: {post_id}")

            # Test viewing the post
            response = requests.get(f"{base_url}/post/{post_id}")
            if response.status_code == 200 and "Test Post from Script" in response.text:
                print("✅ Post can be viewed successfully")
            else:
                print("❌ Could not view the created post")
    else:
        print(f"❌ Failed to create post. Status code: {response.status_code}")

    print("-" * 40)
    print("Test complete!")
    return True


if __name__ == "__main__":
    success = test_blog()
    sys.exit(0 if success else 1)
