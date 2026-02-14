"""
TrustClaw Brain - LLM-powered analysis engine.
Evaluates tokens, scores opportunities, generates buy/sell signals.
"""
import json
from datetime import datetime, timezone
from loguru import logger
from groq import Groq
from config import Config


class Brain:
    """AI brain that analyzes opportunities and generates signals."""

    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.LLM_MODEL
        self.signal_history = []

    def analyze_token(self, token_data: dict) -> dict:
        """Deep analysis of a token opportunity."""
        prompt = f"""You are TrustClaw, an elite Solana alpha hunter AI. Analyze this token and give a trading signal.

TOKEN DATA:
{json.dumps(token_data, indent=2, default=str)}

Evaluate on these criteria:
1. LIQUIDITY: Is there enough liquidity (>$5k)? Low liquidity = rug risk
2. VOLUME: Is 24h volume healthy relative to market cap?
3. MOMENTUM: Price action - is it pumping organically or artificially?
4. AGE: How old is the token? New (<1h) = higher risk but higher reward
5. SOCIAL: Any social signals or hype around it?
6. RUG RISK: Contract renounced? Liquidity locked? Top holders concentrated?

Respond in this EXACT JSON format:
{{
    "signal": "BUY" | "WATCH" | "SKIP" | "DANGER",
    "confidence": 1-10,
    "risk_level": "LOW" | "MEDIUM" | "HIGH" | "EXTREME",
    "reasoning": "2-3 sentence explanation",
    "entry_price": "suggested entry or 'market'",
    "target": "price target or percentage",
    "stop_loss": "suggested stop loss",
    "time_horizon": "scalp (mins) | swing (hours) | hold (days)"
}}

Be BRUTALLY honest. Most tokens are scams. Only signal BUY for genuinely interesting opportunities."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a crypto trading analyst. Respond only in valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            result_text = response.choices[0].message.content.strip()

            # Parse JSON from response (handle markdown code blocks)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            analysis = json.loads(result_text)
            analysis["token_address"] = token_data.get("address", "")
            analysis["token_name"] = token_data.get("name", token_data.get("symbol", "Unknown"))
            analysis["analyzed_at"] = datetime.now(timezone.utc).isoformat()

            self.signal_history.append(analysis)
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Brain.analyze_token JSON parse error: {e}")
            return {"signal": "SKIP", "confidence": 0, "reasoning": "Analysis failed - could not parse LLM response"}
        except Exception as e:
            logger.error(f"Brain.analyze_token error: {e}")
            return {"signal": "SKIP", "confidence": 0, "reasoning": f"Analysis error: {str(e)}"}

    def generate_market_brief(self, data: dict) -> str:
        """Generate a comprehensive market brief from all scanner data."""
        prompt = f"""You are TrustClaw, a Solana alpha hunting AI. Generate a concise market brief from this data.

SCANNER DATA:
- New tokens found: {data.get('new_tokens_count', 0)}
- Pumping tokens: {json.dumps(data.get('pumps', [])[:5], default=str)}
- Whale activity: {json.dumps(data.get('whale_activity', [])[:5], default=str)}
- Social signals: {json.dumps(data.get('sentiment', {}).get('posts', [])[:5], default=str)}
- Trending tokens: {json.dumps(data.get('trending', [])[:5], default=str)}

Generate a Telegram-friendly brief (use emojis, keep it scannable):
1. Top 3 opportunities right now (with reasoning)
2. Any danger signals / rugs detected
3. Overall market sentiment (bullish/bearish/neutral)
4. Actionable next steps

Keep it under 2000 characters. Be direct and actionable."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise crypto market analyst. Use emojis. Be direct."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Brain.generate_market_brief error: {e}")
            return f"\u26a0\ufe0f Market brief generation failed: {str(e)}"

    def score_opportunity(self, token_data: dict) -> float:
        """Quick numerical score for an opportunity (0-100)."""
        score = 0.0

        liquidity = token_data.get("liquidity_usd", 0) or 0
        volume = token_data.get("volume_24h", 0) or 0
        h1_change = token_data.get("h1_change", 0) or 0
        market_cap = token_data.get("market_cap", 0) or 0

        # Liquidity score (0-25)
        if liquidity > 100000:
            score += 25
        elif liquidity > 50000:
            score += 20
        elif liquidity > 10000:
            score += 15
        elif liquidity > 5000:
            score += 10

        # Volume score (0-25)
        if volume > 500000:
            score += 25
        elif volume > 100000:
            score += 20
        elif volume > 50000:
            score += 15
        elif volume > 10000:
            score += 10

        # Momentum score (0-25)
        if 10 <= h1_change <= 100:
            score += 25  # Healthy pump
        elif 5 <= h1_change <= 200:
            score += 15
        elif h1_change > 200:
            score += 5  # Too much, likely dump incoming

        # Market cap score (0-25) - smaller = more upside
        if 10000 <= market_cap <= 500000:
            score += 25  # Sweet spot for moonshots
        elif 500000 < market_cap <= 5000000:
            score += 20
        elif 5000000 < market_cap <= 50000000:
            score += 15
        elif market_cap > 50000000:
            score += 10

        return min(score, 100)
