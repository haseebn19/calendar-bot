"""Database repository for Calendar Bot."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import aiosqlite

from calendar_bot.database.models import Event, PrivacySetting, User

if TYPE_CHECKING:
    from pathlib import Path

    from aiosqlite import Connection

logger = logging.getLogger(__name__)


class DatabaseRepository:
    """Async repository for database operations."""

    _SCHEMA = """
        CREATE TABLE IF NOT EXISTS users (
            discord_id INTEGER PRIMARY KEY,
            timezone TEXT,
            privacy TEXT DEFAULT 'private'
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_events_user_timestamp ON events(user_id, timestamp);
    """

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._connection: Connection | None = None

    async def initialize(self) -> None:
        """Open the database, creating the file and tables if needed."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Connecting to database: %s", self._database_path)
        self._connection = await aiosqlite.connect(self._database_path)
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.executescript(self._SCHEMA)
        await self._connection.commit()

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    @property
    def _db(self) -> Connection:
        if self._connection is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._connection

    async def get_user(self, discord_id: int) -> User | None:
        cursor = await self._db.execute(
            "SELECT discord_id, timezone, privacy FROM users WHERE discord_id = ?", (discord_id,)
        )
        row = await cursor.fetchone()
        return User.from_row(row) if row else None

    async def update_user_timezone(self, discord_id: int, timezone: str) -> None:
        """Set the user's timezone, creating the user if needed."""
        await self._db.execute(
            "INSERT INTO users (discord_id, timezone) VALUES (?, ?) "
            "ON CONFLICT (discord_id) DO UPDATE SET timezone = excluded.timezone",
            (discord_id, timezone),
        )
        await self._db.commit()

    async def update_user_privacy(self, discord_id: int, privacy: PrivacySetting) -> None:
        """Set the user's privacy mode, creating the user if needed."""
        await self._db.execute(
            "INSERT INTO users (discord_id, privacy) VALUES (?, ?) "
            "ON CONFLICT (discord_id) DO UPDATE SET privacy = excluded.privacy",
            (discord_id, privacy),
        )
        await self._db.commit()

    async def add_event(self, user_id: int, title: str, timestamp: int) -> Event:
        cursor = await self._db.execute(
            "INSERT INTO events (user_id, title, timestamp) VALUES (?, ?, ?)",
            (user_id, title, timestamp),
        )
        await self._db.commit()
        return Event(id=cursor.lastrowid, user_id=user_id, title=title, timestamp=timestamp)

    async def get_events(self, user_id: int) -> list[Event]:
        """Return the user's events, soonest first."""
        cursor = await self._db.execute(
            "SELECT id, user_id, title, timestamp FROM events WHERE user_id = ? ORDER BY timestamp",
            (user_id,),
        )
        return [Event.from_row(row) for row in await cursor.fetchall()]

    async def remove_event(self, event_id: int, user_id: int) -> Event | None:
        """Delete one of the user's events and return it, or None if they have no such event."""
        cursor = await self._db.execute(
            "DELETE FROM events WHERE id = ? AND user_id = ? RETURNING id, user_id, title, timestamp",
            (event_id, user_id),
        )
        row = await cursor.fetchone()
        await self._db.commit()
        return Event.from_row(row) if row else None

    async def wipe_events(self, user_id: int) -> int:
        """Delete all of the user's events and return how many there were."""
        cursor = await self._db.execute("DELETE FROM events WHERE user_id = ?", (user_id,))
        await self._db.commit()
        return cursor.rowcount

    async def count_events(self, user_id: int) -> int:
        cursor = await self._db.execute("SELECT COUNT(*) FROM events WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def delete_user(self, discord_id: int) -> tuple[int, bool]:
        """Delete the user and their events. Returns (events_deleted, user_existed)."""
        # The foreign key would also delete the events, but deleting them first counts them
        events = await self._db.execute("DELETE FROM events WHERE user_id = ?", (discord_id,))
        user = await self._db.execute("DELETE FROM users WHERE discord_id = ?", (discord_id,))
        await self._db.commit()
        return events.rowcount, user.rowcount > 0
