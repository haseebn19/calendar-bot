"""The bot class and the `calendar-bot` command that runs it."""

from __future__ import annotations

import asyncio
import logging
import sys

import discord
from discord import app_commands
from discord.ext import commands

from calendar_bot.config import Config, setup_logging
from calendar_bot.database import DatabaseRepository

logger = logging.getLogger(__name__)

COG_MODULES = [
    "calendar_bot.cogs.calendar",
    "calendar_bot.cogs.timezone",
    "calendar_bot.cogs.settings",
    "calendar_bot.cogs.help",
]


class CalendarBot(commands.Bot):
    def __init__(self, config: Config) -> None:
        # Every command is a slash command; commands.Bot still needs a prefix, so use mentions.
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
            help_command=None,  # /help commands replaces the built-in help
        )

        self.config = config
        self.db = DatabaseRepository(config.database_path)

    async def setup_hook(self) -> None:
        """Open the database, load the commands, and register them with Discord."""
        await self.db.initialize()

        for cog in COG_MODULES:
            await self.load_extension(cog)
            logger.info("Loaded cog: %s", cog)

        self.tree.error(self.on_app_command_error)

        # Global commands can take up to an hour to appear in Discord after the first sync
        logger.info("Syncing slash commands...")
        synced = await self.tree.sync()
        logger.info("Synced %d commands", len(synced))

    async def on_ready(self) -> None:
        if self.user:
            logger.info("Logged in as %s (ID: %s)", self.user.name, self.user.id)
            logger.info("Connected to %d guilds", len(self.guilds))

            # Shown under the bot's name, so people can find the commands
            activity = discord.Activity(type=discord.ActivityType.watching, name="/help commands")
            await self.change_presence(activity=activity)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        """Log a slash command that failed and tell the user, so the command does not hang."""
        command = interaction.command.qualified_name if interaction.command else "unknown"
        logger.error("Command /%s failed", command, exc_info=error)

        message = "❌ Something went wrong. Please try again."
        if interaction.response.is_done():
            await interaction.edit_original_response(content=message, embed=None, view=None)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    async def close(self) -> None:
        logger.info("Shutting down")
        await self.db.close()
        await super().close()


async def run_bot(config: Config) -> None:
    async with CalendarBot(config) as bot:
        await bot.start(config.discord_token)


def main() -> None:
    try:
        config = Config.from_env()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config)
    try:
        asyncio.run(run_bot(config))
    except discord.LoginFailure:
        logger.error("Discord rejected the login. Check DISCORD_TOKEN in your .env file.")
        sys.exit(1)
    except KeyboardInterrupt:
        pass  # Ctrl+C stops the bot, which closes cleanly on the way out


if __name__ == "__main__":
    main()
