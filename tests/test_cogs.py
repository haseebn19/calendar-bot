"""Tests for the slash command cogs, with a real database and a mocked Discord interaction."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from discord import app_commands

from calendar_bot.bot import CalendarBot
from calendar_bot.cogs.base import plural
from calendar_bot.cogs.calendar import TIMEZONE_REQUIRED_MESSAGE, CalendarCog
from calendar_bot.cogs.help import HelpCog
from calendar_bot.cogs.settings import SettingsCog
from calendar_bot.cogs.timezone import TimezoneCog, timezones_by_offset
from calendar_bot.config import Config
from calendar_bot.database.models import Event, PrivacySetting
from calendar_bot.utils.views import EventListView

if TYPE_CHECKING:
    from pathlib import Path

    from calendar_bot.database import DatabaseRepository

USER_ID = 123456789
OTHER_ID = 987654321


def make_interaction(user_id: int = USER_ID) -> MagicMock:
    """Return an interaction that has already been deferred."""
    interaction = MagicMock()
    interaction.user.id = user_id
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=True)
    interaction.edit_original_response = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


def answering(value: bool | None) -> type:
    """A ConfirmView stand-in that gets `value` as its answer (None is a timeout)."""

    class AnsweredConfirmView:
        def __init__(self, **_options: object) -> None:
            self.value: bool | None = None

        async def wait(self) -> None:
            self.value = value

    return AnsweredConfirmView


def reply(interaction: MagicMock) -> dict:
    """Return the keyword arguments of the last edit to the response."""
    return interaction.edit_original_response.call_args.kwargs


@pytest.fixture
def calendar_cog(db: DatabaseRepository) -> CalendarCog:
    return CalendarCog(SimpleNamespace(db=db))


async def add_event(cog: CalendarCog, interaction: MagicMock, **options) -> None:
    await CalendarCog.add_event.callback(cog, interaction, title="Dentist", **options)


class TestAddEvent:
    async def test_requires_a_timezone(self, calendar_cog: CalendarCog, db) -> None:
        interaction = make_interaction()
        await add_event(calendar_cog, interaction, day="15")

        assert reply(interaction)["content"] == TIMEZONE_REQUIRED_MESSAGE
        assert await db.count_events(USER_ID) == 0

    async def test_requires_a_date_or_time(self, calendar_cog: CalendarCog) -> None:
        interaction = make_interaction()
        await add_event(calendar_cog, interaction)

        assert (
            reply(interaction)["content"] == "❌ Please provide at least one date or time option."
        )

    async def test_reports_invalid_input(self, calendar_cog: CalendarCog, db) -> None:
        await db.update_user_timezone(USER_ID, "UTC")
        interaction = make_interaction()

        await add_event(calendar_cog, interaction, time="25:00")

        assert reply(interaction)["content"].startswith("❌ Invalid time: '25:00'")
        assert await db.count_events(USER_ID) == 0

    async def test_saves_the_event_in_the_users_timezone(
        self, calendar_cog: CalendarCog, db
    ) -> None:
        await db.update_user_timezone(USER_ID, "America/Toronto")
        interaction = make_interaction()

        await add_event(calendar_cog, interaction, year=2030, month="Jan", day="15", time="10am")

        [event] = await db.get_events(USER_ID)
        assert event.timestamp == 1894719600  # 2030-01-15 15:00 UTC, 10am in Toronto
        assert reply(interaction)["content"].startswith("✅ Event added!")


class TestListAndRemove:
    async def test_private_calendars_are_hidden_from_others(
        self, calendar_cog: CalendarCog, db
    ) -> None:
        await db.update_user_timezone(OTHER_ID, "UTC")  # Calendars are private by default
        member = SimpleNamespace(id=OTHER_ID, display_name="Sam")
        interaction = make_interaction()

        await CalendarCog.list_events.callback(calendar_cog, interaction, member=member)

        assert reply(interaction)["content"] == "🔒 This user's calendar is private."

    async def test_public_calendars_show_the_members_events(
        self, calendar_cog: CalendarCog, db
    ) -> None:
        await db.update_user_privacy(OTHER_ID, PrivacySetting.PUBLIC)
        await db.add_event(OTHER_ID, "Concert", 1894719600)
        member = SimpleNamespace(id=OTHER_ID, display_name="Sam")
        interaction = make_interaction()

        await CalendarCog.list_events.callback(calendar_cog, interaction, member=member)

        embed = reply(interaction)["embed"]
        assert embed.title == "Sam's Events"
        assert "Concert" in embed.fields[0].name

    async def test_removing_a_missing_event(self, calendar_cog: CalendarCog) -> None:
        interaction = make_interaction()
        await CalendarCog.remove_event.callback(calendar_cog, interaction, event_id=99)
        assert reply(interaction)["content"] == "❌ Event with ID `99` not found."


class TestCalendarWipe:
    async def test_deletes_the_events_after_confirming(
        self, calendar_cog: CalendarCog, db, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await db.update_user_timezone(USER_ID, "UTC")
        await db.add_event(USER_ID, "Dentist", 1894719600)
        await db.add_event(USER_ID, "Concert", 1894723200)
        monkeypatch.setattr("calendar_bot.cogs.calendar.ConfirmView", answering(True))
        interaction = make_interaction()

        await CalendarCog.wipe_events.callback(calendar_cog, interaction)

        assert reply(interaction)["content"] == "🗑️ Deleted **2 events**."
        assert await db.count_events(USER_ID) == 0

    @pytest.mark.parametrize(
        ("answer", "message"),
        [
            (False, "❌ Operation cancelled. No events were deleted."),
            (None, "⏰ Confirmation timed out. No events were deleted."),
        ],
    )
    async def test_keeps_the_events_unless_confirmed(
        self,
        calendar_cog: CalendarCog,
        db,
        monkeypatch: pytest.MonkeyPatch,
        answer: bool | None,
        message: str,
    ) -> None:
        await db.update_user_timezone(USER_ID, "UTC")
        await db.add_event(USER_ID, "Dentist", 1894719600)
        monkeypatch.setattr("calendar_bot.cogs.calendar.ConfirmView", answering(answer))
        interaction = make_interaction()

        await CalendarCog.wipe_events.callback(calendar_cog, interaction)

        assert reply(interaction)["content"] == message
        assert await db.count_events(USER_ID) == 1

    async def test_with_no_events(self, calendar_cog: CalendarCog) -> None:
        interaction = make_interaction()
        await CalendarCog.wipe_events.callback(calendar_cog, interaction)
        assert reply(interaction)["content"] == "📭 You don't have any events to delete."


class TestSettings:
    @pytest.fixture
    def settings_cog(self, db: DatabaseRepository) -> SettingsCog:
        return SettingsCog(SimpleNamespace(db=db))

    async def test_commands_do_not_store_anything_by_themselves(
        self, settings_cog: SettingsCog, db
    ) -> None:
        interaction = make_interaction()

        await SettingsCog.view_settings.callback(settings_cog, interaction)

        embed = interaction.followup.send.call_args.kwargs["embed"]
        assert [field.value for field in embed.fields] == ["Private", "Not set"]
        assert await db.get_user(USER_ID) is None

    async def test_public_mode_is_saved_and_announced_in_the_channel(
        self, settings_cog: SettingsCog, db
    ) -> None:
        interaction = make_interaction()

        await SettingsCog.set_privacy.callback(settings_cog, interaction, mode="public")

        user = await db.get_user(USER_ID)
        assert user is not None and not user.is_private
        assert interaction.response.send_message.call_args.kwargs == {"ephemeral": False}

    async def test_wipe_with_no_data(self, settings_cog: SettingsCog) -> None:
        interaction = make_interaction()
        await SettingsCog.wipe_data.callback(settings_cog, interaction)
        assert reply(interaction)["content"] == "📭 You don't have any data to delete."

    async def test_wipe_deletes_everything_after_confirming(
        self, settings_cog: SettingsCog, db, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await db.update_user_timezone(USER_ID, "UTC")
        await db.add_event(USER_ID, "Dentist", 1894719600)
        monkeypatch.setattr("calendar_bot.cogs.settings.ConfirmView", answering(True))
        interaction = make_interaction()

        await SettingsCog.wipe_data.callback(settings_cog, interaction)

        assert reply(interaction)["content"] == (
            "🗑️ All your data has been deleted: 1 event and account settings."
        )
        assert await db.get_user(USER_ID) is None
        assert await db.count_events(USER_ID) == 0

    async def test_wipe_keeps_everything_when_cancelled(
        self, settings_cog: SettingsCog, db, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await db.update_user_timezone(USER_ID, "UTC")
        monkeypatch.setattr("calendar_bot.cogs.settings.ConfirmView", answering(False))
        interaction = make_interaction()

        await SettingsCog.wipe_data.callback(settings_cog, interaction)

        assert reply(interaction)["content"] == "❌ Operation cancelled. No data was deleted."
        assert await db.get_user(USER_ID) is not None


class TestTimezone:
    @pytest.fixture
    def timezone_cog(self, db: DatabaseRepository) -> TimezoneCog:
        return TimezoneCog(SimpleNamespace(db=db))

    async def test_set_saves_a_valid_timezone(self, timezone_cog: TimezoneCog, db) -> None:
        interaction = make_interaction()

        await TimezoneCog.set_timezone.callback(
            timezone_cog, interaction, timezone_name="Europe/London"
        )

        user = await db.get_user(USER_ID)
        assert user is not None and user.timezone == "Europe/London"
        assert reply(interaction)["content"].startswith("✅ Timezone set to **Europe/London**")

    async def test_set_rejects_an_unknown_timezone(self, timezone_cog: TimezoneCog, db) -> None:
        interaction = make_interaction()

        await TimezoneCog.set_timezone.callback(
            timezone_cog, interaction, timezone_name="Mars/Base"
        )

        assert reply(interaction)["content"].startswith("❌ Invalid timezone: `Mars/Base`")
        assert await db.get_user(USER_ID) is None

    async def test_get_without_a_timezone(self, timezone_cog: TimezoneCog) -> None:
        interaction = make_interaction()
        await TimezoneCog.get_timezone.callback(timezone_cog, interaction)
        assert reply(interaction)["content"].startswith("❌ You haven't set a timezone yet.")

    async def test_autocomplete_suggests_matching_timezones(
        self, timezone_cog: TimezoneCog
    ) -> None:
        choices = await timezone_cog.timezone_autocomplete(make_interaction(), "toronto")
        assert [choice.value for choice in choices] == ["America/Toronto"]

    async def test_autocomplete_returns_at_most_25_choices(self, timezone_cog: TimezoneCog) -> None:
        choices = await timezone_cog.timezone_autocomplete(make_interaction(), "")
        assert len(choices) == 25


async def test_help_lists_every_command_group(db) -> None:
    cog = HelpCog(SimpleNamespace(db=db))
    interaction = make_interaction()

    await HelpCog.show_commands.callback(cog, interaction)

    embed = interaction.followup.send.call_args.kwargs["embed"]
    assert [field.name for field in embed.fields] == [
        "Calendar",
        "Timezone",
        "Settings",
        "Help",
    ]


def test_event_list_keeps_its_title_on_every_page() -> None:
    events = [Event(id=i, user_id=OTHER_ID, title=f"Event {i}", timestamp=0) for i in range(11)]
    view = EventListView(items=events, author_id=USER_ID, title="Sam's Events")

    view.page = 1
    embed = view.create_embed()

    assert embed.title == "Sam's Events"
    assert embed.footer.text == "Page 2/2"


def test_event_list_shortens_titles_discord_would_reject() -> None:
    event = Event(id=1, user_id=USER_ID, title="x" * 300, timestamp=0)
    embed = EventListView(items=[event], author_id=USER_ID, title="Your Events").create_embed()

    name = embed.fields[0].name
    assert len(name) == 256
    assert name.startswith("`#1` xxx")
    assert name.endswith("...")


def test_timezones_are_sorted_by_offset() -> None:
    timezones = timezones_by_offset()
    labels = [label for _, label in timezones]

    assert labels[0].startswith("UTC-")
    assert labels[-1].startswith("UTC+")
    assert ("UTC", "UTC+00:00") in timezones


@pytest.mark.parametrize(("count", "expected"), [(0, "0 events"), (1, "1 event"), (2, "2 events")])
def test_plural(count: int, expected: str) -> None:
    assert plural(count, "event") == expected


async def test_failed_commands_tell_the_user(tmp_path: Path) -> None:
    bot = CalendarBot(Config(discord_token="token", database_path=tmp_path / "bot.db"))
    interaction = make_interaction()

    await bot.on_app_command_error(interaction, app_commands.AppCommandError("boom"))

    assert reply(interaction)["content"] == "❌ Something went wrong. Please try again."
    await bot.close()
