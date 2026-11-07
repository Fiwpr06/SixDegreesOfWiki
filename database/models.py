"""SQLAlchemy tables for Wikipedia link cache and search history."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    # SQLite DATETIME values are stored as naive UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class PageCache(Base):
    __tablename__ = "page_links_cache"
    __table_args__ = (UniqueConstraint("title", "lang", "direction", name="uq_page_lang_direction"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    lang: Mapped[str] = mapped_column(String(10), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    links_json: Mapped[str] = mapped_column(Text, nullable=False)
    link_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_title: Mapped[str] = mapped_column(String(255), nullable=False)
    lang: Mapped[str] = mapped_column(String(10), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="found")
    depth: Mapped[int] = mapped_column(Integer, nullable=False)
    intermediate_count: Mapped[int] = mapped_column(Integer, nullable=False)
    path_json: Mapped[str] = mapped_column(Text, nullable=False)
    execution_time: Mapped[float] = mapped_column(Float, nullable=False)
    nodes_visited: Mapped[int] = mapped_column(Integer, nullable=False)
    expanded_nodes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_hits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_misses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

