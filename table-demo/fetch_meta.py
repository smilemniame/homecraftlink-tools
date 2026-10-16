from typing import Optional
from bs4 import BeautifulSoup


def extract_page_title(html: str) -> Optional[str]:
    """
    Extract the title from HTML that has already been fetched.
    This module does not make HTTP requests.
    """

    if not isinstance(html, str) or not html:
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("title")

        if not title_tag:
            return ""

        title = title_tag.get_text(" ", strip=True)

        return title or ""

    except Exception:
        return None