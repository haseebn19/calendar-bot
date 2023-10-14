from lib import *
import views


# ------------ HELPER FUNCTIONS ------------
import datetime


def to_int(value: str):
    """Convert the value to an integer if possible."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return value


def get_month_number(month: str):
    """Convert the month string to a number (1 for January, 2 for February, etc.)."""
    month = to_int(month)

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


def parse_hours_minutes(time: str):
    """Parse the hours and minutes from the input string."""
    if not time:
        return None, None

    # Check for am/pm
    time_indicator = time[-2:].lower()

    # Handle "HH:MMam" and "HH:MMpm" formats
    if re.match(r"^(?:[01]?[0-9]|2[0-3]):[0-5][0-9](am|pm)$", time):
        hours, minutes = map(int, time[:-2].split(":"))

    # Handle "HHam" and "HHpm" formats
    elif re.match(r"^(?:[01]?[0-9]|2[0-3])(am|pm)$", time):
        hours = int(time[:-2])
        minutes = 0

    # Handle "HH:MM" format
    elif re.match(r"^(?:[01]?[0-9]|2[0-3]):[0-5][0-9]$", time):
        hours, minutes = map(int, time.split(":"))

    # Handle "HH" format
    elif re.match(r"^(?:[01]?[0-9]|2[0-3])$", time):
        hours = int(time)
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
    day_num = to_int(day)
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


def parse_datetime(user_timezone, year, month, day, time):
    """Parse the date from the given year, month, day, and time."""

    now = datetime.datetime.now()

    # Set default values based on conditions
    year = year or now.year
    month = get_month_number(month) or (now.month if year == now.year else 1)
    day = parse_day(user_timezone, year, month, day) or (
        now.day if month == now.month and year == now.year else 1
    )

    if day == -1:
        return -1, -1, -1, -1, -1

    hour, minute = parse_hours_minutes(time)

    if hour == minute == None:
        hour, minute = (0, 0)

    return year, month, day, hour, minute


# ------------ TIMEZONES GROUP COMMANDS ------------
def setup(bot: commands.Bot):
    calendar = bot.create_group(name="calendar", description="Manage your calendar")

    async def send_response(ctx, content=None, embed=None, view=None):
        """Send responses based on privacy setting"""
        user_id = str(ctx.author.id)
        privacy = bot.user_data_handler.get_key(user_id, "privacy", "private")

        if privacy == "private" and ctx.guild:
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
        time: str = None,
    ):
        """Command to add an event to the calendar"""
        await ctx.defer()
        user_id = str(ctx.author.id)
        user_timezone = bot.user_data_handler.get_key(user_id, "timezone")

        if not user_timezone:
            await ctx.edit(
                content="Please set your timezone first using `/timezone set <timezone_name>`."
            )
            return

        # Check if all time parameters are None
        if year == month == day == time == None:
            await ctx.edit(content="At least one time parameter is required.")
            return

        year, month, day, hour, minute = parse_datetime(
            user_timezone, year, month, day, time
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

        # Create the new event
        new_event = {
            "title": title,
            "timestamp": int(utc_time.timestamp()),  # Store time as Unix timestamp
        }

        # Call the add_event method from UserDataHandler
        bot.user_data_handler.add_event(user_id, new_event)

        timestamp = int(utc_time.timestamp())
        await send_response(
            ctx, content=f"**{title}**: <t:{timestamp}:f>, <t:{timestamp}:R>"
        )

    @calendar.command(name="list", description="List events")
    async def eventlist(ctx: commands.Context, member: discord.Member = None):
        """Command to list events"""
        await ctx.defer()

        user_id = str(member.id) if member else str(ctx.author.id)

        # Get privacy setting
        privacy = bot.user_data_handler.get_key(user_id, "privacy")

        # Check privacy if someone other than the owner is trying to view the list
        if member and privacy == "private" and ctx.author.id != member.id:
            await ctx.edit(content="This user's calendar is private.")
            return

        events = bot.user_data_handler.get_key(user_id, "events")

        if not events:
            await ctx.edit(content="No events found.")
            return
        events.sort(key=lambda x: x["timestamp"])

        # Split the list into chunks of 10
        event_chunks = [events[i : i + 10] for i in range(0, len(events), 10)]

        view = views.EventListView(event_chunks, ctx)
        await send_response(ctx, embed=view.create_embed(), view=view)

    @calendar.command(name="remove", description="Remove an event by its ID")
    async def removeevent(ctx: commands.Context, event_id: int):
        """Command to remove an event by its ID"""
        await ctx.defer()
        user_id = str(ctx.author.id)

        # Call the remove_event method from UserDataHandler
        result_message = bot.user_data_handler.remove_event(user_id, event_id)

        await send_response(ctx, content=result_message)

    @calendar.command(name="wipe", description="Delete all events")
    async def wipe(ctx: commands.Context):
        """Command to delete all events"""
        await ctx.defer()
        user_id = str(ctx.author.id)

        confirm_response = views.Confirm(user_id=ctx.author.id, timeout=15)
        await ctx.edit(
            content="Are you sure you want to delete all events?", view=confirm_response
        )
        await confirm_response.wait()

        if confirm_response.value is None:
            await ctx.send(content="You didn't respond in time, please try again.")
        elif confirm_response.value:
            result_message = bot.user_data_handler.wipe_events(user_id)
            await ctx.send(content=result_message)
        else:
            await ctx.send(content="Operation cancelled.")

    print("Calendar group loaded")
