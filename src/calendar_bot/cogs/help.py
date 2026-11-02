"""Help command cog for Calendar Bot."""

from __future__ import annotations

from importlib.metadata import version
from typing import TYPE_CHECKING

import discord
from discord import app_commands

from calendar_bot.cogs.base import BaseCog

if TYPE_CHECKING:
    from calendar_bot.bot import CalendarBot


class HelpCog(BaseCog):
    """Cog for help and information commands."""

    help_group = app_commands.Group(
        name="help",
        description="Get help with bot commands",
    )

    @help_group.command(name="commands", description="Show all available commands")
    async def show_commands(self, interaction: discord.Interaction) -> None:
        """Show all available commands grouped by category."""
        embed = discord.Embed(title="Calendar Bot Commands", color=discord.Color.blue())

        embed.add_field(
            name="Calendar",
            value=(
                "`/calendar add` - Add an event to your calendar\n"
                "`/calendar list` - List your events\n"
                "`/calendar remove` - Remove an event by ID\n"
                "`/calendar wipe` - Delete all your events"
            ),
            inline=False,
        )
        embed.add_field(
            name="Timezone",
            value=(
                "`/timezone set` - Set your timezone\n"
                "`/timezone get` - Show your current timezone\n"
                "`/timezone list` - List all available timezones"
            ),
            inline=False,
        )
        embed.add_field(
            name="Settings",
            value=(
                "`/settings privacy` - Set your privacy mode\n"
                "`/settings view` - View your current settings\n"
                "`/settings wipe` - Delete all your data (events and account)"
            ),
            inline=False,
        )
        embed.add_field(
            name="Help",
            value="`/help commands` - Show this help message\n`/help about` - Learn about the bot",
            inline=False,
        )
        embed.set_footer(text="Tip: press Tab to autocomplete commands and options.")

        await self.send_response(interaction, embed=embed)

    @help_group.command(name="about", description="Learn about Calendar Bot")
    async def show_about(self, interaction: discord.Interaction) -> None:
        """Show what the bot does and how to get started."""
        embed = discord.Embed(
            title="About Calendar Bot",
            description="Keep track of your events on Discord, in your own timezone.",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Features",
            value=(
                "• Create and manage calendar events\n"
                "• Dates and times in your own timezone\n"
                "• Privacy controls (public/private mode)\n"
                "• View other users' public calendars\n"
                "• Events shown in each viewer's local time"
            ),
            inline=False,
        )
        embed.add_field(
            name="Getting Started",
            value=(
                "1. Set your timezone: `/timezone set America/New_York`\n"
                "2. Add an event: `/calendar add title:Meeting month:January day:15 time:10am`\n"
                "3. View events: `/calendar list`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Privacy",
            value=(
                "By default, your calendar is **private**. "
                "Use `/settings privacy` to make it public if you want others to see your events."
            ),
            inline=False,
        )

        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text=f"Version {version('calendar-bot')}, running on discord.py {discord.__version__}"
        )

        await self.send_response(interaction, embed=embed)


async def setup(bot: CalendarBot) -> None:
    """Load the help cog."""
    await bot.add_cog(HelpCog(bot))
