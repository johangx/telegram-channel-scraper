import pandas as pd

try:
    # Read the Excel file from the filtered scraper
    df = pd.read_excel('tgstat_filtered_channels.xlsx')

    print(f"Total channels scraped: {len(df)}")
    
    if len(df) > 0:
        print("\nFirst 20 channels from the latest run:")
        print("=" * 80)

        for idx, row in df.head(20).iterrows():
            name = row['name']
            subscribers = row['subscribers']
            link = row['link'] if pd.notna(row['link']) else 'N/A'
            
            # Ensure subscribers is treated as a number for formatting
            try:
                sub_count = f"{int(subscribers):,}"
            except (ValueError, TypeError):
                sub_count = subscribers

            print(f"{idx+1:2d}. {name} - {sub_count} subscribers")
            print(f"    Link: {link}")
            print()

        print("\nTop 10 channels by subscriber count:")
        print("=" * 50)
        # Ensure subscribers column is numeric before finding the largest
        df['subscribers'] = pd.to_numeric(df['subscribers'], errors='coerce')
        top_channels = df.nlargest(10, 'subscribers')
        for idx, row in top_channels.iterrows():
            name = row['name']
            subscribers = row['subscribers']
            link = row['link']
            print(f"- {name} ({int(subscribers):,}) - {link}")
    else:
        print("No channels were scraped in the last run. The file is empty.")

except FileNotFoundError:
    print("The results file 'tgstat_filtered_channels.xlsx' was not found.")
except Exception as e:
    print(f"An error occurred while reading the results: {e}") 