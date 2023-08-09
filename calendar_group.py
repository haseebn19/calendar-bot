from lib import *
import views


# ------------ VARIABLES ------------
# Define valid time formats using regex patterns
valid_formats = [
    r"^[1-9]am$",
    r"^[1-9]pm$",
    r"^1[0-2]am$",
    r"^1[0-2]pm$",
    r"^([0-9]|1[0-9]|2[0-3]):[0-5][0-9]$",
    r"^([0-9]|1[0-9]|2[0-3])$",
]

# ------------ HELPER FUNCTIONS ------------
import datetime


def parse_integer(value: str):
    """Parse a string to integer."""
    try:
        return int(value)
    except ValueError:
        return value


def get_month_number(month: str):
    """Get the month number from the input month (Aug = August = 8)."""
    month = parse_integer(month)

    if isinstance(month, int):
        return month

    try:
        # Try parsing full month name
        return int(datetime.datetime.strptime(month, "%B").strftime("%m"))
    except ValueError:
        try:
            # Try parsing abbreviated month name
            return int(datetime.datetime.strptime(month, "%b").strftime("%m"))
        except ValueError:
            return -1


def parse_hours_minutes(hour_minute: str):
    """Parse hours and minutes from a given string."""
    if hour_minute is None:
        return -1, -1

    # Check if the input matches any of the valid formats
    if not any(re.match(pattern, hour_minute) for pattern in valid_formats):
        return -1, -1

    # Split hours and minutes
    if ":" in hour_minute:
        hours, minutes = hour_minute.split(":")[:2]
    else:
        hours, minutes = hour_minute[:-2], "00"  # Exclude am/pm from hours

    hours = int(hours)
    minutes = int(minutes)

    # Check for am/pm
    is_pm = hour_minute[-2:].lower() == "pm"
    is_am = hour_minute[-2:].lower() == "am"

    # Handle am/pm
    if is_pm and hours != 12:
        hours += 12
    if is_am and hours == 12:
        hours = 0

    # Validate hours and minutes
    if not (0 <= hours < 24) or not (0 <= minutes < 60):
        return -1, -1

    return hours, minutes


def parse_datetime(year, month, day, hour_minute):
    """Parse the date from the given year, month, day, and hour_minute."""

    now = datetime.datetime.now()

    # Set default values based on conditions
    if year is None:
        year = now.year

    if month is None:
        month = now.month if year == now.year else 1
    else:
        month = get_month_number(month)

    if day is None:
        day = now.day if month == now.month and year == now.year else 1

    # Use the parse_hours_minutes function
    hour, minute = parse_hours_minutes(hour_minute)
    if hour is None and minute is None:
        if year is None and month is None and day is None:
            hour, minute = 23, 59
        else:
            hour, minute = 0, 0

    return year, month, day, hour, minute


# ------------ TIMEZONES GROUP COMMANDS ------------
def setup(bot: commands.Bot):
    calendar = bot.create_group(name="calendar", description="Manage your calendar")

    # Send responses based on visibility setting
    async def send_response(ctx, content=None, embed=None, view=None):
        user_id = str(ctx.author.id)
        user_data = bot.user_data_handler.load_user_data(user_id)
        visibility = user_data.get("visibility", "private")

        if visibility == "private":
            await ctx.author.send(content=content, embed=embed, view=view)
            if ctx.guild:  # Check if the command was invoked in a guild
                await ctx.edit(content="I've sent you a private message!")
        else:
            await ctx.edit(content=content, embed=embed, view=view)

    # Command to add an event to the calendar
    @calendar.command(name="add", description="Add an event to the calendar")
    async def addevent(
        ctx: commands.Context,
        title: str,
        year: int = None,
        month: str = None,
        day: int = None,
        hour_minute: str = None,
    ):
        await ctx.defer()
        user_id = str(ctx.author.id)
        user_timezone = bot.user_data_handler.get_user_timezone(user_id)

        if not user_timezone:
            await ctx.edit(
                content="Please set your timezone first using `/timezone set <timezone_name>`."
            )
            return

        # Check if all time parameters are None
        if year is None and month is None and day is None and hour_minute is None:
            await ctx.edit(content="At least one time parameter is required.")
            return

        year, month, day, hour, minute = parse_datetime(year, month, day, hour_minute)

        local_tz = pytz.timezone(user_timezone)
        try:
            local_datetime = local_tz.localize(
                datetime.datetime(year, month, day, hour, minute)
            )
        except (ValueError, OverflowError, TypeError) as error:
            print(f"@{ctx.author.name} {error}")
            await ctx.edit(
                content="The date or time provided is invalid. Please check the values and try again."
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
        await send_response(
            ctx, content=f"**{title}**: <t:{timestamp}:f>, <t:{timestamp}:R>"
        )

    # Command to list events
    @calendar.command(name="list", description="List events")
    async def eventlist(ctx: commands.Context, member: discord.Member = None):
        await ctx.defer()

        user_id = str(member.id) if member else str(ctx.author.id)
        user_data = bot.user_data_handler.load_user_data(user_id)

        # Check visibility if someone other than the owner is trying to view the list
        if (
            member
            and user_data.get("visibility", "private") == "private"
            and ctx.author.id != member.id
        ):
            await ctx.edit(content="This user's calendar is private.")
            return

        if "events" not in user_data or not user_data["events"]:
            await ctx.edit(content="No events found.")
            return

        events = user_data["events"]
        events.sort(key=lambda x: x["time"])

        # Split the list into chunks of 10
        event_chunks = [events[i : i + 10] for i in range(0, len(events), 10)]

        view = views.EventListView(event_chunks, ctx)
        await send_response(ctx, embed=view.create_embed(), view=view)

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
            await send_response(ctx, content=f'Event "**{event_name}**" removed.')
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
            await ctx.send(
                content="All events have been deleted.",
            )
        else:
            await ctx.send(content="Operation cancelled.")

    print("Calendar group loaded")
