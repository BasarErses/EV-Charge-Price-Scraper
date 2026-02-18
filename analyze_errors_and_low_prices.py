import json
from collections import defaultdict

def analyze():
    try:
        with open("results/all_prices.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("results/all_prices.json not found.")
        return

    failed_sites = []
    zero_price_sites = [] 
    
    for item in data:
        url = item.get("source_url", "unknown")
        provider = item.get("provider_name", "unknown")
        status = item.get("status")
        error = item.get("error")
        prices = item.get("prices", [])

        # 1. Check for Failed / No Data
        if status != "success":
            failed_sites.append(f"- {provider} ({url}): {status} - {error}")
            continue

        # 2. Check for 0.0 Prices (Success but price is 0)
        # We only care if ALL prices are 0, or if there are specific 0 entries that look wrong.
        # Let's list any site that has at least one 0.0 price.
        found_zero = False
        zero_entries = []
        for p in prices:
            try:
                price_val = float(p.get("price", 0))
                if price_val == 0.0:
                    found_zero = True
                    zero_entries.append(f"{p.get('kw_range')}: 0.0 {p.get('unit')}")
            except (ValueError, TypeError):
                continue
        
        if found_zero:
            details = ", ".join(zero_entries)
            zero_price_sites.append(f"- {provider} ({url}): {details}")

    print(f"=== Failed / No Data Sites ({len(failed_sites)}) ===")
    for site in failed_sites:
        print(site)
    
    print(f"\n=== Sites with 0.0 Prices ({len(zero_price_sites)}) ===")
    for site in zero_price_sites:
        print(site)

if __name__ == "__main__":
    analyze()
