"""Tests for the database repository."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from calendar_bot.database import DatabaseRepository
from calendar_bot.database.models import PrivacySetting, User

if TYPE_CHECKING:
    from pathlib import Path

Database = tuple[DatabaseRepository, int]


class TestUsers:
    async def test_unknown_user(self, db: DatabaseRepository) -> None:
        assert await db.get_user(999999) is None

    async def test_settings_create_the_user_and_keep_each_other(
        self, db: DatabaseRepository
    ) -> None:
        await db.update_user_timezone(1, "Europe/London")
        assert await db.get_user(1) == User(1, "Europe/London", PrivacySetting.PRIVATE)

        await db.update_user_privacy(1, PrivacySetting.PUBLIC)
        await db.update_user_timezone(1, "Asia/Tokyo")
        assert await db.get_user(1) == User(1, "Asia/Tokyo", PrivacySetting.PUBLIC)

    async def test_privacy_without_a_timezone(self, db: DatabaseRepository) -> None:
        await db.update_user_privacy(2, PrivacySetting.PUBLIC)
        assert await db.get_user(2) == User(2, None, PrivacySetting.PUBLIC)

    async def test_two_commands_at_once_from_a_new_user(self, db: DatabaseRepository) -> None:
        await asyncio.gather(
            db.update_user_timezone(555, "Asia/Tokyo"),
            db.update_user_privacy(555, PrivacySetting.PUBLIC),
        )
        assert await db.get_user(555) == User(555, "Asia/Tokyo", PrivacySetting.PUBLIC)


class TestEvents:
    async def test_add_event(self, db_with_user: Database) -> None:
        db, user_id = db_with_user
        event = await db.add_event(user_id, "Test Event", 1704067200)
        assert event.id is not None
        assert await db.get_events(user_id) == [event]

    async def test_events_are_listed_soonest_first(self, db_with_user: Database) -> None:
        db, user_id = db_with_user
        await db.add_event(user_id, "Later", 1704153600)
        await db.add_event(user_id, "Sooner", 1704067200)
        assert [event.title for event in await db.get_events(user_id)] == ["Sooner", "Later"]

    async def test_users_only_see_their_own_events(self, db: DatabaseRepository) -> None:
        await db.update_user_timezone(1, "UTC")
        await db.update_user_timezone(2, "UTC")
        await db.add_event(1, "Mine", 1704067200)

        assert [event.title for event in await db.get_events(1)] == ["Mine"]
        assert await db.get_events(2) == []

    async def test_remove_event(self, db_with_events: Database) -> None:
        db, user_id = db_with_events
        first = (await db.get_events(user_id))[0]

        assert await db.remove_event(first.id, 999999) is None
        assert await db.remove_event(first.id, user_id) == first
        assert await db.count_events(user_id) == 2
        assert await db.remove_event(first.id, user_id) is None

    async def test_wipe_and_count_events(self, db_with_events: Database) -> None:
        db, user_id = db_with_events
        assert await db.count_events(user_id) == 3
        assert await db.wipe_events(user_id) == 3
        assert await db.count_events(user_id) == 0


class TestDeleteUser:
    async def test_deletes_the_user_and_their_events(self, db_with_events: Database) -> None:
        db, user_id = db_with_events

        assert await db.delete_user(user_id) == (3, True)
        assert await db.get_user(user_id) is None
        assert await db.get_events(user_id) == []

    async def test_users_without_events_or_settings(self, db_with_user: Database) -> None:
        db, user_id = db_with_user
        assert await db.delete_user(user_id) == (0, True)
        assert await db.delete_user(user_id) == (0, False)


async def test_using_the_database_before_initializing_it_fails(tmp_path: Path) -> None:
    db = DatabaseRepository(tmp_path / "test.db")
    with pytest.raises(RuntimeError, match="not initialized"):
        await db.get_user(123)
