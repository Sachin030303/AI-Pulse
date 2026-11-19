
"""Service for ingesting articles from registered RSS sources."""

import hashlib
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import NewsSource, Article
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


def ingest_rss_source(source_id: int) -> dict:
    """Fetch RSS articles and save new articles with available content."""

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

        incoming_urls = {
            item["url"]
            for item in fetched_articles
            if item.get("url")
        }

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

        extraction_successful = 0
        extraction_failed = 0
        extraction_not_needed = 0

        for item in fetched_articles:
            url = item.get("url")

            if not url:
                continue

            if url in existing_urls or url in seen_urls:
                continue

            seen_urls.add(url)

            title = item["title"]
            summary = item.get("summary")
            content = item.get("content")

            # Use webpage extraction when RSS has no full content.
            if not content:
                try:
                    extracted = extract_article_content(url)

                    content = extracted.get("content")

                    if content:
                        extraction_successful += 1
                    else:
                        extraction_failed += 1

                except Exception as error:
                    extraction_failed += 1
                    print(
                        f"Content extraction failed for {url}: {error}"
                    )

            else:
                extraction_not_needed += 1

            article = Article(
                source_id=source.id,
                title=title,
                url=url,
                summary=summary,
                content=content,
                content_hash=generate_content_hash(
                    title,
                    content or summary,
                ),
                published_at=item.get("published_at"),
            )

            inserted_articles.append(article)

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
            "extraction_successful": extraction_successful,
            "extraction_failed": extraction_failed,
            "extraction_not_needed": extraction_not_needed,
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
