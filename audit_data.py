import json
from collections import defaultdict

def audit_prices():
    try:
        with open("results/all_prices.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("results/all_prices.json not found.")
        return

    suspicious_low = []
    suspicious_high = []
    example_leakage = []
    zero_prices = []
    
    # Thresholds
    MIN_PRICE = 1.0
    MAX_PRICE = 50.0 # Most EV prices in TR are 6-15 TL. 50 is a safe upper bound.
    
    # Known examples from prompt
    EXAMPLES = [123.45, 678.90, 5.0, 5, 22, 60] # 22/60 are kW values sometimes mistaken for price

    for item in data:
        url = item.get("source_url")
        name = item.get("provider_name")
        prices = item.get("prices") or []
        
        for p in prices:
            val = p.get("price")
            if val is None:
                continue
                
            # Check for 0
            if val == 0:
                zero_prices.append((name, url, val))
                continue

            # Check for low (non-zero)
            if val <= MIN_PRICE:
                suspicious_low.append((name, url, val))
            
            # Check for high
            if val > MAX_PRICE:
                suspicious_high.append((name, url, val))
                
            # Check for specific leakage or common mistakes
            if val in EXAMPLES:
                 example_leakage.append((name, url, val))

    print(f"=== Audit Results ({len(data)} providers checked) ===\n")
    
    if suspicious_low:
        print(f"--- Suspiciously Low Prices (<= {MIN_PRICE} but > 0) ---")
        for name, url, val in suspicious_low:
            print(f"[{val}] {name} ({url})")
    else:
        print("--- No Suspiciously Low Prices Found ---")

    print("\n")

    if suspicious_high:
        print(f"--- Suspiciously High Prices (> {MAX_PRICE}) ---")
        for name, url, val in suspicious_high:
            print(f"[{val}] {name} ({url})")
    else:
        print("--- No Suspiciously High Prices Found ---")

    print("\n")

    if example_leakage:
        print("--- Potential Prompt Leakage / Common Misinterpretations ---")
        for name, url, val in example_leakage:
            print(f"[{val}] {name} ({url})")
    else:
        print("--- No Example Leakage Found ---")

    print("\n")
    
    # Group zero prices by provider
    zero_counts = defaultdict(int)
    for name, _, _ in zero_prices:
        zero_counts[name] += 1
        
    if zero_prices:
        print(f"--- Zero Price Entries ({len(zero_counts)} providers) ---")
        for name in zero_counts:
            count = zero_counts[name]
            # Find one url example
            ex_url = next(u for n, u, v in zero_prices if n == name)
            print(f"[{count} entries] {name} ({ex_url})")

if __name__ == "__main__":
    audit_prices()
