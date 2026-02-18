import asyncio
import json
import logging
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Import existing logic (adjust imports as needed based on your project structure)
from config import RESULTS_BY_URL, LINKS_FILE
from run import main_async as run_scraper_main
from aggregate import aggregate_results, CSV_PATH, ALL_JSON_PATH

app = FastAPI()

# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# State
SCRAPER_RUNNING = False
TOTAL_URLS = 0
CURRENT_TASK: asyncio.Task | None = None

def count_urls():
    """Count total URLs in links file for progress tracking."""
    try:
        if LINKS_FILE.exists():
            with open(LINKS_FILE, "r") as f:
                return len([line for line in f if line.strip()])
    except Exception:
        return 0
    return 0

# Initialize total count
TOTAL_URLS = count_urls()

async def run_scraper_wrapper():
    global SCRAPER_RUNNING
    SCRAPER_RUNNING = True
    try:
        # Import inside to avoid circular deps if any
        from scraper import run_scraper_async
        
        # Re-read config/args
        limit = 165 
        concurrency = 5
        
        print(f"Starting scraper task... Links file: {LINKS_FILE}")
        if not LINKS_FILE.exists():
            print(f"ERROR: Links file not found at {LINKS_FILE}")
            
        await run_scraper_async(
            limit=limit,
            links_path=LINKS_FILE,
            out_dir=RESULTS_BY_URL,
            delay_sec=0.0,
            use_mock=False,
            concurrency=concurrency
        )
        
        # 3. Aggregate
        print("Aggregating results...")
        try:
            aggregate_results()
            print(f"Aggregation complete. Checking file: {Path('results/all_prices.json').absolute()}")
            if not Path('results/all_prices.json').exists():
                print("ERROR: all_prices.json not found after aggregation!")
        except Exception as agg_e:
            print(f"Aggregation failed: {agg_e}")
            
    except asyncio.CancelledError:
        print("Scraper task was CANCELLED.")
    except Exception as e:
        print(f"Scraper task failed: {e}")
    finally:
        SCRAPER_RUNNING = False
        print("Scraper task finished/stopped.")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/api/start")
async def start_scraper():
    global SCRAPER_RUNNING, CURRENT_TASK
    if SCRAPER_RUNNING:
        return {"status": "error", "message": "Scraper is already running."}
    
    # Reset aggregated file if exists to avoid showing old data
    master_json = Path("results/all_prices.json")
    if master_json.exists():
        master_json.unlink()

    # Clear individual results? Optional.
    if RESULTS_BY_URL.exists():
        for f in RESULTS_BY_URL.glob("*.json"):
            f.unlink()
            
    CURRENT_TASK = asyncio.create_task(run_scraper_wrapper())
    return {"status": "started", "message": "Scraping process started."}

@app.post("/api/stop")
async def stop_scraper():
    global SCRAPER_RUNNING, CURRENT_TASK
    if not SCRAPER_RUNNING or not CURRENT_TASK:
        return {"status": "error", "message": "Scraper is not running."}
    
    print("Stopping scraper task...")
    CURRENT_TASK.cancel()
    # Wait for cancel to propagate? No need, async will handle.
    return {"status": "stopped", "message": "Scraper task cancellation requested."}

@app.get("/api/check_one")
async def check_one(query: str):
    """
    Find a URL matching 'query' in links file and scrape it immediately.
    Returns the result.
    """
    if not query:
        return {"error": "Query parameter required."}
    
    # 1. Search for URL
    target_url = None
    if LINKS_FILE.exists():
        with open(LINKS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                # Simple case-insensitive match
                if query.lower() in line.lower():
                    target_url = line
                    break
    
    if not target_url:
        return {"error": f"No URL found matching '{query}' in links list."}

    # 2. Scrape it
    from scraper import scrape_one_async
    try:
        # Force re-scrape (out_dir=None prevents loading from cache, 
        # OR we can let it cache but we want fresh? User said "check one by one", likely implies fresh.)
        # Let's use out_dir=None to force fresh fetch logic mostly, but wait, scraper uses out_dir to save too.
        # We can just call _scrape_logic directly or pass None for out_dir to avoid cache READ, 
        # but we might want to SAVE it?
        # Let's act like a fresh probe.
        print(f"Checking single URL: {target_url}")
        
        # We need to import the internal logic or use the wrapper. 
        # scrape_one_async checks cache if out_dir is passed. 
        # Let's pass None for out_dir to ignore cache and get fresh data.
        result = await scrape_one_async(target_url, use_mock=False, out_dir=None)
        
        # Return as dict
        return result.model_dump()
        
    except Exception as e:
        return {"error": f"Scrape failed: {str(e)}"}

@app.get("/api/status")
async def get_status():
    """Check progress by counting generated JSON files."""
    processed = 0
    if RESULTS_BY_URL.exists():
        processed = len(list(RESULTS_BY_URL.glob("*.json")))
    
    # Calculate percentage (approximate)
    total = TOTAL_URLS if TOTAL_URLS > 0 else 165
    progress = min(100, int((processed / total) * 100))
    
    state = "running" if SCRAPER_RUNNING else "idle"
    if not SCRAPER_RUNNING and processed > 0 and processed >= (total - 5): 
        # approximate completion check
        state = "done"
    elif not SCRAPER_RUNNING and processed == 0:
        state = "idle"
        
    return {
        "state": state,
        "processed": processed,
        "total": total,
        "progress": progress
    }

@app.get("/api/results")
async def get_results():
    master_json = Path("results/all_prices.json")
    if master_json.exists():
        try:
            data = json.loads(master_json.read_text(encoding="utf-8"))
            return data
        except Exception as e:
            return {"error": str(e)}
    return {"error": "No results found yet."}

@app.get("/api/download/csv")
async def download_csv():
    if CSV_PATH.exists():
        return FileResponse(CSV_PATH, media_type="text/csv", filename="prices_flat.csv")
    return {"error": "CSV file not found. Please run the scraper first."}

@app.get("/api/download/json")
async def download_json():
    if ALL_JSON_PATH.exists():
        return FileResponse(ALL_JSON_PATH, media_type="application/json", filename="all_prices.json")
    return {"error": "JSON file not found. Please run the scraper first."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
