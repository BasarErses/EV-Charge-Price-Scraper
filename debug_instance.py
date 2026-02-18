import asyncio
from fetcher import fetch_page

URL = "https://ekosmobility.com"

async def main():
    print(f"--- Simulating repeated fetches for {URL} ---")
    
    for i in range(3):
        print(f"\nAttempt {i+1}...")
        text, err = await fetch_page(URL)
        if err:
            print(f"FAILED: {err}")
        else:
            print(f"SUCCESS: Got {len(text)} chars")

if __name__ == "__main__":
    asyncio.run(main())
