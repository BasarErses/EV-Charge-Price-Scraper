import json
import os
from pathlib import Path

def get_low_price_urls():
    results_dir = Path("results/by_url")
    if not results_dir.exists():
        print("results/by_url not found.")
        return

    low_price_urls = []
    deleted_count = 0

    for json_file in results_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                item = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"Error reading {json_file}")
            continue

        prices = item.get("prices", [])
        if not prices:
            continue

        found_low = False
        for p in prices:
            try:
                price = float(p.get("price", 0))
                # Check if price is suspiciously low (e.g. <= 5.5 and > 0)
                if 0 < price <= 5.5: 
                    found_low = True
                    break
            except (ValueError, TypeError):
                continue
        
        if found_low:
            url = item.get("source_url")
            if url:
                low_price_urls.append(url)
                print(f"Deleting bad result for {url} ({json_file.name})")
                json_file.unlink() # Delete the file
                deleted_count += 1

    if low_price_urls:
        print(f"Found and deleted {deleted_count} files with low prices.")
        with open("fix_urls.txt", "w", encoding="utf-8") as f:
            for url in low_price_urls:
                f.write(url + "\n")
        print("Saved URLs to fix_urls.txt")
    else:
        print("No low price URLs found.")

if __name__ == "__main__":
    get_low_price_urls()
