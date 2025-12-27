"""Pytest configuration and fixtures for Calendar Bot tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio

from calendar_bot.database import DatabaseRepository


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db(tmp_path: Path) -> AsyncGenerator[DatabaseRepository, None]:
    """Create a temporary database for testing.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Yields:
        Initialized DatabaseRepository.
    """
    db_path = tmp_path / "test_calendar.db"
    repo = DatabaseRepository(db_path)
    await repo.initialize()

    yield repo

    await repo.close()


@pytest_asyncio.fixture
async def db_with_user(
    db: DatabaseRepository,
) -> AsyncGenerator[tuple[DatabaseRepository, int], None]:
    """Create a database with a test user.

    Args:
        db: Database repository fixture.

    Yields:
        Tuple of (database, user_id).
    """
    user_id = 123456789
    await db.get_or_create_user(user_id)
    await db.update_user_timezone(user_id, "America/New_York")

    yield db, user_id


@pytest_asyncio.fixture
async def db_with_events(
    db_with_user: tuple[DatabaseRepository, int],
) -> AsyncGenerator[tuple[DatabaseRepository, int], None]:
    """Create a database with a user and some events.

    Args:
        db_with_user: Database with user fixture.

    Yields:
        Tuple of (database, user_id).
    """
    db, user_id = db_with_user

    # Add some test events
    await db.add_event(user_id, "Test Event 1", 1704067200)  # Jan 1, 2024
    await db.add_event(user_id, "Test Event 2", 1704153600)  # Jan 2, 2024
    await db.add_event(user_id, "Test Event 3", 1704240000)  # Jan 3, 2024

    yield db, user_id
