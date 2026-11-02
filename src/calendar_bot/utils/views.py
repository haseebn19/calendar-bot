"""Discord UI views for Calendar Bot: paginated lists and confirmation dialogs."""

from __future__ import annotations

import discord

# Discord rejects an embed whose field names are longer than this
FIELD_NAME_LIMIT = 256


class AuthorOnlyView(discord.ui.View):
    """A view whose buttons only respond to the user who ran the command."""

    def __init__(self, author_id: int, *, timeout: float) -> None:
        super().__init__(timeout=timeout)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
            return False
        return True


class PaginatedView(AuthorOnlyView):
    """Previous and Next buttons for paging through a list, which must not be empty.

    Subclasses implement create_embed() to show `current_items`.
    """

    def __init__(
        self,
        items: list,
        author_id: int,
        *,
        title: str,
        timeout: float = 180.0,
        items_per_page: int = 10,
    ) -> None:
        super().__init__(author_id, timeout=timeout)
        self.title = title
        self.page = 0
        self.pages: list[list] = [
            items[i : i + items_per_page] for i in range(0, len(items), items_per_page)
        ]

        if len(self.pages) <= 1:
            self.previous_button.disabled = True
            self.next_button.disabled = True

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    @property
    def current_items(self) -> list:
        return self.pages[self.page]

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Show the previous page, wrapping round to the last."""
        self.page = (self.page - 1) % self.total_pages
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """Show the next page, wrapping round to the first."""
        self.page = (self.page + 1) % self.total_pages
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    def create_embed(self) -> discord.Embed:
        """Create the embed for the current page."""
        raise NotImplementedError("Subclasses must implement create_embed()")

    def _page_footer(self, embed: discord.Embed) -> discord.Embed:
        embed.set_footer(text=f"Page {self.page + 1}/{self.total_pages}")
        return embed


class TimezoneView(PaginatedView):
    """Paginated list of (timezone name, UTC offset) pairs."""

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title=self.title, color=discord.Color.blue())
        embed.description = "\n".join(f"`{offset}` {name}" for name, offset in self.current_items)
        return self._page_footer(embed)


class EventListView(PaginatedView):
    """Paginated list of calendar events."""

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title=self.title, color=discord.Color.green())
        for event in self.current_items:
            name = f"`#{event.id}` {event.title}"
            if len(name) > FIELD_NAME_LIMIT:
                name = name[: FIELD_NAME_LIMIT - 3] + "..."
            embed.add_field(
                name=name,
                value=f"{event.discord_timestamp} ({event.discord_relative})",
                inline=False,
            )
        return self._page_footer(embed)


class ConfirmView(AuthorOnlyView):
    """Confirm and Cancel buttons for a destructive action.

    After `wait()`, `value` is True if confirmed, False if cancelled, or None if it timed out.
    """

    def __init__(
        self,
        author_id: int,
        *,
        confirm_label: str,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(author_id, timeout=timeout)
        self.value: bool | None = None
        self.confirm_button.label = confirm_label

    async def _finish(self, interaction: discord.Interaction, value: bool) -> None:
        """Record the choice and disable both buttons."""
        self.value = value
        self.stop()
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._finish(interaction, True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self._finish(interaction, False)
