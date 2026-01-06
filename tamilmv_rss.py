import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree
import time, json, os
from urllib.parse import parse_qs, urlparse

# ================= CONFIG =================
BASE_URL = "https://www.1tamilmv.lc/"
OUT_FILE = "tamilmv.xml"
STATE_FILE = "state.json"
MAX_SIZE_GB = 4          # ⛔ Skip torrents above 4GB
TOPIC_LIMIT = 10         # Only latest 10 topics
TOPIC_DELAY = 5          # Seconds between topic requests
# ==========================================

# Cloudflare-safe scraper
scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

# Load processed magnets
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
else:
    state = {"magnets": []}

processed = set(state.get("magnets", []))

# Create RSS structure
rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "1TamilMV Torrent RSS"
SubElement(channel, "link").text = BASE_URL
SubElement(channel, "description").text = "Auto Torrent RSS (Below 4GB only)"
SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime(
    "%a, %d %b %Y %H:%M:%S GMT"
)

# Fetch homepage
home = scraper.get(BASE_URL, timeout=30)
soup = BeautifulSoup(home.text, "lxml")

# Get latest topics
posts = [
    (a.get_text(strip=True), a["href"])
    for a in soup.select("a[href*='forums/topic']")
][:TOPIC_LIMIT]

def magnet_size_gb(magnet):
    qs = parse_qs(urlparse(magnet).query)
    if "xl" in qs:
        return int(qs["xl"][0]) / (1024 ** 3)
    return None

new_magnets_added = False

# Process topics
for title, post_url in posts:
    try:
        time.sleep(TOPIC_DELAY)

        page = scraper.get(post_url, timeout=30)
        psoup = BeautifulSoup(page.text, "lxml")

        for a in psoup.find_all("a", href=True):
            magnet = a["href"]

            if not magnet.startswith("magnet:?"):
                continue

            if magnet in processed:
                continue

            size = magnet_size_gb(magnet)
            if size and size > MAX_SIZE_GB:
                continue

            # Add RSS item
            item = SubElement(channel, "item")
            SubElement(item, "title").text = (
                f"{title} [{round(size, 2)}GB]" if size else title
            )
            SubElement(item, "link").text = magnet
            SubElement(item, "guid").text = magnet
            SubElement(item, "pubDate").text = datetime.utcnow().strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )

            processed.add(magnet)
            new_magnets_added = True
            print("ADDED:", title, size)

    except Exception as e:
        print("ERROR:", title, e)

# Write RSS only if new magnets found
if new_magnets_added:
    ElementTree(rss).write(OUT_FILE, encoding="utf-8", xml_declaration=True)
    print("RSS UPDATED")
else:
    print("NO NEW TORRENTS")

# Save processed state
with open(STATE_FILE, "w") as f:
    json.dump({"magnets": list(processed)}, f, indent=2)

print("DONE")
