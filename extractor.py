"""AI extraction: send page content to Claude, Gemini, or Ollama (local) and parse JSON result."""
import json
import re
import time

import requests

from config import (
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    EXTRACTION_RETRIES,
    EXTRACTION_RETRY_DELAY_SEC,
    GEMINI_API_KEY,
    OLLAMA_HOST,
    OLLAMA_MODEL,
)
from models import PriceRow, ProviderPrice
from prompts import EXTRACTION_SYSTEM, build_extraction_prompt, EXAMPLE_PRICE_AC, EXAMPLE_PRICE_DC


def _parse_json_from_response(text: str) -> dict | None:
    """Try to extract JSON from model output (handle markdown code blocks)."""
    text = text.strip()
    # Strip markdown code block if present
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            text = text[start:end]
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            text = text[start:end]
    # Find first { ... } block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        text = match.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            # Simple cleanup for common LLM JSON errors (trailing commas)
            text = re.sub(r",\s*([\]}])", r"\1", text)
            return json.loads(text)
        except json.JSONDecodeError:
            return None


def extract_with_claude(url: str, content: str) -> ProviderPrice:
    """Use Anthropic Claude to extract prices from page content (with retries)."""
    if not ANTHROPIC_API_KEY:
        return ProviderPrice(
            provider_name=url.split("/")[2] if "://" in url else "unknown",
            source_url=url,
            status="failed",
            error="ANTHROPIC_API_KEY not set",
        )
    try:
        from anthropic import Anthropic
    except ImportError:
        return ProviderPrice(
            provider_name=url.split("/")[2] if "://" in url else "unknown",
            source_url=url,
            status="failed",
            error="anthropic package not installed",
        )

    client = Anthropic()
    user_message = build_extraction_prompt(url, content)
    last_error = None
    for attempt in range(EXTRACTION_RETRIES):
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                system=EXTRACTION_SYSTEM,
                messages=[{"role": "user", "content": user_message}],
            )
            text = response.content[0].text if response.content else ""
            data = _parse_json_from_response(text)
            return _dict_to_provider_price(url, data, text)
        except Exception as e:
            last_error = e
            if attempt < EXTRACTION_RETRIES - 1:
                time.sleep(EXTRACTION_RETRY_DELAY_SEC)
    return ProviderPrice(
        provider_name=url.split("/")[2] if "://" in url else "unknown",
        source_url=url,
        status="failed",
        error=str(last_error)[:500],
    )


def extract_with_gemini(url: str, content: str) -> ProviderPrice:
    """Use Google Gemini to extract prices from page content (with retries)."""
    if not GEMINI_API_KEY:
        return ProviderPrice(
            provider_name=url.split("/")[2] if "://" in url else "unknown",
            source_url=url,
            status="failed",
            error="GEMINI_API_KEY not set",
        )
    try:
        import google.generativeai as genai
    except ImportError:
        return ProviderPrice(
            provider_name=url.split("/")[2] if "://" in url else "unknown",
            source_url=url,
            status="failed",
            error="google-generativeai package not installed",
        )

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    user_message = build_extraction_prompt(url, content)
    last_error = None
    for attempt in range(EXTRACTION_RETRIES):
        try:
            response = model.generate_content(
                EXTRACTION_SYSTEM + "\n\n" + user_message,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048,
                ),
            )
            text = (getattr(response, "text", None) or "").strip()
            if not text and response.candidates:
                part = response.candidates[0].content.parts[0] if response.candidates[0].content.parts else None
                text = (getattr(part, "text", None) or "").strip()
            if not text:
                last_error = ValueError("Empty or blocked model response")
                continue
            data = _parse_json_from_response(text)
            return _dict_to_provider_price(url, data, text)
        except Exception as e:
            last_error = e
            if attempt < EXTRACTION_RETRIES - 1:
                time.sleep(EXTRACTION_RETRY_DELAY_SEC)
    return ProviderPrice(
        provider_name=url.split("/")[2] if "://" in url else "unknown",
        source_url=url,
        status="failed",
        error=str(last_error)[:500],
    )


def extract_with_ollama(url: str, content: str) -> ProviderPrice:
    """Use local Ollama LLM to extract prices (no API key). Requires Ollama running and a model pulled."""
    user_message = build_extraction_prompt(url, content)
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        "options": {
            "temperature": 0.1,  # Lower temp for more deterministic code output
        }
    }
    last_error = None
    for attempt in range(EXTRACTION_RETRIES):
        try:
            r = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json=payload,
                timeout=120,
            )
            r.raise_for_status()
            data_resp = r.json()
            text = (data_resp.get("message") or {}).get("content") or ""
            text = text.strip()
            if not text:
                last_error = ValueError("Empty Ollama response")
                continue
            data = _parse_json_from_response(text)
            return _dict_to_provider_price(url, data, text)
        except requests.RequestException as e:
            last_error = e
            if attempt < EXTRACTION_RETRIES - 1:
                time.sleep(EXTRACTION_RETRY_DELAY_SEC)
        except Exception as e:
            last_error = e
            if attempt < EXTRACTION_RETRIES - 1:
                time.sleep(EXTRACTION_RETRY_DELAY_SEC)
    return ProviderPrice(
        provider_name=url.split("/")[2] if "://" in url else "unknown",
        source_url=url,
        status="failed",
        error=str(last_error)[:500] if last_error else "Ollama request failed",
    )


