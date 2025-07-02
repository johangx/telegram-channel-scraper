import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://tgstat.ru/en/channels/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

FILTERS = {
    "lang": ["ru", "en"],
    "type": "public",
    "subscribers_from": "10000",
    "age_from": "1"
}

CHANNELS_TO_SCRAPE = 100


def build_query(page=1):
    params = {
        "page": page,
        "lang": FILTERS["lang"],
        "type": FILTERS["type"],
        "subscribers_from": FILTERS["subscribers_from"],
        "age_from": FILTERS["age_from"]
    }
    return params


def parse_channel_block(block):
    name = block.find("a", class_="channel-info__title-link").get_text(strip=True)
    link = block.find("a", class_="channel-info__title-link")['href']
    if not link.startswith("http"):
        link = "https://tgstat.ru" + link
    subscribers = block.find("div", class_="channel-info__subscribers").get_text(strip=True).split()[0].replace(",", "")
    try:
        subscribers = int(subscribers)
    except Exception:
        subscribers = None
    # Category/Topic
    category_tag = block.find("div", class_="channel-info__tags")
    category = category_tag.get_text(strip=True) if category_tag else "Unknown"
    # Language (from tags)
    lang_tag = block.find("div", class_="channel-info__lang")
    language = lang_tag.get_text(strip=True) if lang_tag else "Unknown"
    # Age (from tags)
    age_tag = block.find("div", class_="channel-info__age")
    age = age_tag.get_text(strip=True) if age_tag else "Unknown"
    return {
        "name": name,
        "link": link,
        "subscribers": subscribers,
        "category": category,
        "language": language,
        "age": age
    }


def scrape_channels():
    channels = []
    page = 1
    while len(channels) < CHANNELS_TO_SCRAPE:
        params = build_query(page)
        response = requests.get(BASE_URL, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch page {page}, status: {response.status_code}")
            break
        soup = BeautifulSoup(response.text, "html.parser")
        channel_blocks = soup.find_all("div", class_="channel-info__main")
        if not channel_blocks:
            print("No more channels found.")
            break
        for block in channel_blocks:
            channel = parse_channel_block(block)
            channels.append(channel)
            if len(channels) >= CHANNELS_TO_SCRAPE:
                break
        print(f"Scraped {len(channels)} channels so far...")
        page += 1
        time.sleep(1)  # Be polite to the server
    return channels


def main():
    print("Starting TGStat web scraping...")
    channels = scrape_channels()
    if channels:
        df = pd.DataFrame(channels)
        df.to_excel("tgstat_channels.xlsx", index=False)
        print(f"Exported {len(channels)} channels to tgstat_channels.xlsx")
    else:
        print("No channels scraped.")

if __name__ == "__main__":
    main() 