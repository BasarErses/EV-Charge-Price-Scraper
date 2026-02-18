"""Orchestrate fetch -> AI extract -> save for many URLs using AsyncIO."""
import asyncio
import re
import time
import functools
import json
from pathlib import Path

from config import LINKS_FILE, RATE_LIMIT_DELAY_SEC, RESULTS_BY_URL
from extractor import extract
from fetcher import fetch_page, url_to_provider_name
from models import ProviderPrice


def slug_from_url(url: str) -> str:
    """Safe filename from URL (domain + path snippet)."""
    url = url.strip().rstrip("/")
    s = re.sub(r"^https?://", "", url, flags=re.I)
    s = re.sub(r"[^\w\-.]", "_", s)[:80]
    return s or "unknown"


def load_urls(links_path: Path | None = None, limit: int | None = None) -> list[str]:
    """Load URLs from links file; skip empty and invalid lines."""
    path = links_path or LINKS_FILE
    if not path.exists():
        return []
    urls = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("http://") or line.startswith("https://"):
                urls.append(line)
                if limit and len(urls) >= limit:
                    break
    return urls


async def scrape_one_async(
    url: str,
    use_mock: bool = False,
    semaphore: asyncio.Semaphore | None = None,
    out_dir: Path | None = None
) -> ProviderPrice:
    """
    Async: fetch with Playwright, extract with AI (in thread), return result.
    Checks if output file already exists to skip re-scraping.
    """
    # Check if already done
    if out_dir:
        slug = slug_from_url(url)
        path = out_dir / f"{slug}.json"
        if path.exists():
            try:
                # Load existing to return it (so it appears in aggregation)
                data = json.loads(path.read_text(encoding="utf-8"))
                existing = ProviderPrice(**data)
                
                # Only return cached if it was a success.
                # If it failed previously, we want to retry!
                if existing.status == "success":
                    return existing
                
                # If it was "no_data" or "failed", proceed to re-scrape
            except Exception:
                pass # If corrupt, re-scrape

    if semaphore:
        async with semaphore:
            return await _scrape_logic(url, use_mock)
    else:
        return await _scrape_logic(url, use_mock)


async def _scrape_logic(url: str, use_mock: bool) -> ProviderPrice:
    """Core logic for scraping one URL."""
    # 1. Async Fetch
    text, err = await fetch_page(url)
    
    if err:
        return ProviderPrice(
            provider_name=url_to_provider_name(url),
            source_url=url,
            status="failed",
            error=err,
        )
    if not text or not text.strip():
        return ProviderPrice(
            provider_name=url_to_provider_name(url),
            source_url=url,
            status="failed",
            error="Empty page content",
        )

    # 2. Extract (AI calls are sync, so run in thread pool)
    loop = asyncio.get_running_loop()
    # partial to pass args cleanly
    extract_func = functools.partial(extract, url, text, use_mock=use_mock)
    
    try:
        # Run extraction in default executor (thread pool)
        result = await loop.run_in_executor(None, extract_func)
    except Exception as e:
        return ProviderPrice(
            provider_name=url_to_provider_name(url),
            source_url=url,
            status="failed",
            error=f"Extraction error: {str(e)}",
        )
        
    result.source_url = url
    return result


def save_result(result: ProviderPrice, out_dir: Path) -> Path:
    """Save ProviderPrice as JSON in out_dir; return path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slug_from_url(result.source_url)
    path = out_dir / f"{slug}.json"
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return path


async def run_scraper_async(
    limit: int = 5,
    links_path: Path | None = None,
    out_dir: Path | None = None,
    delay_sec: float = RATE_LIMIT_DELAY_SEC,
    use_mock: bool = False,
    concurrency: int = 5,
) -> list[ProviderPrice]:
    """
    Main entry point: scrape URLs concurrently using asyncio.
    """
    urls = load_urls(links_path=links_path, limit=limit)
    if not urls:
        print("No URLs to scrape.")
        return []
    
    if use_mock:
        print("(mock mode: no API key, fake price data)")
        
    out = out_dir or RESULTS_BY_URL
    print(f"Starting crawl for {len(urls)} URLs with concurrency={concurrency}...")
    
    semaphore = asyncio.Semaphore(concurrency)
    tasks = []
    
    # Create tasks
    for i, url in enumerate(urls):
        tasks.append(scrape_one_async(url, use_mock=use_mock, semaphore=semaphore, out_dir=out))
        
    # Run all
    results = []
    
    # We want to print progress.
    for f in asyncio.as_completed(tasks):
        result = await f
        # Only save if we just scraped it? Or always overwrite? 
        # If we loaded it from disk, saving again is fine (idempotent).
        # We save to ensure consistency.
        save_result(result, out)
        results.append(result)
        
        # Check if it was fresh or cached (by verifying timestamp strictly? or just context)
        # We'll just print status.
        status_icon = "✅" if result.status == "success" else ("⚠️" if result.status == "no_data" else "❌")
        err_msg = f" ({result.error[:50]}...)" if result.error else ""
        print(f"{status_icon} {result.source_url[:60]}... -> {result.status}: {len(result.prices)} prices{err_msg}")

    return results

# Sync wrapper if needed
def run_scraper(*args, **kwargs):
    return asyncio.run(run_scraper_async(*args, **kwargs))
