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

    def test_event_from_row_with_none_created_at(self) -> None:
        row = (1, 123456789, "Test Event", 1704067200, None)

        event = Event.from_row(row)

        assert event.id == 1
        assert event.created_at is not None

    def test_event_with_none_id(self) -> None:
        event = Event(id=None, user_id=1, title="New Event", timestamp=1704067200)
        assert event.id is None


class TestUserEdgeCases:

    def test_user_from_row_with_null_privacy(self) -> None:
        now = datetime.now(UTC).isoformat()
        row = (123456789, "Europe/London", None, now, now)

        user = User.from_row(row)

        # Should default to private
        assert user.privacy == PrivacySetting.PRIVATE

    def test_user_from_row_with_null_dates(self) -> None:
        row = (123456789, None, "public", None, None)

        user = User.from_row(row)

        assert user.discord_id == 123456789
        assert user.timezone is None
        assert user.privacy == PrivacySetting.PUBLIC
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_with_timezone(self) -> None:
        user = User(discord_id=1, timezone="America/New_York")
        assert user.timezone == "America/New_York"

    def test_user_public_is_not_private(self) -> None:
        user = User(discord_id=1, privacy=PrivacySetting.PUBLIC)
        assert user.is_private is False


class TestPrivacySettingEdgeCases:

    def test_privacy_enum_values(self) -> None:
        assert PrivacySetting.PUBLIC.value == "public"
        assert PrivacySetting.PRIVATE.value == "private"

    def test_privacy_comparison(self) -> None:
        assert PrivacySetting.PUBLIC != PrivacySetting.PRIVATE
        assert PrivacySetting.PUBLIC == PrivacySetting.PUBLIC
