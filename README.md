# Telegram Channel Scraper

This script scrapes Telegram channels from TGStat's crypto catalog and exports the data to an Excel file.

## Features

- Scrapes channel information including:
  - Channel name
  - Telegram link
  - Number of subscribers
- Exports data to Excel format
- Handles pagination and rate limiting
- Error handling and logging

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the script:
```bash
python telegram_scraper.py
```

## Output

The script will create an Excel file named `telegram_channels.xlsx` in the same directory with the following columns:
- name: Channel name
- telegram_link: Direct link to the channel
- subscribers: Number of subscribers

## Note

The script uses the TGStat API and includes rate limiting to avoid overwhelming the API. Please be mindful of the API usage limits. 