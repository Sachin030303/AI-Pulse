
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Article


db = SessionLocal()

try:
    articles = db.scalars(
        select(Article)
        .where(Article.source_id == 3)
        .order_by(Article.created_at.desc())
        .limit(5)
    ).all()

    for article in articles:
        print(f"TITLE: {article.title}")
        print(f"CONTENT LENGTH: {len(article.content or '')}")
        print(f"HASH: {article.content_hash[:16]}")
        print("-" * 50)

finally:
    db.close()
