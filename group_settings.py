from lib import *


def setup(bot: commands.Bot):
    settings = bot.create_group(name="settings", description="Manage your settings")

    @settings.command(name="privacy", description="Set your calendar privacy settings")
    async def privacy(
        ctx: commands.Context,
        privacy: discord.commands.Option(
            str,
            "Choose privacy setting",
            choices=[
                discord.commands.OptionChoice(name="public", value="public"),
                discord.commands.OptionChoice(name="private", value="private"),
            ],
        ),
    ):
        """Adjust privacy settings for user data"""
        await ctx.defer()
        user_id = str(ctx.author.id)

        bot.user_data_handler.set_key(user_id, key="privacy", new_value=privacy)

        await ctx.edit(content=f"Your privacy setting has been set to {privacy}.")

    print("Settings group loaded")
