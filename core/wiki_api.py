"""MediaWiki Action API client with complete, direction-aware link caching."""

from datetime import timedelta
import json
from typing import Any, Callable, Iterator, Literal

import requests
from requests.adapters import HTTPAdapter
from sqlalchemy import select
from urllib3.util.retry import Retry

from config import Settings
from database import Database, PageCache
from database.models import utc_now


Direction = Literal["forward", "backward"]


class WikiAPIError(RuntimeError):
    """An API or response error that must not be cached as an empty page."""


class WikiAPI:
    def __init__(self, database: Database, settings: Settings | None = None, session: requests.Session | None = None):
        self.database = database
        self.settings = settings or database.settings
        self.session = session or requests.Session()
        if session is None:
            retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
            self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.headers.update({"User-Agent": "SixDegreesOfWiki/0.1 (educational Wikipedia graph explorer)"})
        self.cache_hits = 0
        self.cache_misses = 0

    @staticmethod
    def _validate(title: str, lang: str) -> str:
        if lang not in {"vi", "en"}:
            raise ValueError("Language must be 'vi' or 'en'")
        title = title.strip().replace("_", " ")
        if not title:
            raise ValueError("Article title must not be empty")
        return title

    def _query(self, lang: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.session.get(
                f"https://{lang}.wikipedia.org/w/api.php",
                params={"action": "query", "format": "json", "formatversion": 2, **params},
                timeout=self.settings.request_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise WikiAPIError(f"MediaWiki request failed: {exc}") from exc
        if not isinstance(payload, dict) or "error" in payload or "query" not in payload:
            raise WikiAPIError(f"Unexpected MediaWiki response: {payload!r}")
        return payload

    def resolve_title(self, title: str, lang: str = "vi") -> str:
        """Validate a main-namespace page and return its canonical title."""
        title = self._validate(title, lang)
        payload = self._query(lang, {"titles": title, "redirects": 1, "prop": "info"})
        pages = payload["query"].get("pages", [])
        if len(pages) != 1 or pages[0].get("missing") or pages[0].get("ns") != 0:
            raise ValueError(f"Article does not exist in Wikipedia namespace 0: {title}")
        return pages[0]["title"]

    def suggest_titles(self, prefix: str, lang: str = "vi", limit: int = 8) -> list[str]:
        """Suggest main-namespace article titles for the UI."""
        prefix = self._validate(prefix, lang)
        if not 1 <= limit <= 20:
            raise ValueError("Suggestion limit must be between 1 and 20")
        payload = self._query(lang, {
            "list": "prefixsearch", "pssearch": prefix,
            "psnamespace": 0, "pslimit": limit,
        })
        return [item["title"] for item in payload["query"].get("prefixsearch", [])]

    def get_links(self, title: str, lang: str = "vi", direction: Direction = "forward",
                  check: Callable[[], None] | None = None) -> list[str]:
        """Fetch all namespace-0 links; cache only complete successful responses."""
        return list(self.iter_links(title, lang, direction, check))

    def iter_links(self, title: str, lang: str = "vi", direction: Direction = "forward",
                   check: Callable[[], None] | None = None) -> Iterator[str]:
        """Yield links as API pages arrive; cache only after full consumption."""
        title = self._validate(title, lang)
        if direction not in {"forward", "backward"}:
            raise ValueError("Direction must be 'forward' or 'backward'")
        if check:
            check()
        with self.database.session() as db:
            cached = db.scalar(select(PageCache).where(
                PageCache.title == title, PageCache.lang == lang, PageCache.direction == direction
            ))
            if cached and cached.updated_at >= utc_now() - timedelta(seconds=self.settings.cache_ttl_seconds):
                self.cache_hits += 1
                yield from json.loads(cached.links_json)
                return

        self.cache_misses += 1
        links = []
        for link in self._iter_fetched_links(title, lang, direction, check):
            links.append(link)
            yield link
        with self.database.session() as db:
            cached = db.scalar(select(PageCache).where(
                PageCache.title == title, PageCache.lang == lang, PageCache.direction == direction
            ))
            if cached is None:
                cached = PageCache(title=title, lang=lang, direction=direction, links_json="[]", link_count=0)
                db.add(cached)
            cached.links_json = json.dumps(links, ensure_ascii=False)
            cached.link_count = len(links)
            cached.updated_at = utc_now()
            db.commit()

    def _iter_fetched_links(self, title: str, lang: str, direction: Direction,
                            check: Callable[[], None] | None = None) -> Iterator[str]:
        if direction == "forward":
            params: dict[str, Any] = {"prop": "links", "titles": title, "plnamespace": 0, "pllimit": "max"}
            result_key = "links"
        else:
            params = {"list": "backlinks", "bltitle": title, "blnamespace": 0, "bllimit": "max"}
            result_key = "backlinks"

        seen: set[str] = set()
        while True:
            if check:
                check()
            payload = self._query(lang, params)
            if check:
                check()
            query = payload["query"]
            if direction == "forward":
                pages = query.get("pages", [])
                if len(pages) != 1 or pages[0].get("missing") or pages[0].get("ns") != 0:
                    raise ValueError(f"Article does not exist in Wikipedia namespace 0: {title}")
                items = pages[0].get(result_key, [])
            else:
                items = query.get(result_key, [])
            for item in items:
                if item.get("ns") == 0 and isinstance(item.get("title"), str):
                    name = item["title"]
                    if name not in seen:
                        seen.add(name)
                        yield name
            continuation = payload.get("continue")
            if not continuation:
                break
            params.update(continuation)

