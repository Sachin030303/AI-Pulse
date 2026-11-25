"""Daily AI-Pulse news processing jobs."""

from datetime import datetime, timezone
from time import monotonic

from app.services.ingestion_service import ingest_all_rss_sources
from app.services.backfill_service import backfill_missing_article_content
from app.services.classification_service import classify_missing_articles
from app.scheduler.briefing_job import create_daily_briefing


SAFE_METRICS = {
    "total", "processed", "inserted", "created", "updated",
    "skipped", "failed", "classified", "unclassified",
    "rss_successful", "webpage_successful", "generated",
}


def summarize_result(value):
    """Retain numeric statistics without exposing article content."""

    if not isinstance(value, dict):
        return {}

    return {
        key: item
        for key, item in value.items()
        if key in SAFE_METRICS
        and type(item) in (int, float)
    }


def run_daily_pipeline(
    max_backfill: int = 3,
    max_classification: int = 10,
    *,
    include_briefing: bool = False,
    briefing_days: int = 7,
    briefing_max_articles: int = 5,
) -> dict:
    """Run the existing services sequentially.

    Each stage reports failures independently.
    Importing this module never executes a pipeline.
    """

    if max_backfill < 0 or max_classification < 0:
        raise ValueError("Processing limits cannot be negative")

    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": [],
        "failed_count": 0,
    }

    steps = [
        (
            "ingestion",
            ingest_all_rss_sources,
            True,
        ),
        (
            "backfill",
            lambda: backfill_missing_article_content(
                max_articles=max_backfill,
                dry_run=False,
            ),
            max_backfill > 0,
        ),
        (
            "classification",
            lambda: classify_missing_articles(
                max_articles=max_classification,
                dry_run=False,
            ),
            max_classification > 0,
        ),
    ]

    if include_briefing:
        steps.append((
            "briefing",
            lambda: create_daily_briefing(
                days=briefing_days,
                max_articles=briefing_max_articles,
            ),
            True,
        ))

    for name, operation, enabled in steps:
        if not enabled:
            report["steps"].append({
                "name": name,
                "status": "skipped",
            })
            continue

        start = monotonic()

        try:
            result = operation()
            metrics = summarize_result(result)
            has_failures = metrics.get("failed", 0) > 0

            if has_failures:
                report["failed_count"] += 1

            report["steps"].append({
                "name": name,
                "status": (
                    "completed_with_errors"
                    if has_failures else "completed"
                ),
                "duration_seconds": round(
                    monotonic() - start, 2
                ),
                "metrics": metrics,
            })

        except Exception as exc:
            report["failed_count"] += 1
            report["steps"].append({
                "name": name,
                "status": "failed",
                "duration_seconds": round(
                    monotonic() - start, 2
                ),
                "error_type": type(exc).__name__,
            })

    report["finished_at"] = (
        datetime.now(timezone.utc).isoformat()
    )

    report["status"] = (
        "completed"
        if report["failed_count"] == 0
        else "completed_with_errors"
    )

    return report
