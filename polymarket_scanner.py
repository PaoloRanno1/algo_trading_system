import requests
import json
import os

def fetch_top_politics_events(limit=200):
    """
    Fetches active events from Polymarket, filters by 'Politics' tag,
    and sorts them by trading volume (descending).
    """
    print(f"Scanning Polymarket for active Politics events (fetching up to {limit} recent markets)...\n")
    url = f"https://gamma-api.polymarket.com/events?limit={limit}&active=true&closed=false"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching data from Polymarket API: {e}")
        return []

    politics_events = []
    
    for event in data:
        # Check if "Politics" is in the tags
        tags = event.get('tags', [])
        if not isinstance(tags, list):
            tags = []
            
        is_politics = any(tag.get('label', '').lower() == 'politics' for tag in tags)
        
        if is_politics:
            politics_events.append({
                'title': event.get('title', 'Unknown Event'),
                'slug': event.get('slug', ''),
                'volume': float(event.get('volume', 0.0) or 0.0),
                'id': event.get('id', '')
            })
            
    # Sort by descending volume
    politics_events.sort(key=lambda x: x['volume'], reverse=True)
    return politics_events

def format_volume(vol):
    """Formats raw volume float to human-readable string (e.g. $1.2M)"""
    if vol >= 1_000_000_000:
        return f"${vol / 1_000_000_000:.2f}B"
    elif vol >= 1_000_000:
        return f"${vol / 1_000_000:.2f}M"
    elif vol >= 1_000:
        return f"${vol / 1_000:.2f}K"
    else:
        return f"${vol:.2f}"

def main():
    # Fetch top 10 politics events by volume
    events = fetch_top_politics_events()
    
    if not events:
        print("No active politics events found.")
        return
        
    top_events = events[:10]
    
    print("="*60)
    print("   TOP POLYMARKET POLITICS EVENTS BY VOLUME")
    print("="*60)
    
    for i, event in enumerate(top_events):
        print(f"{i + 1}. {event['title']}")
        print(f"   Volume: {format_volume(event['volume'])}")
        print(f"   Slug: {event['slug']}\n")
        
    print("="*60)
    
    try:
        choice = input("Enter the number of the event you want to analyze (1-10): ")
        choice_idx = int(choice) - 1
        
        if 0 <= choice_idx < len(top_events):
            selected = top_events[choice_idx]
            print(f"\n✅ You selected: {selected['title']}")
            print(f"\nTo use this event in your Trading Pipeline, update demo.ipynb:")
            print(f"> POLYMARKET_SLUG = \"{selected['slug']}\"")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
