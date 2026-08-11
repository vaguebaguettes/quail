import os
import urllib.request
import json
import feedparser  # Robust RSS parsing library

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

EE_KEYWORDS = [
    "power grid", "signal processing", "microelectronics", 
    "semiconductor", "photovoltaics", "inverter", 
    "control systems", "circuit design", "fpga", "embedded"
]

def fetch_and_filter_papers():
    url = "https://arxiv.org"
    try:
        # feedparser handles unescaped characters automatically
        feed = feedparser.parse(url)
        
        filtered_papers = []
        for entry in feed.entries:
            title = entry.get('title', '')
            link = entry.get('link', '')
            desc = entry.get('summary', entry.get('description', ''))
            
            search_text = (title + " " + desc).lower()
            if any(keyword in search_text for keyword in EE_KEYWORDS):
                truncated_desc = desc[:300] + "..." if len(desc) > 300 else desc
                filtered_papers.append({"title": title, "link": link, "desc": truncated_desc})
                
            if len(filtered_papers) >= 5:
                break
        return filtered_papers
    except Exception as e:
        print(f"Error fetching papers: {e}")
        return []

def send_to_discord(paper):
    if not WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL is missing!")
        return

    payload = {
        "embeds": [{
            "title": paper["title"],
            "url": paper["link"],
            "description": paper["desc"],
            "color": 3066993
        }]
    }
    
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                print(f"Sent: {paper['title']}")
    except Exception as e:
        print(f"Error sending: {e}")

if __name__ == "__main__":
    matched_papers = fetch_and_filter_papers()
    if not matched_papers:
        print("No papers matched your keywords today.")
    for paper in matched_papers:
        send_to_discord(paper)
