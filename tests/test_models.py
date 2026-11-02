"""Tests for database models."""

from __future__ import annotations

from calendar_bot.database.models import Event, PrivacySetting, User


class TestUser:
    def test_new_users_are_private(self) -> None:
        user = User(discord_id=1)
        assert user.timezone is None
        assert user.is_private

    def test_public_users_are_not_private(self) -> None:
        assert not User(discord_id=1, privacy=PrivacySetting.PUBLIC).is_private

    def test_from_row(self) -> None:
        user = User.from_row((123456789, "Europe/London", "public"))
        assert user == User(123456789, "Europe/London", PrivacySetting.PUBLIC)


class TestEvent:
    def test_discord_markup(self) -> None:
        event = Event(id=1, user_id=1, title="Test", timestamp=1704067200)
        assert event.discord_timestamp == "<t:1704067200:f>"
        assert event.discord_relative == "<t:1704067200:R>"

    def test_from_row(self) -> None:
        event = Event.from_row((1, 123456789, "Test Event", 1704067200))
        assert event == Event(1, 123456789, "Test Event", 1704067200)
