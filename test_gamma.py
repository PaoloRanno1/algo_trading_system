import requests
import json

def fetch_events():
    url = "https://gamma-api.polymarket.com/events?limit=20&active=true&closed=false"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"Fetched {len(data)} events.")
        if data:
            print(json.dumps(data[0], indent=2))
            
            # Print categories/tags of the first few to see how politics are identified
            for i in range(min(5, len(data))):
                tags = [t.get('label') for t in data[i].get('tags', [])] if isinstance(data[i].get('tags'), list) else []
                print(f"Event: {data[i].get('title')} | Tags: {tags}")
    else:
        print(f"Error {response.status_code}")

if __name__ == "__main__":
    fetch_events()
