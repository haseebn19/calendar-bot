# Calendar Bot

[![CI](https://github.com/haseebn19/calendar-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/haseebn19/calendar-bot/actions/workflows/ci.yml)

<img src="docs/logo.svg" alt="Calendar Bot Logo" width="250">

A Discord bot for managing personal events across time zones.

## Features

- **Calendar Management**: Add, list, and remove calendar events
- **Timezone Support**: Timezone selection with autocomplete
- **Privacy Controls**: Private mode (the default) makes responses visible only to you; public mode shows them to the channel
- **Discord Timestamps**: Events display in each viewer's local time using Discord's timestamp formatting

## Prerequisites

- Python 3.11+
- A Discord bot token ([create one here](https://discord.com/developers/applications))

## Installation

```bash
git clone https://github.com/haseebn19/calendar-bot.git
cd calendar-bot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install the package
pip install .
```

## Configuration

Copy the example environment file and add your bot token:

```bash
cp .env.example .env
```

Then edit `.env` and set your `DISCORD_TOKEN`. See `.env.example` for all available options.

## Usage

With the virtual environment activated:

```bash
calendar-bot
```

`python -m calendar_bot.bot` does the same. Events and settings are stored in SQLite at `DATABASE_PATH` (`./data/calendar.db` by default).

### Commands

| Command | Description |
|---------|-------------|
| `/calendar add` | Add an event to your calendar |
| `/calendar list` | List your events |
| `/calendar remove` | Remove an event by ID |
| `/calendar wipe` | Delete all your events |
| `/timezone set` | Set your timezone |
| `/timezone get` | Show your current timezone |
| `/timezone list` | List all available timezones |
| `/settings privacy` | Set your privacy mode (public/private) |
| `/settings view` | View your current settings |
| `/settings wipe` | Delete all your data (events and account) |
| `/help commands` | Show all available commands |
| `/help about` | Learn about the bot |

### Dates and Times

`/calendar add` takes any of `year`, `month`, `day`, and `time`, read in your timezone. Parts you leave out are filled with the next date that matches: `day:15` is the next 15th, `day:Friday time:6pm` is the coming Friday, and `time:9am` is today if it is still before 9am, otherwise tomorrow. A month on its own means the 1st, and the time defaults to midnight. With a `year`, the date is exactly the one given.

### Examples

1. Set your timezone:
   ```
   /timezone set America/New_York
   ```

2. Add an event:
   ```
   /calendar add title:Team Meeting month:January day:15 time:10am
   ```

3. List your events:
   ```
   /calendar list
   ```

## Development

### Setup

```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# Run one test file
pytest tests/test_database.py
```

With coverage:

```bash
pytest --cov --cov-report=html
# Open htmlcov/index.html to view the coverage report
```

### Linting and Type Checking

```bash
ruff check .
ruff format --check .
mypy src
```

`ruff check --fix .` and `ruff format .` apply fixes and formatting.

## Project Structure

```text
calendar-bot/
+-- docs/                    Logo, terms of service, and privacy policy (GitHub Pages)
+-- src/calendar_bot/
|   +-- bot.py               Bot class and entry point
|   +-- config.py            Settings loaded from .env
|   +-- cogs/                Slash command groups: calendar, timezone, settings, help
|   +-- database/            Data models and the SQLite repository
|   +-- utils/               Date and time parsing, and interactive views
+-- tests/                   pytest suite
+-- .env.example             Example configuration
+-- pyproject.toml           Package, Ruff, mypy, and pytest configuration
```

The [terms of service](https://haseebn19.github.io/calendar-bot/terms-of-service) and [privacy policy](https://haseebn19.github.io/calendar-bot/privacy-policy) are published from `docs/`.

## Credits

- [discord.py](https://discordpy.readthedocs.io/) - Discord API wrapper
- [aiosqlite](https://aiosqlite.omnilib.dev/) - Async SQLite
- [pytz](https://pythonhosted.org/pytz/) - Timezone handling

## License

This project is licensed under the [GPL-3.0 License](LICENSE).
