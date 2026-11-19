
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx
from bs4 import BeautifulSoup


def clean_html(value: str | None) -> str | None:
    """Remove HTML tags and normalize text."""

    if not value:
        return None

    soup = BeautifulSoup(value, "html.parser")
    cleaned = soup.get_text(separator="\n", strip=True)

    lines = [
        line.strip()
        for line in cleaned.splitlines()
        if line.strip()
    ]

    return "\n".join(lines) or None


def is_generic_summary(value: str | None) -> bool:
    """Identify low-quality RSS summaries."""

    if not value:
        return True

    text = value.lower()

    generic_patterns = [
        "appeared first on",
        "the post",
    ]

    return any(
        pattern in text
        for pattern in generic_patterns
    )


def extract_rss_content(entry: Any) -> str | None:
    """Extract full article text from RSS content."""

    contents = entry.get("content", [])

    for item in contents:
        cleaned = clean_html(item.get("value", ""))

        if cleaned and len(cleaned) > 300:
            return cleaned

    return None


def extract_rss_summary(entry: Any) -> str | None:
    """Extract a meaningful short RSS description."""

    summary = clean_html(entry.get("summary"))

    if summary and not is_generic_summary(summary):
        return summary

    description = clean_html(entry.get("description"))

    if description and not is_generic_summary(description):
        return description

    return None


def parse_published_date(entry: Any) -> datetime | None:
    """Convert RSS publication date into a timezone-aware datetime."""

    published = (
        entry.get("published_parsed")
        or entry.get("updated_parsed")
    )

    if not published:
        return None

    return datetime(
        *published[:6],
        tzinfo=timezone.utc,
    )


def collect_rss_feed(feed_url: str) -> list[dict]:
    """Fetch and normalize RSS articles."""

    articles = []

    try:
        response = httpx.get(
            feed_url,
            timeout=20.0,
            follow_redirects=True,
            headers={
                "User-Agent": "AI-Pulse/1.0 RSS Reader"
            },
        )

        response.raise_for_status()

        feed = feedparser.parse(response.content)

        for entry in feed.entries:

            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()

            if not title or not url:
                continue

            article = {
                "title": title,
                "url": url,
                "summary": extract_rss_summary(entry),
                "content": extract_rss_content(entry),
                "published_at": parse_published_date(entry),
            }

            articles.append(article)

        return articles

    except httpx.HTTPError as error:
        raise RuntimeError(
            f"Failed to fetch RSS feed {feed_url}: {error}"
        ) from error

    except Exception as error:
        raise RuntimeError(
            f"Failed to parse RSS feed {feed_url}: {error}"
        ) from error
