"""Company news and market sentiment analysis service.

Retrieves news articles via Yahoo Finance, standardizes heterogeneous payload
formats, supports multi-window time filtering, and provides headline sentiment
scoring using VADER.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional, Tuple
import streamlit as st
import yfinance as yf

from src.services.market_data import sanitize_ticker

# Lightweight VADER sentiment analyzer with fallback
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER_ANALYZER = SentimentIntensityAnalyzer()
except ImportError:
    _VADER_ANALYZER = None


def classify_headline_sentiment(text: str) -> Dict[str, Any]:
    """Classify text sentiment into Positive, Negative, or Neutral.

    Uses VADER compound polarity thresholds:
    - Compound >= 0.05 -> Positive
    - Compound <= -0.05 -> Negative
    - Otherwise -> Neutral
    """
    if not text or not text.strip():
        return {
            "label": "Neutral",
            "compound": 0.0,
            "pos": 0.0,
            "neg": 0.0,
            "neu": 1.0,
        }

    if _VADER_ANALYZER is not None:
        scores = _VADER_ANALYZER.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"

        return {
            "label": label,
            "compound": round(compound, 4),
            "pos": round(scores["pos"], 3),
            "neg": round(scores["neg"], 3),
            "neu": round(scores["neu"], 3),
        }
    else:
        # Fallback keyword-based heuristic if VADER is unavailable
        pos_words = {"surge", "gain", "profit", "bull", "growth", "boost", "beat", "rally", "upgrade", "record"}
        neg_words = {"fall", "drop", "loss", "bear", "decline", "warn", "miss", "slump", "downgrade", "crisis"}
        words = set(text.lower().split())
        pos_count = len(words.intersection(pos_words))
        neg_count = len(words.intersection(neg_words))
        if pos_count > neg_count:
            return {"label": "Positive", "compound": 0.5, "pos": 0.5, "neg": 0.0, "neu": 0.5}
        elif neg_count > pos_count:
            return {"label": "Negative", "compound": -0.5, "pos": 0.0, "neg": 0.5, "neu": 0.5}
        else:
            return {"label": "Neutral", "compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}


def _parse_timestamp(raw_date: Any) -> Tuple[float, str]:
    """Parse various datetime representations into Unix epoch and clean string."""
    now_epoch = time.time()
    if raw_date is None:
        return now_epoch, "Recent"

    if isinstance(raw_date, (int, float)):
        # Epoch seconds
        dt = datetime.fromtimestamp(raw_date, tz=timezone.utc)
        return float(raw_date), dt.strftime("%Y-%m-%d %H:%M UTC")

    if isinstance(raw_date, str):
        # ISO string format: e.g. "2026-11-23T09:43:44Z"
        try:
            cleaned_str = raw_date.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned_str)
            return dt.timestamp(), dt.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            return now_epoch, raw_date[:16]

    return now_epoch, "Recent"


def normalize_news_item(item: dict, ticker: str) -> Optional[Dict[str, Any]]:
    """Normalize news dictionary across yfinance schema variations."""
    if not isinstance(item, dict):
        return None

    # Handle yfinance 1.8.0 nested 'content' dictionary
    content = item.get("content", item)
    if not isinstance(content, dict):
        content = item

    title = content.get("title") or item.get("title")
    if not title or not isinstance(title, str) or not title.strip():
        return None

    title = title.strip()
    summary = content.get("summary") or content.get("description") or item.get("summary") or ""
    if isinstance(summary, str):
        summary = summary.strip()
    else:
        summary = ""

    # Provider / Publisher resolution
    provider_raw = content.get("provider") or item.get("publisher")
    if isinstance(provider_raw, dict):
        publisher = provider_raw.get("displayName") or provider_raw.get("name") or "Yahoo Finance"
    elif isinstance(provider_raw, str) and provider_raw.strip():
        publisher = provider_raw.strip()
    else:
        publisher = "Financial News"

    # URL resolution
    url_obj = content.get("canonicalUrl") or content.get("clickThroughUrl") or item.get("link")
    if isinstance(url_obj, dict):
        article_url = url_obj.get("url") or "#"
    elif isinstance(url_obj, str) and url_obj.startswith("http"):
        article_url = url_obj
    else:
        article_url = "#"

    # Publication date
    raw_date = content.get("pubDate") or item.get("providerPublishTime") or content.get("displayTime")
    epoch, formatted_date = _parse_timestamp(raw_date)

    # Sentiment analysis on headline and summary
    text_to_score = f"{title}. {summary}" if summary else title
    sentiment = classify_headline_sentiment(text_to_score)

    return {
        "id": str(item.get("id") or content.get("id") or hash(title)),
        "title": title,
        "summary": summary,
        "publisher": publisher,
        "url": article_url,
        "published_at": formatted_date,
        "published_timestamp": epoch,
        "related_ticker": ticker,
        "sentiment": sentiment,
    }


@st.cache_data(ttl=300, show_spinner=False)
def fetch_company_news(ticker: str) -> List[Dict[str, Any]]:
    """Fetch and standardize latest news items for a given ticker."""
    clean_ticker = sanitize_ticker(ticker)
    if not clean_ticker:
        return []

    try:
        stock = yf.Ticker(clean_ticker)
        raw_news = stock.news
        if not raw_news or not isinstance(raw_news, list):
            return []

        results = []
        for item in raw_news:
            norm = normalize_news_item(item, clean_ticker)
            if norm:
                results.append(norm)

        # Sort newest first
        results.sort(key=lambda x: x["published_timestamp"], reverse=True)
        return results

    except Exception:
        return []


def filter_news_by_time(
    news_items: List[Dict[str, Any]], filter_option: str
) -> List[Dict[str, Any]]:
    """Filter list of news articles based on publication timeframe."""
    if not news_items:
        return []

    now = time.time()
    time_windows = {
        "Last 24 Hours": 86400,
        "Last 7 Days": 86400 * 7,
        "Last 30 Days": 86400 * 30,
    }

    max_age_seconds = time_windows.get(filter_option)
    if not max_age_seconds:
        # Default: Latest News (all)
        return sorted(news_items, key=lambda x: x["published_timestamp"], reverse=True)

    cutoff = now - max_age_seconds
    filtered = [item for item in news_items if item["published_timestamp"] >= cutoff]

    # If strict window filters out everything, fall back to newest items rather than blanking out
    if not filtered:
        return sorted(news_items, key=lambda x: x["published_timestamp"], reverse=True)

    return sorted(filtered, key=lambda x: x["published_timestamp"], reverse=True)


def calculate_sentiment_summary(news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregate sentiment metrics for a collection of news articles."""
    if not news_items:
        return {
            "total_articles": 0,
            "positive_count": 0,
            "positive_pct": 0.0,
            "negative_count": 0,
            "negative_pct": 0.0,
            "neutral_count": 0,
            "neutral_pct": 0.0,
            "average_compound": 0.0,
            "overall_label": "Neutral",
        }

    total = len(news_items)
    pos = sum(1 for item in news_items if item["sentiment"]["label"] == "Positive")
    neg = sum(1 for item in news_items if item["sentiment"]["label"] == "Negative")
    neu = sum(1 for item in news_items if item["sentiment"]["label"] == "Neutral")
    avg_comp = sum(item["sentiment"]["compound"] for item in news_items) / total

    if pos > neg and pos >= neu:
        overall = "Bullish / Positive"
    elif neg > pos and neg >= neu:
        overall = "Bearish / Negative"
    else:
        overall = "Neutral / Balanced"

    return {
        "total_articles": total,
        "positive_count": pos,
        "positive_pct": round((pos / total) * 100.0, 1),
        "negative_count": neg,
        "negative_pct": round((neg / total) * 100.0, 1),
        "neutral_count": neu,
        "neutral_pct": round((neu / total) * 100.0, 1),
        "average_compound": round(avg_comp, 3),
        "overall_label": overall,
    }
