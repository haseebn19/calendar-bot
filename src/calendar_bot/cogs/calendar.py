"""Calendar management cog for Calendar Bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from calendar_bot.cogs.base import BaseCog, plural
from calendar_bot.utils.datetime_parser import DateTimeParser
from calendar_bot.utils.views import ConfirmView, EventListView

if TYPE_CHECKING:
    from calendar_bot.bot import CalendarBot

MAX_TITLE_LENGTH = 100

DATE_OPTION_DESCRIPTIONS = {
    "year": "Year. Leave it out to use the next matching date",
    "month": "Month name or number",
    "day": "Day of the month, or a day name like 'Monday'",
    "time": "Time such as '10am', '14:30', or '10:30pm'. Defaults to midnight",
}

TIMEZONE_REQUIRED_MESSAGE = (
    "❌ Please set your timezone first using `/timezone set <timezone>`\n\n"
    "Example: `/timezone set America/New_York`"
)


class CalendarCog(BaseCog):
    """Cog for calendar event management commands."""

    calendar_group = app_commands.Group(
        name="calendar",
        description="Manage your calendar events",
    )

    @calendar_group.command(name="add", description="Add an event to your calendar")
    @app_commands.describe(
        title=f"The event title, up to {MAX_TITLE_LENGTH} characters", **DATE_OPTION_DESCRIPTIONS
    )
    async def add_event(
        self,
        interaction: discord.Interaction,
        title: app_commands.Range[str, 1, MAX_TITLE_LENGTH],
        year: int | None = None,
        month: str | None = None,
        day: str | None = None,
        time: str | None = None,
    ) -> None:
        """Add a new event to the user's calendar."""
        await self.defer_response(interaction)

        timestamp = await self.resolve_timestamp(
            interaction, year=year, month=month, day=day, time=time
        )
        if timestamp is None:
            return

        event = await self.db.add_event(
            user_id=interaction.user.id,
            title=title,
            timestamp=timestamp,
        )

        await self.edit_response(
            interaction,
            content=(
                f"✅ Event added!\n\n"
                f"**{event.title}**\n"
                f"{event.discord_timestamp} ({event.discord_relative})"
            ),
        )
        # Event titles are the user's own text, so they are kept out of the logs
        self.logger.info("User %s added event %s", interaction.user.id, event.id)

    async def resolve_timestamp(
        self,
        interaction: discord.Interaction,
        *,
        year: int | None,
        month: str | None,
        day: str | None,
        time: str | None,
    ) -> int | None:
        """Turn the date and time options into a UTC timestamp, in the user's timezone.

        The response must already be deferred. If no option was given, the user has no
        timezone, or the options do not make a date, this replies with the reason and
        returns None.
        """
        if all(part is None for part in (year, month, day, time)):
            await self.edit_response(
                interaction, content="❌ Please provide at least one date or time option."
            )
            return None

        user = await self.db.get_user(interaction.user.id)
        if not user or not user.timezone:
            await self.edit_response(interaction, content=TIMEZONE_REQUIRED_MESSAGE)
            return None

        parser = DateTimeParser(user.timezone)
        parsed = parser.parse(year=year, month=month, day=day, time=time)
        timestamp = parser.to_utc_timestamp(parsed)
        if timestamp is None:
            reason = parsed.error_message or "The date or time provided is invalid."
            await self.edit_response(interaction, content=f"❌ {reason}")
        return timestamp

    @calendar_group.command(name="list", description="List your calendar events")
    @app_commands.describe(member="View another user's calendar (if public)")
    async def list_events(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ) -> None:
        """List the user's events, or another member's if their calendar is public."""
        await self.defer_response(interaction)

        other = member if member is not None and member.id != interaction.user.id else None
        if other is not None:
            other_user = await self.db.get_user(other.id)
            if other_user and other_user.is_private:
                await self.edit_response(
                    interaction,
                    content="🔒 This user's calendar is private.",
                )
                return

        target_id = other.id if other is not None else interaction.user.id
        events = await self.db.get_events(target_id)

        if not events:
            await self.edit_response(
                interaction,
                content=(
                    f"📭 {other.display_name} doesn't have any events."
                    if other is not None
                    else "📭 You don't have any events yet.\nUse `/calendar add` to create one!"
                ),
            )
            return

        view = EventListView(
            items=events,
            author_id=interaction.user.id,
            title=f"{other.display_name}'s Events" if other is not None else "Your Events",
        )
        await self.edit_response(interaction, embed=view.create_embed(), view=view)

    @calendar_group.command(name="remove", description="Remove an event by ID")
    @app_commands.describe(event_id="The ID of the event to remove (shown in /calendar list)")
    async def remove_event(
        self,
        interaction: discord.Interaction,
        event_id: int,
    ) -> None:
        """Remove one of the user's events by its ID."""
        await self.defer_response(interaction)

        event = await self.db.remove_event(event_id, interaction.user.id)

        if not event:
            await self.edit_response(
                interaction,
                content=f"❌ Event with ID `{event_id}` not found.",
            )
            return

        await self.edit_response(
            interaction,
            content=f"✅ Removed event: **{event.title}**",
        )
        self.logger.info("User %s removed event %s", interaction.user.id, event_id)

    @calendar_group.command(name="wipe", description="Delete all your events")
    async def wipe_events(self, interaction: discord.Interaction) -> None:
        """Delete all of the user's events after they confirm."""
        await self.defer_response(interaction)

        event_count = await self.db.count_events(interaction.user.id)
        if event_count == 0:
            await self.edit_response(
                interaction,
                content="📭 You don't have any events to delete.",
            )
            return

        events = plural(event_count, "event")
        view = ConfirmView(
            author_id=interaction.user.id,
            confirm_label=f"Yes, delete {events}",
        )
        await self.edit_response(
            interaction,
            content=(
                f"⚠️ Are you sure you want to delete **{events}**?\n\nThis action cannot be undone."
            ),
            view=view,
        )
        await view.wait()

        if view.value is None:
            await self.edit_response(
                interaction,
                content="⏰ Confirmation timed out. No events were deleted.",
                view=None,
            )
        elif view.value:
            deleted = await self.db.wipe_events(interaction.user.id)
            await self.edit_response(
                interaction,
                content=f"🗑️ Deleted **{plural(deleted, 'event')}**.",
                view=None,
            )
            self.logger.info("User %s wiped %d events", interaction.user.id, deleted)
        else:
            await self.edit_response(
                interaction,
                content="❌ Operation cancelled. No events were deleted.",
                view=None,
            )


async def setup(bot: CalendarBot) -> None:
    """Load the calendar cog."""
    await bot.add_cog(CalendarCog(bot))
