from lib import *
import views


class TimezoneCog(commands.Cog):
    def __init__(self, bot, user_data_handler):
        self.bot = bot
        self.user_data_handler = user_data_handler

    @commands.group(name="timezone")
    async def timezone(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid timezone command passed...")

    @timezone.command(name="set", description="Set your timezone")
    async def set_timezone(self, ctx, timezone_name: str):
        await ctx.defer()
        if timezone_name not in pytz.all_timezones_set:
            await ctx.edit(
                content="Invalid timezone. Please use `/timezone list` to see available timezones."
            )
            return
        self.user_data_handler.set_user_timezone(str(ctx.author.id), timezone_name)
        await ctx.edit(content=f"Your timezone has been set to {timezone_name}.")

    @timezone.command(name="list", description="List all available timezones")
    async def list_timezones(self, ctx):
        await ctx.defer()
        # Create a list of all timezones with their current UTC offset
        timezone_list = [
            (tz, datetime.datetime.now(pytz.timezone(tz)).strftime("%z"))
            for tz in pytz.all_timezones_set
        ]
        # Convert the UTC offset to minutes and sort the list by the offset
        timezone_list.sort(
            key=lambda x: int(x[1][:3]) * 60 + int(x[1][3:5])
            if x[1][0] == "+"
            else -int(x[1][1:3]) * 60 - int(x[1][3:5])
        )
        # Split the list into chunks of 10
        timezone_chunks = [
            timezone_list[i : i + 10] for i in range(0, len(timezone_list), 10)
        ]
        view = views.TimezoneView(timezone_chunks, ctx)
        await ctx.edit(embed=view.create_embed(), view=view)


def setup(bot, user_data_handler):
    bot.add_cog(TimezoneCog(bot, user_data_handler))
