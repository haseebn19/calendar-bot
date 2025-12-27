"""Calendar management cog for Calendar Bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from calendar_bot.cogs.base import BaseCog
from calendar_bot.utils.datetime_parser import DateTimeParser
from calendar_bot.utils.views import ConfirmView, EventListView

if TYPE_CHECKING:
    from calendar_bot.bot import CalendarBot


class CalendarCog(BaseCog):
    """Cog for calendar event management commands."""

    calendar_group = app_commands.Group(
        name="calendar",
        description="Manage your calendar events",
    )

    @calendar_group.command(name="add", description="Add an event to your calendar")
    @app_commands.describe(
        title="The event title",
        year="Year (defaults to current year)",
        month="Month (name or number, defaults to current month)",
        day="Day (number or name like 'Monday', defaults to current day)",
        time="Time (e.g., '10am', '14:30', '10:30pm')",
    )
    async def add_event(
        self,
        interaction: discord.Interaction,
        title: str,
        year: int | None = None,
        month: str | None = None,
        day: str | None = None,
        time: str | None = None,
    ) -> None:
        """Add a new event to the user's calendar.

        Args:
            interaction: The Discord interaction.
            title: Event title.
            year: Optional year.
            month: Optional month (name or number).
            day: Optional day (number or name).
            time: Optional time string.
        """
        await self.defer_response(interaction)

        # Validate at least one date/time parameter
        if all(param is None for param in [year, month, day, time]):
            await self.edit_response(
                interaction,
                content="❌ Please provide at least one date or time parameter.",
            )
            return

        # Get user's timezone
        user = await self.db.get_user(interaction.user.id)
        if not user or not user.timezone:
            await self.edit_response(
                interaction,
                content=(
                    "❌ Please set your timezone first using `/timezone set <timezone>`\n\n"
                    "Example: `/timezone set America/New_York`"
                ),
            )
            return

        # Parse the datetime
        parser = DateTimeParser(user.timezone)
        parsed = parser.parse(year=year, month=month, day=day, time=time)

        if not parsed.is_valid:
            await self.edit_response(
                interaction,
                content=f"❌ {parsed.error_message}",
            )
            return

        # Convert to UTC timestamp
        timestamp = parser.to_utc_timestamp(parsed)
        if timestamp is None:
            await self.edit_response(
                interaction,
                content="❌ The date or time provided is invalid. Please check the values.",
            )
            return

        # Add the event
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
        self.logger.info(
            "User %s added event: %s at %s",
            interaction.user.id,
            title,
            timestamp,
        )

    @calendar_group.command(name="list", description="List your calendar events")
    @app_commands.describe(member="View another user's calendar (if public)")
    async def list_events(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ) -> None:
        """List calendar events.

        Args:
            interaction: The Discord interaction.
            member: Optional member to view events for.
        """
        await self.defer_response(interaction)

        target_id = member.id if member else interaction.user.id
        is_own_calendar = target_id == interaction.user.id

        # Check privacy if viewing someone else's calendar
        if not is_own_calendar:
            target_user = await self.db.get_user(target_id)
            if target_user and target_user.is_private:
                await self.edit_response(
                    interaction,
                    content="🔒 This user's calendar is private.",
                )
                return

        # Get events
        events = await self.db.get_events(target_id)

        if not events:
            if is_own_calendar:
                await self.edit_response(
                    interaction,
                    content=(
                        "📭 You don't have any events yet.\nUse `/calendar add` to create one!"
                    ),
                )
            else:
                await self.edit_response(
                    interaction,
                    content=f"📭 {member.display_name} doesn't have any events.",
                )
            return

        # Create paginated view
        view = EventListView(
            items=events,
            author_id=interaction.user.id,
        )

        embed = view.create_embed()
        if not is_own_calendar:
            embed.title = f"📅 {member.display_name}'s Events"

        await self.edit_response(
            interaction,
            embed=embed,
            view=view,
        )

    @calendar_group.command(name="remove", description="Remove an event by ID")
    @app_commands.describe(event_id="The ID of the event to remove (shown in /calendar list)")
    async def remove_event(
        self,
        interaction: discord.Interaction,
        event_id: int,
    ) -> None:
        """Remove an event by its ID.

        Args:
            interaction: The Discord interaction.
            event_id: The event ID to remove.
        """
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
        self.logger.info("User %s removed event: %s", interaction.user.id, event_id)

    @calendar_group.command(name="wipe", description="Delete all your events")
    async def wipe_events(self, interaction: discord.Interaction) -> None:
        """Delete all events for the user.

        Args:
            interaction: The Discord interaction.
        """
        await self.defer_response(interaction)

        # Check if user has any events
        event_count = await self.db.count_events(interaction.user.id)

        if event_count == 0:
            await self.edit_response(
                interaction,
                content="📭 You don't have any events to delete.",
            )
            return

        # Show confirmation
        view = ConfirmView(
            author_id=interaction.user.id,
            confirm_label=f"Yes, delete {event_count} events",
        )

        await self.edit_response(
            interaction,
            content=f"⚠️ Are you sure you want to delete **{event_count}** events?\n\nThis action cannot be undone.",
            view=view,
        )

        # Wait for response
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
                content=f"🗑️ Deleted **{deleted}** events.",
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
    """Load the calendar cog.

    Args:
        bot: The bot instance.
    """
    await bot.add_cog(CalendarCog(bot))
