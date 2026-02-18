import asyncio
from fetcher import fetch_page

async def main():
    url = "https://www.monokonev.com"
    print(f"Fetching {url}...")
    text, err = await fetch_page(url)
    if err:
        print(f"Error: {err}")
    else:
        print(f"Content length: {len(text)}")
        print("--- CONTENT START ---")
        print(text[:2000]) # Print first 2000 chars
        print("--- CONTENT END (truncated) ---")

if __name__ == "__main__":
    asyncio.run(main())
