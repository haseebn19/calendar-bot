"""Timezone management cog for Calendar Bot."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import discord
import pytz
from discord import app_commands

from calendar_bot.cogs.base import BaseCog
from calendar_bot.utils.views import TimezoneView

if TYPE_CHECKING:
    from calendar_bot.bot import CalendarBot

# Discord shows at most 25 autocomplete choices
MAX_AUTOCOMPLETE_CHOICES = 25


def timezones_by_offset() -> list[tuple[str, str]]:
    """Return (name, "UTC+hh:mm") for each common timezone, sorted by current UTC offset."""
    entries = []
    for name in pytz.common_timezones:
        local = datetime.now(pytz.timezone(name))
        offset = local.strftime("%z")
        entries.append((local.utcoffset(), name, f"UTC{offset[:3]}:{offset[3:]}"))
    entries.sort()
    return [(name, label) for _, name, label in entries]


class TimezoneCog(BaseCog):
    """Cog for timezone management commands."""

    timezone_group = app_commands.Group(
        name="timezone",
        description="Manage your timezone settings",
    )

    @timezone_group.command(name="set", description="Set your timezone")
    @app_commands.describe(timezone_name="The timezone to set (e.g., America/New_York)")
    async def set_timezone(
        self,
        interaction: discord.Interaction,
        timezone_name: str,
    ) -> None:
        """Set the user's timezone."""
        await self.defer_response(interaction)

        if timezone_name not in pytz.all_timezones_set:
            await self.edit_response(
                interaction,
                content=(
                    f"❌ Invalid timezone: `{timezone_name}`\n\n"
                    "Use `/timezone list` to see available timezones, "
                    "or try common ones like:\n"
                    "• `America/New_York`\n"
                    "• `Europe/London`\n"
                    "• `Asia/Tokyo`"
                ),
            )
            return

        await self.db.update_user_timezone(interaction.user.id, timezone_name)

        current_time = datetime.now(pytz.timezone(timezone_name)).strftime("%I:%M %p")
        await self.edit_response(
            interaction,
            content=f"✅ Timezone set to **{timezone_name}**\nCurrent time: **{current_time}**",
        )
        self.logger.info("User %s set timezone to %s", interaction.user.id, timezone_name)

    @set_timezone.autocomplete("timezone_name")
    async def timezone_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Suggest common timezones containing the text typed so far."""
        current_lower = current.lower()
        matches = [tz for tz in pytz.common_timezones if current_lower in tz.lower()]
        return [app_commands.Choice(name=tz, value=tz) for tz in matches[:MAX_AUTOCOMPLETE_CHOICES]]

    @timezone_group.command(name="list", description="List all available timezones")
    async def list_timezones(self, interaction: discord.Interaction) -> None:
        """List the common timezones with their UTC offsets, a page at a time."""
        await self.defer_response(interaction)

        view = TimezoneView(
            items=timezones_by_offset(),
            author_id=interaction.user.id,
            title="Available Timezones",
        )
        await self.edit_response(interaction, embed=view.create_embed(), view=view)

    @timezone_group.command(name="get", description="Show your current timezone")
    async def get_timezone(self, interaction: discord.Interaction) -> None:
        """Show the user's timezone and the current time there."""
        await self.defer_response(interaction)

        user = await self.db.get_user(interaction.user.id)
        if not user or not user.timezone:
            await self.edit_response(
                interaction,
                content=(
                    "❌ You haven't set a timezone yet.\nUse `/timezone set <timezone>` to set one."
                ),
            )
            return

        current_time = datetime.now(pytz.timezone(user.timezone)).strftime(
            "%A, %B %d, %Y at %I:%M %p"
        )
        await self.edit_response(
            interaction,
            content=f"🕐 Your timezone: **{user.timezone}**\nCurrent time: **{current_time}**",
        )


async def setup(bot: CalendarBot) -> None:
    """Load the timezone cog."""
    await bot.add_cog(TimezoneCog(bot))
