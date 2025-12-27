"""Discord UI Views for Calendar Bot.

This module provides reusable UI components like paginated embeds
and confirmation dialogs.
"""

from __future__ import annotations

import discord


class PaginatedView(discord.ui.View):
    """Base class for paginated views with navigation buttons.

    This view provides Previous/Next buttons for navigating through
    pages of items. Subclasses must implement create_embed().
    """

    def __init__(
        self,
        items: list,
        author_id: int,
        *,
        timeout: float = 180.0,
        items_per_page: int = 10,
    ) -> None:
        """Initialize the paginated view.

        Args:
            items: List of items to paginate (will be chunked by items_per_page).
            author_id: Discord ID of the user who initiated the view.
            timeout: View timeout in seconds.
            items_per_page: Number of items per page.
        """
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.items_per_page = items_per_page
        self.page = 0

        # Chunk items into pages
        self.pages: list[list] = [
            items[i : i + items_per_page] for i in range(0, len(items), items_per_page)
        ]

        # Hide buttons if single page
        if len(self.pages) <= 1:
            self.previous_button.disabled = True
            self.next_button.disabled = True

    @property
    def total_pages(self) -> int:
        """Get total number of pages."""
        return len(self.pages)

    @property
    def current_items(self) -> list:
        """Get items for current page."""
        if not self.pages:
            return []
        return self.pages[self.page]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the interaction is from the original author."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Navigate to the previous page."""
        self.page = (self.page - 1) % self.total_pages
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Navigate to the next page."""
        self.page = (self.page + 1) % self.total_pages
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    def create_embed(self) -> discord.Embed:
        """Create the embed for the current page.

        Must be implemented by subclasses.

        Returns:
            The embed to display.
        """
        raise NotImplementedError("Subclasses must implement create_embed()")


class TimezoneView(PaginatedView):
    """View for displaying available timezones."""

    def create_embed(self) -> discord.Embed:
        """Create an embed showing timezones for the current page."""
        embed = discord.Embed(
            title="🌍 Available Timezones",
            color=discord.Color.blue(),
        )

        if not self.current_items:
            embed.description = "No timezones found."
            return embed

        # Build timezone list
        lines = []
        for tz_name, offset in self.current_items:
            lines.append(f"`{offset}` — {tz_name}")

        embed.description = "\n".join(lines)
        embed.set_footer(text=f"Page {self.page + 1}/{self.total_pages}")

        return embed


class EventListView(PaginatedView):
    """View for displaying calendar events."""

    def create_embed(self) -> discord.Embed:
        """Create an embed showing events for the current page."""
        embed = discord.Embed(
            title="📅 Your Events",
            color=discord.Color.green(),
        )

        if not self.current_items:
            embed.description = "No events found."
            return embed

        # Build event list
        for event in self.current_items:
            embed.add_field(
                name=f"`#{event.id}` — {event.title}",
                value=f"{event.discord_timestamp} ({event.discord_relative})",
                inline=False,
            )

        embed.set_footer(text=f"Page {self.page + 1}/{self.total_pages}")

        return embed


class ConfirmView(discord.ui.View):
    """View for confirming destructive actions."""

    def __init__(
        self,
        author_id: int,
        *,
        timeout: float = 30.0,
        confirm_label: str = "Yes, delete",
        cancel_label: str = "Cancel",
    ) -> None:
        """Initialize the confirmation view.

        Args:
            author_id: Discord ID of the user who can interact.
            timeout: View timeout in seconds.
            confirm_label: Label for the confirm button.
            cancel_label: Label for the cancel button.
        """
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value: bool | None = None

        # Update button labels
        self.confirm_button.label = confirm_label
        self.cancel_button.label = cancel_label

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the interaction is from the original author."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Handle confirmation."""
        self.value = True
        self.stop()
        # Disable buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Handle cancellation."""
        self.value = False
        self.stop()
        # Disable buttons
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await interaction.response.edit_message(view=self)

    async def on_timeout(self) -> None:
        """Handle view timeout."""
        self.value = None
        self.stop()
