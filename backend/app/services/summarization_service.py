import re
from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.models import Article
from app.llm.ollama_client import generate_response


SYSTEM_PROMPT = """
You are a professional news intelligence analyst.

Summarize news articles for a news intelligence dashboard.

STRICT OUTPUT RULES:
- Write exactly 3 sentences.
- Keep the summary between 60 and 100 words.
- Output exactly one paragraph.
- Focus on the most important information.
- Preserve important names, organizations, numbers, and events.
- Do not add facts that are not in the article.
- Do not speculate or express opinions.
- Use neutral, clear language.
- Do not use bullet points.
- Do not include headings.
- Do not repeat the article title.
- Output only the summary.
"""

def clean_summary_output(summary: str) -> str:
    """Clean common formatting artifacts from AI-generated summaries."""

    if not summary:
        return ""

    summary = summary.strip()

    # Remove common AI-generated introductory phrases
    preamble_patterns = [
        r"^(here is|here's|below is)\s+(an?\s+)?"
        r"(accurate\s+)?(news\s+)?summary\s*:\s*",

        r"^a news summary of the provided text.*?"
        r"(is as follows|as follows)\s*:\s*",

        r"^this news summary discusses\s*:\s*",

        r"^here['’]s a news summary of the article"
        r".*?:\s*",

        r"^the following is a summary\s*:\s*",
    ]

    for pattern in preamble_patterns:
        summary = re.sub(
            pattern,
            "",
            summary,
            flags=re.IGNORECASE | re.DOTALL,
        )

    # Remove markdown horizontal separators
    summary = re.sub(r"(?m)^\s*[-*_]{3,}\s*$", "", summary)

    # Remove bullet markers, including inline bullets
    summary = re.sub(r"(?m)(^|\s)[-*•]\s+", r"\1", summary)

    # Remove numbered list markers, including inline numbering
    summary = re.sub(r"(?m)(^|\s)\d+[.)]\s+", r"\1", summary)

    # Normalize whitespace
    summary = re.sub(r"\s+", " ", summary)

    return summary.strip()

def summarize_article_text(title: str, content: str) -> str:
    """Generate a concise summary of a news article."""

    if not content or not content.strip():
        raise ValueError("Article content cannot be empty.")

    prompt = f"""
Article title:
{title}

Article content:
{content}

Write an accurate news summary following the instructions.
"""

    summary = generate_response(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.2,
    )

    summary = clean_summary_output(summary)

    if not summary:
        raise ValueError("The AI returned an empty summary.")

    return summary


def summarize_missing_articles(
    max_articles: int = 3,
    dry_run: bool = False,
) -> dict:
    """
    Summarize articles that have content but no existing summary.

    Each successful article is committed individually.
    """

    db = SessionLocal()

    try:
        statement = (
            select(Article)
            .where(
                Article.content.is_not(None),
                func.trim(Article.content) != "",
                (
                    Article.summary.is_(None)
                    | (func.trim(Article.summary) == "")
                ),
            )
            .order_by(Article.id.asc())
            .limit(max_articles)
        )

        articles = db.scalars(statement).all()

        if dry_run:
            return {
                "dry_run": True,
                "selected": len(articles),
                "article_ids": [article.id for article in articles],
                "message": "No summaries generated or saved.",
            }

        successful = []
        failed = []

        for article in articles:
            try:
                summary = summarize_article_text(
                    title=article.title,
                    content=article.content,
                )

                article.summary = summary
                db.commit()

                successful.append({
                    "article_id": article.id,
                    "title": article.title,
                    "summary": summary,
                })

            except Exception as error:
                db.rollback()

                failed.append({
                    "article_id": article.id,
                    "title": article.title,
                    "error": str(error),
                })

        return {
            "selected": len(articles),
            "successful": len(successful),
            "failed": len(failed),
            "results": successful,
            "failures": failed,
        }

    finally:
        db.close()