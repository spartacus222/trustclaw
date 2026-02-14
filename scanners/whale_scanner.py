"""
Whale Scanner - Monitors large Solana wallet transactions.
Uses Helius API for transaction monitoring.
"""
import asyncio
import httpx
from datetime import datetime, timezone
from loguru import logger
from config import Config


class WhaleScanner:
    """Monitors whale wallets and large transactions on Solana."""

    def __init__(self):
        self.api_key = Config.HELIUS_API_KEY
        self.base_url = f"https://api.helius.xyz/v0"
        self.client = httpx.AsyncClient(timeout=30)
        self.last_signatures = {}  # wallet -> last seen signature

    async def get_wallet_transactions(self, wallet: str, limit: int = 10) -> list[dict]:
        """Get recent transactions for a wallet using Helius enhanced API."""
        try:
            resp = await self.client.get(
                f"{self.base_url}/addresses/{wallet}/transactions",
                params={"api-key": self.api_key, "limit": limit}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"WhaleScanner.get_wallet_transactions error for {wallet[:8]}...: {e}")
            return []

    async def get_wallet_balances(self, wallet: str) -> dict:
        """Get token balances for a wallet."""
        try:
            resp = await self.client.post(
                f"{self.base_url}/addresses/{wallet}/balances",
                params={"api-key": self.api_key}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"WhaleScanner.get_wallet_balances error: {e}")
            return {}

    async def detect_large_swaps(self, wallet: str) -> list[dict]:
        """Detect large token swaps from a wallet."""
        txns = await self.get_wallet_transactions(wallet, limit=20)
        large_swaps = []

        for tx in txns:
            sig = tx.get("signature", "")
            if sig in self.last_signatures.get(wallet, set()):
                continue

            # Check for swap events
            events = tx.get("events", {})
            swap = events.get("swap", {})
            if swap:
                native_input = swap.get("nativeInput", {})
                native_output = swap.get("nativeOutput", {})
                token_inputs = swap.get("tokenInputs", [])
                token_outputs = swap.get("tokenOutputs", [])

                # Estimate USD value (rough)
                amount_sol = (
                    native_input.get("amount", 0) + native_output.get("amount", 0)
                ) / 1e9  # lamports to SOL

                if amount_sol * 150 >= Config.WHALE_MIN_USD:  # rough SOL price estimate
                    large_swaps.append({
                        "signature": sig,
                        "wallet": wallet,
                        "type": "swap",
                        "sol_amount": round(amount_sol, 2),
                        "token_inputs": token_inputs,
                        "token_outputs": token_outputs,
                        "timestamp": tx.get("timestamp", 0),
                        "url": f"https://solscan.io/tx/{sig}",
                    })

        # Update last seen signatures
        if txns:
            self.last_signatures[wallet] = {tx.get("signature", "") for tx in txns[:5]}

        return large_swaps

    async def scan_all_whales(self) -> list[dict]:
        """Scan all configured whale wallets for activity."""
        all_swaps = []
        for wallet in Config.WHALE_WALLETS:
            swaps = await self.detect_large_swaps(wallet)
            all_swaps.extend(swaps)
            await asyncio.sleep(0.5)  # rate limiting
        return all_swaps

    async def close(self):
        await self.client.aclose()
