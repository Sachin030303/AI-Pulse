from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Article


db = SessionLocal()

try:
    articles = db.scalars(
        select(Article)
        .where(Article.source_id == 5)
        .order_by(Article.created_at.desc())
    ).all()

    for article in articles:
        print(f"TITLE: {article.title}")
        print(f"CONTENT LENGTH: {len(article.content or '')}")
        print(f"SUMMARY LENGTH: {len(article.summary or '')}")
        print(f"URL: {article.url}")
        print("-" * 60)

finally:
    db.close()