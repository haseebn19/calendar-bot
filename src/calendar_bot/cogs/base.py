"""Base cog with shared functionality."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from discord.ext import commands

if TYPE_CHECKING:
    import discord

    from calendar_bot.bot import CalendarBot
    from calendar_bot.database import DatabaseRepository

# Sentinel to distinguish "not passed" from "explicitly None"
_UNSET: Any = object()


def plural(count: int, word: str) -> str:
    """Return the count with the word, adding an "s" unless the count is 1."""
    return f"{count} {word}{'' if count == 1 else 's'}"


class BaseCog(commands.Cog):
    """Base class for all cogs with privacy-aware responses."""

    def __init__(self, bot: CalendarBot) -> None:
        self.bot = bot
        self.logger = logging.getLogger(f"calendar_bot.cogs.{self.__class__.__name__}")

    @property
    def db(self) -> DatabaseRepository:
        return self.bot.db

    async def is_private(self, user_id: int) -> bool:
        """Whether the user's responses are private. Users who have not chosen are private.

        This only reads the setting, so running a command does not store anything.
        """
        user = await self.db.get_user(user_id)
        return user.is_private if user else True

    async def send_response(
        self,
        interaction: discord.Interaction,
        content: str | None = None,
        *,
        embed: discord.Embed | None = None,
        view: discord.ui.View | None = None,
        force_ephemeral: bool = False,
    ) -> None:
        """Send response, respecting user's privacy setting."""
        ephemeral = force_ephemeral or await self.is_private(interaction.user.id)

        # Only pass the parts that were given
        kwargs: dict = {"ephemeral": ephemeral}
        if content is not None:
            kwargs["content"] = content
        if embed is not None:
            kwargs["embed"] = embed
        if view is not None:
            kwargs["view"] = view

        if interaction.response.is_done():
            await interaction.followup.send(**kwargs)
        else:
            await interaction.response.send_message(**kwargs)

    async def edit_response(
        self,
        interaction: discord.Interaction,
        content: str | None = None,
        *,
        embed: discord.Embed | None = None,
        view: discord.ui.View | None = _UNSET,
    ) -> None:
        """Edit original response. Pass view=None to remove the view."""
        kwargs: dict = {}
        if content is not None:
            kwargs["content"] = content
        if embed is not None:
            kwargs["embed"] = embed
        if view is not _UNSET:
            kwargs["view"] = view

        await interaction.edit_original_response(**kwargs)

    async def defer_response(self, interaction: discord.Interaction) -> None:
        """Defer response, respecting user's privacy setting."""
        await interaction.response.defer(ephemeral=await self.is_private(interaction.user.id))
