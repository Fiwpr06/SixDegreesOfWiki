"""Smoke test the Streamlit search flow without network calls."""

import unittest
import os
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from core.wiki_api import WikiAPI


class AppTests(unittest.TestCase):
    def test_initial_page_and_direct_path(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        def links(_wiki, title, _lang, direction, check=None):
            return ["Python (programming language)"] if direction == "backward" and title == "ADMB" else []

        with patch.dict(os.environ, {"SQLITE_PATH": str(app_path.parent / ".test_app.db")}), \
             patch.object(WikiAPI, "resolve_title", side_effect=lambda title, lang: title) as resolve, \
             patch.object(WikiAPI, "suggest_titles", return_value=[]), \
             patch.object(WikiAPI, "get_links", autospec=True, side_effect=links):
            app = AppTest.from_file(str(app_path), default_timeout=20).run()
            self.assertFalse(app.exception)
            app.toggle[0].set_value(True).run()
            self.assertFalse(app.exception)
            self.assertEqual(0, len(app.slider))
            app.toggle[0].set_value(False).run()
            app.selectbox[0].set_value("en").run()
            app.text_input[0].set_value("https://en.wikipedia.org/wiki/Python_(programming_language)").run()
            app.text_input[1].set_value("https://en.wikipedia.org/wiki/ADMB").run()
            app.button[0].click().run()
            self.assertFalse(app.exception)
            resolve.assert_any_call("Python (programming language)", "en")
            resolve.assert_any_call("ADMB", "en")
            self.assertTrue(any("Bidirectional IDS" in item.value for item in app.subheader))
            self.assertTrue(any("Đã tìm thấy" in item.value for item in app.info))


if __name__ == "__main__":
    unittest.main()
