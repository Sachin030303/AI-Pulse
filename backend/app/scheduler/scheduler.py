"""Run AI-Pulse daily processing as a separate process."""

import argparse
import hashlib
import json
import os
import tempfile

from contextlib import contextmanager
from pathlib import Path

from app.scheduler.jobs import run_daily_pipeline


ROOT = Path(__file__).resolve().parents[2]

LOCK_NAME = (
    "ai-pulse-"
    + hashlib.sha256(
        str(ROOT).encode("utf-8")
    ).hexdigest()[:16]
    + ".lock"
)

LOCK_PATH = Path(tempfile.gettempdir()) / LOCK_NAME


class PipelineAlreadyRunning(RuntimeError):
    """Another pipeline process holds the lock."""


@contextmanager
def exclusive_pipeline_lock():
    """Prevent overlapping runs on Windows and Unix."""

    with LOCK_PATH.open("a+b") as handle:
        # Do not read or write the byte before locking it.
        # Windows supports locking ranges beyond the end of a file.
        handle.seek(0)

        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(
                    handle.fileno(),
                    msvcrt.LK_NBLCK,
                    1,
                )
            except OSError:
                raise PipelineAlreadyRunning(
                    "Another pipeline run is active"
                ) from None

            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(
                    handle.fileno(),
                    msvcrt.LK_UNLCK,
                    1,
                )

        else:
            import fcntl

            try:
                fcntl.flock(
                    handle.fileno(),
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
            except BlockingIOError:
                raise PipelineAlreadyRunning(
                    "Another pipeline run is active"
                ) from None

            try:
                yield
            finally:
                fcntl.flock(
                    handle.fileno(),
                    fcntl.LOCK_UN,
                )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="AI-Pulse daily news pipeline"
    )

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument(
        "--check",
        action="store_true",
        help="Show configuration without processing articles",
    )

    mode.add_argument(
        "--once",
        action="store_true",
        help="Execute one real pipeline run",
    )

    parser.add_argument(
        "--backfill-limit",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--classification-limit",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--with-briefing",
        action="store_true",
        help="Generate and save a Gemini briefing",
    )

    parser.add_argument(
        "--briefing-days",
        type=int,
        default=7,
    )

    parser.add_argument(
        "--briefing-max-articles",
        type=int,
        default=5,
    )

    args = parser.parse_args(argv)

    if args.backfill_limit < 0 or args.classification_limit < 0:
        parser.error("Limits must be nonnegative")

    if not 1 <= args.briefing_days <= 30:
        parser.error("Briefing days must be between 1 and 30")

    if not 1 <= args.briefing_max_articles <= 20:
        parser.error("Briefing article limit must be between 1 and 20")

    if args.check:
        print(json.dumps({
            "mode": "check_only",
            "ingestion": "enabled",
            "backfill_limit": args.backfill_limit,
            "classification_limit": args.classification_limit,
            "briefing": (
                "enabled" if args.with_briefing else "disabled"
            ),
            "database_changes": False,
        }, indent=2))
        return 0

    try:
        with exclusive_pipeline_lock():
            options = {
                "max_backfill": args.backfill_limit,
                "max_classification": args.classification_limit,
            }

            if args.with_briefing:
                options.update({
                    "include_briefing": True,
                    "briefing_days": args.briefing_days,
                    "briefing_max_articles": args.briefing_max_articles,
                })

            report = run_daily_pipeline(**options)

    except PipelineAlreadyRunning:
        print("SKIPPED: Another pipeline run is active")
        return 2

    print(json.dumps(report, indent=2))
    return 1 if report["failed_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
