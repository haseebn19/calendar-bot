from lib import *
import views


# ------------ HELPER FUNCTIONS ------------
import datetime


def parse_integer(value: str):
    """Parse a string to integer."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return value


def get_month_number(month: str):
    """Get the month number from the input month (Aug = August = 8)."""
    month = parse_integer(month)

    if month is None or isinstance(month, int):
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
    if not hour_minute:
        return None, None

    # Check for am/pm
    time_indicator = hour_minute[-2:].lower()

    # Handle "HH:MMam" and "HH:MMpm" formats
    if re.match(r"^(?:[01]?[0-9]|2[0-3]):[0-5][0-9](am|pm)$", hour_minute):
        hours, minutes = map(int, hour_minute[:-2].split(":"))

    # Handle "HHam" and "HHpm" formats
    elif re.match(r"^(?:[01]?[0-9]|2[0-3])(am|pm)$", hour_minute):
        hours = int(hour_minute[:-2])
        minutes = 0

    # Handle "HH:MM" format
    elif re.match(r"^(?:[01]?[0-9]|2[0-3]):[0-5][0-9]$", hour_minute):
        hours, minutes = map(int, hour_minute.split(":"))

    # Handle "HH" format
    elif re.match(r"^(?:[01]?[0-9]|2[0-3])$", hour_minute):
        hours = int(hour_minute)
        minutes = 0

    else:
        return -1, -1

    # Validate time indicator and hours:
    if hours > 12 and time_indicator in ["am", "pm"]:
        return -1, -1

    # Adjust hours for am/pm
    if time_indicator == "pm" and hours != 12:
        hours += 12
    elif time_indicator == "am" and hours == 12:
        hours = 0

    return hours, minutes


def get_day_number(day: str):
    """Convert the day string to a number (0 for Monday, 1 for Tuesday, etc.)."""
    day = day.lower()
    for day_number, day_name in enumerate(
        ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    ):
        if day_name.startswith(day):
            return day_number
    return -1  # Invalid day string


def parse_day(user_timezone, year, month, day):
    """Get the day number from the input day (Monday = Mon = DD)."""

    # Check if the day is an integer or None
    day_num = parse_integer(day)
    if isinstance(day_num, int) or day_num is None:
        return day_num

    # Get the target day number
    target_day_num = get_day_number(day)
    if target_day_num == -1:
        return -1  # Invalid day string

    # Get the current day of the week
    now = datetime.datetime.now(pytz.timezone(user_timezone))
    current_day_num = now.weekday()

    # Calculate the difference to the next occurrence
    days_difference = (target_day_num - current_day_num + 7) % 7
    if days_difference == 0:
        days_difference = 7  # If the day is today, get the next week's occurrence

    # Calculate the next occurrence date
    next_occurrence = now + datetime.timedelta(days=days_difference)

    # Check if the next occurrence goes past the provided month
    if next_occurrence.month != month or next_occurrence.year != year:
        return -1

    return next_occurrence.day


def parse_datetime(user_timezone, year, month, day, hour_minute):
    """Parse the date from the given year, month, day, and hour_minute."""

    now = datetime.datetime.now()

    # Set default values based on conditions
    year = year or now.year
    month = get_month_number(month) or (now.month if year == now.year else 1)
    day = parse_day(user_timezone, year, month, day) or (
        now.day if month == now.month and year == now.year else 1
    )

    if day == -1:
        return -1, -1, -1, -1, -1

    
    hour, minute = parse_hours_minutes(hour_minute)

    if hour == minute == None:
        hour, minute = (0, 0)

    return year, month, day, hour, minute


# ------------ TIMEZONES GROUP COMMANDS ------------
def setup(bot: commands.Bot):
    calendar = bot.create_group(name="calendar", description="Manage your calendar")

    async def send_response(ctx, content=None, embed=None, view=None):
        """Send responses based on visibility setting"""
        user_id = str(ctx.author.id)
        user_data = bot.user_data_handler.load_user_data(user_id)
        visibility = user_data.get("visibility", "private")

        if visibility == "private" and ctx.guild:
            await ctx.author.send(content=content, embed=embed, view=view)
            await ctx.edit(content="I've sent you a private message!")
        else:
            await ctx.edit(content=content, embed=embed, view=view)

    @calendar.command(name="add", description="Add an event to the calendar")
    async def addevent(
        ctx: commands.Context,
        title: str,
        year: int = None,
        month: str = None,
        day: str = None,
        hour_minute: str = None,
    ):
        """Command to add an event to the calendar"""
        await ctx.defer()
        user_id = str(ctx.author.id)
        user_timezone = bot.user_data_handler.get_user_timezone(user_id)

        if not user_timezone:
            await ctx.edit(
                content="Please set your timezone first using `/timezone set <timezone_name>`."
            )
            return

        # Check if all time parameters are None
        if year == month == day == hour_minute == None:
            await ctx.edit(content="At least one time parameter is required.")
            return

        year, month, day, hour, minute = parse_datetime(
            user_timezone, year, month, day, hour_minute
        )
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

    @calendar.command(name="list", description="List events")
    async def eventlist(ctx: commands.Context, member: discord.Member = None):
        """Command to list events"""
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

    @calendar.command(name="remove", description="Remove an event by its ID")
    async def removeevent(ctx: commands.Context, event_id: int):
        """Command to remove an event by its ID"""
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

    @calendar.command(name="wipe", description="Delete all events")
    async def wipe(ctx: commands.Context):
        """Command to delete all events"""
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
