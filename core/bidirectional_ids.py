"""Bidirectional iterative deepening with directed incoming edges on the target side."""

from itertools import count

from .search_types import SearchLimits, SearchResult, SearchStopped, SearchTracker, ProgressCallback, TraceCallback, finish_result


def bidirectional_ids(wiki, start: str, target: str, lang: str, limits: SearchLimits,
                      progress: ProgressCallback | None = None,
                      trace: TraceCallback | None = None) -> SearchResult:
    tracker = SearchTracker(limits)
    initial_hits, initial_misses = wiki.cache_hits, wiki.cache_misses
    status = "not_found"
    found_path: list[str] = []
    current_limit = 0
    cached_forward_depth = -1
    cached_forward: dict[str, list[str]] = {}

    def enumerate_paths(root: str, depth_limit: int, direction: str,
                        opposite: dict[str, list[str]] | None = None
                        ) -> tuple[dict[str, list[str]], list[str] | None]:
        # Values are root-to-node paths; the backward map is reversed on joining.
        shortest: dict[str, list[str]] = {}

        def walk(node: str, remaining: int, path: list[str], in_path: set[str]) -> list[str] | None:
            tracker.visit()
            tracker.publish(trace, wiki, "Bidirectional IDS", current_limit, direction,
                            "Đang duyệt", node, path, initial_hits, initial_misses)
            previous = shortest.get(node)
            if previous is None or len(path) < len(previous):
                shortest[node] = path.copy()
            if opposite is not None and node in opposite:
                candidate = (path + list(reversed(opposite[node]))[1:] if direction == "forward"
                             else opposite[node] + list(reversed(path))[1:])
                if len(candidate) == len(set(candidate)):
                    return candidate
            if remaining == 0:
                return None
            tracker.expand()
            tracker.publish(trace, wiki, "Bidirectional IDS", current_limit, direction,
                            "Đang tải liên kết", node, path, initial_hits, initial_misses)
            try:
                iter_links = getattr(wiki, "iter_links", None)
                neighbors = (iter_links(node, lang, direction, check=tracker.check)
                             if iter_links is not None else wiki.get_links(node, lang, direction, check=tracker.check))
                sampled_edges = 0
                for neighbor in neighbors:
                    tracker.check()
                    if sampled_edges < 15:
                        tracker.record_edges(node, [neighbor], direction)
                        sampled_edges += 1
                    if neighbor in in_path:
                        continue
                    path.append(neighbor)
                    in_path.add(neighbor)
                    try:
                        match = walk(neighbor, remaining - 1, path, in_path)
                    finally:
                        path.pop()
                        in_path.remove(neighbor)
                    if match is not None:
                        return match
            except ValueError:
                # A red link discovered on the forward side is a leaf.
                return None

        match = walk(root, depth_limit, [root], {root})
        return shortest, match

    try:
        depths = count() if limits.max_depth is None else range(limits.max_depth + 1)
        for total_depth in depths:
            tracker.check()
            current_limit = total_depth
            if progress:
                progress(total_depth, limits.max_depth)
            tracker.publish(trace, wiki, "Bidirectional IDS", total_depth, "hai chiều",
                            "Bắt đầu mức sâu", start, [start], initial_hits, initial_misses, force=True)
            forward_depth = (total_depth + 1) // 2
            backward_depth = total_depth // 2
            if forward_depth != cached_forward_depth:
                cached_forward, match = enumerate_paths(
                    start, forward_depth, "forward", {target: [target]})
                cached_forward_depth = forward_depth
            else:
                match = None
                tracker.publish(trace, wiki, "Bidirectional IDS", total_depth, "forward",
                                "Dùng lại mức sâu phía xuôi", start, [start],
                                initial_hits, initial_misses, force=True)
            if match is None:
                _, match = enumerate_paths(target, backward_depth, "backward", cached_forward)
            if match is not None:
                found_path = match
                status = "found"
                tracker.publish(trace, wiki, "Bidirectional IDS", total_depth, "hai chiều",
                                "Đã tìm thấy", target, found_path,
                                initial_hits, initial_misses, force=True)
                break
    except SearchStopped as exc:
        status = exc.status
        tracker.publish(trace, wiki, "Bidirectional IDS", current_limit, "hai chiều",
                        status, start, [start], initial_hits, initial_misses, force=True)
    return finish_result(wiki, tracker, "Bidirectional IDS", start, target, lang,
                         status, found_path, initial_hits, initial_misses)
