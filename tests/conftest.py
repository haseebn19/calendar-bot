"""Shared fixtures: a temporary database, optionally with a user and some events."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest_asyncio

from calendar_bot.database import DatabaseRepository

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

USER_ID = 123456789


@pytest_asyncio.fixture
async def db(tmp_path: Path) -> AsyncGenerator[DatabaseRepository, None]:
    repo = DatabaseRepository(tmp_path / "test_calendar.db")
    await repo.initialize()
    yield repo
    await repo.close()


@pytest_asyncio.fixture
async def db_with_user(db: DatabaseRepository) -> tuple[DatabaseRepository, int]:
    """A database with one user, whose timezone is America/New_York."""
    await db.update_user_timezone(USER_ID, "America/New_York")
    return db, USER_ID


@pytest_asyncio.fixture
async def db_with_events(
    db_with_user: tuple[DatabaseRepository, int],
) -> tuple[DatabaseRepository, int]:
    """The user from `db_with_user`, with events on January 1, 2, and 3, 2024."""
    db, user_id = db_with_user
    await db.add_event(user_id, "Test Event 1", 1704067200)
    await db.add_event(user_id, "Test Event 2", 1704153600)
    await db.add_event(user_id, "Test Event 3", 1704240000)
    return db, user_id
