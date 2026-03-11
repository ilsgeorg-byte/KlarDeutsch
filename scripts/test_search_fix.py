import requests
import sys

def test_search(query):
    # Adjust port if necessary, assuming default 5000 based on standard flask apps
    url = f"http://localhost:5000/api/words/search?q={query}"
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: Found {len(data.get('data', []))} results")
            print("First result:", data.get('data', [])[0] if data.get('data') else "None")
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Connection failed: {e}")
        # If connection fails, we might rely on code review or user verification since the backend might not be running locally

if __name__ == "__main__":
    test_search("und")
