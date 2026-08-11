import os
import urllib.request
import json

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Queries the Electrical Engineering category (eess) for the 10 newest papers
API_URL = "https://arxiv.org"

EE_KEYWORDS = [
    "power grid", "signal processing", "microelectronics", 
    "semiconductor", "photovoltaics", "inverter", 
    "control systems", "circuit design", "fpga", "embedded"
]

def fetch_and_filter_papers():
    try:
        req = urllib.request.Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            raw_text = response.read().decode('utf-8')
        
        filtered_papers = []
        
        # Split the text by the <entry> tag to isolate each paper cleanly
        entries = raw_text.split("<entry>")
        for entry in entries[1:]:  # Skip the feed header metadata
            try:
                # Safely slice strings to extract title, link, and summary
                title = entry.split("<title>")[1].split("</title>")[0].strip()
                link = entry.split('<link href="')[1].split('"')[0].strip()
                desc = entry.split("<summary>")[1].split("</summary>")[0].strip()
                
                # Filter against your target keywords
                search_text = (title + " " + desc).lower()
                if any(keyword in search_text for keyword in EE_KEYWORDS):
                    truncated_desc = desc[:300] + "..." if len(desc) > 300 else desc
                    filtered_papers.append({
                        "title": title,
                        "link": link,
                        "desc": truncated_desc
                    })
            except IndexError:
                continue  # Skip any trailing fragments safely
                
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
