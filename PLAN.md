# AI Price Scraper – Comprehensive Plan

## 1. Goal

Build a tool that:
- Takes a list of website URLs (e.g. EV charging / electricity pricing pages)
- Uses AI-powered scraping (e.g. ScrapegraphAI SmartScraper) to extract **price information** and **kW (kilowatt) ranges**
- Outputs structured data (provider name, URL, kW ranges, prices, currency, notes)

---

## 2. Scope

- **Input**: Your `links copy.txt` (~167 URLs) – EV charging and electricity tariff pages (mostly Turkish)
- **Output**: Normalized price tables with kW ranges (e.g. AC 7–22 kW, DC 50–150 kW) and corresponding prices (₺/kWh or similar)
- **Constraints**: API credits (ScrapegraphAI: ~10 credits/page), rate limits, and varying page structures

---

## 3. Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  links.txt      │────▶│  Scraper Engine  │────▶│  Structured     │
│  (URL list)     │     │  (AI + fallback) │     │  Output         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                 │                         │
                                 ▼                         ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Cache / State   │     │  JSON / CSV     │
                        │  (skip done)    │     │  Reports        │
                        └──────────────────┘     └─────────────────┘
```

---

## 4. Tech Stack

| Layer           | Choice                | Purpose                          |
|-----------------|-----------------------|----------------------------------|
| AI Scraping     | ScrapegraphAI (Python)| SmartScraper for price + kW      |
| Language        | Python 3.10+          | Scripts, CLI, optional API       |
| Config / Secrets| `.env` + `python-dotenv` | API key, paths                 |
| Output          | JSON, CSV             | Per-URL and aggregated           |
| Optional        | Requests + BeautifulSoup | Fallback for simple HTML pages |

---

## 5. Data Model

### 5.1 Target Schema (per provider / URL)

```json
{
  "provider_name": "Econ",
  "source_url": "https://econ.net.tr/fiyat-tarifeleri",
  "scraped_at": "2025-02-02T12:00:00Z",
  "currency": "TRY",
  "prices": [
    {
      "kw_range": "AC 7-22 kW",
      "unit": "kWh",
      "price": 4.50,
      "note": "optional description"
    },
    {
      "kw_range": "DC 50-150 kW",
      "unit": "kWh",
      "price": 8.00,
      "note": null
    }
  ],
  "raw_notes": "Optional free text from page",
  "status": "success",
  "error": null
}
```

### 5.2 Aggregated Output

- **Single JSON**: `results/all_prices_YYYY-MM-DD.json` – array of the above objects
- **Single CSV**: `results/prices_flat_YYYY-MM-DD.csv` – one row per (provider, kw_range, price) for easy analysis

---

## 6. Workflow (Step-by-Step)

### Phase 1 – Setup
1. Create Python project with `requirements.txt` (e.g. `scrapegraph-py`, `python-dotenv`, `requests`).
2. Load URLs from `links copy.txt` (skip empty lines and invalid URLs).
3. Store API key in `.env`; load with `python-dotenv`.

### Phase 2 – Scraping Loop
1. **State file**: e.g. `state/scraped_urls.json` – list of URLs already processed (and optionally hash of page to detect changes).
2. For each URL (optionally filtered by pattern or index):
   - If URL in state and “success”, skip (or re-scrape if `--force`).
   - Call SmartScraper with a **fixed user prompt** (see below).
   - Map response to the data model (provider name from URL or from AI, kW ranges, prices).
   - Save one JSON file per URL under e.g. `results/by_url/<slug>.json`.
   - Append to state; optionally write incremental CSV.
3. **Rate limiting**: e.g. 1 request every 2–3 seconds to avoid throttling (and to stay within API limits).
4. **Retries**: 2–3 retries with backoff for 5xx or rate-limit errors.

### Phase 3 – User Prompt (Critical for Quality)

Use a single, clear prompt so the AI consistently returns structure you can parse:

```text
Extract all price and tariff information for electric vehicle (EV) charging or electricity supply.
Focus on:
1. Price per kWh (or per minute if applicable) for different power levels.
2. kW ranges or power levels (e.g. AC 7 kW, AC 22 kW, DC 50 kW, DC 150 kW, etc.).
3. Currency (TRY, EUR, USD).
4. Any membership or monthly fees.
Return a structured list: for each tariff/power level give "kw_range", "price", "unit" (kWh or minute), and optional "note".
If the page has no prices, say so clearly.
```

You can refine this prompt once you see a few real responses.

### Phase 4 – Normalization (Optional but Recommended)
- Normalize `kw_range` strings (e.g. “AC 7-22” → “AC 7-22 kW”) for consistency.
- Convert numeric fields; if AI returns “4,50” or “4.50 TL”, parse to float and set `currency: "TRY"`.
- Deduplicate identical (provider, kw_range, price) rows in aggregated output.

### Phase 5 – Aggregation and Export
1. Read all `results/by_url/*.json`.
2. Build `all_prices_YYYY-MM-DD.json`.
3. Flatten to CSV: columns e.g. `provider_name, source_url, kw_range, price, unit, currency, scraped_at`.
4. Optionally generate a short summary (e.g. `stats.txt`: total URLs, success/fail counts, date).

---

## 7. Project Structure (Suggested)

```text
Price Scraper/
├── .env                    # SGRAPHI_API_KEY=...
├── .gitignore              # .env, results/, state/, __pycache__
├── requirements.txt
├── config.py               # Load .env, paths, prompt text
├── scraper.py              # Main loop: load URLs → call API → save per-URL JSON
├── prompts.py              # User prompt(s) for SmartScraper
├── models.py               # Pydantic/dataclass for ProviderPrice, PriceRow
├── normalize.py            # Normalize kw_range, price, currency
├── aggregate.py            # Merge by_url JSON → one JSON + one CSV
├── run.py                  # CLI: run scraper (optional: --limit, --force, --from-index)
├── links copy.txt          # Input URL list
├── results/
│   ├── by_url/             # One JSON per URL
│   ├── all_prices_*.json
│   └── prices_flat_*.csv
├── state/
│   └── scraped_urls.json   # Progress and status per URL
└── PLAN.md                 # This document
```

---

## 8. Error Handling and Robustness

| Scenario           | Action |
|--------------------|--------|
| Invalid URL        | Log, add to state as `status: "invalid_url"`, skip. |
| Timeout / 5xx      | Retry 2–3 times with backoff; then `status: "failed"`, save error message. |
| Rate limit (429)   | Backoff (e.g. 60 s), retry; then mark failed. |
| No price on page   | Save with `prices: []`, `status: "no_data"`, optional `raw_notes`. |
| API key missing    | Fail fast with clear message. |
| Malformed AI reply | Try to parse what’s possible; set `status: "partial"` and store raw response. |

---

## 9. API Credit Awareness (ScrapegraphAI)

- **~10 credits per page** (confirm in latest docs).
- **167 URLs** → ~1,670 credits per full run.
- Plan: use **state file** so you can stop/resume; use `--limit 20` during development; consider batching and running overnight for full list.

---

## 10. Implementation Order

1. **Setup**: `requirements.txt`, `.env`, `config.py`, `models.py`.
2. **Single-URL test**: One URL with SmartScraper + your prompt; inspect JSON and refine prompt in `prompts.py`.
3. **Scraper loop**: `scraper.py` – read links, state, loop with rate limit and retries, save per-URL JSON.
4. **Normalize**: `normalize.py` – kw_range and price cleanup.
5. **Aggregate**: `aggregate.py` – build all_prices JSON and flat CSV.
6. **CLI**: `run.py` with `--limit`, `--force`, `--from-index`, optional `--url "single url"`.
7. **Docs**: Short README with how to run and where to put the API key.

---

## 11. Optional Enhancements (Later)

- **Fallback scraper**: For known simple HTML tables, use Requests + BeautifulSoup and map to same schema (saves credits).
- **Diff report**: Compare two runs (e.g. `all_prices_2025-02-01.json` vs `2025-02-15.json`) to see price changes.
- **Dashboard**: Simple HTML or Streamlit table of provider vs kW range vs price.
- **Scheduling**: Cron or Task Scheduler to run weekly and append new files.

---

## 12. Success Criteria

- All URLs in `links copy.txt` are processed (success, no_data, or failed).
- Each success/no_data URL has a corresponding JSON in `results/by_url/`.
- One aggregated JSON and one CSV per run with at least (provider, kw_range, price) for every extracted row.
- No API key in code or in git; credentials only in `.env`.

---

You can start with **Phase 1 + Phase 2 (single-URL test)** and then implement the full loop and aggregation. If you share your preferred project layout (e.g. no `aggregate.py`, or different output paths), the plan can be adjusted to match.