def _parse_price(val: any) -> float:
    """Robustly parse price from string/float/int."""
    if isinstance(val, (int, float)):
        return float(val)
    if not val:
        return 0.0
    
    s = str(val).strip().lower()
    # Normalize comma to dot if looks like European structure "4,50" -> "4.50"
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    # If both, remove dots (thousands) and replace comma with dot
    elif "," in s and "." in s:
         # e.g. "1.234,56" -> "1234.56"
         if s.rfind(",") > s.rfind("."):
             s = s.replace(".", "").replace(",", ".")
         else:
             # e.g. "1,234.56" -> "1234.56"
             s = s.replace(",", "")
    
    # Remove currency symbols and text
    s = re.sub(r"[^\d.]", "", s)
    try:
        return float(s)
    except ValueError:
        return 0.0


def _dict_to_provider_price(url: str, data: dict | None, raw_text: str) -> ProviderPrice:
    """Convert parsed JSON dict to ProviderPrice model."""
    if not data:
        return ProviderPrice(
            provider_name=url.split("/")[2] if "://" in url else "unknown",
            source_url=url,
            status="failed",
            error="AI response was not valid JSON",
            raw_notes=raw_text[:500] if raw_text else None,
        )
    try:
        prices = []
        hallucination_detected = False
        
        for p in data.get("prices") or []:
            if isinstance(p, dict):
                p_val = _parse_price(p.get("price", 0))
                
                # Check for hallucination (values from few-shot example)
                if abs(p_val - EXAMPLE_PRICE_AC) < 0.01 or abs(p_val - EXAMPLE_PRICE_DC) < 0.01:
                    hallucination_detected = True
                    continue # Skip this fake price
                
                # Check for discount false positives (e.g. "%5 indirim")
                # If the AI extracted it as a price but the note says "discount" or "indirim", skip it.
                note_lower = (p.get("note") or "").lower()
                if "indirim" in note_lower or "discount" in note_lower:
                    continue
                
                # Skip clearly invalid 0 prices if extraction failed, unless noted as free?
                # Actually keeping 0 is safer if the model explicitly said 0.
                
                prices.append(
                    PriceRow(
                        kw_range=str(p.get("kw_range", "")).strip() or "—",
                        unit=str(p.get("unit", "kWh")).strip() or "kWh",
                        price=p_val,
                        note=p.get("note") if p.get("note") else None,
                    )
                )
        
        status = "success"
        error = None
        if not prices:
            status = "no_data"
            if hallucination_detected:
                # If we filtered everything out because it was fake, it means no real data was found
                # We can optionally tag the error
                # error = "Hallucination detected (examples returned)"
                pass

        return ProviderPrice(
            provider_name=(data.get("provider_name") or "").strip() or url.split("/")[2],
            source_url=url,
            currency=(data.get("currency") or "TRY").strip().upper(),
            prices=prices,
            raw_notes=data.get("raw_notes") if data.get("raw_notes") else None,
            status=status,
            error=error,
        )
    except (TypeError, ValueError) as e:
        return ProviderPrice(
            provider_name=(data.get("provider_name") or url.split("/")[2]),
            source_url=url,
            status="failed",
            error=str(e),
            raw_notes=raw_text[:500] if raw_text else None,
        )


# Sample price rows for mock; number used per URL varies (2–5) so schema supports variable length
_MOCK_PRICE_POOL: list[PriceRow] = [
    PriceRow(kw_range="AC 7 kW", unit="kWh", price=3.8, note=None),
    PriceRow(kw_range="AC 11 kW", unit="kWh", price=4.0, note=None),
    PriceRow(kw_range="AC 7-22 kW", unit="kWh", price=4.5, note=None),
    PriceRow(kw_range="DC 50 kW", unit="kWh", price=6.5, note=None),
    PriceRow(kw_range="DC 50-150 kW", unit="kWh", price=8.0, note=None),
    PriceRow(kw_range="DC 150+ kW", unit="kWh", price=9.5, note=None),
    PriceRow(kw_range="Üyelik / Aylık", unit="TRY/ay", price=49.0, note="Aylık sabit ücret"),
]


def extract_mock(url: str, content: str) -> ProviderPrice:
    """Return fake extraction (no API key). Use for testing the full flow. Price row count varies per URL (2–5)."""
    from fetcher import url_to_provider_name

    name = url_to_provider_name(url)
    # Deterministic but varying count per URL: 2–5 rows (stable across runs)
    seed = sum(ord(c) for c in url) % 4
    n = min(2 + seed, len(_MOCK_PRICE_POOL))
    prices = list(_MOCK_PRICE_POOL[:n])
    return ProviderPrice(
        provider_name=name,
        source_url=url,
        currency="TRY",
        prices=prices,
        raw_notes="[MOCK] No API call; sample data only.",
        status="success",
    )


def extract(url: str, content: str, use_mock: bool = False) -> ProviderPrice:
    """Run extraction with configured AI provider (Claude, Gemini, or Ollama), or mock if use_mock."""
    if use_mock:
        return extract_mock(url, content)
    if AI_PROVIDER == "gemini":
        return extract_with_gemini(url, content)
    if AI_PROVIDER == "ollama":
        return extract_with_ollama(url, content)
    return extract_with_claude(url, content)
