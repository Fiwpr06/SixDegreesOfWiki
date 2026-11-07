"""Shared result, limits and accounting for bounded graph searches."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import monotonic
from typing import Callable


ProgressCallback = Callable[[int, int | None], None]


@dataclass(frozen=True)
class SearchProgress:
    algorithm: str
    iteration_depth: int
    max_depth: int | None
    side: str
    phase: str
    title: str
    path_tail: tuple[str, ...]
    visited_nodes: int
    expanded_nodes: int
    cache_hits: int
    cache_misses: int
    elapsed_seconds: float


TraceCallback = Callable[[SearchProgress], None]


@dataclass(frozen=True)
class SearchLimits:
    max_depth: int | None = 3
    timeout_seconds: float | None = 30.0
    max_visited_nodes: int | None = 2000

    def __post_init__(self) -> None:
        if self.max_depth is not None and not 0 <= self.max_depth <= 6:
            raise ValueError("max_depth must be between 0 and 6")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout must be positive")
        if self.max_visited_nodes is not None and self.max_visited_nodes <= 0:
            raise ValueError("timeout and max_visited_nodes must be positive")


@dataclass
class SearchResult:
    algorithm: str
    start: str
    target: str
    lang: str
    status: str
    path: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    visited_nodes: int = 0
    expanded_nodes: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    edges: list[tuple[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def found(self) -> bool:
        return self.status == "found"

    @property
    def depth(self) -> int:
        return len(self.path) - 1 if self.found else -1

    @property
    def intermediate_count(self) -> int:
        return max(0, self.depth - 1) if self.found else 0

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return 100 * self.cache_hits / total if total else 0.0


class SearchStopped(Exception):
    def __init__(self, status: str):
        self.status = status


class SearchTracker:
    def __init__(self, limits: SearchLimits):
        self.limits = limits
        self.started = monotonic()
        self.visited_nodes = 0
        self.expanded_nodes = 0
        self.edges: list[tuple[str, str]] = []
        self._edge_set: set[tuple[str, str]] = set()
        self._last_report_at = self.started
        self._observer_seconds = 0.0

    def elapsed(self) -> float:
        return monotonic() - self.started - self._observer_seconds

    def check(self) -> None:
        if (self.limits.timeout_seconds is not None
                and self.elapsed() >= self.limits.timeout_seconds):
            raise SearchStopped("timeout")

    def visit(self) -> None:
        self.check()
        if (self.limits.max_visited_nodes is not None
                and self.visited_nodes >= self.limits.max_visited_nodes):
            raise SearchStopped("node_limit")
        self.visited_nodes += 1

    def expand(self) -> None:
        self.check()
        self.expanded_nodes += 1

    def record_edges(self, node: str, neighbors: list[str], direction: str) -> None:
        for neighbor in neighbors[:15]:
            edge = (node, neighbor) if direction == "forward" else (neighbor, node)
            if edge not in self._edge_set and len(self.edges) < 250:
                self._edge_set.add(edge)
                self.edges.append(edge)

    def publish(self, callback: TraceCallback | None, wiki, algorithm: str,
                iteration_depth: int, side: str, phase: str, title: str,
                path: list[str], initial_hits: int, initial_misses: int,
                force: bool = False) -> None:
        if callback is None:
            return
        now = monotonic()
        if not force and now - self._last_report_at < 0.25:
            return
        self._last_report_at = now
        event = SearchProgress(
            algorithm=algorithm,
            iteration_depth=iteration_depth,
            max_depth=self.limits.max_depth,
            side=side,
            phase=phase,
            title=title,
            path_tail=tuple(path[-4:]),
            visited_nodes=self.visited_nodes,
            expanded_nodes=self.expanded_nodes,
            cache_hits=wiki.cache_hits - initial_hits,
            cache_misses=wiki.cache_misses - initial_misses,
            elapsed_seconds=now - self.started - self._observer_seconds,
        )
        callback_started = monotonic()
        try:
            callback(event)
        finally:
            self._observer_seconds += monotonic() - callback_started


def finish_result(wiki, tracker: SearchTracker, algorithm: str, start: str, target: str,
                  lang: str, status: str, path: list[str], initial_hits: int,
                  initial_misses: int) -> SearchResult:
    return SearchResult(
        algorithm=algorithm, start=start, target=target, lang=lang, status=status,
        path=path, elapsed_seconds=tracker.elapsed(),
        visited_nodes=tracker.visited_nodes, expanded_nodes=tracker.expanded_nodes,
        cache_hits=wiki.cache_hits - initial_hits, cache_misses=wiki.cache_misses - initial_misses,
        edges=tracker.edges,
    )
