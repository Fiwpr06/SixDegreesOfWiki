import json
import random
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import inspect

from config import PROJECT_ROOT, Settings
from core.bidirectional_ids import bidirectional_ids
from core.ids_search import standard_ids
from core.search_types import SearchLimits
from database import Database
from database.history import list_searches, save_search
from utils.exporter import report_from_history, report_from_result


class GraphWiki:
    def __init__(self, edges):
        self.edges = edges
        self.cache_hits = 0
        self.cache_misses = 0

    def get_links(self, title, lang, direction, check=None):
        if check:
            check()
        self.cache_misses += 1
        if direction == "forward":
            return self.edges.get(title, [])
        return [source for source, targets in self.edges.items() if title in targets]

class SearchTests(unittest.TestCase):
    def setUp(self):
        self.graph = GraphWiki({
            "A": ["X", "B", "C"], "X": ["Y"], "Y": ["D"],
            "B": ["D", "A"], "C": ["D"], "D": [],
        })

    def test_both_algorithms_find_shortest_directed_path(self):
        for runner in (standard_ids, bidirectional_ids):
            with self.subTest(runner=runner.__name__):
                events = []
                result = runner(self.graph, "A", "D", "en", SearchLimits(4, 10, 1000),
                                trace=events.append)
                self.assertTrue(result.found)
                self.assertEqual(2, result.depth)
                self.assertEqual(1, result.intermediate_count)
                self.assertEqual("A", result.path[0])
                self.assertEqual("D", result.path[-1])
                self.assertTrue(all(right in self.graph.edges[left]
                                    for left, right in zip(result.path, result.path[1:])))
                self.assertEqual("Đã tìm thấy", events[-1].phase)
                self.assertEqual(result.visited_nodes, events[-1].visited_nodes)
                self.assertTrue(any(event.phase == "Bắt đầu mức sâu" for event in events))

    def test_zero_depth_and_direct_edge(self):
        for runner in (standard_ids, bidirectional_ids):
            self.assertEqual(["A"], runner(self.graph, "A", "A", "en", SearchLimits(0, 10, 100)).path)
            self.assertEqual(["B", "D"], runner(self.graph, "B", "D", "en", SearchLimits(1, 10, 100)).path)

    def test_bidirectional_direct_edge_does_not_fetch_backlinks(self):
        class RecordingWiki(GraphWiki):
            def __init__(self):
                super().__init__({"A": ["T"], "T": []})
                self.directions = []

            def get_links(self, title, lang, direction, check=None):
                self.directions.append(direction)
                return super().get_links(title, lang, direction, check)

        wiki = RecordingWiki()
        result = bidirectional_ids(wiki, "A", "T", "en", SearchLimits(1, 10, 100))
        self.assertEqual(["A", "T"], result.path)
        self.assertEqual(["forward"], wiki.directions)

    def test_no_reverse_path_or_insufficient_depth(self):
        for runner in (standard_ids, bidirectional_ids):
            self.assertEqual("not_found", runner(self.graph, "D", "A", "en", SearchLimits(3, 10, 1000)).status)
            self.assertEqual("not_found", runner(self.graph, "A", "D", "en", SearchLimits(1, 10, 1000)).status)

    def test_shortest_path_matches_bfs_on_small_directed_graphs(self):
        rng = random.Random(17)
        vertices = list("ABCDE")
        for _ in range(30):
            edges = {source: [target for target in vertices
                              if target != source and rng.random() < 0.35]
                     for source in vertices}
            frontier = [("A", 0)]
            seen = {"A"}
            shortest = None
            while frontier:
                node, depth = frontier.pop(0)
                if node == "E":
                    shortest = depth
                    break
                for neighbor in edges[node]:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        frontier.append((neighbor, depth + 1))
            for runner in (standard_ids, bidirectional_ids):
                result = runner(GraphWiki(edges), "A", "E", "en", SearchLimits(4, 10, 10000))
                self.assertEqual(shortest, result.depth if result.found else None)

    def test_red_link_is_treated_as_leaf(self):
        class RedLinkWiki(GraphWiki):
            def get_links(self, title, lang, direction, check=None):
                if title == "Red":
                    raise ValueError("Article does not exist")
                return super().get_links(title, lang, direction, check)

        wiki = RedLinkWiki({"A": ["Red", "B"], "B": ["D"], "D": []})
        result = standard_ids(wiki, "A", "D", "en", SearchLimits(2, 10, 100))
        self.assertEqual(["A", "B", "D"], result.path)

    def test_unlimited_mode_reaches_beyond_bounded_depth(self):
        chain = {f"N{index}": [f"N{index + 1}"] for index in range(7)}
        chain["N7"] = []
        for runner in (standard_ids, bidirectional_ids):
            with self.subTest(runner=runner.__name__):
                progress = []
                result = runner(GraphWiki(chain), "N0", "N7", "en",
                                SearchLimits(None, None, None),
                                lambda depth, maximum: progress.append((depth, maximum)))
                self.assertEqual("found", result.status)
                self.assertEqual(7, result.depth)
                self.assertEqual((7, None), progress[-1])

    def test_node_and_time_limits_are_inconclusive(self):
        for runner in (standard_ids, bidirectional_ids):
            self.assertEqual("node_limit", runner(self.graph, "A", "D", "en", SearchLimits(4, 10, 1)).status)
            with patch("core.search_types.monotonic", side_effect=[0, 1, 2]):
                self.assertEqual("timeout", runner(self.graph, "A", "D", "en", SearchLimits(4, 0.5, 100)).status)

    def test_history_and_json_report(self):
        result = standard_ids(self.graph, "A", "D", "en", SearchLimits(3, 10, 1000))
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as directory:
            database = Database(Settings(sqlite_path=Path(directory) / "history.db"))
            try:
                identifier = save_search(database, result)
                rows = list_searches(database)
                self.assertEqual(identifier, rows[0].id)
                self.assertEqual("found", rows[0].status)
                self.assertEqual(result.path, json.loads(rows[0].path_json))
                self.assertEqual(2, report_from_history(rows[0])["results"]["depth"])
                self.assertEqual(2, report_from_result(result)["results"]["depth"])
                self.assertEqual(result.expanded_nodes, report_from_history(rows[0])["performance"]["expanded_nodes"])
                self.assertEqual(result.cache_misses, report_from_history(rows[0])["performance"]["cache_misses"])
            finally:
                database.close()

    def test_existing_stage_one_database_is_migrated(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as directory:
            path = Path(directory) / "old.db"
            connection = sqlite3.connect(path)
            try:
                connection.execute("CREATE TABLE search_history (id INTEGER PRIMARY KEY, depth INTEGER NOT NULL)")
                connection.commit()
            finally:
                connection.close()
            database = Database(Settings(sqlite_path=path))
            try:
                columns = {column["name"] for column in inspect(database.engine).get_columns("search_history")}
                self.assertTrue({"status", "expanded_nodes", "cache_hits", "cache_misses"} <= columns)
            finally:
                database.close()


if __name__ == "__main__":
    unittest.main()
