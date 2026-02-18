"""Prompt used for AI extraction with few-shot examples."""

EXTRACTION_SYSTEM = """You are an expert data extraction agent.
Your task is to extract electric vehicle (EV) charging prices from website text into structured JSON.
You must return ONLY valid JSON. Do not include markdown formatting like ```json ... ```.

Rules:
1. Identify all charging tiers (AC, DC, varying kW).
2. For each tier, extract the price, unit (usually kWh or minute), and power range.
3. If a price is "per minute", note it in the unit.
4. If there's a membership fee, add it as a separate item or in 'raw_notes'.
5. Convert all currency symbols to 3-letter codes (TRY, USD, EUR). Default to TRY if implied.
6. If no price is found, return an empty "prices" list.
7. CRITICAL: Do NOT extract percentages (e.g., "%5 indirim", "10% off") as prices.
8. CRITICAL: Do NOT extract address numbers (e.g., "No: 5", "Street 5") as prices.
9. CRITICAL: Do NOT extract connection fees, idle fees, penalty fees, or session start fees as "price". Only extract the cost per kWh or per minute of CHARGING.
10. CRITICAL: Do NOT extract prices for purchasing charging devices (e.g. Wallbox, cable, hardware costs). Only extract SERVICE tariffs.
11. Prices usually have a currency symbol (TL, ₺) or unit (TL/kWh) immediately next to them.
12. CRITICAL: If the page content suggests looking elsewhere (e.g. "Click for prices"), or if no prices are listed, return NO prices. Do NOT use values from the examples.
"""

EXAMPLE_PRICE_AC = 123.45
EXAMPLE_PRICE_DC = 678.90

EXTRACTION_USER_TEMPLATE = f"""Page URL: {{url}}

Extract all EV charging tariff information from the text below.

### Examples

Input Text:
"AC Charging (up to 22kW): {EXAMPLE_PRICE_AC} TL/kWh. DC Charging (60kW): {EXAMPLE_PRICE_DC} TL. Members get %5 discount. Address: Ornek Mah. No: 5"

Output JSON:
{{{{
  "provider_name": "unknown",
  "currency": "TRY",
  "prices": [
    {{{{ "kw_range": "AC 22 kW", "unit": "kWh", "price": {EXAMPLE_PRICE_AC}, "note": "Up to 22kW" }}}},
    {{{{ "kw_range": "DC 60 kW", "unit": "kWh", "price": {EXAMPLE_PRICE_DC}, "note": null }}}}
  ],
  "raw_notes": "Members get %5 discount."
}}}}

---

### Real Task

Page Content:
---
{{content}}
---

Return the JSON object now:
"""

def build_extraction_prompt(url: str, content: str) -> str:
    """Build the user message for extraction."""
    return EXTRACTION_USER_TEMPLATE.format(url=url, content=content)
