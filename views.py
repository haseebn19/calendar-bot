from lib import *


# Base class for paginated views
class PaginatedView(discord.ui.View):
    def __init__(self, items, ctx):
        super().__init__(timeout=None)
        self.items = items  # Items to be displayed in the view
        self.ctx = ctx  # Context of the command
        self.page = 0  # Current page index

    # Button to go to the previous page
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        # Decrement page index or wrap around if at the beginning
        if self.page > 0:
            self.page -= 1
        else:
            self.page = len(self.items) - 1
        await interaction.response.edit_message(embed=self.create_embed())

    # Button to go to the next page
    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        # Increment page index or wrap around if at the end
        if self.page < len(self.items) - 1:
            self.page += 1
        else:
            self.page = 0
        await interaction.response.edit_message(embed=self.create_embed())

    # Method to create an embed for the current page
    # Must be implemented by subclasses
    def create_embed(self):
        raise NotImplementedError


# View for displaying timezones
class TimezoneView(PaginatedView):
    def create_embed(self):
        embed = discord.Embed(
            title="Available Timezones", colour=discord.Colour.green()
        )
        embed.set_footer(text=f"Page {self.page+1}/{len(self.items)}")
        # Add each timezone and its UTC offset as a field
        for timezone, offset in self.items[self.page]:
            embed.add_field(name=timezone, value=f"`UTC {offset}`", inline=False)
        return embed


# View for displaying events
class EventListView(PaginatedView):
    def create_embed(self):
        embed = discord.Embed(title="Your Events", colour=discord.Colour.green())
        embed.set_footer(text=f"Page {self.page+1}/{len(self.items)}")
        # Add each event with its ID, name, and time as a field
        for event in self.items[self.page]:
            event_time = datetime.datetime.fromtimestamp(event["time"])
            timestamp = int(event_time.timestamp())
            embed.add_field(
                name=f"`{event['id']}` - **{event['name']}**",
                value=f"<t:{timestamp}:f>, <t:{timestamp}:R>",
                inline=False,
            )
        return embed


# View for confirming an action
class Confirm(discord.ui.View):
    def __init__(self, user_id: str, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.user_id = user_id  # ID of the user who initiated the command

    # Button to confirm the action
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        # Check if the interaction is from the user who initiated the command
        if interaction.user.id == self.user_id:
            self.value = True
            self.stop()
            await interaction.message.edit(view=None)

    # Button to cancel the action
    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Check if the interaction is from the user who initiated the command
        if interaction.user.id == self.user_id:
            self.value = False
            self.stop()
            await interaction.message.edit(view=None)
