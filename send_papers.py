import os
import urllib.request
import json

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# arXiv allows querying directly via URL parameters
# This queries the eess (Electrical Engineering) category for the last 5 entries
API_URL = "https://arxiv.org"

EE_KEYWORDS = [
    "power grid", "signal processing", "microelectronics", 
    "semiconductor", "photovoltaics", "inverter", 
    "control systems", "circuit design", "fpga", "embedded"
]

def fetch_and_filter_papers():
    try:
        # Requesting data as a plain text string
        req = urllib.request.Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode('utf-8')
            
        filtered_papers = []
        
        # Simple structural parsing using string splits to completely bypass XML parsers
        entries = html_content.split("<entry>")
        for entry in entries[1:]:  # Skip the header metadata
            try:
                title = entry.split("<title>")[1].split("</title>")[0].strip()
                link = entry.split('<link href="')[1].split('"')[0].strip()
                desc = entry.split("<summary>")[1].split("</summary>")[0].strip()
                
                search_text = (title + " " + desc).lower()
                if any(keyword in search_text for keyword in EE_KEYWORDS):
                    truncated_desc = desc[:300] + "..." if len(desc) > 300 else desc
                    filtered_papers.append({"title": title, "link": link, "desc": truncated_desc})
            except IndexError:
                continue # Skip malformed splits safely
                
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
