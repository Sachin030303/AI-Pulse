
"""Service for ingesting articles from registered RSS sources."""

import hashlib
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import NewsSource, Article
from app.ingestion.rss_collector import collect_rss_feed


def generate_content_hash(title: str, summary: str | None) -> str:
    """Generate a SHA-256 hash for article content."""

    content = f"{title.strip()} {summary or ''}".strip().lower()

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def ingest_rss_source(source_id: int) -> dict:
    """Fetch RSS articles and efficiently save only new articles."""

    db = SessionLocal()

    try:
        source = db.execute(
            select(NewsSource).where(
                NewsSource.id == source_id,
                NewsSource.is_active.is_(True),
            )
        ).scalar_one_or_none()

        if source is None:
            raise ValueError(
                f"Active news source {source_id} was not found."
            )

        fetched_articles = collect_rss_feed(source.url)

        # Collect unique URLs from the incoming feed.
        incoming_urls = {
            item["url"]
            for item in fetched_articles
            if item.get("url")
        }

        # Fetch all existing URLs in one database query.
        existing_urls = set()

        if incoming_urls:
            existing_urls = set(
                db.scalars(
                    select(Article.url).where(
                        Article.url.in_(incoming_urls)
                    )
                ).all()
            )

        inserted_articles = []
        seen_urls = set()

        for item in fetched_articles:
            url = item.get("url")

            if not url:
                continue

            # Skip URLs already in the database or this feed batch.
            if url in existing_urls or url in seen_urls:
                continue

            seen_urls.add(url)

            article = Article(
                source_id=source.id,
                title=item["title"],
                url=url,
                summary=item.get("summary"),
                content_hash=generate_content_hash(
                    item["title"],
                    item.get("summary"),
                ),
                published_at=item.get("published_at"),
            )

            inserted_articles.append(article)

        # Add all new articles together.
        if inserted_articles:
            db.add_all(inserted_articles)

        source.last_fetched_at = datetime.now(timezone.utc)

        db.commit()

        inserted = len(inserted_articles)
        skipped = len(fetched_articles) - inserted

        return {
            "source": source.name,
            "fetched": len(fetched_articles),
            "inserted": inserted,
            "skipped": skipped,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
def ingest_all_rss_sources() -> dict:
    """Ingest articles from every active RSS source."""

    db = SessionLocal()

    try:
        sources = db.scalars(
            select(NewsSource).where(
                NewsSource.is_active.is_(True),
                NewsSource.source_type == "rss",
            )
        ).all()

        # Extract IDs before closing the database session.
        source_ids = [source.id for source in sources]

    finally:
        db.close()

    results = []
    failures = []

    for source_id in source_ids:
        try:
            result = ingest_rss_source(source_id)
            results.append(result)

        except Exception as error:
            failures.append({
                "source_id": source_id,
                "error": str(error),
            })

    return {
        "total_sources": len(source_ids),
        "successful": len(results),
        "failed": len(failures),
        "results": results,
        "failures": failures,
    }