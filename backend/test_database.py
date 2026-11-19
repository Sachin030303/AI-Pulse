
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import NewsSource

db = SessionLocal()

try:
    feed_url = "https://huggingface.co/blog/feed.xml"

    source = db.execute(
        select(NewsSource).where(
            NewsSource.url == feed_url
        )
    ).scalar_one_or_none()

    if source is None:
        source = NewsSource(
            name="Hugging Face Blog",
            url=feed_url,
            source_type="rss",
            description="Official Hugging Face technical blogs and AI announcements",
        )

        db.add(source)
        db.commit()
        db.refresh(source)

        print("Hugging Face RSS source registered!")
    else:
        print("Hugging Face RSS source already exists!")

    print("ID:", source.id)
    print("Name:", source.name)
    print("URL:", source.url)
    print("Type:", source.source_type)

except Exception as error:
    db.rollback()
    print("Error:", error)

finally:
    db.close()
