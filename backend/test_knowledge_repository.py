import json

from app.db.session import SessionLocal
from app.repositories.knowledge_repository import (
    search_articles,
    get_topics,
    get_knowledge_stats,
)


def main():
    db = SessionLocal()

    try:
        print("\n=== TEST 1: Knowledge Statistics ===")

        stats = get_knowledge_stats(db)

        print(json.dumps(stats, indent=2))

        print("\n=== TEST 2: Available Topics ===")

        topics = get_topics(db)

        print(json.dumps(topics, indent=2))

        print("\n=== TEST 3: Knowledge Search ===")

        query = "AI agents"

        articles, total = search_articles(
            db=db,
            query=query,
            page=1,
            page_size=5,
        )

        print(f"Search query: {query}")
        print(f"Total matches: {total}")

        for article in articles:
            print(f"\nID: {article.id}")
            print(f"Title: {article.title}")
            print(f"Category: {article.category}")
            print(f"URL: {article.url}")

        print("\nAll Knowledge repository tests completed.")

    finally:
        db.close()


if __name__ == "__main__":
    main()