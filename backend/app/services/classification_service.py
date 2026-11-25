
"""AI-powered article classification service."""

import re

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Article
from app.llm.gemini_client import generate_response


# Category IDs are mapped directly to their database values.
CATEGORIES = {
    1: "AI Models",
    2: "AI Agents",
    3: "Research",
    4: "Robotics",
    5: "Infrastructure",
    6: "Startups & Funding",
    7: "Products & Releases",
    8: "Policy & Regulation",
    9: "Industry News",
    10: "Other",
}


SYSTEM_PROMPT = """
You are a highly accurate AI industry news classification system.

Your task is to classify an article into EXACTLY ONE category.

AVAILABLE CATEGORIES:

1. AI Models
Model releases, LLM architectures, model capabilities,
model training, fine-tuning and model performance.

2. AI Agents
Autonomous AI agents, agent frameworks, agent orchestration,
multi-agent systems and agent workflows.

3. Research
Academic research, scientific experiments, research papers,
new benchmarks, evaluation methodologies and scientific
discoveries about artificial intelligence.

4. Robotics
Robots, embodied AI, autonomous machines and physical AI.

5. Infrastructure
AI inference engines, deployment frameworks, GPU systems,
chips, cloud computing, data centers, hardware backends,
local inference runtimes and AI developer infrastructure.

6. Startups & Funding
Startup launches, venture capital, investments,
funding rounds, acquisitions and company financing.

7. Products & Releases
New AI applications, commercial tools, software products,
product updates and feature announcements.

8. Policy & Regulation
AI legislation, government policies, governance,
regulation and safety policies.

9. Industry News
Major industry events, partnerships, company developments
and general AI business news.

10. Other
Content that does not meaningfully fit the above categories.


CLASSIFICATION RULES:

- Classify based on the PRIMARY SUBJECT, not keywords.
- Academic benchmarks and evaluation methodologies
  belong in Research.
- Inference engines and deployment runtimes belong
  in Infrastructure.
- New model releases and model architectures belong
  in AI Models.
- Commercial AI applications belong in Products & Releases.
- Do not classify every article mentioning an LLM as AI Models.

EXAMPLES:

XYBench academic AI evaluation benchmark: 3
llama.cpp local inference engine: 5
New Granite foundation model release: 1
Commercial AI writing application: 7

STRICT OUTPUT REQUIREMENTS:

Return ONLY the numeric ID of the best category.

Valid outputs:
1
2
3
4
5
6
7
8
9
10

Never return category names.
Never explain your decision.
Never return multiple numbers.
Never add punctuation or other text.
"""


def classify_article(title: str, text: str) -> str:
    """
    Classify an article and return its validated category name.
    """

    if not title or not title.strip():
        raise ValueError("Article title cannot be empty")

    if not text or not text.strip():
        raise ValueError("Article text cannot be empty")

    prompt = f"""
Article title:
{title.strip()}

Article content:
{text[:6000]}

Select the single best category.

Return ONLY its numeric ID.
"""

    response = generate_response(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.0,
    )

    result = response.strip()

    # Strictly accept only IDs from 1 to 10.
    if not re.fullmatch(r"(10|[1-9])", result):
        raise ValueError(
            f"Invalid classification response from Ollama: {response!r}"
        )

    category_id = int(result)

    return CATEGORIES[category_id]


def classify_missing_articles(
    max_articles: int = 10,
    dry_run: bool = False,
) -> dict:
    """
    Classify articles that do not have a category.

    Args:
        max_articles: Maximum number of articles to process.
        dry_run: If True, classify without saving to PostgreSQL.

    Returns:
        Dictionary containing processing statistics and results.
    """

    if max_articles < 1:
        raise ValueError("max_articles must be at least 1")

    db = SessionLocal()

    successful = 0
    failed = 0
    skipped = 0
    results = []

    try:
        query = (
            select(Article)
            .where(Article.category.is_(None))
            .order_by(Article.id)
            .limit(max_articles)
        )

        articles = db.execute(query).scalars().all()

        for article in articles:

            article_id = article.id
            article_title = article.title

            try:
                # Combine summary and content when available.
                text_parts = []

                if article.summary and article.summary.strip():
                    text_parts.append(article.summary.strip())

                if article.content and article.content.strip():
                    text_parts.append(article.content.strip())

                text = "\n\n".join(text_parts)

                # Skip articles without usable text.
                if not article_title or not article_title.strip():
                    skipped += 1

                    results.append({
                        "id": article_id,
                        "title": article_title,
                        "status": "skipped",
                        "reason": "Article title is empty",
                    })

                    continue

                if not text:
                    skipped += 1

                    results.append({
                        "id": article_id,
                        "title": article_title,
                        "status": "skipped",
                        "reason": "Article has neither summary nor content",
                    })

                    continue

                # Generate classification.
                category = classify_article(
                    title=article_title,
                    text=text,
                )

                # Save only when dry_run is disabled.
                if not dry_run:
                    article.category = category
                    db.commit()

                successful += 1

                results.append({
                    "id": article_id,
                    "title": article_title,
                    "category": category,
                    "status": "dry_run" if dry_run else "saved",
                })

            except Exception as exc:

                db.rollback()

                failed += 1

                results.append({
                    "id": article_id,
                    "title": article_title,
                    "status": "failed",
                    "error": str(exc),
                })

        return {
            "processed": successful + failed + skipped,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "dry_run": dry_run,
            "results": results,
        }

    finally:
        db.close()

