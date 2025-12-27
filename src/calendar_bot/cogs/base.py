"""Base cog with shared functionality."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from calendar_bot.bot import CalendarBot

# Sentinel to distinguish "not passed" from "explicitly None"
_UNSET: Any = object()


class BaseCog(commands.Cog):
    """Base class for all cogs with privacy-aware responses."""

    def __init__(self, bot: CalendarBot) -> None:
        self.bot = bot
        self.logger = logging.getLogger(f"calendar_bot.cogs.{self.__class__.__name__}")

    @property
    def db(self):
        return self.bot.db

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
        user = await self.db.get_or_create_user(interaction.user.id)
        ephemeral = force_ephemeral or user.is_private

        # Build kwargs, only include view if it's not None
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
        user = await self.db.get_or_create_user(interaction.user.id)
        await interaction.response.defer(ephemeral=user.is_private)
