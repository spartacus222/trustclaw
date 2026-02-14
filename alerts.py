"""
TrustClaw Alerts - Telegram notification system.
Sends alerts for opportunities, whale moves, and market briefs.
"""
import asyncio
import httpx
from datetime import datetime, timezone
from loguru import logger
from config import Config


class TelegramAlerts:
    """Sends formatted alerts to Telegram."""

    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.client = httpx.AsyncClient(timeout=30)
        self.message_queue = asyncio.Queue()

    async def send_message(self, text: str, parse_mode: str = "HTML", disable_preview: bool = True):
        """Send a message to Telegram."""
        if not self.token or not self.chat_id:
            logger.warning("Telegram not configured - skipping alert")
            return

        try:
            # Telegram message limit is 4096 chars
            if len(text) > 4000:
                text = text[:4000] + "\n\n... (truncated)"

            resp = await self.client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": disable_preview,
                }
            )
            if resp.status_code != 200:
                logger.error(f"Telegram send error: {resp.text}")
        except Exception as e:
            logger.error(f"TelegramAlerts.send_message error: {e}")

    async def alert_new_token(self, token_data: dict):
        """Alert for a new token launch."""
        name = token_data.get("name", "Unknown")
        symbol = token_data.get("symbol", "???")
        address = token_data.get("address", token_data.get("tokenAddress", ""))
        url = token_data.get("url", f"https://dexscreener.com/solana/{address}")

        msg = (
            f"\U0001f7e2 <b>NEW TOKEN DETECTED</b>\n"
            f"\n"
            f"<b>{name}</b> (${symbol})\n"
            f"<code>{address}</code>\n"
            f"\n"
            f"\U0001f517 <a href=\"{url}\">DexScreener</a> | "
            f"<a href=\"https://solscan.io/token/{address}\">Solscan</a> | "
            f"<a href=\"https://birdeye.so/token/{address}?chain=solana\">Birdeye</a>\n"
            f"\n"
            f"<i>Analyzing...</i>"
        )
        await self.send_message(msg)

    async def alert_buy_signal(self, analysis: dict):
        """Alert for a BUY signal."""
        signal = analysis.get("signal", "UNKNOWN")
        confidence = analysis.get("confidence", 0)
        name = analysis.get("token_name", "Unknown")
        risk = analysis.get("risk_level", "UNKNOWN")
        reasoning = analysis.get("reasoning", "No reasoning provided")
        target = analysis.get("target", "N/A")
        stop = analysis.get("stop_loss", "N/A")
        horizon = analysis.get("time_horizon", "N/A")

        emoji = {"BUY": "\U0001f680", "WATCH": "\U0001f440", "SKIP": "\u23ed\ufe0f", "DANGER": "\u2620\ufe0f"}.get(signal, "\u2753")
        risk_emoji = {"LOW": "\U0001f7e2", "MEDIUM": "\U0001f7e1", "HIGH": "\U0001f7e0", "EXTREME": "\U0001f534"}.get(risk, "\u26aa")

        msg = (
            f"{emoji} <b>SIGNAL: {signal}</b> | Confidence: {confidence}/10\n"
            f"\n"
            f"<b>{name}</b>\n"
            f"{risk_emoji} Risk: {risk}\n"
            f"\n"
            f"<b>Analysis:</b> {reasoning}\n"
            f"\n"
            f"\U0001f3af Target: {target}\n"
            f"\U0001f6d1 Stop: {stop}\n"
            f"\u23f0 Horizon: {horizon}\n"
        )
        await self.send_message(msg)

    async def alert_whale_move(self, swap_data: dict):
        """Alert for whale wallet activity."""
        wallet = swap_data.get("wallet", "")[:8] + "..."
        sol_amount = swap_data.get("sol_amount", 0)
        url = swap_data.get("url", "")

        msg = (
            f"\U0001f433 <b>WHALE ALERT</b>\n"
            f"\n"
            f"Wallet: <code>{swap_data.get('wallet', '')}</code>\n"
            f"Amount: ~{sol_amount} SOL\n"
            f"\n"
            f"\U0001f517 <a href=\"{url}\">View Transaction</a>"
        )
        await self.send_message(msg)

    async def alert_pump(self, pump_data: dict):
        """Alert for a token pump."""
        name = pump_data.get("name", "Unknown")
        symbol = pump_data.get("symbol", "???")
        h1 = pump_data.get("h1_change", 0)
        h6 = pump_data.get("h6_change", 0)
        vol = pump_data.get("volume_24h", 0)
        liq = pump_data.get("liquidity_usd", 0)
        url = pump_data.get("url", "")

        direction = "\U0001f4c8" if h1 > 0 else "\U0001f4c9"
        msg = (
            f"{direction} <b>PUMP DETECTED</b>\n"
            f"\n"
            f"<b>{name}</b> (${symbol})\n"
            f"1H: {h1:+.1f}% | 6H: {h6:+.1f}%\n"
            f"Volume: ${vol:,.0f} | Liq: ${liq:,.0f}\n"
            f"\n"
            f"\U0001f517 <a href=\"{url}\">DexScreener</a>"
        )
        await self.send_message(msg)

    async def send_market_brief(self, brief: str):
        """Send the full market brief."""
        msg = (
            f"\U0001f43a <b>TRUSTCLAW MARKET BRIEF</b>\n"
            f"<i>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</i>\n"
            f"\n"
            f"{brief}"
        )
        await self.send_message(msg)

    async def send_startup_message(self):
        """Send a startup notification."""
        msg = (
            f"\U0001f43a <b>TrustClaw v1.0 ONLINE</b>\n"
            f"\n"
            f"\u2705 DEX Scanner: Active\n"
            f"\u2705 Whale Monitor: Active\n"
            f"\u2705 Sentiment Scanner: Active\n"
            f"\u2705 AI Brain: Active\n"
            f"\n"
            f"Scanning Solana for alpha... \U0001f680"
        )
        await self.send_message(msg)

    async def close(self):
        await self.client.aclose()
