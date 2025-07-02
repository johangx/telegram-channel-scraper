from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
import pandas as pd
import time
import re

TGSTAT_BLOGS_URL = "https://tgstat.com/blogs"

chrome_options = Options()
# To keep the browser open for login, we can't use headless mode.
# chrome_options.add_argument('--headless') 
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

browser = webdriver.Chrome(options=chrome_options)
browser.get(TGSTAT_BLOGS_URL)
browser.maximize_window()

# --- Manual Login Step ---
print("="*80)
print("Please log in to TGStat using your Telegram account in the browser window.")
print("The script is now paused. After you have successfully logged in,")
input("PRESS ENTER HERE TO CONTINUE...")
print("="*80)
print("Resuming script...")

time.sleep(5) # Give the page a moment to settle after login

try:
    modal_close_btns = browser.find_elements(By.CSS_SELECTOR, '.modal .close, .modal .btn-close, [data-dismiss="modal"]')
    for btn in modal_close_btns:
        if btn.is_displayed():
            btn.click()
            time.sleep(1)
except:
    pass

channels = []
unique_names = set()
page = 1
# Let's try to scrape more pages now that we're logged in
max_pages = 20 

while page <= max_pages:
    time.sleep(3)
    print(f"Processing page {page}...")
    if page == 1:
        browser.save_screenshot('debug_blogs_page.png')
        print("Screenshot saved as debug_blogs_page.png")
    channel_containers = browser.find_elements(By.XPATH, '//div[contains(@class, "channel-card")] | //div[contains(@class, "channel-item")]')
    if not channel_containers:
        channel_containers = browser.find_elements(By.CSS_SELECTOR, 'div.row > div.col-12')
    if not channel_containers:
        print("No channel containers found. Trying different approach...")
        all_elements = browser.find_elements(By.XPATH, '//*[contains(text(), "subscribers")]')
        print(f"Found {len(all_elements)} elements containing 'subscribers'")
        break
    print(f"Found {len(channel_containers)} potential channel containers")
    for container in channel_containers:
        try:
            container_text = container.text.strip()
            if not container_text or len(container_text) < 10:
                continue
            subscriber_match = re.search(r'(\d[\d\s]*)\s*subscribers?', container_text, re.IGNORECASE)
            if not subscriber_match:
                continue
            subscribers = int(subscriber_match.group(1).replace(' ', '').replace(',', ''))
            lines = container_text.split('\n')
            name = None
            for line in lines:
                line = line.strip()
                if line and not 'subscribers' in line.lower() and not line.isdigit() and len(line) > 1:
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
            telegram_link = None
            handle_match = re.search(r'/@([\w_]+)', channel_page_link)
            if handle_match:
                handle = handle_match.group(1)
                telegram_link = f"https://t.me/{handle}"
            else:
                if channel_page_link.startswith('/'):
                    telegram_link = "https://tgstat.com" + channel_page_link
                else:
                    telegram_link = channel_page_link
            
            # Extract category information
            category = None
            # Look for category tags/badges in the container
            category_elements = container.find_elements(By.CSS_SELECTOR, '.badge, .tag, .category, [class*="category"], [class*="tag"], [class*="badge"]')
            if category_elements:
                for elem in category_elements:
                    cat_text = elem.text.strip()
                    if cat_text and len(cat_text) > 0 and len(cat_text) < 50:
                        category = cat_text
                        break
            
            # If no category found in badges, try to find it in the text
            if not category:
                for line in lines:
                    line = line.strip()
                    # Look for common category patterns
                    if line and len(line) < 30 and not 'subscribers' in line.lower() and not line.isdigit():
                        # Skip if it's the name or looks like a number
                        if line != name and not re.match(r'^\d+$', line):
                            # Check if it looks like a category (short, no special chars)
                            if re.match(r'^[A-Za-zА-Яа-я\s]+$', line):
                                category = line
                                break
            
            channels.append({
                'name': name,
                'subscribers': subscribers,
                'link': telegram_link,
                'category': category
            })
            unique_names.add(name)
            print(f"Added: {name} - {subscribers:,} subscribers - {telegram_link} - Category: {category}")
        except Exception as e:
            print(f"Error processing container: {e}")
            continue
    print(f"Total channels scraped so far: {len(channels)}")
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    try:
        show_more_btn = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Show more") or contains(text(), "Показать еще")]'))
        )
        browser.execute_script("arguments[0].click();", show_more_btn)
        print("Clicked 'Show more' button.")
        time.sleep(3)
    except TimeoutException:
        print("No 'Show more' button found or it's not clickable. Ending scrape.")
        break
    except Exception as e:
        print(f"Error clicking 'Show more' button: {e}")
        break
    page += 1

browser.quit()

if channels:
    df = pd.DataFrame(channels)
    # Save to a new file to avoid confusion
    df.to_excel('RU_1.xlsx', index=False)
    print(f"\nExported {len(channels)} channels to RU_1.xlsx")
    print("\nFirst 10 channels:")
    for i, channel in enumerate(channels[:10]):
        print(f"{i+1}. {channel['name']} - {channel['subscribers']:,} subscribers - {channel['link']} - Category: {channel['category']}")
else:
    print("\nNo channels were scraped. Check the debug screenshot.") 