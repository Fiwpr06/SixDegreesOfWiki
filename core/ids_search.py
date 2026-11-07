"""Standard iterative deepening depth-first search on directed Wikipedia links."""

from itertools import count

from .search_types import SearchLimits, SearchResult, SearchStopped, SearchTracker, ProgressCallback, TraceCallback, finish_result


def standard_ids(wiki, start: str, target: str, lang: str, limits: SearchLimits,
                 progress: ProgressCallback | None = None,
                 trace: TraceCallback | None = None) -> SearchResult:
    tracker = SearchTracker(limits)
    initial_hits, initial_misses = wiki.cache_hits, wiki.cache_misses
    status = "not_found"
    found_path: list[str] = []
    current_limit = 0

    def dfs(node: str, remaining: int, path: list[str], in_path: set[str]) -> list[str] | None:
        tracker.visit()
        tracker.publish(trace, wiki, "Standard IDS", current_limit, "xuôi", "Đang duyệt",
                        node, path, initial_hits, initial_misses)
        if node == target:
            return path.copy()
        if remaining == 0:
            return None
        tracker.expand()
        tracker.publish(trace, wiki, "Standard IDS", current_limit, "xuôi", "Đang tải liên kết",
                        node, path, initial_hits, initial_misses)
        try:
            neighbors = wiki.get_links(node, lang, "forward", check=tracker.check)
        except ValueError:
            # prop=links may include a red link to a page that does not exist.
            return None
        tracker.check()
        tracker.record_edges(node, neighbors, "forward")
        for neighbor in neighbors:
            tracker.check()
            if neighbor in in_path:
                continue
            in_path.add(neighbor)
            path.append(neighbor)
            result = dfs(neighbor, remaining - 1, path, in_path)
            if result is not None:
                return result
            path.pop()
            in_path.remove(neighbor)
        return None

    try:
        depths = count() if limits.max_depth is None else range(limits.max_depth + 1)
        for depth in depths:
            current_limit = depth
            if progress:
                progress(depth, limits.max_depth)
            tracker.publish(trace, wiki, "Standard IDS", depth, "xuôi", "Bắt đầu mức sâu",
                            start, [start], initial_hits, initial_misses, force=True)
            found = dfs(start, depth, [start], {start})
            if found is not None:
                status, found_path = "found", found
                tracker.publish(trace, wiki, "Standard IDS", depth, "xuôi", "Đã tìm thấy",
                                target, found, initial_hits, initial_misses, force=True)
                break
    except SearchStopped as exc:
        status = exc.status
        tracker.publish(trace, wiki, "Standard IDS", current_limit, "xuôi", status,
                        start, [start], initial_hits, initial_misses, force=True)
    return finish_result(wiki, tracker, "Standard IDS", start, target, lang,
                         status, found_path, initial_hits, initial_misses)
