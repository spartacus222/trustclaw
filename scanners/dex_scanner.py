"""
DexScreener Scanner - Detects new Solana token launches and pumps.
Uses DexScreener free API (no key needed).
"""
import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from loguru import logger
from config import Config


class DexScanner:
    """Scans DexScreener for new Solana token launches and price movements."""

    BASE_URL = "https://api.dexscreener.com"
    SEEN_PAIRS = set()

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30, headers={"User-Agent": "TrustClaw/1.0"})

    async def get_new_pairs(self) -> list[dict]:
        """Fetch newly created Solana pairs from DexScreener."""
        try:
            # Get latest Solana pairs
            resp = await self.client.get(
                f"{self.BASE_URL}/token-profiles/latest/v1",
                params={"chainId": "solana"}
            )
            resp.raise_for_status()
            data = resp.json()

            # Also check latest boosted tokens
            resp2 = await self.client.get(f"{self.BASE_URL}/token-boosts/latest/v1")
            resp2.raise_for_status()
            boosted = resp2.json()

            results = []
            all_tokens = []
            if isinstance(data, list):
                all_tokens.extend(data)
            if isinstance(boosted, list):
                all_tokens.extend(boosted)

            for token in all_tokens:
                if token.get("chainId") != "solana":
                    continue
                addr = token.get("tokenAddress", "")
                if addr and addr not in self.SEEN_PAIRS:
                    self.SEEN_PAIRS.add(addr)
                    results.append(token)

            return results
        except Exception as e:
            logger.error(f"DexScanner.get_new_pairs error: {e}")
            return []

    async def get_trending_solana(self) -> list[dict]:
        """Get trending tokens on Solana."""
        try:
            resp = await self.client.get(
                f"{self.BASE_URL}/tokens/trending/v1",
                params={"chainId": "solana"}
            )
            resp.raise_for_status()
            return resp.json() if isinstance(resp.json(), list) else []
        except Exception as e:
            logger.error(f"DexScanner.get_trending error: {e}")
            return []

    async def get_token_data(self, token_address: str) -> dict | None:
        """Get detailed data for a specific Solana token."""
        try:
            resp = await self.client.get(
                f"{self.BASE_URL}/tokens/v1/solana/{token_address}"
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data if isinstance(data, dict) else None
        except Exception as e:
            logger.error(f"DexScanner.get_token_data error: {e}")
            return None

    async def scan_for_pumps(self, min_pump_pct: float = None) -> list[dict]:
        """Find tokens that are pumping hard right now."""
        min_pump_pct = min_pump_pct or Config.PUMP_THRESHOLD_PCT
        pumps = []
        try:
            trending = await self.get_trending_solana()
            for token in trending:
                price_change = token.get("priceChange", {})
                h1_change = price_change.get("h1", 0) or 0
                h6_change = price_change.get("h6", 0) or 0

                if abs(h1_change) >= min_pump_pct or abs(h6_change) >= min_pump_pct * 1.5:
                    pumps.append({
                        "address": token.get("tokenAddress", ""),
                        "name": token.get("name", "Unknown"),
                        "symbol": token.get("symbol", "???"),
                        "price_usd": token.get("priceUsd", "0"),
                        "h1_change": h1_change,
                        "h6_change": h6_change,
                        "h24_change": price_change.get("h24", 0),
                        "volume_24h": token.get("volume", {}).get("h24", 0),
                        "liquidity_usd": token.get("liquidity", {}).get("usd", 0),
                        "market_cap": token.get("marketCap", 0),
                        "url": f"https://dexscreener.com/solana/{token.get('tokenAddress', '')}",
                    })
            return sorted(pumps, key=lambda x: abs(x.get("h1_change", 0)), reverse=True)
        except Exception as e:
            logger.error(f"DexScanner.scan_for_pumps error: {e}")
            return []

    async def search_tokens(self, query: str) -> list[dict]:
        """Search for tokens by name or symbol."""
        try:
            resp = await self.client.get(
                f"{self.BASE_URL}/latest/dex/search",
                params={"q": query}
            )
            resp.raise_for_status()
            data = resp.json()
            pairs = data.get("pairs", [])
            return [p for p in pairs if p.get("chainId") == "solana"]
        except Exception as e:
            logger.error(f"DexScanner.search_tokens error: {e}")
            return []

    async def close(self):
        await self.client.aclose()
