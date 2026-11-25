"""Windows-friendly AI-Pulse scheduled pipeline runner."""

import argparse
import json
from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from uuid import uuid4

from app.scheduler.jobs import run_daily_pipeline
from app.scheduler.scheduler import (
    PipelineAlreadyRunning,
    exclusive_pipeline_lock,
)


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "data" / "pipeline_reports"


def main(argv=None):
    parser = argparse.ArgumentParser()

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--once", action="store_true")

    args = parser.parse_args(argv)

    if args.check:
        print("PASS: Scheduled runner available")
        print("Pipeline execution: disabled in check mode")
        print("Briefing generation: enabled for real runs")
        return 0

    try:
        with exclusive_pipeline_lock():
            # Avoid recording article text or verbose output.
            with redirect_stdout(StringIO()):
                report = run_daily_pipeline(
                    max_backfill=3,
                    max_classification=10,
                    include_briefing=True,
                    briefing_days=7,
                    briefing_max_articles=5,
                )

    except PipelineAlreadyRunning:
        print("SKIPPED: Another AI-Pulse pipeline is running")
        return 2

    except Exception as exc:
        report = {
            "status": "runner_failed",
            "failed_count": 1,
            "error_type": type(exc).__name__,
        }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    path = REPORT_DIR / (
        f"pipeline-{stamp}-{uuid4().hex[:8]}.json"
    )

    path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("Pipeline status:", report["status"])
    print("Report saved:", path)

    return 1 if report.get("failed_count", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
