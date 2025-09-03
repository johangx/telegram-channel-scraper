from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import re

# The URL for the advanced search page
TGSTAT_SEARCH_URL = "https://tgstat.com/channels/search"

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

browser = webdriver.Chrome(options=chrome_options)
browser.get(TGSTAT_SEARCH_URL)
browser.maximize_window()

# --- Manual Login and Filter Step ---
print("="*80)
print("The script is now paused. Please follow these steps in the browser window:")
print("1. Log in to your TGStat account if you haven't already.")
print("2. Apply your desired filters (category, country, subscribers, etc.).")
print("3. Click the 'Search' or 'Apply' button on the website to see the results.")
input("4. Once the filtered channel list is displayed, PRESS ENTER HERE TO CONTINUE...")
print("="*80)
print("Resuming script and scraping filtered results...")

time.sleep(3) # Give the results a moment to load

channels = []
unique_names = set()
page = 1
max_pages = 50 # Allow for more pages of filtered results
# Remove the test limit for real run
# max_channels = 10  # Limit for test run

while page <= max_pages:
    print(f"Processing page {page} of filtered results...")
    
    # Using the same reliable selectors from our previous script
    channel_containers = browser.find_elements(By.XPATH, '//div[contains(@class, "channel-card")] | //div[contains(@class, "channel-item")]')
    if not channel_containers:
        # Fallback for different layouts
        channel_containers = browser.find_elements(By.CSS_SELECTOR, 'div.row > div.col-12')

    if not channel_containers and page == 1:
        print("No channel containers found on the page. Please ensure you have run a search.")
        browser.save_screenshot('debug_filtered_search.png')
        print("A screenshot 'debug_filtered_search.png' has been saved.")
        break
    elif not channel_containers:
        print("No more channel containers found.")
        break

    print(f"Found {len(channel_containers)} potential channel containers on this page.")

    for container in channel_containers:
        try:
            container_text = container.text.strip()
            if not container_text or len(container_text) < 10:
                continue

            subscriber_match = re.search(r'(\d[\d\s,]*)\s*subscribers?', container_text, re.IGNORECASE)
            if not subscriber_match:
                continue
            
            subscribers = int(subscriber_match.group(1).replace(' ', '').replace(',', ''))
            
            lines = container_text.split('\n')
            name = None
            for line in lines:
                line = line.strip()
                if line and 'subscribers' not in line.lower() and not line.isdigit() and len(line) > 1:
                    name = line
                    break
            
            if not name or name in unique_names:
                continue

            channel_page_link = None
            link_elements = container.find_elements(By.CSS_SELECTOR, 'a[href*="/channel/"], a[href*="/@"]')
            if link_elements:
                channel_page_link = link_elements[0].get_attribute('href')

            if not channel_page_link:
                continue

            telegram_link = "N/A"
            handle_match = re.search(r'/@([\w_]+)', channel_page_link)
            if handle_match:
                handle = handle_match.group(1)
                telegram_link = f"https://t.me/{handle}"
            
            # Extract category directly from the channel container
            category = "Unknown"
            try:
                category_elem = container.find_element(By.CSS_SELECTOR, 'span.border.rounded.bg-light.px-1')
                if category_elem and category_elem.text.strip():
                    category = category_elem.text.strip()
            except Exception:
                pass

            channels.append({
                'name': name,
                'subscribers': subscribers,
                'link': telegram_link,
                'category': category,
            })
            unique_names.add(name)
            print(f"Added: {name} - {subscribers:,} subscribers - {telegram_link}")
            # Remove the test limit break
            # if len(channels) >= max_channels:
            #     break

        except Exception as e:
            continue
            
    print(f"Total channels scraped so far: {len(channels)}")

    try:
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        show_more_btn = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Show more")] | //a[contains(@class, "page-link") and contains(text(), "›")]'))
        )
        browser.execute_script("arguments[0].click();", show_more_btn)
        print("Clicked 'Show more' or 'Next page' button.")
        time.sleep(3)
    except TimeoutException:
        print("No more pages or 'Show more' button found. Ending scrape.")
        break
    except Exception as e:
        print(f"Error clicking button: {e}")
        break
        
    page += 1

browser.quit()

if channels:
    df = pd.DataFrame(channels)
    df.to_excel('game.xlsx', index=False)
    print(f"\nExported {len(channels)} channels to game.xlsx")
    print("\nFirst 10 channels:")
    df_sorted = df.sort_values(by='subscribers', ascending=False)
    for i, (_, channel) in enumerate(df_sorted.head(10).iterrows()):
        print(f"{i+1}. {channel['name']} - {channel['subscribers']:,} subscribers - {channel['link']}")
else:
    print("\nNo channels were scraped.") 