"""Utility commands for Calendar Bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from calendar_bot.cogs.base import BaseCog
from calendar_bot.utils.datetime_parser import DateTimeParser

if TYPE_CHECKING:
    from calendar_bot.bot import CalendarBot


class UtilityCog(BaseCog):
    """Cog for utility commands."""

    @app_commands.command(
        name="timestamp", description="Convert a date/time to Discord timestamp format"
    )
    @app_commands.describe(
        year="Year (defaults to current year)",
        month="Month (name or number, defaults to current month)",
        day="Day (number or name like 'Monday', defaults to current day)",
        time="Time (e.g., '10am', '14:30', '10:30pm')",
    )
    async def timestamp(
        self,
        interaction: discord.Interaction,
        year: int | None = None,
        month: str | None = None,
        day: str | None = None,
        time: str | None = None,
    ) -> None:
        """Convert date/time to Discord timestamp formats."""
        await self.defer_response(interaction)

        # Require at least one parameter
        if all(param is None for param in [year, month, day, time]):
            await self.edit_response(
                interaction,
                content="Please provide at least one date or time parameter.",
            )
            return

        # Get user's timezone
        user = await self.db.get_user(interaction.user.id)
        if not user or not user.timezone:
            await self.edit_response(
                interaction,
                content=(
                    "Please set your timezone first using `/timezone set <timezone>`\n\n"
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
                content=f"{parsed.error_message}",
            )
            return

        # Convert to UTC timestamp
        ts = parser.to_utc_timestamp(parsed)
        if ts is None:
            await self.edit_response(
                interaction,
                content="The date or time provided is invalid.",
            )
            return

        # Build response with all formats
        embed = discord.Embed(
            title="Discord Timestamps",
            description=f"Copy these to use in your messages:\n\n**Parsed:** {parsed.month}/{parsed.day}/{parsed.year} at {parsed.hour:02d}:{parsed.minute:02d}",
            color=discord.Color.blue(),
        )

        formats = [
            ("Short Time", "t", f"<t:{ts}:t>"),
            ("Long Time", "T", f"<t:{ts}:T>"),
            ("Short Date", "d", f"<t:{ts}:d>"),
            ("Long Date", "D", f"<t:{ts}:D>"),
            ("Short Date/Time", "f", f"<t:{ts}:f>"),
            ("Long Date/Time", "F", f"<t:{ts}:F>"),
            ("Relative", "R", f"<t:{ts}:R>"),
        ]

        for name, code, fmt in formats:
            # Show the raw format and what it looks like
            embed.add_field(
                name=f"{name} (:{code})",
                value=f"`{fmt}`\n{fmt}",
                inline=True,
            )

        embed.set_footer(text=f"Unix timestamp: {ts}")

        await self.edit_response(interaction, embed=embed)


async def setup(bot: CalendarBot) -> None:
    """Load the utility cog."""
    await bot.add_cog(UtilityCog(bot))
