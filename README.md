# Calendar Bot

The Calendar Bot is a personal project designed to enhance event management and organization among Discord server members. By allowing users to manage their events and timezones directly within Discord, it simplifies the process of checking availability and planning events. Whether it's for appointments, meetings, or anything else, the Calendar Bot ensures that everyone is on the same page. Not to be confused with discord's event system, this is for the organization of personal events

## Features

- **Personalized Timezone Management**: Users can set their own timezone, ensuring that events are set in their local time.
- **Event Management**: Users can add, list, remove, and wipe events from their personal calendar.
- **Event Views**: Events are displayed in a paginated manner, making it easy to navigate through large lists of events.
- **Timezone Views**: Available timezones can be listed and viewed in a paginated manner.

## Prerequisites

- Python 3.11
- `py-cord` library
- `dotenv` for environment variable management
- Other dependencies as listed in the `lib` module.

## Installation

1. Clone the repository:
   ```powershell
   git clone https://github.com/haseebn19/calendar-bot.git
   ```

2. Navigate to the project directory:
   ```powershell
   cd calendar-bot
   ```

3. Install the required dependencies using `pip3.11`:
   ```powershell
   pip3.11 install -r requirements.txt
   ```

4. Set up your `.env` file with the necessary environment variables:
   ```env
   ENCRYPTION_KEY=<your-encryption-key>
   DISCORD_TOKEN=<your-discord-bot-token>
   ```

5. Run the bot using Python 3.11:
   ```powershell
   py -3.11 main.py
   ```

## Commands

- **Timezone Commands**:
  - `/timezone set <timezone_name>`: Set your timezone.
  - `/timezone list`: List all available timezones.

- **Calendar Commands**:
  - `/calendar add <title> <year> <month> <day> <hour> <minute>`: Add an event to your calendar.
  - `/calendar list`: List all your events.
  - `/calendar remove <event_id>`: Remove an event by its ID.
  - `/calendar wipe`: Delete all your events.

## Contributing

If you'd like to contribute to the development of my Calendar Bot or have suggestions for improvements, please fork the repository and submit a pull request.

## License

This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

