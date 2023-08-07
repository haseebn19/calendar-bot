from lib import *
import views


# ------------ TIMEZONES GROUP COMMANDS ------------
def setup(bot: commands.Bot):
    calendar = bot.create_group(name="calendar")

    # Command to add an event to the calendar
    @calendar.command(name="add", description="Add an event to the calendar")
    async def addevent(
        ctx: commands.Context,
        title: str,
        year: int,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
    ):
        user_id = str(ctx.author.id)
        user_timezone = bot.user_data_handler.get_user_timezone(user_id)
        await ctx.defer()

        if not user_timezone:
            await ctx.edit(
                content="Please set your timezone first using `/timezone set <timezone_name>`."
            )
            return

        local_tz = pytz.timezone(user_timezone)
        try:
            local_datetime = local_tz.localize(
                datetime.datetime(year, month, day, hour, minute)
            )
        except ValueError as e:
            await ctx.edit(
                content="The date or time provided is out of range. Please check the values and try again."
            )
            return
        except OverflowError as e:
            await ctx.edit(
                content="The values provided are too large. Please enter valid date and time values."
            )
            return

        utc_time = local_datetime.astimezone(pytz.UTC)

        user_data = bot.user_data_handler.load_user_data(user_id)
        if "events" not in user_data:
            user_data["events"] = []

        event_id = len(user_data["events"])
        new_event = {
            "id": event_id,
            "name": title,
            "time": int(utc_time.timestamp()),  # Store time as Unix timestamp
        }
        user_data["events"].append(new_event)
        bot.user_data_handler.save_user_data(user_id, user_data)

        timestamp = int(utc_time.timestamp())
        await ctx.edit(content=f"**{title}**: <t:{timestamp}:f>, <t:{timestamp}:R>")

    # Command to list events
    @calendar.command(name="list", description="List events")
    async def eventlist(ctx: commands.Context, member: discord.Member = None):
        await ctx.defer()
        user_id = str(member.id) if member else str(ctx.author.id)
        user_data = bot.user_data_handler.load_user_data(user_id)

        if "events" not in user_data or not user_data["events"]:
            await ctx.edit(content="No events found.")
            return

        events = user_data["events"]
        events.sort(key=lambda x: x["time"])

        # Split the list into chunks of 10
        event_chunks = [events[i : i + 10] for i in range(0, len(events), 10)]

        view = views.EventListView(event_chunks, ctx)
        await ctx.edit(embed=view.create_embed(), view=view)

    # Command to remove an event by its ID
    @calendar.command(name="remove", description="Remove an event by its ID")
    async def removeevent(ctx: commands.Context, event_id: int):
        await ctx.defer()
        user_id = str(ctx.author.id)
        user_data = bot.user_data_handler.load_user_data(user_id)

        if "events" not in user_data or not user_data["events"]:
            await ctx.edit(content="No events found.")
            return

        events = user_data["events"]
        event_index = next(
            (index for (index, event) in enumerate(events) if event["id"] == event_id),
            None,
        )

        if event_index is not None:
            event_name = events[event_index]["name"]
            events.pop(event_index)
            bot.user_data_handler.save_user_data(user_id, user_data)
            await ctx.edit(content=f'Event "{event_name}" removed.')
        else:
            await ctx.edit(content="Event not found.")

    # Command to delete all events
    @calendar.command(name="wipe", description="Delete all events")
    async def wipe(ctx: commands.Context):
        await ctx.defer()
        user_id = str(ctx.author.id)
        user_data = bot.user_data_handler.load_user_data(user_id)

        if "events" not in user_data or not user_data["events"]:
            await ctx.edit(content="No events found.")
            return

        confirm_response = views.Confirm(user_id=ctx.author.id, timeout=15)
        await ctx.edit(
            content="Are you sure you want to delete all events?", view=confirm_response
        )
        await confirm_response.wait()

        if confirm_response.value is None:
            await ctx.send(content="You didn't respond in time, please try again.")
        elif confirm_response.value:
            user_data["events"] = []
            bot.user_data_handler.save_user_data(user_id, user_data)
            await ctx.send(content="All events have been deleted.")
        else:
            await ctx.send(content="Operation cancelled.")

    print("Calendar group loaded")
