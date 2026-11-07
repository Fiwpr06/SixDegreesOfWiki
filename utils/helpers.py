"""Normalize a Wikipedia article title or pasted article URL."""

from urllib.parse import unquote, urlsplit


def parse_article_reference(value: str) -> tuple[str, str | None]:
    """Return (article title, URL language); plain titles have no URL language."""
    value = value.strip()
    if not value:
        raise ValueError("Vui lòng nhập tên bài viết hoặc URL Wikipedia.")

    if value.lower().startswith(("http://", "https://")):
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "vi.wikipedia.org", "en.wikipedia.org"
        }:
            raise ValueError("Chỉ hỗ trợ URL bài viết trên vi.wikipedia.org hoặc en.wikipedia.org.")
        if not parsed.path.startswith("/wiki/"):
            raise ValueError("URL Wikipedia phải có dạng /wiki/Ten_bai_viet.")
        title = unquote(parsed.path[len("/wiki/"):]).replace("_", " ").strip()
        if not title:
            raise ValueError("URL Wikipedia chưa có tên bài viết.")
        return title, parsed.hostname.split(".", 1)[0]

    return value.replace("_", " "), None
