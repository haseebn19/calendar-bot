# ------------ LIBRARIES ------asdg-----+
from lib import *
from views import *
from datahandler import *

# ------------ ENVIRONMENT VARIABLES -----sadgsd-----
# Load environment variables from .env file
dotenv.load_dotenv()


# Function to check and load required environment variables
def load_env_vars(var_list: list):
    env_vars = []
    for var in var_list:
        env_var = os.getenv(var)
        if env_var is None:
            raise EnvironmentError(f"{var} is not set in the environment variables.")
        env_vars.append(env_var)
    return env_vars


# Load encryption key and Discord token from environment variables
ENCRYPTION_KEY, TOKEN = load_env_vars(["ENCRYPTION_KEY", "DISCORD_TOKEN"])

# ------------ BOT VARIABLES ------------d
intents = discord.Intents.default()
bot = commands.Bot(intents=intents)
user_data_handler = UserDataHandler(ENCRYPTION_KEY, events_folder="events")


# Event triggered when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ------------ TIMEZONES GROUP COMMANDS --------
timezone = bot.create_group(name="timezone")


# Command to set user's timezone
@timezone.command(name="set", description="Set your timezone")
async def set_timezone(ctx: commands.Context, timezone_name: str):
    await ctx.defer()
    if timezone_name not in pytz.all_timezones_set:
        await ctx.edit(
            content="Invalid timezone. Please use `/timezone list` to see available timezones."
        )
        return
    user_data_handler.set_user_timezone(str(ctx.author.id), timezone_name)
    await ctx.edit(content=f"Your timezone has been set to {timezone_name}.")


# Command to list all available timezones
@timezone.command(name="list", description="List all available timezones")
async def list_timezones(ctx: commands.Context):
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
    view = TimezoneView(timezone_chunks, ctx)
    await ctx.edit(embed=view.create_embed(), view=view)


# ------------ CALENDAR GROUP COMMANDS 
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
    user_timezone = user_data_handler.get_user_timezone(user_id)
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

    user_data = user_data_handler.load_user_data(user_id)
    if "events" not in user_data:
        user_data["events"] = []

    event_id = len(user_data["events"])
    new_event = {
        "id": event_id,
        "name": title,
        "time": int(utc_time.timestamp()),  # Store time as Unix timestamp
    }
    user_data["events"].append(new_event)
    user_data_handler.save_user_data(user_id, user_data)

    timestamp = int(utc_time.timestamp())
    await ctx.edit(content=f"**{title}**: <t:{timestamp}:f>, <t:{timestamp}:R>")


# Command to list events
@calendar.command(name="list", description="List events")
async def eventlist(ctx: commands.Context, member: discord.Member = None):
    await ctx.defer()
    user_id = str(member.id) if member else str(ctx.author.id)
    user_data = user_data_handler.load_user_data(user_id)

    if "events" not in user_data or not user_data["events"]:
        await ctx.edit(content="No events found.")
        return

    events = user_data["events"]
    events.sort(key=lambda x: x["time"])

    # Split the list into chunks of 10
    event_chunks = [events[i : i + 10] for i in range(0, len(events), 10)]

    view = EventListView(event_chunks, ctx)
    await ctx.edit(embed=view.create_embed(), view=view)


# Command to remove an event by its ID
@calendar.command(name="remove", description="Remove an event by its ID")
async def removeevent(ctx: commands.Context, event_id: int):
    await ctx.defer()
    user_id = str(ctx.author.id)
    user_data = user_data_handler.load_user_data(user_id)

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
        user_data_handler.save_user_data(user_id, user_data)
        await ctx.edit(content=f'Event "{event_name}" removed.')
    else:
        await ctx.edit(content="Event not found.")


# Command to delete all events
@calendar.command(name="wipe", description="Delete all events")
async def wipe(ctx: commands.Context):
    await ctx.defer()
    user_id = str(ctx.author.id)
    user_data = user_data_handler.load_user_data(user_id)

    if "events" not in user_data or not user_data["events"]:
        await ctx.edit(content="No events found.")
        return

    confirm_response = Confirm(user_id=ctx.author.id, timeout=15)
    await ctx.edit(
        content="Are you sure you want to delete all events?", view=confirm_response
    )
    await confirm_response.wait()

    if confirm_response.value is None:
        await ctx.send(content="You didn't respond in time, please try again.")
    elif confirm_response.value:
        user_data["events"] = []
        user_data_handler.save_user_data(user_id, user_data)
        await ctx.send(content="All events have been deleted.")
    else:
        await ctx.send(content="Operation cancelled.")


# ------------ START BOT 
bot.run(TOKEN)
