# Project Analysis and Improvement Guideline

## 1. Analysis of Current Implementation

### 1.1. Architecture & Technology
- **Current State**: The project uses a custom implementation combining `requests` + `BeautifulSoup` for fetching and an LLM (Claude/Gemini/Ollama) for extraction.
- **Discrepancy**: The original `PLAN.md` suggested using the `ScrapegraphAI` library, but the actual code implements a custom "fetch-then-prompt" pipeline.
- **Issue - JavaScript Rendering**: The use of `requests` (`fetcher.py`) is the most critical flaw. Many modern websites (especially pricing tables) load data dynamically via JavaScript (React, Vue, Angular, or simple AJAX). `requests` fetches only the static HTML, which often contains loading spinners instead of prices. **This will result in a high failure rate.**

### 1.2. Performance & Scalability
- **Sequential Execution**: `scraper.py` loops through URLs one by one (`for i, url in enumerate(urls)`).
    - If 200 sites take ~30s each (fetch + AI latency + delays), the run will take ~1.6 hours.
    - If errors occur, it could take much longer.
- **Cost/Token Usage**: Sending the entire stripped text of a page to an LLM is token-heavy. While `fetcher.py` attempts to strip scripts and styles, navigation bars and footers often remain, consuming context window and increasing API costs.

### 1.3. Robustness
- **Error Handling**: Basic retries exist for the AI step, but if the `fetcher` returns incomplete HTML (due to JS), the AI will hallucinate or fail.
- **State Management**: The project relies on checking if a JSON file exists to see if a URL is done? Use of a dedicated state file (SQLite or JSON tracker) is cleaner to track "retries needed", "failed", "success", "no data".

## 2. Guideline for Fixes & Improvements

### Phase 1: Fix Core Scraping Capability (Critical)
**Objective**: Ensure the scraper actually sees the data.

1.  **Switch to Browser Automation**:
    -   Replace `requests` with a headless browser tool like **Playwright** or **Selenium**.
    -   *Why*: This allows JavaScript to execute, rendering the actual pricing tables before extraction.
    -   *Action*: Update `fetcher.py` to use `playwright.sync_api` (or async) to `.goto(url)`, wait for network idle or specific selectors, and then get `.inner_text()` or `.content()`.

2.  **Smart Content Cleaning**:
    -   Instead of simple `BeautifulSoup` tag removal, use the browser to identify the "main" content.
    -   Use library like `trafilatura` or `readabilipy` which are specialized in extracting main article text/tables from HTML, reducing token noise significantly.

### Phase 2: Improve Performance (High Priority)
**Objective**: Reduce total runtime.

1.  **Implement Concurrency**:
    -   Use `asyncio` for the main loop.
    -   Allow processing multiple URLs in parallel (e.g., batch size of 5-10).
    -   *Constraint*: Be mindful of LLM API rate limits (TPM/RPM). Implement a `Samephore` to limit concurrent AI calls.

2.  **Caching**:
    -   Cache the raw HTML or extracted text specifically. If the AI extraction fails but the fetch was good, don't re-fetch.

### Phase 3: Enhance AI Extraction
**Objective**: Improve accuracy and structure.

1.  **Refine Prompts**:
    -   Add "Zero-shot" examples to the prompt in `prompts.py`.
    -   Explicitly tell the model to look for "tables" or "lists".
2.  **Validation**:
    -   Use a library like `instructor` (for OpenAI/Anthropic) or straight `Pydantic` validation to ensure the LLM output matches the schema strictly, avoiding `json.loads` errors.

### Phase 4: Aggregation & detailed Reporting
**Objective**: Make the data usable.

1.  **Aggregator Script**:
    -   Create `aggregate.py` to read all individual JSONs and merge them into a master `CSV` / `Excel` file.
    -   Columns: `Provider`, `Range`, `Price`, `Currency`, `Unit`, `Note`, `Source URL`.
2.  **Quality Report**:
    -   Generate a `report.md` showing:
        -   Success Rate
        -   List of URLs with "No data found" (to inspect manually).
        -   List of extraction errors.

## 3. Recommended Implementation Steps

1.  **Update `requirements.txt`**: Add `playwright`, `pytest`, `pandas` (for aggregation).
2.  **Rewrite `fetcher.py`**: Implement `fetch_with_playwright(url)`.
3.  **Refactor `scraper.py`**: Turn `scraper.py` into an `async` script using `asyncio.gather` with a semaphore.
4.  **Create `aggregate.py`**: For final data compilation.
