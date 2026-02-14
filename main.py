"""
TrustClaw v1.0 - Autonomous Solana Alpha Hunter
================================================
Crawls the net 24/7 to find money-making opportunities on Solana.
Sends real-time alerts to Telegram.

Architecture:
  - DexScanner: Monitors new token launches, pumps, trending tokens
  - WhaleScanner: Tracks large wallet transactions
  - SentimentScanner: Scrapes Reddit, news for alpha signals
  - Brain: LLM-powered analysis engine (Groq/OpenAI)
  - Alerts: Telegram notification system

Deploy: Railway (one-click) or any VPS with Docker.
"""
import asyncio
import signal
import sys
from datetime import datetime, timezone
from loguru import logger

from config import Config
from scanners.dex_scanner import DexScanner
from scanners.whale_scanner import WhaleScanner
from scanners.sentiment_scanner import SentimentScanner
from brain import Brain
from alerts import TelegramAlerts

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add("data/trustclaw.log", rotation="10 MB", retention="7 days", level="DEBUG")


class TrustClaw:
    """Main orchestrator for the TrustClaw alpha hunting system."""

    def __init__(self):
        self.dex = DexScanner()
        self.whale = WhaleScanner()
        self.sentiment = SentimentScanner()
        self.brain = Brain()
        self.alerts = TelegramAlerts()
        self.running = True
        self.scan_count = 0

    async def scan_new_tokens(self):
        """Scan for new token launches and analyze them."""
        while self.running:
            try:
                logger.info("\U0001f50d Scanning for new tokens...")
                new_tokens = await self.dex.get_new_pairs()

                for token in new_tokens[:10]:  # Process top 10 new tokens
                    address = token.get("tokenAddress", "")
                    if not address:
                        continue

                    # Get detailed data
                    details = await self.dex.get_token_data(address)
                    if not details:
                        continue

                    # Quick score check
                    score = self.brain.score_opportunity({
                        "liquidity_usd": details.get("liquidity", {}).get("usd", 0),
                        "volume_24h": details.get("volume", {}).get("h24", 0),
                        "h1_change": details.get("priceChange", {}).get("h1", 0),
                        "market_cap": details.get("marketCap", 0),
                    })

                    if score >= 40:  # Only analyze promising tokens
                        logger.info(f"\U0001f3af High-score token found: {details.get('baseToken', {}).get('name', 'Unknown')} (score: {score})")
                        await self.alerts.alert_new_token({
                            "name": details.get("baseToken", {}).get("name", "Unknown"),
                            "symbol": details.get("baseToken", {}).get("symbol", "???"),
                            "address": address,
                        })

                        # Deep AI analysis
                        analysis = self.brain.analyze_token({
                            "name": details.get("baseToken", {}).get("name", "Unknown"),
                            "symbol": details.get("baseToken", {}).get("symbol", "???"),
                            "address": address,
                            "price_usd": details.get("priceUsd", "0"),
                            "liquidity_usd": details.get("liquidity", {}).get("usd", 0),
                            "volume_24h": details.get("volume", {}).get("h24", 0),
                            "market_cap": details.get("marketCap", 0),
                            "h1_change": details.get("priceChange", {}).get("h1", 0),
                            "h6_change": details.get("priceChange", {}).get("h6", 0),
                            "h24_change": details.get("priceChange", {}).get("h24", 0),
                            "pair_created_at": details.get("pairCreatedAt", ""),
                            "dex": details.get("dexId", "unknown"),
                            "score": score,
                        })

                        if analysis.get("signal") in ("BUY", "WATCH"):
                            await self.alerts.alert_buy_signal(analysis)

                    await asyncio.sleep(1)  # Rate limiting

            except Exception as e:
                logger.error(f"scan_new_tokens error: {e}")

            await asyncio.sleep(Config.NEW_TOKEN_SCAN_INTERVAL)

    async def scan_pumps(self):
        """Scan for pumping tokens."""
        while self.running:
            try:
                logger.info("\U0001f4c8 Scanning for pumps...")
                pumps = await self.dex.scan_for_pumps()

                for pump in pumps[:5]:  # Top 5 pumps
                    if pump.get("liquidity_usd", 0) >= Config.MIN_LIQUIDITY_USD:
                        await self.alerts.alert_pump(pump)

                        # Analyze if significant
                        if abs(pump.get("h1_change", 0)) >= 100:
                            analysis = self.brain.analyze_token(pump)
                            if analysis.get("signal") in ("BUY", "WATCH"):
                                await self.alerts.alert_buy_signal(analysis)

                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"scan_pumps error: {e}")

            await asyncio.sleep(Config.NEW_TOKEN_SCAN_INTERVAL * 2)

    async def scan_whales(self):
        """Monitor whale wallets."""
        while self.running:
            try:
                if Config.WHALE_WALLETS:
                    logger.info("\U0001f433 Scanning whale wallets...")
                    swaps = await self.whale.scan_all_whales()
                    for swap in swaps:
                        await self.alerts.alert_whale_move(swap)
                else:
                    logger.debug("No whale wallets configured, skipping...")

            except Exception as e:
                logger.error(f"scan_whales error: {e}")

            await asyncio.sleep(Config.WHALE_SCAN_INTERVAL)

    async def scan_sentiment(self):
        """Scan social media and news for alpha."""
        while self.running:
            try:
                logger.info("\U0001f4f0 Scanning sentiment...")
                sentiment = await self.sentiment.scan_all()

                if sentiment.get("total_signals", 0) > 0:
                    logger.info(f"Found {sentiment['total_signals']} social signals")

            except Exception as e:
                logger.error(f"scan_sentiment error: {e}")

            await asyncio.sleep(Config.SENTIMENT_SCAN_INTERVAL)

    async def generate_hourly_brief(self):
        """Generate and send a comprehensive market brief every hour."""
        while self.running:
            try:
                await asyncio.sleep(Config.FULL_ANALYSIS_INTERVAL)

                logger.info("\U0001f4ca Generating market brief...")

                # Gather all data
                trending = await self.dex.get_trending_solana()
                pumps = await self.dex.scan_for_pumps(min_pump_pct=20)
                sentiment = await self.sentiment.scan_all()
                whale_activity = await self.whale.scan_all_whales() if Config.WHALE_WALLETS else []

                # Generate brief with AI
                brief = self.brain.generate_market_brief({
                    "new_tokens_count": len(self.dex.SEEN_PAIRS),
                    "trending": [
                        {
                            "name": t.get("name", "?"),
                            "symbol": t.get("symbol", "?"),
                            "price_change_1h": t.get("priceChange", {}).get("h1", 0),
                            "volume_24h": t.get("volume", {}).get("h24", 0),
                        }
                        for t in trending[:10]
                    ],
                    "pumps": pumps[:5],
                    "whale_activity": whale_activity[:5],
                    "sentiment": sentiment,
                })

                await self.alerts.send_market_brief(brief)
                self.scan_count += 1
                logger.info(f"\u2705 Market brief #{self.scan_count} sent")

            except Exception as e:
                logger.error(f"generate_hourly_brief error: {e}")

    async def run(self):
        """Start all scanning loops."""
        logger.info("\U0001f43a TrustClaw v1.0 starting...")

        # Ensure data directory exists
        import os
        os.makedirs("data", exist_ok=True)

        # Validate config
        if not Config.TELEGRAM_BOT_TOKEN:
            logger.warning("\u26a0\ufe0f TELEGRAM_BOT_TOKEN not set - alerts will be disabled")
        if not Config.GROQ_API_KEY:
            logger.error("\u274c GROQ_API_KEY not set - AI analysis will fail")
            return
        if not Config.HELIUS_API_KEY:
            logger.warning("\u26a0\ufe0f HELIUS_API_KEY not set - whale scanning will be limited")

        # Send startup message
        await self.alerts.send_startup_message()

        # Run all scanners concurrently
        tasks = [
            asyncio.create_task(self.scan_new_tokens()),
            asyncio.create_task(self.scan_pumps()),
            asyncio.create_task(self.scan_whales()),
            asyncio.create_task(self.scan_sentiment()),
            asyncio.create_task(self.generate_hourly_brief()),
        ]

        logger.info("\u2705 All scanners running. Hunting for alpha...")

        # Handle graceful shutdown
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Shutting down...")

    async def shutdown(self):
        """Graceful shutdown."""
        self.running = False
        await self.dex.close()
        await self.whale.close()
        await self.sentiment.close()
        await self.alerts.close()
        logger.info("\U0001f43a TrustClaw shutdown complete.")


async def main():
    claw = TrustClaw()

    # Handle SIGINT/SIGTERM
    loop = asyncio.get_event_loop()
    for sig_name in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig_name, lambda: asyncio.create_task(claw.shutdown()))

    await claw.run()


if __name__ == "__main__":
    asyncio.run(main())
