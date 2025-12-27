"""Main bot module for Calendar Bot.

This module contains the CalendarBot class and the main entry point.
"""

from __future__ import annotations

import asyncio
import logging
import sys

import discord
from discord.ext import commands

from calendar_bot.config import Config, setup_logging
from calendar_bot.database import DatabaseRepository

logger = logging.getLogger(__name__)


class CalendarBot(commands.Bot):
    """The main Calendar Bot class.

    This bot uses slash commands (app_commands) for all interactions.
    """

    def __init__(self, config: Config) -> None:
        """Initialize the bot.

        Args:
            config: Bot configuration.
        """
        intents = discord.Intents.default()

        super().__init__(
            command_prefix=commands.when_mentioned,  # Only respond to mentions
            intents=intents,
            help_command=None,  # We use our own help command
        )

        self.config = config
        self.db = DatabaseRepository(config.database_path)
        self._logger = logging.getLogger("calendar_bot.bot")

    async def setup_hook(self) -> None:
        """Called when the bot is starting up.

        This is where we:
        1. Initialize the database
        2. Load all cogs
        3. Sync slash commands
        """
        self._logger.info("Starting bot setup...")

        # Initialize database
        await self.db.initialize()

        # Load cogs
        cog_modules = [
            "calendar_bot.cogs.calendar",
            "calendar_bot.cogs.timezone",
            "calendar_bot.cogs.settings",
            "calendar_bot.cogs.utility",
            "calendar_bot.cogs.help",
        ]

        for cog in cog_modules:
            try:
                await self.load_extension(cog)
                self._logger.info("Loaded cog: %s", cog)
            except Exception as e:
                self._logger.error("Failed to load cog %s: %s", cog, e)
                raise

        # Sync commands globally
        # In production, you might want to sync to specific guilds first for faster updates
        self._logger.info("Syncing slash commands...")
        synced = await self.tree.sync()
        self._logger.info("Synced %d commands", len(synced))

    async def on_ready(self) -> None:
        """Called when the bot is ready and connected."""
        if self.user:
            self._logger.info("Logged in as %s (ID: %s)", self.user.name, self.user.id)
            self._logger.info("Connected to %d guilds", len(self.guilds))

            # Set presence
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="/help commands",
            )
            await self.change_presence(activity=activity)

    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ) -> None:
        """Global error handler for prefix commands (if any)."""
        self._logger.error("Command error: %s", error)

    async def close(self) -> None:
        """Clean up resources when the bot shuts down."""
        self._logger.info("Shutting down...")
        await self.db.close()
        await super().close()


async def run_bot(config: Config) -> None:
    """Run the bot with the given configuration.

    Args:
        config: Bot configuration.
    """
    async with CalendarBot(config) as bot:
        await bot.start(config.discord_token)


def main() -> None:
    """Main entry point for the bot."""
    try:
        # Load configuration
        config = Config.from_env()

        # Setup logging
        setup_logging(config)

        # Run the bot
        asyncio.run(run_bot(config))

    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
