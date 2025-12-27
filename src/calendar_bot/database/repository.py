"""Database repository for Calendar Bot."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import aiosqlite

from calendar_bot.database.models import Event, PrivacySetting, User

if TYPE_CHECKING:
    from aiosqlite import Connection

logger = logging.getLogger(__name__)


class DatabaseRepository:
    """Async repository for database operations."""

    _SCHEMA = """
        CREATE TABLE IF NOT EXISTS users (
            discord_id INTEGER PRIMARY KEY,
            timezone TEXT,
            privacy TEXT DEFAULT 'private',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
        CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
    """

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._connection: Connection | None = None

    async def initialize(self) -> None:
        """Initialize database connection and schema."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Connecting to database: %s", self._database_path)
        self._connection = await aiosqlite.connect(self._database_path)
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.executescript(self._SCHEMA)
        await self._connection.commit()
        logger.info("Database initialized successfully")

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    @asynccontextmanager
    async def _get_connection(self) -> AsyncGenerator[Connection, None]:
        if not self._connection:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        yield self._connection

    async def get_user(self, discord_id: int) -> User | None:
        async with self._get_connection() as conn:
            cursor = await conn.execute(
                "SELECT discord_id, timezone, privacy, created_at, updated_at "
                "FROM users WHERE discord_id = ?",
                (discord_id,),
            )
            row = await cursor.fetchone()
            return User.from_row(row) if row else None

    async def get_or_create_user(self, discord_id: int) -> User:
        user = await self.get_user(discord_id)
        if user:
            return user

        async with self._get_connection() as conn:
            now = datetime.now(UTC).isoformat()
            await conn.execute(
                "INSERT INTO users (discord_id, privacy, created_at, updated_at) "
                "VALUES (?, ?, ?, ?)",
                (discord_id, str(PrivacySetting.PRIVATE), now, now),
            )
            await conn.commit()

        return User(discord_id=discord_id)

    async def update_user_timezone(self, discord_id: int, timezone: str) -> None:
        await self.get_or_create_user(discord_id)

        async with self._get_connection() as conn:
            now = datetime.now(UTC).isoformat()
            await conn.execute(
                "UPDATE users SET timezone = ?, updated_at = ? WHERE discord_id = ?",
                (timezone, now, discord_id),
            )
            await conn.commit()

    async def update_user_privacy(self, discord_id: int, privacy: PrivacySetting) -> None:
        await self.get_or_create_user(discord_id)

        async with self._get_connection() as conn:
            now = datetime.now(UTC).isoformat()
            await conn.execute(
                "UPDATE users SET privacy = ?, updated_at = ? WHERE discord_id = ?",
                (str(privacy), now, discord_id),
            )
            await conn.commit()

    async def add_event(self, user_id: int, title: str, timestamp: int) -> Event:
        async with self._get_connection() as conn:
            now = datetime.now(UTC).isoformat()
            cursor = await conn.execute(
                "INSERT INTO events (user_id, title, timestamp, created_at) VALUES (?, ?, ?, ?)",
                (user_id, title, timestamp, now),
            )
            await conn.commit()
            event_id = cursor.lastrowid

        return Event(
            id=event_id,
            user_id=user_id,
            title=title,
            timestamp=timestamp,
        )

    async def get_events(
        self,
        user_id: int,
        *,
        include_past: bool = True,
        limit: int | None = None,
    ) -> list[Event]:
        async with self._get_connection() as conn:
            query = "SELECT id, user_id, title, timestamp, created_at FROM events WHERE user_id = ?"
            params: list = [user_id]

            if not include_past:
                import time

                query += " AND timestamp >= ?"
                params.append(int(time.time()))

            query += " ORDER BY timestamp ASC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            return [Event.from_row(row) for row in rows]

    async def get_event(self, event_id: int, user_id: int) -> Event | None:
        async with self._get_connection() as conn:
            cursor = await conn.execute(
                "SELECT id, user_id, title, timestamp, created_at "
                "FROM events WHERE id = ? AND user_id = ?",
                (event_id, user_id),
            )
            row = await cursor.fetchone()
            return Event.from_row(row) if row else None

    async def remove_event(self, event_id: int, user_id: int) -> Event | None:
        event = await self.get_event(event_id, user_id)
        if not event:
            return None

        async with self._get_connection() as conn:
            await conn.execute(
                "DELETE FROM events WHERE id = ? AND user_id = ?",
                (event_id, user_id),
            )
            await conn.commit()

        return event

    async def wipe_events(self, user_id: int) -> int:
        async with self._get_connection() as conn:
            cursor = await conn.execute(
                "DELETE FROM events WHERE user_id = ?",
                (user_id,),
            )
            await conn.commit()
            return cursor.rowcount

    async def count_events(self, user_id: int) -> int:
        async with self._get_connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM events WHERE user_id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def delete_user(self, discord_id: int) -> tuple[int, bool]:
        """Delete user and all their data. Returns (events_deleted, user_existed)."""
        async with self._get_connection() as conn:
            # Count events before deletion
            event_count = await self.count_events(discord_id)

            # Delete user (CASCADE will delete events, but we do it explicitly for clarity)
            await conn.execute("DELETE FROM events WHERE user_id = ?", (discord_id,))
            cursor = await conn.execute("DELETE FROM users WHERE discord_id = ?", (discord_id,))
            await conn.commit()

            user_existed = cursor.rowcount > 0
            return event_count, user_existed
