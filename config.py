"""TrustClaw Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    # LLM
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    # Solana
    HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")
    SOLANA_RPC_URL = os.getenv(
        "SOLANA_RPC_URL",
        f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY', '')}"
    )
    BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY", "")

    # Scan intervals (seconds)
    NEW_TOKEN_SCAN_INTERVAL = int(os.getenv("NEW_TOKEN_SCAN_INTERVAL", "30"))
    WHALE_SCAN_INTERVAL = int(os.getenv("WHALE_SCAN_INTERVAL", "60"))
    SENTIMENT_SCAN_INTERVAL = int(os.getenv("SENTIMENT_SCAN_INTERVAL", "300"))
    FULL_ANALYSIS_INTERVAL = int(os.getenv("FULL_ANALYSIS_INTERVAL", "3600"))

    # Thresholds
    MIN_LIQUIDITY_USD = 5000       # Minimum liquidity to consider a token
    MIN_VOLUME_24H = 10000         # Minimum 24h volume
    MAX_TOKEN_AGE_HOURS = 24       # Only look at tokens < 24h old for new launches
    WHALE_MIN_USD = 10000          # Minimum USD value for whale alert
    PUMP_THRESHOLD_PCT = 50        # Alert if token pumps > 50% in short window

    # Watchlist (tokens we're actively tracking)
    WATCHLIST = []

    # Known whale wallets to monitor (add known smart money addresses)
    WHALE_WALLETS = []
