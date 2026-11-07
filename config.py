"""Configuration shared by the data and MediaWiki layers."""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    sqlite_path: Path = PROJECT_ROOT / "wiki_cache.db"
    request_timeout_seconds: float = 15.0
    cache_ttl_seconds: int = 604800
    default_max_depth: int = 3
    default_timeout_seconds: float = 30.0
    default_max_visited_nodes: int = 2000

    @classmethod
    def from_env(cls) -> "Settings":
        sqlite_path = Path(os.getenv("SQLITE_PATH", "wiki_cache.db"))
        if not sqlite_path.is_absolute():
            sqlite_path = PROJECT_ROOT / sqlite_path
        settings = cls(
            sqlite_path=sqlite_path,
            request_timeout_seconds=float(os.getenv("WIKI_REQUEST_TIMEOUT_SECONDS", "15")),
            cache_ttl_seconds=int(os.getenv("WIKI_CACHE_TTL_SECONDS", "604800")),
            default_max_depth=int(os.getenv("DEFAULT_MAX_DEPTH", "3")),
            default_timeout_seconds=float(os.getenv("DEFAULT_TIMEOUT_SECONDS", "30")),
            default_max_visited_nodes=int(os.getenv("DEFAULT_MAX_VISITED_NODES", "2000")),
        )
        if settings.request_timeout_seconds <= 0 or settings.cache_ttl_seconds < 0:
            raise ValueError("Request timeout must be positive and cache TTL non-negative")
        if not 0 <= settings.default_max_depth <= 6:
            raise ValueError("Default max depth must be between 0 and 6")
        if settings.default_timeout_seconds <= 0 or settings.default_max_visited_nodes <= 0:
            raise ValueError("Search timeout and node limit must be positive")
        return settings

