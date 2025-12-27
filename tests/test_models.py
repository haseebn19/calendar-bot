"""Tests for database models."""

from __future__ import annotations

from datetime import UTC, datetime

from calendar_bot.database.models import Event, PrivacySetting, User


class TestPrivacySetting:
    def test_privacy_string_values(self) -> None:
        assert str(PrivacySetting.PUBLIC) == "public"
        assert str(PrivacySetting.PRIVATE) == "private"

    def test_privacy_from_string(self) -> None:
        assert PrivacySetting("public") == PrivacySetting.PUBLIC
        assert PrivacySetting("private") == PrivacySetting.PRIVATE


class TestUser:
    def test_user_defaults(self) -> None:
        user = User(discord_id=123456789)

        assert user.discord_id == 123456789
        assert user.timezone is None
        assert user.privacy == PrivacySetting.PRIVATE
        assert user.is_private is True

    def test_user_is_private(self) -> None:
        private_user = User(discord_id=1, privacy=PrivacySetting.PRIVATE)
        public_user = User(discord_id=2, privacy=PrivacySetting.PUBLIC)

        assert private_user.is_private is True
        assert public_user.is_private is False

    def test_user_from_row(self) -> None:
        now = datetime.now(UTC).isoformat()
        row = (123456789, "Europe/London", "private", now, now)

        user = User.from_row(row)

        assert user.discord_id == 123456789
        assert user.timezone == "Europe/London"
        assert user.privacy == PrivacySetting.PRIVATE


class TestEvent:
    def test_event_creation(self) -> None:
        event = Event(
            id=1,
            user_id=123456789,
            title="Test Event",
            timestamp=1704067200,
        )

        assert event.id == 1
        assert event.user_id == 123456789
        assert event.title == "Test Event"
        assert event.timestamp == 1704067200

    def test_event_discord_timestamp(self) -> None:
        event = Event(id=1, user_id=1, title="Test", timestamp=1704067200)
        assert event.discord_timestamp == "<t:1704067200:f>"

    def test_event_discord_relative(self) -> None:
        event = Event(id=1, user_id=1, title="Test", timestamp=1704067200)
        assert event.discord_relative == "<t:1704067200:R>"

    def test_event_datetime_property(self) -> None:
        event = Event(id=1, user_id=1, title="Test", timestamp=1704067200)

        dt = event.event_datetime
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1

    def test_event_from_row(self) -> None:
        now = datetime.now(UTC).isoformat()
        row = (1, 123456789, "Test Event", 1704067200, now)

        event = Event.from_row(row)

        assert event.id == 1
        assert event.user_id == 123456789
        assert event.title == "Test Event"
        assert event.timestamp == 1704067200
