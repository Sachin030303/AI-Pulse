
"""Extract readable article content from web pages."""

import httpx
from bs4 import BeautifulSoup


def extract_article_content(url: str) -> dict:
    """
    Extract the title and readable text from an article webpage.

    Returns:
        {
            "title": str | None,
            "content": str | None,
            "url": str
        }
    """

    headers = {
        "User-Agent": "AI-Pulse/1.0 (Article Content Extractor)"
    }

    try:
        response = httpx.get(
            url,
            headers=headers,
            timeout=20.0,
            follow_redirects=True,
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove elements that do not contain article content.
        for element in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
            "noscript",
        ]):
            element.decompose()

        # Extract page title.
        title = None

        if soup.title:
            title = soup.title.get_text(strip=True)

        # Find the main article content.
        article = soup.find("article")

        if article is None:
            article = soup.find("main")

        if article is None:
            article = soup.body

        if article is None:
            return {
                "title": title,
                "content": None,
                "url": str(response.url),
            }

        # Extract readable text.
        content = article.get_text(
            separator="\n",
            strip=True,
        )

        # Normalize excessive blank lines.
        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        content = "\n".join(lines)

        return {
            "title": title,
            "content": content or None,
            "url": str(response.url),
        }

    except httpx.HTTPError as error:
        raise RuntimeError(
            f"Failed to extract article from {url}: {error}"
        ) from error
