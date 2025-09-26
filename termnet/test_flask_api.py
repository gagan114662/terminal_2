import json

import requests

BASE_URL = "http://localhost:5000"


def test_api():
    print("Testing Flask REST API...\n")

    print("1. Testing home endpoint:")
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")

    print("2. Testing /hello endpoint:")
    response = requests.get(f"{BASE_URL}/hello")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")

    print("3. Testing /hello/<name> endpoint:")
    response = requests.get(f"{BASE_URL}/hello/Python")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}\n")

    print("All tests completed successfully!")


if __name__ == "__main__":
    test_api()
