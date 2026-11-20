import json
import time

from app.db.session import SessionLocal
from app.services.knowledge_service import ask_knowledge


def main():
    db = SessionLocal()

    try:
        question = "What are the latest developments in AI agents?"

        start_time = time.perf_counter()

        result = ask_knowledge(
            db=db,
            question=question,
            max_sources=3,
        )

        print(json.dumps(
            result.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        ))

        print(f"\nResponse time: {time.perf_counter() - start_time:.2f} seconds")

    finally:
        db.close()


if __name__ == "__main__":
    main()