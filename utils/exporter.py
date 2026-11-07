"""Create downloadable JSON reports for current and historical searches."""

from datetime import timezone
import json
from urllib.parse import quote

from core.search_types import SearchResult
from database.models import SearchHistory


def article_url(title: str, lang: str) -> str:
    return f"https://{lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'), safe='')}"


def _path_items(path: list[str], lang: str) -> list[dict]:
    return [
        {"step": index, "title": title, "url": article_url(title, lang),
         "role": "START" if index == 0 else "TARGET" if index == len(path) - 1 else "INTERMEDIATE"}
        for index, title in enumerate(path)
    ]


def report_from_result(result: SearchResult) -> dict:
    return {
        "project": "SixDegreesOfWiki - Wikipedia Link Depth Analyzer",
        "query": {
            "start_article": result.start,
            "target_article": result.target,
            "language": result.lang,
            "algorithm_used": result.algorithm,
            "timestamp": result.created_at.isoformat(),
        },
        "results": {
            "status": result.status,
            "found": result.found,
            "depth": result.depth if result.found else None,
            "intermediate_articles_count": result.intermediate_count,
            "path": _path_items(result.path, result.lang),
            "intermediate_articles_list": result.path[1:-1],
        },
        "performance": {
            "execution_time_seconds": round(result.elapsed_seconds, 3),
            "total_nodes_visited": result.visited_nodes,
            "expanded_nodes": result.expanded_nodes,
            "cache_hits": result.cache_hits,
            "cache_misses": result.cache_misses,
            "cache_hit_rate_percent": round(result.cache_hit_rate, 1),
            "database_engine": "SQLite",
        },
    }


def report_from_history(row: SearchHistory) -> dict:
    path = json.loads(row.path_json)
    return {
        "project": "SixDegreesOfWiki - Wikipedia Link Depth Analyzer",
        "query": {
            "start_article": row.start_title, "target_article": row.target_title,
            "language": row.lang, "algorithm_used": row.algorithm,
            "timestamp": row.created_at.replace(tzinfo=timezone.utc).isoformat(),
        },
        "results": {
            "status": row.status, "found": row.status == "found",
            "depth": row.depth if row.status == "found" else None,
            "intermediate_articles_count": row.intermediate_count,
            "path": _path_items(path, row.lang),
            "intermediate_articles_list": path[1:-1],
        },
        "performance": {
            "execution_time_seconds": round(row.execution_time, 3),
            "total_nodes_visited": row.nodes_visited,
            "expanded_nodes": row.expanded_nodes,
            "cache_hits": row.cache_hits,
            "cache_misses": row.cache_misses,
            "cache_hit_rate_percent": round(100 * row.cache_hits / (row.cache_hits + row.cache_misses), 1)
                                      if row.cache_hits + row.cache_misses else 0.0,
            "database_engine": "SQLite",
        },
    }


def to_json(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)

