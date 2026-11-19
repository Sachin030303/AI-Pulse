
"""Backfill missing article content from RSS feeds and webpages."""

import hashlib

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import Article, NewsSource
from app.ingestion.rss_collector import collect_rss_feed
from app.ingestion.content_extractor import extract_article_content


def generate_content_hash(
    title: str,
    article_text: str | None,
) -> str:
    """Generate a SHA-256 hash for article content."""

    content = f"{title.strip()} {article_text or ''}".strip().lower()

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def backfill_missing_article_content(
    max_articles: int | None = 3,
    dry_run: bool = True,
) -> dict:
    """
    Fill missing article content using RSS first, then webpage extraction.

    Args:
        max_articles: Maximum number of articles to process.
                     None means process all eligible articles.
        dry_run: If True, roll back database changes.
                 If False, commit changes.

    Returns:
        Dictionary containing backfill statistics.
    """

    if max_articles is not None and max_articles < 0:
        raise ValueError("max_articles cannot be negative.")

    db = SessionLocal()

    updated = 0
    rss_successful = 0
    webpage_successful = 0
    failed = 0
    skipped = 0
    failures = []

    try:
        # Find articles with missing, empty, or whitespace-only content.
        statement = (
            select(Article)
            .where(
                Article.content.is_(None)
                | (func.trim(Article.content) == "")
            )
            .order_by(Article.id)
        )

        if max_articles is not None:
            statement = statement.limit(max_articles)

        articles = db.scalars(statement).all()

        # Group incomplete articles by their source.
        articles_by_source = {}

        for article in articles:
            if article.source_id is None:
                skipped += 1
                continue

            articles_by_source.setdefault(
                article.source_id, []
            ).append(article)

        # Fetch each RSS feed only once per source.
        for source_id, source_articles in articles_by_source.items():

            source = db.get(NewsSource, source_id)

            if source is None:
                skipped += len(source_articles)
                continue

            try:
                rss_articles = collect_rss_feed(source.url)

                # Build URL lookup for RSS articles.
                rss_lookup = {
                    item["url"]: item
                    for item in rss_articles
                    if item.get("url")
                }

            except Exception as error:
                rss_lookup = {}

                print(
                    f"RSS fetch failed for {source.name}: {error}"
                )

            # Process articles belonging to this source.
            for article in source_articles:

                content = None
                method = None

                # First priority: Full RSS content.
                rss_item = rss_lookup.get(article.url)

                if rss_item:
                    content = rss_item.get("content")

                    if content and content.strip():
                        method = "rss"

                # Second priority: Webpage extraction.
                if not content or not content.strip():
                    try:
                        extracted = extract_article_content(
                            article.url
                        )

                        content = extracted.get("content")

                        if content and content.strip():
                            method = "webpage"

                    except Exception as error:
                        print(
                            f"Extraction failed for "
                            f"{article.url}: {error}"
                        )

                        content = None

                # Skip articles when no usable content was found.
                if not content or not content.strip():
                    failed += 1

                    failures.append({
                        "article_id": article.id,
                        "title": article.title,
                        "url": article.url,
                    })

                    continue

                # Update article content and hash.
                article.content = content.strip()

                article.content_hash = generate_content_hash(
                    article.title,
                    article.content,
                )

                updated += 1

                if method == "rss":
                    rss_successful += 1
                else:
                    webpage_successful += 1

        # Protect database during testing.
        if dry_run:
            db.rollback()
        else:
            db.commit()

        return {
            "dry_run": dry_run,
            "articles_checked": len(articles),
            "updated": updated,
            "rss_successful": rss_successful,
            "webpage_successful": webpage_successful,
            "failed": failed,
            "skipped": skipped,
            "failures": failures,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
