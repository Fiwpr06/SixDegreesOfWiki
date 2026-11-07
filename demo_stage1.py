"""Small terminal demo for the implemented MediaWiki and cache layer."""

import argparse

from core.wiki_api import WikiAPI, WikiAPIError
from database import Database


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo MediaWiki links and SQLite cache")
    parser.add_argument("title", nargs="?", default="ADMB", help="Wikipedia article title")
    parser.add_argument("--lang", choices=["vi", "en"], default="en")
    args = parser.parse_args()

    db = Database()
    try:
        wiki = WikiAPI(db)
        title = wiki.resolve_title(args.title, args.lang)
        print(f"Article: {title} ({args.lang})")
        print(f"Database: {db.backend}")
        for direction, label in (("forward", "Outgoing"), ("backward", "Incoming")):
            links = wiki.get_links(title, args.lang, direction)
            print(f"{label}: {len(links)} links; examples: {links[:5]}")
        print(f"First pass: {wiki.cache_hits} cache hits, {wiki.cache_misses} cache misses")
        wiki.get_links(title, args.lang, "forward")
        wiki.get_links(title, args.lang, "backward")
        print(f"After repeat: {wiki.cache_hits} cache hits, {wiki.cache_misses} cache misses")
    except (ValueError, WikiAPIError) as exc:
        parser.exit(1, f"Demo failed: {exc}\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
