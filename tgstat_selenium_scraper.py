from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import time

# CONFIGURABLE
TGSTAT_URL = "https://tgstat.ru/en/channels/search"
CHANNELS_TO_SCRAPE = 100

# Set up Chrome options
chrome_options = Options()
# chrome_options.add_argument('--headless')  # Commented out for debugging
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Start WebDriver
browser = webdriver.Chrome(options=chrome_options)
browser.get(TGSTAT_URL)
wait = WebDriverWait(browser, 20)
time.sleep(3)

# Set filters
try:
    # Find the label for 'Channel language' and click the next sibling div to open the dropdown
    lang_label = wait.until(EC.presence_of_element_located((By.XPATH, '//label[contains(text(), "Channel language")]')))
    lang_filter_area = lang_label.find_element(By.XPATH, 'following-sibling::div')
    lang_filter_area.click()
    time.sleep(1)
    browser.save_screenshot('debug_after_lang_dropdown.png')
    # Select Russian
    russian_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "select__option") and text()="Russian"]')))
    russian_option.click()
    time.sleep(0.5)
    # Select English
    lang_filter_area.click()
    time.sleep(0.5)
    english_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "select__option") and text()="English"]')))
    english_option.click()
    time.sleep(0.5)
except Exception as e:
    print("[DEBUG] Could not set language filter:", e)
    browser.save_screenshot('debug_language_filter.png')
    browser.quit()
    raise

try:
    # Type: public
    type_select = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@name="type"]')))
    type_select.send_keys('public')
except Exception as e:
    print("[DEBUG] Could not set type filter:", e)
    browser.save_screenshot('debug_type_filter.png')
    browser.quit()
    raise

try:
    # Min subscribers: 10,000
    subs_box = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="subscribers_from"]')))
    subs_box.clear()
    subs_box.send_keys('10000')
except Exception as e:
    print("[DEBUG] Could not set subscribers filter:", e)
    browser.save_screenshot('debug_subs_filter.png')
    browser.quit()
    raise

try:
    # Channel age: 1 month
    age_box = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="age_from"]')))
    age_box.clear()
    age_box.send_keys('1')
except Exception as e:
    print("[DEBUG] Could not set age filter:", e)
    browser.save_screenshot('debug_age_filter.png')
    browser.quit()
    raise

# Submit the filters (the page auto-updates)
time.sleep(3)

# Scrape channels
channels = []
page = 1
while len(channels) < CHANNELS_TO_SCRAPE:
    time.sleep(2)
    channel_blocks = browser.find_elements(By.CSS_SELECTOR, 'div.channel-info__main')
    for block in channel_blocks:
        try:
            name = block.find_element(By.CSS_SELECTOR, 'a.channel-info__title-link').text
            link = block.find_element(By.CSS_SELECTOR, 'a.channel-info__title-link').get_attribute('href')
            subscribers = block.find_element(By.CSS_SELECTOR, 'div.channel-info__subscribers').text.split()[0].replace(',', '')
            try:
                subscribers = int(subscribers)
            except Exception:
                subscribers = None
            category = block.find_element(By.CSS_SELECTOR, 'div.channel-info__tags').text if block.find_elements(By.CSS_SELECTOR, 'div.channel-info__tags') else 'Unknown'
            language = block.find_element(By.CSS_SELECTOR, 'div.channel-info__lang').text if block.find_elements(By.CSS_SELECTOR, 'div.channel-info__lang') else 'Unknown'
            age = block.find_element(By.CSS_SELECTOR, 'div.channel-info__age').text if block.find_elements(By.CSS_SELECTOR, 'div.channel-info__age') else 'Unknown'
            channels.append({
                'name': name,
                'link': link,
                'subscribers': subscribers,
                'category': category,
                'language': language,
                'age': age
            })
            if len(channels) >= CHANNELS_TO_SCRAPE:
                break
        except Exception as e:
            continue
    # Go to next page if needed
    if len(channels) < CHANNELS_TO_SCRAPE:
        next_btns = browser.find_elements(By.CSS_SELECTOR, 'a.pagination__item[rel="next"]')
        if next_btns:
            next_btns[0].click()
            page += 1
        else:
            break

browser.quit()

# Export to Excel
df = pd.DataFrame(channels)
df.to_excel('tgstat_channels_selenium.xlsx', index=False)
print(f"Exported {len(channels)} channels to tgstat_channels_selenium.xlsx") 