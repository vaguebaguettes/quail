```python
import os
import json
import random
import time
import urllib.request
import urllib.error
import feedparser

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

POSTED_FILE = "posted.json"

# arXiv Electrical Engineering RSS feeds
RSS_FEEDS = [
    "https://rss.arxiv.org/rss/eess",
    "https://rss.arxiv.org/rss/eess.SP",
    "https://rss.arxiv.org/rss/eess.SY",
    "https://rss.arxiv.org/rss/eess.ES",
]

KEYWORDS = [
    "power",
    "power electronics",
    "power grid",
    "motor",
    "motor control",
    "converter",
    "inverter",
    "battery",
    "embedded",
    "embedded systems",
    "fpga",
    "microcontroller",
    "esp32",
    "semiconductor",
    "signal processing",
    "wireless",
    "antenna",
    "control",
    "control systems",
    "robot",
    "robotics",
    "microelectronics",
    "analog",
    "digital",
    "photovoltaic",
    "solar",
    "circuit",
    "sensor",
    "communication",
    "machine learning",
    "artificial intelligence",
]


def load_posted():
    """Load IDs of papers that have already been sent."""

    if not os.path.exists(POSTED_FILE):
        return set()

    try:
        with open(POSTED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        return set()


def save_posted(posted):
    """Save posted paper IDs."""

    with open(POSTED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(posted), f, indent=2)


def get_paper_id(entry):
    """Get a unique ID for an arXiv paper."""

    # feedparser normally gives us the arXiv URL as id/link
    if hasattr(entry, "id") and entry.id:
        return entry.id

    if hasattr(entry, "link") and entry.link:
        return entry.link

    return None


def fetch_papers():
    """Fetch recent papers from arXiv RSS feeds."""

    papers = []
    seen_ids = set()

    for feed_url in RSS_FEEDS:

        print(f"Fetching: {feed_url}")

        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                print(f"Warning: RSS feed had parsing issues: {feed.bozo_exception}")

            for entry in feed.entries:

                paper_id = get_paper_id(entry)

                if not paper_id:
                    continue

                # Don't process the same paper twice
                if paper_id in seen_ids:
                    continue

                seen_ids.add(paper_id)

                title = getattr(entry, "title", "").strip()
                summary = getattr(entry, "summary", "").strip()
                link = getattr(entry, "link", paper_id)

                search_text = (
                    title + " " + summary
                ).lower()

                # Check whether the paper matches our EE interests
                matched_keywords = [
                    keyword
                    for keyword in KEYWORDS
                    if keyword.lower() in search_text
                ]

                if not matched_keywords:
                    continue

                # RSS feeds may provide publication dates
                published = getattr(
                    entry,
                    "published",
                    "Unknown"
                )

                # Get authors if available
                authors = []

                if hasattr(entry, "authors"):
                    authors = [
                        author.name
                        for author in entry.authors
                        if hasattr(author, "name")
                    ]

                # Fallback for feeds that don't provide authors
                if not authors:
                    authors = ["Unknown"]

                papers.append({
                    "id": paper_id,
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "published": published,
                    "authors": authors,
                    "keywords": matched_keywords,
                })

        except Exception as e:
            print(f"Error reading {feed_url}: {e}")

        # Small delay between feeds
        time.sleep(2)

    print(f"Found {len(papers)} matching papers.")

    return papers


def send_to_discord(paper):
    """Send one paper to Discord."""

    if not WEBHOOK_URL:
        print("ERROR: DISCORD_WEBHOOK_URL is missing!")
        return False

    description = paper["summary"]

    # Discord embed description limit
    if len(description) > 350:
        description = description[:347] + "..."

    authors = ", ".join(paper["authors"])

    if len(authors) > 1024:
        authors = authors[:1021] + "..."

    keywords = ", ".join(paper["keywords"])

    if len(keywords) > 1024:
        keywords = keywords[:1021] + "..."

    payload = {
        "embeds": [
            {
                "title": paper["title"],
                "url": paper["url"],
                "description": description,
                "color": 0x5865F2,
                "fields": [
                    {
                        "name": "Authors",
                        "value": authors,
                        "inline": False
                    },
                    {
                        "name": "Published",
                        "value": paper["published"],
                        "inline": True
                    },
                    {
                        "name": "Topics",
                        "value": keywords,
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Daily Electrical Engineering Research"
                }
            }
        ]
    }

    request = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Afiq-Research-Paper-Bot/1.0"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(request) as response:

            if response.status == 204:
                print(f"Successfully sent: {paper['title']}")
                return True

            print(f"Discord returned HTTP {response.status}")
            return False

    except urllib.error.HTTPError as e:

        print(f"Discord HTTP error: {e.code}")

        try:
            print(e.read().decode())
        except Exception:
            pass

        return False

    except Exception as e:

        print(f"Discord error: {e}")
        return False


def main():

    print("===================================")
    print(" Daily Electrical Engineering Bot")
    print("===================================")

    posted = load_posted()

    print(f"Previously posted papers: {len(posted)}")

    papers = fetch_papers()

    # Only use papers we haven't sent before
    unseen = [
        paper
        for paper in papers
        if paper["id"] not in posted
    ]

    print(f"New unseen papers: {len(unseen)}")

    if not unseen:
        print("No new matching papers found today.")
        return

    # Pick a random paper
    paper = random.choice(unseen)

    print()
    print("Selected paper:")
    print(paper["title"])
    print()

    # Send to Discord
    if send_to_discord(paper):

        posted.add(paper["id"])

        save_posted(posted)

        print("posted.json updated.")

    else:

        print("Paper was NOT added to posted.json.")


if __name__ == "__main__":
    main()
```
