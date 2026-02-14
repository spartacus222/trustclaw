# 🐺 TrustClaw - Autonomous Solana Alpha Hunter

**AI-powered agent that crawls the net 24/7 to find money-making opportunities on Solana.**

Built with ❤️ by [KG ⚡](https://github.com/spartacus222)

---

## 🔥 What It Does

TrustClaw runs 24/7 and autonomously:

| Scanner | What It Monitors | Frequency |
|---------|-----------------|-----------|
| **DEX Scanner** | New token launches, pumping tokens, trending pairs | Every 30s |
| **Whale Monitor** | Large wallet transactions, smart money moves | Every 60s |
| **Sentiment Scanner** | Reddit, news, social signals for alpha | Every 5min |
| **AI Brain** | Analyzes every opportunity with LLM scoring | Real-time |
| **Market Brief** | Comprehensive hourly intelligence report | Every 1hr |

All alerts go straight to your **Telegram** in real-time.

---

## 🚀 Quick Deploy (Railway - One Click)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/trustclaw)

1. Click the button above
2. Set your environment variables (see below)
3. Deploy. That's it. TrustClaw is hunting.

---

## 🛠 Manual Setup

### Prerequisites
- Python 3.12+
- Telegram Bot Token (free from [@BotFather](https://t.me/BotFather))
- Groq API Key (free at [console.groq.com](https://console.groq.com))
- Helius API Key (free at [helius.dev](https://helius.dev))

### Install & Run

```bash
# Clone
git clone https://github.com/spartacus222/trustclaw.git
cd trustclaw

# Setup
cp .env.example .env
# Edit .env with your keys

# Install deps
pip install -r requirements.txt

# Run
python main.py
```

### Docker

```bash
docker-compose up -d
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Get from @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | ✅ | Your Telegram user/group ID |
| `GROQ_API_KEY` | ✅ | Free LLM API from Groq |
| `HELIUS_API_KEY` | ⭐ | Free Solana RPC from Helius |
| `BIRDEYE_API_KEY` | ❌ | Optional deeper token data |

### Getting Your Telegram Chat ID
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your Chat ID
3. Put that number in `TELEGRAM_CHAT_ID`

---

## 📊 Alert Types

### 🟢 New Token Detected
Fires when a new Solana token is found with decent liquidity/volume.

### 🚀 BUY Signal
AI analyzed the token and thinks it's worth entering. Includes confidence score, risk level, entry/target/stop.

### 👀 WATCH Signal  
Interesting but not actionable yet. Keep an eye on it.

### 📈 Pump Detected
Token is pumping >50% in a short window.

### 🐳 Whale Alert
Large transaction detected from a tracked wallet.

### 🐺 Market Brief
Hourly comprehensive report with top opportunities and market sentiment.

---

## 🧠 How The AI Works

1. **Score** - Quick numerical score (0-100) based on liquidity, volume, momentum, market cap
2. **Filter** - Only tokens scoring 40+ get deep analysis
3. **Analyze** - LLM evaluates risk, opportunity, timing
4. **Signal** - BUY / WATCH / SKIP / DANGER with confidence rating
5. **Alert** - Sends to your Telegram instantly

---

## 📁 Project Structure

```
trustclaw/
├── main.py              # Orchestrator - runs all scanners
├── config.py            # Configuration from .env
├── brain.py             # LLM analysis engine
├── alerts.py            # Telegram notification system
├── scanners/
│   ├── dex_scanner.py   # DexScreener API scanner
│   ├── whale_scanner.py # Helius whale monitor
│   └── sentiment_scanner.py  # Reddit/news scraper
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── railway.json         # One-click Railway deploy
└── .env.example
```

---

## ⚠️ Disclaimer

This is an experimental tool for educational and research purposes. **Not financial advice.** Crypto trading carries extreme risk. You can lose everything. The AI can be wrong. Always DYOR.

---

## 🔮 Roadmap

- [ ] Pump.fun integration (real-time new launches)
- [ ] Jupiter swap monitoring
- [ ] Raydium pool detection
- [ ] Token holder analysis
- [ ] Rug pull detection (contract analysis)
- [ ] Portfolio tracking
- [ ] Auto-trading (with safety limits)
- [ ] Discord integration
- [ ] Web dashboard

---

*Powered by Composio, Groq, Helius, and DexScreener*
