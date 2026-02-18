import asyncio
import requests
import subprocess
from playwright.async_api import async_playwright

URL = "https://ekosmobility.com"

def test_curl():
    print(f"\n--- Testing CURL ({URL}) ---")
    try:
        # standard curl with -I for headers
        result = subprocess.run(["curl", "-I", "-L", "--max-time", "10", URL], capture_output=True, text=True)
        print("Return Code:", result.returncode)
        print("Output:\n", result.stdout[:500])
        if result.stderr:
            print("Error:\n", result.stderr[:500])
    except Exception as e:
        print(f"CURL failed: {e}")

def test_requests():
    print(f"\n--- Testing Python requests ({URL}) ---")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(URL, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Content Length: {len(resp.text)}")
    except Exception as e:
        print(f"Requests failed: {e}")

async def test_playwright(headless=True):
    mode = "HEADLESS" if headless else "HEADED"
    print(f"\n--- Testing Playwright {mode} ({URL}) ---")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                response = await page.goto(URL, timeout=15000, wait_until="domcontentloaded")
                if response:
                    print(f"Status: {response.status}")
                    print(f"Title: {await page.title()}")
                else:
                    print("No response object returned.")
            except Exception as e:
                print(f"Playwright navigation failed: {e}")
                
            await browser.close()
        except Exception as e:
            print(f"Playwright launch failed: {e}")

async def main():
    test_curl()
    test_requests()
    await test_playwright(headless=True)
    # await test_playwright(headless=False) # Cannot run headed in this environment usually, but let's try headless first.

if __name__ == "__main__":
    asyncio.run(main())
