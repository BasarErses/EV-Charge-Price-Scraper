"""Aggregate per-URL JSON results into one master CSV and JSON file."""
import csv
import json
from pathlib import Path

from config import RESULTS_BY_URL
from models import ProviderPrice

RESULTS_DIR = RESULTS_BY_URL.parent
ALL_JSON_PATH = RESULTS_DIR / "all_prices.json"
CSV_PATH = RESULTS_DIR / "prices_flat.csv"


def aggregate_results() -> None:
    """Read all JSON files in results/by_url, merge, and save CSV/JSON."""
    if not RESULTS_BY_URL.exists():
        print(f"No results directory found at {RESULTS_BY_URL}")
        return

    json_files = sorted(list(RESULTS_BY_URL.glob("*.json")))
    if not json_files:
        print("No JSON files found to aggregate.")
        return

    all_data = []
    flat_rows = []

    print(f"Aggregating {len(json_files)} files...")

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            # Validate with model (optional but good for consistency)
            # handle cases where models might have changed slightly
            try:
                # If using pydantic
                obj = ProviderPrice(**data)
            except Exception:
                # Fallback if validation fails, just use dict
                obj = None
            
            # Use dict for export
            item = obj.model_dump() if obj else data
            # Filter out suspicious high prices (e.g. hardware costs, hallucinations)
            if "prices" in item and item["prices"]:
                item["prices"] = [p for p in item["prices"] if p.get("price", 0.0) <= 60.0]

            all_data.append(item)

            provider = item.get("provider_name", "unknown")
            url = item.get("source_url", "")
            scraped_at = item.get("scraped_at", "")
            currency = item.get("currency", "TRY")
            status = item.get("status", "unknown")
            error = item.get("error", "")

            # If no prices (or all filtered out), add a row indicating status
            if not item.get("prices"):
                flat_rows.append({
                    "provider": provider,
                    "kw_range": "N/A",
                    "price": 0.0,
                    "unit": "",
                    "currency": currency,
                    "note": f"Status: {status} {error or ''}".strip(),
                    "scraped_at": scraped_at,
                    "url": url
                })
            else:
                for p in item["prices"]:
                    flat_rows.append({
                        "provider": provider,
                        "kw_range": p.get("kw_range", ""),
                        "price": p.get("price", 0.0),
                        "unit": p.get("unit", ""),
                        "currency": currency,
                        "note": p.get("note") or "",
                        "scraped_at": scraped_at,
                        "url": url
                    })

        except Exception as e:
            print(f"Error reading {jf.name}: {e}")

    # Write Master JSON
    ALL_JSON_PATH.write_text(json.dumps(all_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved master JSON to {ALL_JSON_PATH} ({len(all_data)} providers)")

    # Write CSV
    if flat_rows:
        keys = ["provider", "kw_range", "price", "unit", "currency", "note", "scraped_at", "url"]
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(flat_rows)
        print(f"Saved CSV to {CSV_PATH} ({len(flat_rows)} rows)")
    else:
        print("No rows to write to CSV.")


if __name__ == "__main__":
    aggregate_results()
