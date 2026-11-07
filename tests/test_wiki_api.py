import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from sqlalchemy import inspect, select

from config import PROJECT_ROOT, Settings
from core.bidirectional_ids import bidirectional_ids
from core.search_types import SearchLimits
from core.wiki_api import WikiAPI, WikiAPIError
from database import Database, PageCache


def api_response(payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


class WikiAPITests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(dir=PROJECT_ROOT)
        self.settings = Settings(sqlite_path=Path(self.tempdir.name) / "cache.db")
        self.database = Database(self.settings)
        self.session = Mock()
        self.session.headers = {}
        self.api = WikiAPI(self.database, self.settings, self.session)

    def tearDown(self):
        self.database.close()
        self.tempdir.cleanup()

    def test_schema_is_created(self):
        self.assertEqual({"page_links_cache", "search_history"}, set(inspect(self.database.engine).get_table_names()))

    def test_sqlite_file_persists(self):
        self.assertEqual("sqlite", self.database.backend)
        self.assertTrue(self.settings.sqlite_path.exists())

    def test_forward_pagination_namespace_filter_and_cache(self):
        self.session.get.side_effect = [
            api_response({"query": {"pages": [{"ns": 0, "title": "A", "links": [
                {"ns": 0, "title": "B"}, {"ns": 14, "title": "Category:X"}
            ]}]}, "continue": {"continue": "||", "plcontinue": "42|0|B"}}),
            api_response({"query": {"pages": [{"ns": 0, "title": "A", "links": [
                {"ns": 0, "title": "B"}, {"ns": 0, "title": "C"}
            ]}]}}),
        ]
        self.assertEqual(["B", "C"], self.api.get_links("A", "vi"))
        self.assertEqual(["B", "C"], self.api.get_links("A", "vi"))
        self.assertEqual(2, self.session.get.call_count)
        self.assertEqual("42|0|B", self.session.get.call_args_list[1].kwargs["params"]["plcontinue"])
        self.assertEqual(1, self.api.cache_hits)
        with self.database.session() as db:
            row = db.scalar(select(PageCache))
            self.assertEqual(2, row.link_count)

    def test_backward_uses_separate_cache_and_namespace_filter(self):
        self.session.get.side_effect = [
            api_response({"query": {"backlinks": [{"ns": 0, "title": "C"}, {"ns": 1, "title": "Talk:A"}]}}),
            api_response({"query": {"pages": [{"ns": 0, "title": "A", "links": []}]}}),
        ]
        self.assertEqual(["C"], self.api.get_links("A", "en", "backward"))
        self.assertEqual([], self.api.get_links("A", "en", "forward"))
        self.assertEqual(0, self.session.get.call_args_list[0].kwargs["params"]["blnamespace"])
        self.assertEqual(2, self.session.get.call_count)

    def test_incomplete_response_is_not_cached(self):
        self.session.get.side_effect = [
            api_response({"query": {"pages": [{"ns": 0, "title": "A", "links": [{"ns": 0, "title": "B"}]}]},
                          "continue": {"continue": "||", "plcontinue": "next"}}),
            api_response({"error": {"code": "ratelimited"}}),
        ]
        with self.assertRaises(WikiAPIError):
            self.api.get_links("A")
        with self.database.session() as db:
            self.assertIsNone(db.scalar(select(PageCache)))

    def test_streaming_backlinks_stops_at_meeting_page(self):
        self.session.get.side_effect = [
            api_response({"query": {"pages": [{"ns": 0, "title": "A", "links": [
                {"ns": 0, "title": "X"}
            ]}]}}),
            api_response({"query": {"backlinks": [
                {"ns": 0, "title": "X"}, {"ns": 0, "title": "Other"}
            ]}, "continue": {"continue": "-||", "blcontinue": "next"}}),
        ]
        result = bidirectional_ids(self.api, "A", "T", "en", SearchLimits(2, 10, 100))
        self.assertEqual(["A", "X", "T"], result.path)
        self.assertEqual(2, self.session.get.call_count)
        with self.database.session() as db:
            cached = db.scalars(select(PageCache)).all()
            self.assertEqual([("A", "forward")], [(row.title, row.direction) for row in cached])

    def test_resolve_title_rejects_missing_and_non_article(self):
        self.session.get.side_effect = [
            api_response({"query": {"pages": [{"ns": 14, "title": "Category:X"}]}}),
            api_response({"query": {"pages": [{"ns": 0, "title": "Missing", "missing": True}]}}),
            api_response({"query": {"pages": [{"ns": 0, "title": "Canonical"}]}}),
        ]
        with self.assertRaises(ValueError):
            self.api.resolve_title("Category:X")
        with self.assertRaises(ValueError):
            self.api.resolve_title("Missing")
        self.assertEqual("Canonical", self.api.resolve_title("Alias"))

    def test_invalid_language_does_not_make_request(self):
        with self.assertRaises(ValueError):
            self.api.get_links("A", "de")
        self.session.get.assert_not_called()

    def test_title_suggestions_use_namespace_zero(self):
        self.session.get.return_value = api_response({"query": {"prefixsearch": [
            {"ns": 0, "title": "Python"}, {"ns": 0, "title": "Pythonidae"}
        ]}})
        self.assertEqual(["Python", "Pythonidae"], self.api.suggest_titles("Pyth", "en"))
        self.assertEqual(0, self.session.get.call_args.kwargs["params"]["psnamespace"])

if __name__ == "__main__":
    unittest.main()
