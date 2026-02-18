import requests
import json
import time

def test_registration():
    url = "http://127.0.0.1:5000/api/auth/register"
    timestamp = int(time.time())
    payload = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "password123"
    }
    headers = {"Content-Type": "application/json"}

    print(f"Testing registration for: {payload['email']}")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 201:
            data = response.json()
            if "token" in data and "user" in data:
                print("SUCCESS: Auto-login token and user data received.")
            else:
                print("FAILURE: Token or user data missing in response.")
        else:
            print("FAILURE: Registration failed.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_registration()
