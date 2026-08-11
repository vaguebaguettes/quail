import os
import json
import random
import time
import urllib.request
import xml.etree.ElementTree as ET

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

ARXIV_API = (
    "https://export.arxiv.org/api/query?"
    "search_query=cat:eess"
    "&sortBy=submittedDate"
    "&sortOrder=descending"
    "&max_results=50"
)

POSTED_FILE = "posted.json"

KEYWORDS = {
    "power",
    "grid",
    "motor",
    "converter",
    "inverter",
    "battery",
    "embedded",
    "fpga",
    "semiconductor",
    "signal",
    "wireless",
    "antenna",
    "control",
    "robot",
    "robotics",
    "microelectronics",
    "analog",
    "digital",
    "photovoltaic",
    "solar",
    "circuit",
    "microcontroller",
    "sensor",
    "communication",
    "machine learning",
    "ai"
}


def load_posted():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_posted(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted), f, indent=2)


def fetch_papers():
    req = urllib.request.Request(
        ARXIV_API,
        headers={"User-Agent": "ResearchPaperBot/1.0"}
    )

    with urllib.request.urlopen(req) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)

    ns = {
        "atom": "http://www.w3.org/2005/Atom"
    }

    papers = []

    for entry in root.findall("atom:entry", ns):

        title = entry.find("atom:title", ns).text.strip()

        summary = entry.find("atom:summary", ns).text.strip()

        paper_id = entry.find("atom:id", ns).text.strip()

        published = entry.find("atom:published", ns).text[:10]

        authors = [
            a.find("atom:name", ns).text
            for a in entry.findall("atom:author", ns)
        ]

        search_text = (title + " " + summary).lower()

        if not any(k in search_text for k in KEYWORDS):
            continue

        papers.append({
            "id": paper_id,
            "title": title,
            "summary": summary,
            "authors": authors,
            "published": published,
            "url": paper_id
        })

    return papers


def send_to_discord(paper):

    if WEBHOOK_URL is None:
        print("Missing DISCORD_WEBHOOK_URL")
        return False

    description = paper["summary"]

    if len(description) > 350:
        description = description[:347] + "..."

    payload = {
        "embeds": [
            {
                "title": paper["title"],
                "url": paper["url"],
                "description": description,
                "color": 0x2ECC71,
                "fields": [
                    {
                        "name": "Authors",
                        "value": ", ".join(paper["authors"])[:1024],
                        "inline": False
                    },
                    {
                        "name": "Published",
                        "value": paper["published"],
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Daily Electrical Engineering Paper"
                }
            }
        ]
    }

    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "ResearchPaperBot/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                print("Sent:", paper["title"])
                return True
    except Exception as e:
        print(e)

    return False


def main():

    posted = load_posted()

    papers = fetch_papers()

    unseen = [
        p for p in papers
        if p["id"] not in posted
    ]

    if not unseen:
        print("No new matching papers.")
        return

    paper = random.choice(unseen)

    if send_to_discord(paper):
        posted.add(paper["id"])
        save_posted(posted)


if __name__ == "__main__":
    main()
