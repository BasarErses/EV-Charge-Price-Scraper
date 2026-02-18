import json
from collections import Counter

def analyze():
    with open("results/all_prices.json", "r") as f:
        data = json.load(f)

    status_counts = Counter()
    error_counts = Counter()
    no_data_urls = []
    failed_urls = []
    suspicious_prices = []

    for item in data:
        status = item.get("status")
        status_counts[status] += 1
        
        if status == "failed":
            err = item.get("error", "Unknown")
            # Simplify error message for grouping
            if "Target closed" in err: err = "Target closed"
            if "Timeout" in err: err = "Timeout"
            if "404" in err: err = "404 Not Found"
            if "CERT_DATE_INVALID" in err: err = "SSL Cert Error"
            if "valid JSON" in err: err = "Invalid JSON from AI"
            if "float" in err: err = "Float Parse Error"
            error_counts[err] += 1
            failed_urls.append(f"{item['source_url']} ({err})")
        
        elif status == "no_data":
            no_data_urls.append(item['source_url'])
        
        elif status == "success":
            # Check for suspicious prices
            for p in item.get("prices", []):
                price = p.get("price", 0)
                if price == 0 or price > 1000: # Arbitrary thresholds
                    suspicious_prices.append(f"{item['provider_name']}: {price} {item['currency']}")

    print("=== Status Counts ===")
    for s, c in status_counts.items():
        print(f"{s}: {c}")

    print("\n=== Common Errors ===")
    for e, c in error_counts.most_common(10):
        print(f"{e}: {c}")

    print("\n=== Suspicious Prices (0 or >1000) ===")
    for s in suspicious_prices[:10]:
        print(s)
    if len(suspicious_prices) > 10:
        print(f"... and {len(suspicious_prices)-10} more")

    print(f"\nTotal Analyzed: {len(data)}")

if __name__ == "__main__":
    analyze()
