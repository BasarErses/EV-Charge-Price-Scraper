import json

def get_failed_urls():
    try:
        with open("results/all_prices.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("results/all_prices.json not found.")
        return

    retry_urls = []
    
    for item in data:
        status = item.get("status")
        # We want to retry 'failed' and maybe 'no_data' if it was due to connection?
        # Actually, let's just retry 'failed' first. 'no_data' might be valid.
        # But wait, looking at previous logs, some 'no_data' might be due to incomplete loading.
        # Let's retry 'failed'.
        if status == "failed":
            url = item.get("source_url")
            if url:
                retry_urls.append(url)

    if retry_urls:
        print(f"Found {len(retry_urls)} failed URLs.")
        with open("retry_urls.txt", "w", encoding="utf-8") as f:
            for url in retry_urls:
                f.write(url + "\n")
        print("Saved to retry_urls.txt")
    else:
        print("No failed URLs found.")

if __name__ == "__main__":
    get_failed_urls()
