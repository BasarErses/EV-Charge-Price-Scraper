"""CLI: run the price scraper on URLs from the links file."""
import argparse
import asyncio
import sys
from pathlib import Path

from config import AI_PROVIDER, ANTHROPIC_API_KEY, GEMINI_API_KEY, LINKS_FILE, OLLAMA_MODEL, RESULTS_BY_URL
from scraper import run_scraper_async


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Scrape prices from URLs using Playwright + AI.")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Max number of URLs to scrape (default: 5)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent tabs/requests (default: 5)",
    )
    parser.add_argument(
        "--links",
        type=Path,
        default=LINKS_FILE,
        help="Path to file with one URL per line",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=RESULTS_BY_URL,
        help="Directory for per-URL JSON output",
    )
    parser.add_argument(
        "--no-delay",
        action="store_true",
        help="Disable delay (built-in to concurrency control now, but kept for compat)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use fake AI responses (no API key); good for testing fetching loops",
    )
    args = parser.parse_args()

    if not args.mock:
        if AI_PROVIDER == "ollama":
            print(f"Using Ollama (local) — model: {OLLAMA_MODEL}")
        elif AI_PROVIDER == "claude":
            if not ANTHROPIC_API_KEY:
                print("Error: ANTHROPIC_API_KEY required for Claude. Set in .env or use --mock.", file=sys.stderr)
                sys.exit(1)
            print("Using Claude for extraction.")
        else:
            if not GEMINI_API_KEY:
                print("Error: GEMINI_API_KEY required for Gemini. Set in .env or use --mock.", file=sys.stderr)
                sys.exit(1)
            print("Using Gemini for extraction.")

    # Delay param is less relevant with concurrency but can be passed
    delay = 0.0 if args.no_delay else 1.0
    
    results = await run_scraper_async(
        limit=args.limit,
        links_path=args.links,
        out_dir=args.out_dir,
        delay_sec=delay,
        use_mock=args.mock,
        concurrency=args.concurrency
    )
    print(f"\nDone. {len(results)} URL(s) processed. Output: {args.out_dir}")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
