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
        user_data = bot.user_data_handler.load_user_data(user_id)

        # Set the visibility in the user's data
        user_data["visibility"] = visibility
        bot.user_data_handler.save_user_data(user_id, user_data)

        await ctx.edit(content=f"Your visibility setting has been set to {visibility}.")

    print("Settings group loaded")
