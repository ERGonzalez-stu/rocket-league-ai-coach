import requests
from config import BALLCHASING_API_KEY


def test_api_connection():
    """Test if API key works"""
    headers = {"Authorization": BALLCHASING_API_KEY}

    print("Testing Ballchasing API connection...")

    # Simple request - get 1 replay
    response = requests.get(
        "https://ballchasing.com/api/replays",
        headers=headers,
        params={"count": 1}
    )

    if response.status_code == 200:
        print("API connection successful!")
        data = response.json()
        print(f"Found {len(data.get('list', []))} replay(s)")
        print(f"Total replays available: {data.get('count', 'unknown')}")
        return True
    else:
        print(f"API connection failed!")
        print(f"Status code: {response.status_code}")
        print(f"Error: {response.text}")
        return False


if __name__ == "__main__":
    test_api_connection()