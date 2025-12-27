"""Tests for the database repository."""

from __future__ import annotations

import pytest

from calendar_bot.database import DatabaseRepository
from calendar_bot.database.models import PrivacySetting


class TestDatabaseRepository:
    """Tests for DatabaseRepository."""

    @pytest.mark.asyncio
    async def test_initialize_creates_tables(self, db: DatabaseRepository) -> None:
        """Test that initialize creates the required tables."""
        # The fixture already initializes, just verify we can use it
        user = await db.get_user(999999)
        assert user is None  # No user exists yet

    @pytest.mark.asyncio
    async def test_get_or_create_user_creates_new(self, db: DatabaseRepository) -> None:
        """Test that get_or_create_user creates a new user."""
        user_id = 123456789
        user = await db.get_or_create_user(user_id)

        assert user.discord_id == user_id
        assert user.timezone is None
        assert user.privacy == PrivacySetting.PRIVATE

    @pytest.mark.asyncio
    async def test_get_or_create_user_returns_existing(self, db: DatabaseRepository) -> None:
        """Test that get_or_create_user returns existing user."""
        user_id = 123456789

        # Create user
        await db.get_or_create_user(user_id)
        await db.update_user_timezone(user_id, "America/New_York")

        # Get again
        user = await db.get_or_create_user(user_id)
        assert user.timezone == "America/New_York"

    @pytest.mark.asyncio
    async def test_update_user_timezone(self, db: DatabaseRepository) -> None:
        """Test updating user timezone."""
        user_id = 123456789
        timezone = "Europe/London"

        await db.update_user_timezone(user_id, timezone)

        user = await db.get_user(user_id)
        assert user is not None
        assert user.timezone == timezone

    @pytest.mark.asyncio
    async def test_update_user_privacy(self, db: DatabaseRepository) -> None:
        """Test updating user privacy setting."""
        user_id = 123456789

        await db.update_user_privacy(user_id, PrivacySetting.PUBLIC)

        user = await db.get_user(user_id)
        assert user is not None
        assert user.privacy == PrivacySetting.PUBLIC
        assert not user.is_private


class TestEventOperations:
    """Tests for event CRUD operations."""

    @pytest.mark.asyncio
    async def test_add_event(self, db_with_user: tuple[DatabaseRepository, int]) -> None:
        """Test adding an event."""
        db, user_id = db_with_user

        event = await db.add_event(user_id, "Test Event", 1704067200)

        assert event.id is not None
        assert event.user_id == user_id
        assert event.title == "Test Event"
        assert event.timestamp == 1704067200

    @pytest.mark.asyncio
    async def test_get_events_returns_sorted(
        self, db_with_events: tuple[DatabaseRepository, int]
    ) -> None:
        """Test that get_events returns events sorted by timestamp."""
        db, user_id = db_with_events

        events = await db.get_events(user_id)

        assert len(events) == 3
        assert events[0].title == "Test Event 1"
        assert events[1].title == "Test Event 2"
        assert events[2].title == "Test Event 3"

    @pytest.mark.asyncio
    async def test_get_events_empty(self, db: DatabaseRepository) -> None:
        """Test get_events for user with no events."""
        events = await db.get_events(999999)
        assert events == []

    @pytest.mark.asyncio
    async def test_get_event_by_id(self, db_with_events: tuple[DatabaseRepository, int]) -> None:
        """Test getting a specific event by ID."""
        db, user_id = db_with_events

        events = await db.get_events(user_id)
        event_id = events[0].id

        event = await db.get_event(event_id, user_id)
        assert event is not None
        assert event.title == "Test Event 1"

    @pytest.mark.asyncio
    async def test_get_event_wrong_user(
        self, db_with_events: tuple[DatabaseRepository, int]
    ) -> None:
        """Test that get_event returns None for wrong user."""
        db, user_id = db_with_events

        events = await db.get_events(user_id)
        event_id = events[0].id

        # Try to get with different user
        event = await db.get_event(event_id, 999999)
        assert event is None

    @pytest.mark.asyncio
    async def test_remove_event(self, db_with_events: tuple[DatabaseRepository, int]) -> None:
        """Test removing an event."""
        db, user_id = db_with_events

        events = await db.get_events(user_id)
        event_id = events[0].id

        removed = await db.remove_event(event_id, user_id)
        assert removed is not None
        assert removed.title == "Test Event 1"

        # Verify it's gone
        remaining = await db.get_events(user_id)
        assert len(remaining) == 2

    @pytest.mark.asyncio
    async def test_remove_event_not_found(self, db: DatabaseRepository) -> None:
        """Test removing non-existent event."""
        removed = await db.remove_event(999999, 123456)
        assert removed is None

    @pytest.mark.asyncio
    async def test_wipe_events(self, db_with_events: tuple[DatabaseRepository, int]) -> None:
        """Test wiping all events for a user."""
        db, user_id = db_with_events

        deleted = await db.wipe_events(user_id)
        assert deleted == 3

        events = await db.get_events(user_id)
        assert events == []

    @pytest.mark.asyncio
    async def test_count_events(self, db_with_events: tuple[DatabaseRepository, int]) -> None:
        """Test counting events."""
        db, user_id = db_with_events

        count = await db.count_events(user_id)
        assert count == 3

    @pytest.mark.asyncio
    async def test_count_events_empty(self, db: DatabaseRepository) -> None:
        """Test counting events for user with none."""
        count = await db.count_events(999999)
        assert count == 0
