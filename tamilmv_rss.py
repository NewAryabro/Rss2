import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree
import time
import re

BASE_URL = "https://www.1tamilmv.lc/"
OUT_FILE = "tamilmv.xml"

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "1TamilMV TORRENT RSS"
SubElement(channel, "link").text = BASE_URL
SubElement(channel, "description").text = "Experimental auto torrent RSS"
SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime(
    "%a, %d %b %Y %H:%M:%S GMT"
)

# STEP 1: Homepage
home = scraper.get(BASE_URL, timeout=30)
soup = BeautifulSoup(home.text, "lxml")

post_links = []

for a in soup.find_all("a", href=True):
    href = a["href"]
    if "forums/topic" in href:
        post_links.append((a.get_text(strip=True), href))

post_links = post_links[:10]  # LIMIT VERY IMPORTANT

for title, post_url in post_links:
    try:
        time.sleep(6)  # anti-ban

        post = scraper.get(post_url, timeout=30)
        psoup = BeautifulSoup(post.text, "lxml")

        torrent = None

        # Find magnet
        for a in psoup.find_all("a", href=True):
            h = a["href"]
            if h.startswith("magnet:?"):
                torrent = h
                break
            if h.endswith(".torrent"):
                torrent = h
                break

        if not torrent:
            continue

        item = SubElement(channel, "item")
        SubElement(item, "title").text = title
        SubElement(item, "link").text = torrent
        SubElement(item, "guid").text = torrent
        SubElement(item, "pubDate").text = datetime.utcnow().strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        print("ADDED:", title)

    except Exception as e:
        print("SKIPPED:", title, e)

ElementTree(rss).write(OUT_FILE, encoding="utf-8", xml_declaration=True)
print("DONE")
