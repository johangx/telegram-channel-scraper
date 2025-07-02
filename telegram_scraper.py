import requests
import pandas as pd
from typing import List, Dict
import time
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class TGStatScraper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tgstat.ru"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    def get_crypto_channels(self) -> List[Dict]:
        """Fetch crypto channels from TGStat"""
        channels = []
        offset = 0
        limit = 50  # Maximum allowed by API

        while True:
            try:
                # Using the channels/search endpoint as per documentation
                url = f"{self.base_url}/channels/search"
                params = {
                    "token": self.api_key,
                    "q": "a",
                    "country": "RU",
                    "offset": offset,
                    "limit": limit
                }
                
                print(f"Fetching channels (offset: {offset})...")
                response = requests.get(url, params=params)
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 401:
                    print("Authentication failed. Please check your API key.")
                    break
                elif response.status_code == 403:
                    print("Access forbidden. Please check your API permissions.")
                    break
                elif response.status_code == 429:
                    print("Rate limit exceeded. Waiting before retrying...")
                    time.sleep(5)
                    continue
                
                response.raise_for_status()
                data = response.json()

                if not data.get("ok"):
                    print(f"API Error: {data.get('error', 'Unknown error')}")
                    break

                items = data.get("response", {}).get("items", [])
                if not items:
                    print("No more items found.")
                    break

                for channel in items:
                    # Extract basic channel info
                    channel_info = {
                        "name": channel.get("title", ""),
                        "telegram_link": f"https://t.me/{channel.get('username', '')}",
                        "subscribers": channel.get("participants_count", 0),
                        "language": channel.get("language", "Unknown"),  # Extract language if available
                        "category": channel.get("category", {}).get("title", "Unknown")  # Extract category if available
                    }
                    
                    # Get detailed channel info (including creation date) to calculate age
                    channel_id = channel.get("id")
                    if channel_id:
                        detailed_info = self.get_channel_info(channel_id)
                        if detailed_info:
                            created_at = detailed_info.get("created_at")
                            if created_at:
                                age_months = self.calculate_age_months(created_at)
                                channel_info["age_months"] = age_months
                            else:
                                channel_info["age_months"] = "Unknown"
                        else:
                            channel_info["age_months"] = "Unknown"
                    else:
                        channel_info["age_months"] = "Unknown"
                    
                    channels.append(channel_info)
                    print(f"Added channel: {channel_info['name']}")

                if len(items) < limit:
                    print("Reached last page.")
                    break

                offset += limit
                time.sleep(1)  # Rate limiting

            except requests.exceptions.RequestException as e:
                print(f"Error fetching data: {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    print(f"Error response: {e.response.text}")
                break

        return channels

    def get_channel_info(self, channel_id: str) -> Dict:
        """Fetch detailed channel info including creation date"""
        try:
            url = f"{self.base_url}/channels/info"
            params = {
                "token": self.api_key,
                "channel_id": channel_id
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("ok"):
                return data.get("response", {})
            else:
                print(f"API Error fetching channel info: {data.get('error', 'Unknown error')}")
                return {}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching channel info: {e}")
            return {}

    def calculate_age_months(self, created_at: str) -> int:
        """Calculate channel age in months based on creation date"""
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.now()
            age_days = (now - created_date).days
            return age_days // 30  # Approximate months
        except Exception as e:
            print(f"Error calculating age: {e}")
            return 0

    def print_available_categories(self):
        """Fetch and print all available categories from TGStat API"""
        url = f"{self.base_url}/database/categories"
        params = {"token": self.api_key}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("ok"):
                print("Available categories:")
                for cat in data["response"]:
                    print(f"ID: {cat['id']}, Title: {cat['title']}")
            else:
                print(f"API Error fetching categories: {data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Error fetching categories: {e}")

def main():
    # Initialize scraper with API key
    api_key = "d5032d33f61a0ae09e2f5ea7ded76acd"
    scraper = TGStatScraper(api_key)

    # Print available categories
    scraper.print_available_categories()

    # Get channels
    print("Fetching crypto channels...")
    channels = scraper.get_crypto_channels()

    if channels:
        # Create DataFrame
        df = pd.DataFrame(channels)
        
        # Export to Excel
        output_file = "telegram_channels.xlsx"
        df.to_excel(output_file, index=False)
        print(f"Data exported to {output_file}")
        print(f"Total channels scraped: {len(channels)}")
    else:
        print("No channels were scraped. Please check your API key and permissions.")

if __name__ == "__main__":
    main() 