"""
Sentiment Scanner - Crawls the web for crypto sentiment signals.
Scrapes Twitter-like data, Reddit, news, and social signals.
"""
import asyncio
import httpx
from datetime import datetime, timezone
from loguru import logger
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class SentimentScanner:
    """Scans web sources for Solana token sentiment and alpha."""

    SOURCES = {
        "reddit_solana": "https://www.reddit.com/r/solana/new/.json",
        "reddit_crypto": "https://www.reddit.com/r/CryptoMoonShots/new/.json",
        "reddit_defi": "https://www.reddit.com/r/defi/new/.json",
    }

    def __init__(self):
        ua = UserAgent()
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={"User-Agent": ua.random},
            follow_redirects=True
        )
        self.seen_posts = set()

    async def scan_reddit(self, subreddit: str = "solana", limit: int = 25) -> list[dict]:
        """Scan Reddit for Solana-related alpha."""
        posts = []
        try:
            resp = await self.client.get(
                f"https://www.reddit.com/r/{subreddit}/new/.json",
                params={"limit": limit},
                headers={"User-Agent": "TrustClaw/1.0 (Solana Alpha Scanner)"}
            )
            resp.raise_for_status()
            data = resp.json()

            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                post_id = post.get("id", "")
                if post_id in self.seen_posts:
                    continue
                self.seen_posts.add(post_id)

                title = post.get("title", "").lower()
                # Filter for actionable signals
                keywords = ["gem", "launch", "pump", "moon", "airdrop", "100x",
                           "solana", "sol", "raydium", "jupiter", "pump.fun",
                           "new token", "presale", "listing", "dex"]
                if any(kw in title for kw in keywords):
                    posts.append({
                        "source": f"r/{subreddit}",
                        "title": post.get("title", ""),
                        "text": post.get("selftext", "")[:500],
                        "score": post.get("score", 0),
                        "comments": post.get("num_comments", 0),
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "created": post.get("created_utc", 0),
                    })
        except Exception as e:
            logger.error(f"SentimentScanner.scan_reddit error for r/{subreddit}: {e}")

        return posts

    async def scan_solana_news(self) -> list[dict]:
        """Scrape Solana ecosystem news."""
        news = []
        urls = [
            "https://solana.com/news",
        ]
        for url in urls:
            try:
                resp = await self.client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Extract headlines
                    for headline in soup.find_all(["h1", "h2", "h3"], limit=10):
                        text = headline.get_text(strip=True)
                        if text and len(text) > 10:
                            news.append({
                                "source": url,
                                "title": text,
                                "url": url,
                            })
            except Exception as e:
                logger.error(f"SentimentScanner.scan_solana_news error for {url}: {e}")

        return news

    async def scan_all(self) -> dict:
        """Run all sentiment scans in parallel."""
        results = await asyncio.gather(
            self.scan_reddit("solana"),
            self.scan_reddit("CryptoMoonShots"),
            self.scan_reddit("defi"),
            self.scan_solana_news(),
            return_exceptions=True,
        )

        all_posts = []
        for r in results:
            if isinstance(r, list):
                all_posts.extend(r)
            elif isinstance(r, Exception):
                logger.error(f"Sentiment scan error: {r}")

        return {
            "total_signals": len(all_posts),
            "posts": sorted(all_posts, key=lambda x: x.get("score", 0), reverse=True),
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }

    async def close(self):
        await self.client.aclose()
