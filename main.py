# ------------ LIBRARIES ------------
from lib import *
import datahandler

# ------------ ENVIRONMENT VARIABLES ------------
# Load environment variables from .env file
dotenv.load_dotenv()

# Load encryption key and Discord token from environment variables
TOKEN = os.getenv("DISCORD_TOKEN")

# ------------ BOT VARIABLES ------------
intents = discord.Intents.default()
bot = commands.Bot(intents=intents)
bot.user_data_handler = datahandler.UserDataHandler()


# Event triggered when the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ------------ TIMEZONES GROUP COMMANDS ------------
bot.load_extension("timezone_group")

# ------------ CALENDAR GROUP COMMANDS ------------
bot.load_extension("calendar_group")

# ------------ SETTINGS GROUP COMMANDS ------------
bot.load_extension("settings_group")

# ------------ HELP GROUP COMMANDS ------------
bot.load_extension("help_group")

# ------------ START BOT ------------
bot.run(TOKEN)
