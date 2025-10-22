"""
FX Client for Frankfurter API with caching and fallback support.
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class FXCache:
    """Simple in-memory cache with TTL."""

    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, tuple[datetime, dict]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Optional[dict]:
        """Get cached value if not expired."""
        if key in self.cache:
            timestamp, value = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                logger.info(f"Cache hit for key: {key}")
                return value
            else:
                del self.cache[key]
                logger.info(f"Cache expired for key: {key}")
        return None

    def set(self, key: str, value: dict):
        """Store value in cache with current timestamp."""
        self.cache[key] = (datetime.now(), value)
        logger.info(f"Cached key: {key}")

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()


class FXClient:
    """Client for fetching FX rates from Frankfurter API."""

    BASE_URL = "https://api.frankfurter.dev/v1"
    FALLBACK_FILE = Path(__file__).parent / "data" / "sample_fx.json"

    def __init__(self, cache_ttl: int = 300):
        self.cache = FXCache(ttl_seconds=cache_ttl)
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_range(
        self,
        start_date: str,
        end_date: str,
        base: str = "EUR",
        symbols: str = "USD"
    ) -> dict:
        """
        Get FX rates for a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            base: Base currency (default: EUR)
            symbols: Target currency (default: USD)

        Returns:
            dict: Response from Frankfurter API or fallback data
        """
        cache_key = f"range:{start_date}:{end_date}:{base}:{symbols}"

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Try fetching from API
        url = f"{self.BASE_URL}/{start_date}..{end_date}"
        params = {"base": base, "symbols": symbols}

        try:
            logger.info(f"Fetching FX range: {url} with params {params}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Cache successful response
            self.cache.set(cache_key, data)
            return data

        except Exception as e:
            logger.error(f"Failed to fetch from Frankfurter API: {e}")
            return self._load_fallback()

    async def get_latest(self, base: str = "EUR", symbols: str = "USD") -> dict:
        """
        Get latest FX rate.

        Args:
            base: Base currency (default: EUR)
            symbols: Target currency (default: USD)

        Returns:
            dict: Latest FX rate data
        """
        cache_key = f"latest:{base}:{symbols}"

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Try fetching from API
        url = f"{self.BASE_URL}/latest"
        params = {"from": base, "to": symbols}

        try:
            logger.info(f"Fetching latest FX rate: {url} with params {params}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Cache successful response
            self.cache.set(cache_key, data)
            return data

        except Exception as e:
            logger.error(f"Failed to fetch latest from Frankfurter API: {e}")
            return self._load_fallback()

    def _load_fallback(self) -> dict:
        """Load fallback data from local JSON file."""
        try:
            logger.info(f"Loading fallback data from {self.FALLBACK_FILE}")
            with open(self.FALLBACK_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load fallback data: {e}")
            raise ValueError(
                "Unable to fetch FX data from API and fallback file not available. "
                "Please check your connection or ensure data/sample_fx.json exists."
            )
