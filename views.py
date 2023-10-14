from lib import *


class PaginatedView(discord.ui.View):
    """Base class for paginated views"""

    def __init__(self, items, ctx):
        super().__init__(timeout=None)
        self.items = items  # Items to be displayed in the view
        self.ctx = ctx  # Context of the command
        self.page = 0  # Current page index

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        """Button to go to the previous page"""
        # Decrement page index or wrap around if at the beginning
        if self.page > 0:
            self.page -= 1
        else:
            self.page = len(self.items) - 1
        await interaction.response.edit_message(embed=self.create_embed())

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        """Button to go to the next page"""
        # Increment page index or wrap around if at the end
        if self.page < len(self.items) - 1:
            self.page += 1
        else:
            self.page = 0
        await interaction.response.edit_message(embed=self.create_embed())

    def create_embed(self):
        """Method to create an embed for the current page, must be implemented by subclasses"""
        raise NotImplementedError


class TimezoneView(PaginatedView):
    """View for displaying timezones"""

    def create_embed(self):
        embed = discord.Embed(
            title="Available Timezones", colour=discord.Colour.green()
        )
        embed.set_footer(text=f"Page {self.page+1}/{len(self.items)}")
        # Add each timezone and its UTC offset as a field
        for timezone, offset in self.items[self.page]:
            embed.add_field(name=timezone, value=f"`UTC {offset}`", inline=False)
        return embed


class EventListView(PaginatedView):
    """View for displaying events"""

    def create_embed(self):
        embed = discord.Embed(title="Your Events", colour=discord.Colour.green())
        embed.set_footer(text=f"Page {self.page+1}/{len(self.items)}")
        # Add each event with its ID, name, and time as a field
        for event in self.items[self.page]:
            event_time = datetime.datetime.fromtimestamp(event["timestamp"])
            timestamp = int(event_time.timestamp())
            embed.add_field(
                name=f"`{event['id']}` - **{event['title']}**",
                value=f"<t:{timestamp}:f>, <t:{timestamp}:R>",
                inline=False,
            )
        return embed


class Confirm(discord.ui.View):
    """View for confirming an action"""

    def __init__(self, user_id: str, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.user_id = user_id  # ID of the user who initiated the command

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        """Button to confirm the action"""
        # Check if the interaction is from the user who initiated the command
        if interaction.user.id == self.user_id:
            self.value = True
            self.stop()
            await interaction.message.edit(view=None)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Button to cancel the action"""
        # Check if the interaction is from the user who initiated the command
        if interaction.user.id == self.user_id:
            self.value = False
            self.stop()
            await interaction.message.edit(view=None)
