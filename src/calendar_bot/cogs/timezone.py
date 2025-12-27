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
        """Set the user's timezone.

        Args:
            interaction: The Discord interaction.
            timezone_name: The timezone string.
        """
        await self.defer_response(interaction)

        # Validate timezone
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

        # Save timezone
        await self.db.update_user_timezone(interaction.user.id, timezone_name)

        # Get current time in the timezone
        now = datetime.now(pytz.timezone(timezone_name))
        formatted_time = now.strftime("%I:%M %p")

        await self.edit_response(
            interaction,
            content=(f"✅ Timezone set to **{timezone_name}**\nCurrent time: **{formatted_time}**"),
        )
        self.logger.info("User %s set timezone to %s", interaction.user.id, timezone_name)

    @set_timezone.autocomplete("timezone_name")
    async def timezone_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for timezone names.

        Args:
            interaction: The Discord interaction.
            current: Current input string.

        Returns:
            List of matching timezone choices.
        """
        # Filter and sort timezones
        current_lower = current.lower()
        matches = [tz for tz in pytz.common_timezones if current_lower in tz.lower()][
            :25
        ]  # Discord limits to 25 choices

        return [app_commands.Choice(name=tz, value=tz) for tz in sorted(matches)]

    @timezone_group.command(name="list", description="List all available timezones")
    async def list_timezones(self, interaction: discord.Interaction) -> None:
        """List all available timezones with pagination.

        Args:
            interaction: The Discord interaction.
        """
        await self.defer_response(interaction)

        # Create timezone list with current UTC offsets
        timezone_list = []
        for tz_name in pytz.common_timezones:
            try:
                tz = pytz.timezone(tz_name)
                offset = datetime.now(tz).strftime("%z")
                # Format offset nicely
                formatted_offset = f"UTC{offset[:3]}:{offset[3:]}"
                timezone_list.append((tz_name, formatted_offset))
            except Exception:
                continue

        # Sort by offset
        def offset_key(item: tuple) -> int:
            offset = item[1].replace("UTC", "").replace(":", "")
            try:
                return int(offset)
            except ValueError:
                return 0

        timezone_list.sort(key=offset_key)

        # Create paginated view
        view = TimezoneView(
            items=timezone_list,
            author_id=interaction.user.id,
        )

        await self.edit_response(
            interaction,
            embed=view.create_embed(),
            view=view,
        )

    @timezone_group.command(name="get", description="Show your current timezone")
    async def get_timezone(self, interaction: discord.Interaction) -> None:
        """Show the user's current timezone.

        Args:
            interaction: The Discord interaction.
        """
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

        now = datetime.now(pytz.timezone(user.timezone))
        formatted_time = now.strftime("%A, %B %d, %Y at %I:%M %p")

        await self.edit_response(
            interaction,
            content=(f"🕐 Your timezone: **{user.timezone}**\nCurrent time: **{formatted_time}**"),
        )


async def setup(bot: CalendarBot) -> None:
    """Load the timezone cog.

    Args:
        bot: The bot instance.
    """
    await bot.add_cog(TimezoneCog(bot))
