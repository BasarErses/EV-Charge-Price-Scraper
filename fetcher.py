"""Fetch web page and return cleaned text for AI extraction using Async Playwright."""
import re
import asyncio
from urllib.parse import urlparse

# Use async API for concurrency
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

from config import MAX_PAGE_CHARS, REQUEST_TIMEOUT


async def fetch_page(url: str) -> tuple[str | None, str | None]:
    """
    Fetch URL using Async Playwright (headless) to handle JavaScript rendering.
    Return (text_content, error_message).
    """
    url = url.strip()
    if not url or not url.startswith("http"):
        return None, "Invalid URL"

    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            
            # Create context with realistic User-Agent
            # Create context with realistic User-Agent
            # Matching debug_connection.py which worked
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            # Go to page
            to_ms = (REQUEST_TIMEOUT or 30) * 1000
            
            try:
                # Retry logic for network errors
                max_retries = 3
                response = None
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        # Wait for domcontentloaded
                        response = await page.goto(url, timeout=to_ms, wait_until="domcontentloaded")
                        last_error = None
                        break # Success
                    except Exception as e:
                        last_error = e
                        print(f"Attempt {attempt+1} failed for {url}: {e}. Retrying...")
                        await asyncio.sleep(2) # Wait a bit before retry
                
                if last_error:
                    await browser.close()
                    return None, f"Failed after {max_retries} attempts: {last_error}"

                if not response:
                    await browser.close()
                    return None, "No response from page"
                
                # Check status
                if response.status >= 400:
                    status = response.status
                    await browser.close()
                    return None, f"HTTP Error {status}"

                # Robust wait for dynamic content (animations, loaders)
                try:
                    # Wait for network idle to ensure initial assets load
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except PlaywrightTimeoutError:
                    pass  # Proceed even if network doesn't settle completely

                # Scroll down in chunks to trigger intersection observers/lazy loading
                # Human-like scrolling
                last_height = await page.evaluate("document.body.scrollHeight")
                for i in range(1, 6): # Scroll in 5 steps
                    await page.evaluate(f"window.scrollTo(0, {last_height * i / 5})")
                    await page.wait_for_timeout(800) # Wait a bit at each scroll position
                
                # Wait at the bottom for animations to finish
                if "evroad" in url or "magicline" in url:
                    await page.wait_for_timeout(5000) 
                else:
                    await page.wait_for_timeout(2000)
                
                # Scroll back up a bit? No, usually prices are in body. 
                # Sometimes content is at top, but usually scrolling down doesn't unload top content.
                # But let's verify if we need to scroll up. 
                # For safety, let's scroll back up slightly or just leave it. 
                # Some infinite scrolls might hide top content.
                # Let's simple capture content now.

                # Additional fixed small delay for JS animations (e.g. counters)
                # Increase this for known slow sites
                if "evroad" in url or "magicline" in url:
                    await page.wait_for_timeout(8000) # Wait 8s for counters to finish
                else:
                    await page.wait_for_timeout(3000)
                
            except PlaywrightTimeoutError:
                await browser.close()
                return None, "Timeout loading page"
            except Exception as e:
                await browser.close()
                return None, str(e)

            # Get the full HTML content
            html = await page.content()
            
            await browser.close()

            # Clean and trim (CPU bound, fast enough to be sync here or offloaded if needed)
            # html_to_text is synchronous but fast
            text = html_to_text(html)
            if len(text) > MAX_PAGE_CHARS:
                text = text[:MAX_PAGE_CHARS] + "\n\n[... content trimmed ...]"
            
            return text, None

    except Exception as e:
        return None, f"Playwright system error: {str(e)}"


def html_to_text(html: str) -> str:
    """Extract readable text from HTML, remove scripts/styles."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove clutter
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe", "svg"]):
        tag.decompose()
        
    # Get text
    text = soup.get_text(separator="\n", strip=True)
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def url_to_provider_name(url: str) -> str:
    """Derive a short provider name from URL (e.g. econ.net.tr)."""
    try:
        netloc = urlparse(url.strip()).netloc or ""
        # remove www.
        if netloc.lower().startswith("www."):
            netloc = netloc[4:]
        return netloc.split(".")[0] if netloc else "unknown"
    except Exception:
        return "unknown"
