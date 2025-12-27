"""Help command cog for Calendar Bot."""

from __future__ import annotations

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
        """Show all available commands grouped by category.

        Args:
            interaction: The Discord interaction.
        """
        embed = discord.Embed(
            title="📚 Calendar Bot Commands",
            description="Here are all the available commands:",
            color=discord.Color.blue(),
        )

        # Calendar commands
        embed.add_field(
            name="📅 Calendar",
            value=(
                "`/calendar add` — Add an event to your calendar\n"
                "`/calendar list` — List your events\n"
                "`/calendar remove` — Remove an event by ID\n"
                "`/calendar wipe` — Delete all your events"
            ),
            inline=False,
        )

        # Timezone commands
        embed.add_field(
            name="🌍 Timezone",
            value=(
                "`/timezone set` — Set your timezone\n"
                "`/timezone get` — Show your current timezone\n"
                "`/timezone list` — List all available timezones"
            ),
            inline=False,
        )

        # Settings commands
        embed.add_field(
            name="⚙️ Settings",
            value=(
                "`/settings privacy` — Set your privacy mode\n"
                "`/settings view` — View your current settings\n"
                "`/settings wipe` — Delete all your data (events and account)"
            ),
            inline=False,
        )

        # Utility commands
        embed.add_field(
            name="🔧 Utility",
            value="`/timestamp` — Convert date/time to Discord timestamp format",
            inline=False,
        )

        # Help commands
        embed.add_field(
            name="❓ Help",
            value=(
                "`/help commands` — Show this help message\n`/help about` — Learn about the bot"
            ),
            inline=False,
        )

        embed.set_footer(text="Tip: Use Tab to autocomplete commands and options!")

        await self.send_response(interaction, embed=embed)

    @help_group.command(name="about", description="Learn about Calendar Bot")
    async def show_about(self, interaction: discord.Interaction) -> None:
        """Show information about the bot.

        Args:
            interaction: The Discord interaction.
        """
        embed = discord.Embed(
            title="📅 About Calendar Bot",
            description=(
                "A simple and powerful Discord bot for managing your personal calendar events "
                "with full timezone support."
            ),
            color=discord.Color.green(),
        )

        embed.add_field(
            name="✨ Features",
            value=(
                "• Create and manage calendar events\n"
                "• Full timezone support\n"
                "• Privacy controls (public/private mode)\n"
                "• View other users' public calendars\n"
                "• Discord timestamp formatting"
            ),
            inline=False,
        )

        embed.add_field(
            name="🚀 Getting Started",
            value=(
                "1. Set your timezone: `/timezone set America/New_York`\n"
                "2. Add an event: `/calendar add Meeting month:January day:15 time:10am`\n"
                "3. View events: `/calendar list`"
            ),
            inline=False,
        )

        embed.add_field(
            name="🔒 Privacy",
            value=(
                "By default, your calendar is **private**. "
                "Use `/settings privacy` to make it public if you want others to see your events."
            ),
            inline=False,
        )

        # Add bot info
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.set_footer(text=f"Version 2.0.0 • Running on discord.py {discord.__version__}")

        await self.send_response(interaction, embed=embed)


async def setup(bot: CalendarBot) -> None:
    """Load the help cog.

    Args:
        bot: The bot instance.
    """
    await bot.add_cog(HelpCog(bot))
