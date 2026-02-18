# Price Scraper (AI)

Scrapes given websites and extracts **price information with kW ranges** using **Claude** or **Gemini** (no ScrapegraphAI API). Inspired by SmartScraper-style flow: fetch page → send content to LLM → structured JSON.

## Setup

1. **Create a virtualenv and install dependencies**

   ```bash
   cd "Price Scraper"
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Choose AI provider (no API key with Ollama)**

   Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:

   - **Ollama (local, no API key)**  
     Set `AI_PROVIDER=ollama`. Install [Ollama](https://ollama.com), start it, and pull a model:  
     `ollama pull llama3.1`  
     Optional: `OLLAMA_HOST=http://localhost:11434`, `OLLAMA_MODEL=llama3.1`
   - **Claude**: `AI_PROVIDER=claude` and `ANTHROPIC_API_KEY=sk-ant-...` ([Anthropic Console](https://console.anthropic.com/))
   - **Gemini**: `AI_PROVIDER=gemini` and `GEMINI_API_KEY=...` ([Google AI Studio](https://aistudio.google.com/apikey))

## Run

- **Real extraction (5 URLs, default)**  
  Uses Claude, Gemini, or Ollama according to `AI_PROVIDER` in `.env`. Ollama needs no API key (local LLM).  
  ```bash
  python run.py
  ```

- **Custom limit**  
  ```bash
  python run.py --limit 10
  ```

- **Single URL (e.g. first one)**  
  ```bash
  python run.py --limit 1
  ```

- **No delay between requests (faster, may hit rate limits)**  
  ```bash
  python run.py --limit 5 --no-delay
  ```

- **Test without API key (mock mode)**  
  Fetches real pages but uses fake price data instead of calling Claude/Gemini. No API key needed; still requires `pip install -r requirements.txt`.  
  ```bash
  python run.py --mock --limit 5
  ```

Real runs use retries (3 attempts, 5 s delay) on API errors. Output: one JSON file per URL under `results/by_url/` with `provider_name`, `source_url`, `currency`, and `prices[]` (kw_range, price, unit, note).

## Project layout

- `config.py` – env (API keys, paths, limits)
- `models.py` – Pydantic: `ProviderPrice`, `PriceRow`
- `prompts.py` – extraction prompt for the LLM
- `fetcher.py` – fetch HTML, strip to text
- `extractor.py` – call Claude or Gemini, parse JSON
- `scraper.py` – load URLs, scrape one, save result
- `run.py` – CLI (`--limit`, `--links`, `--out-dir`, `--no-delay`)
- `links copy.txt` – input URL list (one per line)
