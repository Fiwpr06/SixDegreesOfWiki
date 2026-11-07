"""SQLite connection and schema migration for local persistence."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from config import Settings
from .models import Base


class Database:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_env()
        self.settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(
            f"sqlite:///{self.settings.sqlite_path.as_posix()}",
            connect_args={"check_same_thread": False, "timeout": 30},
        )
        self.backend = "sqlite"
        Base.metadata.create_all(self.engine)
        self._migrate()

    def _migrate(self) -> None:
        # Existing Stage 1 databases predate the history status column.
        columns = {column["name"] for column in inspect(self.engine).get_columns("search_history")}
        with self.engine.begin() as connection:
            if "status" not in columns:
                connection.execute(text("ALTER TABLE search_history ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'found'"))
                connection.execute(text("UPDATE search_history SET status = 'not_found' WHERE depth < 0"))
            for column in ("expanded_nodes", "cache_hits", "cache_misses"):
                if column not in columns:
                    connection.execute(text(f"ALTER TABLE search_history ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0"))

    def session(self) -> Session:
        return Session(self.engine)

    def close(self) -> None:
        self.engine.dispose()
