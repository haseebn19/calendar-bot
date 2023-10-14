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


# ------------ TIMEZONE GROUP COMMANDS ------------
bot.load_extension("group_timezone")

# ------------ CALENDAR GROUP COMMANDS ------------
bot.load_extension("group_calendar")

# ------------ SETTINGS GROUP COMMANDS ------------
bot.load_extension("group_settings")

# ------------ HELP GROUP COMMANDS ------------
bot.load_extension("group_help")

# ------------ START BOT ------------
bot.run(TOKEN)
