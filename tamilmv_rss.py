import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree
import time, json, os, re
from urllib.parse import parse_qs, urlparse

BASE_URL = "https://www.1tamilmv.lc/"
OUT_FILE = "tamilmv.xml"
STATE_FILE = "state.json"

MAX_SIZE_GB = 4  # 🔥 ONLY BELOW 4GB

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

# Load processed magnets
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        state = json.load(f)
else:
    state = {"magnets": []}

processed = set(state.get("magnets", []))

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "1TamilMV Torrent RSS"
SubElement(channel, "link").text = BASE_URL
SubElement(channel, "description").text = "Auto torrent RSS (Below 4GB only)"
SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime(
    "%a, %d %b %Y %H:%M:%S GMT"
)

home = scraper.get(BASE_URL, timeout=30)
soup = BeautifulSoup(home.text, "lxml")

posts = []
for a in soup.select("a[href*='forums/topic']"):
    posts.append((a.get_text(strip=True), a["href"]))

posts = posts[:10]

def magnet_size_gb(magnet):
    qs = parse_qs(urlparse(magnet).query)
    if "xl" in qs:
        size_bytes = int(qs["xl"][0])
        return size_bytes / (1024**3)
    return None

for title, post_url in posts:
    try:
        time.sleep(5)
        page = scraper.get(post_url, timeout=30)
        psoup = BeautifulSoup(page.text, "lxml")

        for a in psoup.find_all("a", href=True):
            h = a["href"]

            if not h.startswith("magnet:?"):
                continue

            if h in processed:
                continue

            size = magnet_size_gb(h)
            if size and size > MAX_SIZE_GB:
                continue  # ❌ skip 4GB+

            item = SubElement(channel, "item")
            SubElement(item, "title").text = f"{title} [{round(size,2)}GB]"
            SubElement(item, "link").text = h
            SubElement(item, "guid").text = h
            SubElement(item, "pubDate").text = datetime.utcnow().strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )

            processed.add(h)
            print("ADDED:", title, size)

    except Exception as e:
        print("ERROR:", title, e)

ElementTree(rss).write(OUT_FILE, encoding="utf-8", xml_declaration=True)

with open(STATE_FILE, "w") as f:
    json.dump({"magnets": list(processed)}, f, indent=2)

print("RSS DONE")
