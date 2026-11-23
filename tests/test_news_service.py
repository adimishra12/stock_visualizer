"""Unit tests for the Company News and Sentiment Service.

Validates VADER sentiment classification, heterogeneous news payload normalization,
timeframe filtering, and aggregate sentiment metrics calculation without live network calls.
"""

import time
import unittest

from src.services.news_service import (
    calculate_sentiment_summary,
    classify_headline_sentiment,
    filter_news_by_time,
    normalize_news_item,
)


class TestNewsService(unittest.TestCase):
    def test_classify_headline_sentiment_positive(self):
        """Test sentiment classification for distinctly bullish headlines."""
        headline = "NVIDIA Reports Record Profit Surge and Unprecedented AI Revenue Growth"
        res = classify_headline_sentiment(headline)
        self.assertEqual(res["label"], "Positive")
        self.assertGreaterEqual(res["compound"], 0.05)
        self.assertGreater(res["pos"], 0.0)

    def test_classify_headline_sentiment_negative(self):
        """Test sentiment classification for distinctly bearish headlines."""
        headline = "Company Shares Slump Sharply After Disastrous Earnings Miss and Severe Profit Warning"
        res = classify_headline_sentiment(headline)
        self.assertEqual(res["label"], "Negative")
        self.assertLessEqual(res["compound"], -0.05)
        self.assertGreater(res["neg"], 0.0)

    def test_classify_headline_sentiment_neutral_or_empty(self):
        """Test sentiment classification for neutral or empty input."""
        res_empty = classify_headline_sentiment("")
        self.assertEqual(res_empty["label"], "Neutral")
        self.assertEqual(res_empty["compound"], 0.0)

        res_none = classify_headline_sentiment(None)
        self.assertEqual(res_none["label"], "Neutral")

        res_neu = classify_headline_sentiment("The executive committee will convene on Tuesday morning")
        self.assertEqual(res_neu["label"], "Neutral")

    def test_normalize_news_item_yfinance_nested_schema(self):
        """Test normalizer against yfinance 1.8.0 nested 'content' dictionary format."""
        raw_item = {
            "id": "abc-123",
            "content": {
                "id": "content-123",
                "title": "Apple unveils groundbreaking M4 Max MacBook Pro",
                "summary": "Apple announced new hardware models with high performance processors.",
                "pubDate": "2026-11-23T10:00:00Z",
                "provider": {"displayName": "Reuters"},
                "canonicalUrl": {"url": "https://reuters.com/apple-m4-review"},
            },
        }

        norm = normalize_news_item(raw_item, "AAPL")
        self.assertIsNotNone(norm)
        self.assertEqual(norm["title"], "Apple unveils groundbreaking M4 Max MacBook Pro")
        self.assertEqual(norm["publisher"], "Reuters")
        self.assertEqual(norm["url"], "https://reuters.com/apple-m4-review")
        self.assertEqual(norm["related_ticker"], "AAPL")
        self.assertIn("published_at", norm)
        self.assertIn("sentiment", norm)

    def test_normalize_news_item_legacy_schema(self):
        """Test normalizer against legacy top-level yfinance news format."""
        raw_item = {
            "uuid": "xyz-999",
            "title": "Microsoft and OpenAI Expand Strategic Infrastructure Agreement",
            "publisher": "Bloomberg",
            "link": "https://bloomberg.com/msft-openai",
            "providerPublishTime": 1700000000,
        }

        norm = normalize_news_item(raw_item, "MSFT")
        self.assertIsNotNone(norm)
        self.assertEqual(norm["title"], "Microsoft and OpenAI Expand Strategic Infrastructure Agreement")
        self.assertEqual(norm["publisher"], "Bloomberg")
        self.assertEqual(norm["url"], "https://bloomberg.com/msft-openai")
        self.assertEqual(norm["published_timestamp"], 1700000000.0)

    def test_normalize_news_item_invalid(self):
        """Test invalid news items return None gracefully."""
        self.assertIsNone(normalize_news_item(None, "AAPL"))
        self.assertIsNone(normalize_news_item({}, "AAPL"))
        self.assertIsNone(normalize_news_item({"title": "   "}, "AAPL"))
        self.assertIsNone(normalize_news_item("not a dict", "AAPL"))

    def test_filter_news_by_time(self):
        """Test time window filtering across 24h, 7d, 30d, and default."""
        now = time.time()
        articles = [
            {"title": "1 Hour Ago", "published_timestamp": now - 3600},
            {"title": "2 Days Ago", "published_timestamp": now - 172800},
            {"title": "15 Days Ago", "published_timestamp": now - 1296000},
            {"title": "45 Days Ago", "published_timestamp": now - 3888000},
        ]

        f_24h = filter_news_by_time(articles, "Last 24 Hours")
        self.assertEqual(len(f_24h), 1)
        self.assertEqual(f_24h[0]["title"], "1 Hour Ago")

        f_7d = filter_news_by_time(articles, "Last 7 Days")
        self.assertEqual(len(f_7d), 2)

        f_30d = filter_news_by_time(articles, "Last 30 Days")
        self.assertEqual(len(f_30d), 3)

        f_all = filter_news_by_time(articles, "Latest News")
        self.assertEqual(len(f_all), 4)

    def test_calculate_sentiment_summary(self):
        """Test aggregate sentiment metrics calculation."""
        news_items = [
            {"sentiment": {"label": "Positive", "compound": 0.65}},
            {"sentiment": {"label": "Positive", "compound": 0.45}},
            {"sentiment": {"label": "Negative", "compound": -0.50}},
            {"sentiment": {"label": "Neutral", "compound": 0.0}},
        ]

        summary = calculate_sentiment_summary(news_items)
        self.assertEqual(summary["total_articles"], 4)
        self.assertEqual(summary["positive_count"], 2)
        self.assertEqual(summary["positive_pct"], 50.0)
        self.assertEqual(summary["negative_count"], 1)
        self.assertEqual(summary["negative_pct"], 25.0)
        self.assertEqual(summary["neutral_count"], 1)
        self.assertEqual(summary["neutral_pct"], 25.0)
        self.assertAlmostEqual(summary["average_compound"], 0.15, places=2)
        self.assertIn("Bullish", summary["overall_label"])

        # Empty test
        empty_summary = calculate_sentiment_summary([])
        self.assertEqual(empty_summary["total_articles"], 0)
        self.assertEqual(empty_summary["overall_label"], "Neutral")


if __name__ == "__main__":
    unittest.main()
