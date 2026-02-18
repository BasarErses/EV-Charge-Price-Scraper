import asyncio
from fetcher import fetch_page

async def main():
    urls = ["https://evroad.com.tr/", "https://magiclinesarj.com/"]
    for url in urls:
        print(f"Fetching {url}...")
        text, err = await fetch_page(url)
        if err:
            print(f"Error: {err}")
        else:
            print(f"--- CONTENT START ({url}) ---")
            print(text[:4000]) # Print first 4000 chars
            print("--- CONTENT END (truncated) ---")
            print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
