"""Persist and read search runs from SQLite."""

import json

from sqlalchemy import select

from core.search_types import SearchResult
from .connection import Database
from .models import SearchHistory


def save_search(database: Database, result: SearchResult) -> int:
    with database.session() as db:
        row = SearchHistory(
            start_title=result.start,
            target_title=result.target,
            lang=result.lang,
            algorithm=result.algorithm,
            status=result.status,
            depth=result.depth,
            intermediate_count=result.intermediate_count,
            path_json=json.dumps(result.path, ensure_ascii=False),
            execution_time=result.elapsed_seconds,
            nodes_visited=result.visited_nodes,
            expanded_nodes=result.expanded_nodes,
            cache_hits=result.cache_hits,
            cache_misses=result.cache_misses,
            created_at=result.created_at.replace(tzinfo=None),
        )
        db.add(row)
        db.flush()
        row_id = row.id
        db.commit()
        return row_id


def list_searches(database: Database, limit: int = 100) -> list[SearchHistory]:
    with database.session() as db:
        return list(db.scalars(
            select(SearchHistory).order_by(SearchHistory.created_at.desc(), SearchHistory.id.desc()).limit(limit)
        ))

