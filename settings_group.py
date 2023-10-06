from lib import *


def setup(bot: commands.Bot):
    settings = bot.create_group(name="settings", description="Manage your settings")

    @settings.command(name="visibility", description="Set your visibility settings")
    async def visibility(
        ctx: commands.Context,
        visibility: discord.commands.Option(
            str,
            "Choose visibility setting",
            choices=[
                discord.commands.OptionChoice(name="public", value="public"),
                discord.commands.OptionChoice(name="private", value="private"),
            ],
        ),
    ):
        """Adjust visiblity settings for user data"""
        await ctx.defer()
        user_id = str(ctx.author.id)

        # Call the set_privacy method from UserDataHandler
        bot.user_data_handler.set_privacy(user_id, visibility)

        await ctx.edit(content=f"Your visibility setting has been set to {visibility}.")

    print("Settings group loaded")
