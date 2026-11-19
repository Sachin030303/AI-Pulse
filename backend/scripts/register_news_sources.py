import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import NewsSource

sources = [
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "source_type": "rss",
        "description": "Official Google AI news and announcements.",
    },
    {
        "name": "Microsoft AI Blog",
        "url": "https://news.microsoft.com/source/topics/ai/feed/",
        "source_type": "rss",
        "description": "Official Microsoft AI news and updates.",
    },
    {
        "name": "NVIDIA Developer Blog",
        "url": "https://developer.nvidia.com/blog/feed/",
        "source_type": "rss",
        "description": "NVIDIA developer articles, AI research and technology updates.",
    },
]

db = SessionLocal()

try:
    added = 0
    skipped = 0

    for item in sources:
        existing = db.scalar(
            select(NewsSource).where(NewsSource.url == item["url"])
        )

        if existing:
            print(f"Already registered: {item['name']}")
            skipped += 1
            continue

        db.add(NewsSource(**item))
        print(f"Registering: {item['name']}")
        added += 1

    db.commit()

    print("\nRegistration completed.")
    print("Added:", added)
    print("Skipped:", skipped)

except Exception:
    db.rollback()
    raise

finally:
    db.close()
