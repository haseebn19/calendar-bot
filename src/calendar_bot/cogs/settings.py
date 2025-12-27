"""Settings management cog for Calendar Bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands

from calendar_bot.cogs.base import BaseCog
from calendar_bot.database.models import PrivacySetting
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
        mode="Choose your privacy setting - private makes all responses only visible to you"
    )
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="🔒 Private - Only you can see responses", value="private"),
            app_commands.Choice(name="🌍 Public - Everyone can see responses", value="public"),
        ]
    )
    async def set_privacy(
        self,
        interaction: discord.Interaction,
        mode: str,
    ) -> None:
        """Set the user's privacy mode.

        When set to private:
        - All command responses are ephemeral (only visible to you)
        - Other users cannot view your calendar

        When set to public:
        - Command responses are visible to everyone in the channel
        - Other users can view your calendar

        Args:
            interaction: The Discord interaction.
            mode: The privacy mode ('private' or 'public').
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
        """Show the user's current settings.

        Args:
            interaction: The Discord interaction.
        """
        user = await self.db.get_or_create_user(interaction.user.id)

        # Build settings embed
        embed = discord.Embed(
            title="⚙️ Your Settings",
            color=discord.Color.blue(),
        )

        # Privacy setting
        privacy_emoji = "🔒" if user.is_private else "🌍"
        privacy_text = "Private" if user.is_private else "Public"
        embed.add_field(
            name="Privacy Mode",
            value=f"{privacy_emoji} {privacy_text}",
            inline=True,
        )

        # Timezone
        tz_text = user.timezone if user.timezone else "Not set"
        embed.add_field(
            name="Timezone",
            value=f"🕐 {tz_text}",
            inline=True,
        )

        embed.set_footer(
            text="Use /settings privacy to change privacy • /timezone set to change timezone"
        )

        await self.send_response(interaction, embed=embed)

    @settings_group.command(name="wipe", description="Delete all your data (events and account)")
    async def wipe_data(self, interaction: discord.Interaction) -> None:
        """Delete all user data including events and account settings.

        Args:
            interaction: The Discord interaction.
        """
        await self.defer_response(interaction)

        # Check if user has any data
        user = await self.db.get_user(interaction.user.id)
        event_count = await self.db.count_events(interaction.user.id)

        if not user and event_count == 0:
            await self.edit_response(
                interaction,
                content="You don't have any data to delete.",
            )
            return

        # Show confirmation
        data_summary = []
        if event_count > 0:
            data_summary.append(f"{event_count} event{'s' if event_count != 1 else ''}")
        if user:
            data_summary.append("your account settings")
        summary_text = " and ".join(data_summary)

        view = ConfirmView(
            author_id=interaction.user.id,
            confirm_label="Yes, delete all my data",
        )

        await self.edit_response(
            interaction,
            content=(
                f"Are you sure you want to delete **all your data**?\n\n"
                f"This will permanently delete: {summary_text}\n\n"
                f"This action **cannot be undone**."
            ),
            view=view,
        )

        # Wait for response
        await view.wait()

        if view.value is None:
            await self.edit_response(
                interaction,
                content="Confirmation timed out. No data was deleted.",
                view=None,
            )
        elif view.value:
            events_deleted, user_existed = await self.db.delete_user(interaction.user.id)
            deleted_items = []
            if events_deleted > 0:
                deleted_items.append(f"{events_deleted} event{'s' if events_deleted != 1 else ''}")
            if user_existed:
                deleted_items.append("account settings")
            items_text = " and ".join(deleted_items)

            await self.edit_response(
                interaction,
                content=f"All your data has been deleted: {items_text}.",
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
                content="Operation cancelled. No data was deleted.",
                view=None,
            )


async def setup(bot: CalendarBot) -> None:
    """Load the settings cog.

    Args:
        bot: The bot instance.
    """
    await bot.add_cog(SettingsCog(bot))
