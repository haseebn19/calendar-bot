"""Settings management cog for Calendar Bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from calendar_bot.cogs.base import BaseCog, plural
from calendar_bot.database.models import PrivacySetting, User
from calendar_bot.utils.views import ConfirmView

if TYPE_CHECKING:
    from calendar_bot.bot import CalendarBot


class SettingsCog(BaseCog):
    """Cog for user settings commands."""

    settings_group = app_commands.Group(
        name="settings",
        description="Manage your bot settings",
    )

    @settings_group.command(name="privacy", description="Set your privacy mode")
    @app_commands.describe(
        mode="Choose your privacy setting. Private makes all responses only visible to you"
    )
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="Private: only you can see responses", value="private"),
            app_commands.Choice(name="Public: everyone can see responses", value="public"),
        ]
    )
    async def set_privacy(
        self,
        interaction: discord.Interaction,
        mode: str,
    ) -> None:
        """Set the user's privacy mode.

        Private makes every response visible only to the user and hides their calendar from
        others. Public shows responses in the channel and lets others view the calendar.
        """
        privacy = PrivacySetting(mode)
        await self.db.update_user_privacy(interaction.user.id, privacy)

        if privacy == PrivacySetting.PRIVATE:
            await interaction.response.send_message(
                "🔒 Privacy mode set to **private**.\n\n"
                "• All bot responses will only be visible to you\n"
                "• Other users cannot view your calendar",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "🌍 Privacy mode set to **public**.\n\n"
                "• Bot responses will be visible to everyone\n"
                "• Other users can view your calendar",
                ephemeral=False,
            )

        self.logger.info("User %s set privacy to %s", interaction.user.id, mode)

    @settings_group.command(name="view", description="View your current settings")
    async def view_settings(self, interaction: discord.Interaction) -> None:
        """Show the user's privacy mode and timezone."""
        user = await self.db.get_user(interaction.user.id) or User(discord_id=interaction.user.id)

        embed = discord.Embed(title="Your Settings", color=discord.Color.blue())
        embed.add_field(
            name="Privacy Mode",
            value="Private" if user.is_private else "Public",
            inline=True,
        )
        embed.add_field(name="Timezone", value=user.timezone or "Not set", inline=True)
        embed.set_footer(
            text="Use /settings privacy to change privacy, or /timezone set to change timezone"
        )

        await self.send_response(interaction, embed=embed)

    @settings_group.command(name="wipe", description="Delete all your data (events and account)")
    async def wipe_data(self, interaction: discord.Interaction) -> None:
        """Delete the user's events and account settings after they confirm."""
        await self.defer_response(interaction)

        user = await self.db.get_user(interaction.user.id)
        event_count = await self.db.count_events(interaction.user.id)

        if not user and event_count == 0:
            await self.edit_response(
                interaction,
                content="📭 You don't have any data to delete.",
            )
            return

        data_summary = []
        if event_count > 0:
            data_summary.append(plural(event_count, "event"))
        if user:
            data_summary.append("your account settings")

        view = ConfirmView(
            author_id=interaction.user.id,
            confirm_label="Yes, delete all my data",
        )
        await self.edit_response(
            interaction,
            content=(
                "⚠️ Are you sure you want to delete **all your data**?\n\n"
                f"This will permanently delete: {' and '.join(data_summary)}\n\n"
                "This action **cannot be undone**."
            ),
            view=view,
        )
        await view.wait()

        if view.value is None:
            await self.edit_response(
                interaction,
                content="⏰ Confirmation timed out. No data was deleted.",
                view=None,
            )
        elif view.value:
            events_deleted, user_existed = await self.db.delete_user(interaction.user.id)
            deleted_items = []
            if events_deleted > 0:
                deleted_items.append(plural(events_deleted, "event"))
            if user_existed:
                deleted_items.append("account settings")

            await self.edit_response(
                interaction,
                content=f"🗑️ All your data has been deleted: {' and '.join(deleted_items)}.",
                view=None,
            )
            self.logger.info(
                "User %s deleted all data: %d events, user_existed=%s",
                interaction.user.id,
                events_deleted,
                user_existed,
            )
        else:
            await self.edit_response(
                interaction,
                content="❌ Operation cancelled. No data was deleted.",
                view=None,
            )


async def setup(bot: CalendarBot) -> None:
    """Load the settings cog."""
    await bot.add_cog(SettingsCog(bot))
