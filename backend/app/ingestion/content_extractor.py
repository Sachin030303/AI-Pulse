"""Extract readable article content from web pages."""

import httpx
from bs4 import BeautifulSoup


# Common webpage elements that are not article content.
REMOVE_TAGS = [
    "script",
    "style",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
    "noscript",
    "button",
    "svg",
    "iframe",
    "img",
    "input",
    "select",
    "textarea",
]


# Common UI-related class names and IDs.
REMOVE_KEYWORDS = [
    "comment",
    "related",
    "recommend",
    "social",
    "share",
    "subscribe",
    "newsletter",
    "signup",
    "sign-up",
    "upvote",
    "vote-button",
    "follow-button",
    "sidebar",
    "breadcrumb",
    "pagination",
    "toolbar",
    "modal",
    "popup",
    "advertisement",
    "ad-container",
]


# UI text that may appear as standalone lines.
REMOVE_TEXT_LINES = {
    "back to articles",
    "upvote",
    "follow",
    "unfollow",
    "comment",
    "comments",
    "share",
    "subscribe",
    "sign up",
    "log in",
    "login",
}


# Minimum length required for extracted article content.
MIN_CONTENT_LENGTH = 300


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
        # Fetch webpage.
        response = httpx.get(
            url,
            headers=headers,
            timeout=20.0,
            follow_redirects=True,
        )

        response.raise_for_status()

        # Parse HTML.
        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # --------------------------------------------------
        # 1. Remove unwanted HTML tags.
        # --------------------------------------------------

        for element in soup(REMOVE_TAGS):
            element.decompose()

        # --------------------------------------------------
        # 2. Identify UI-related elements.
        # --------------------------------------------------

        elements_to_remove = []

        for element in soup.find_all(True):

            # Ignore already detached elements.
            if element.attrs is None:
                continue

            element_classes = element.get("class", [])
            element_id = element.get("id", "")

            # Normalize class attributes.
            if isinstance(element_classes, str):
                element_classes = [element_classes]

            if not isinstance(element_id, str):
                element_id = ""

            metadata = " ".join(
                element_classes + [element_id]
            ).lower()

            # Check whether the element contains UI keywords.
            if any(
                keyword in metadata
                for keyword in REMOVE_KEYWORDS
            ):
                elements_to_remove.append(element)

        # --------------------------------------------------
        # 3. Remove identified elements.
        # --------------------------------------------------

        for element in elements_to_remove:

            # A parent may have already removed this element.
            if element.parent is not None:
                element.decompose()

        # --------------------------------------------------
        # 4. Extract page title.
        # --------------------------------------------------

        title = None

        if soup.title:
            title = soup.title.get_text(
                separator=" ",
                strip=True,
            )

        # Prefer Open Graph title when available.
        og_title = soup.find(
            "meta",
            property="og:title",
        )

        if og_title and og_title.get("content"):
            title = og_title["content"].strip()

        # --------------------------------------------------
        # 5. Locate main article content.
        # --------------------------------------------------

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

        # --------------------------------------------------
        # 6. Extract readable text.
        # --------------------------------------------------

        raw_content = article.get_text(
            separator="\n",
            strip=True,
        )

        # --------------------------------------------------
        # 7. Clean and normalize text.
        # --------------------------------------------------

        lines = []

        for line in raw_content.splitlines():

            line = line.strip()

            # Ignore empty lines.
            if not line:
                continue

            # Remove common UI labels.
            if line.lower() in REMOVE_TEXT_LINES:
                continue

            # Remove consecutive duplicate lines.
            if lines and line == lines[-1]:
                continue

            lines.append(line)

        content = "\n".join(lines)

        # --------------------------------------------------
        # 8. Validate extracted content.
        # --------------------------------------------------

        if len(content) < MIN_CONTENT_LENGTH:
            content = None

        # --------------------------------------------------
        # 9. Return result.
        # --------------------------------------------------

        return {
            "title": title,
            "content": content,
            "url": str(response.url),
        }

    except httpx.HTTPError as error:

        raise RuntimeError(
            f"Failed to extract article from {url}: {error}"
        ) from error