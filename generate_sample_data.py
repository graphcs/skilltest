"""
Generate sample FX data from Frankfurter API for 2025.
This script queries real data and saves it to data/sample_fx.json for fallback.
"""
import json
import httpx
from pathlib import Path


def fetch_sample_data():
    """Fetch real FX data from Frankfurter for 2025."""
    # Use a range from early 2025
    url = "https://api.frankfurter.dev/v1/2025-01-01..2025-01-31"
    params = {"base": "EUR", "symbols": "USD"}

    print(f"Fetching sample data from Frankfurter API...")
    print(f"URL: {url}")
    print(f"Params: {params}")

    try:
        response = httpx.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        # Save to file
        output_path = Path(__file__).parent / "data" / "sample_fx.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nSuccessfully saved sample data to {output_path}")
        print(f"Data contains {len(data.get('rates', {}))} days of FX rates")

        return data

    except Exception as e:
        print(f"Error fetching sample data: {e}")
        raise


if __name__ == "__main__":
    fetch_sample_data()
