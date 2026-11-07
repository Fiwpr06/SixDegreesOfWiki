import unittest

from utils.helpers import parse_article_reference


class ArticleReferenceTests(unittest.TestCase):
    def test_wikipedia_url_keeps_full_title_after_underscores(self):
        self.assertEqual(
            ("World War II", "en"),
            parse_article_reference("https://en.wikipedia.org/wiki/World_War_II"),
        )
        self.assertEqual(
            ("Trí tuệ nhân tạo", "vi"),
            parse_article_reference("https://vi.wikipedia.org/wiki/Tr%C3%AD_tu%E1%BB%87_nh%C3%A2n_t%E1%BA%A1o#Lịch_sử"),
        )

    def test_plain_title_and_invalid_host(self):
        self.assertEqual(("World War II", None), parse_article_reference("World_War_II"))
        with self.assertRaises(ValueError):
            parse_article_reference("https://example.com/wiki/World_War_II")


if __name__ == "__main__":
    unittest.main()
