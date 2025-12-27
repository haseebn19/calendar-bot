# Calendar Bot

[![CI](https://github.com/haseebn19/calendar-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/haseebn19/calendar-bot/actions/workflows/ci.yml)

<img src="docs/logo.svg" alt="Calendar Bot Logo" width="250">

A Discord bot for managing personal calendar events with full timezone support.

## Features

- **Calendar Management** - Add, list, and remove calendar events
- **Timezone Support** - Full timezone support with autocomplete
- **Privacy Controls** - Choose between public and private modes
- **Ephemeral Responses** - Private mode makes all responses only visible to you
- **Discord Timestamps** - Events display with Discord's native timestamp formatting

## Prerequisites

- Python 3.11 or higher
- A Discord Bot Token ([Create one here](https://discord.com/developers/applications))

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
cp env.example .env
```

Then edit `.env` and set your `DISCORD_TOKEN`. See `env.example` for all available options.

## Usage

```bash
# Make sure virtual environment is activated
python -m calendar_bot.bot
```

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
| `/timestamp` | Convert date/time to Discord timestamp format |
| `/help commands` | Show all available commands |
| `/help about` | Learn about the bot |

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
# Clone and enter directory
git clone https://github.com/haseebn19/calendar-bot.git
cd calendar-bot

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_database.py
```

With coverage:

```bash
pytest --cov=src/calendar_bot --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Linting

```bash
# Run linter
ruff check src tests

# Run linter with auto-fix
ruff check --fix src tests

# Format code
ruff format src tests
```

## Project Structure

```
calendar-bot/
├── docs/
│   └── logo.png
├── src/calendar_bot/
│   ├── bot.py
│   ├── config.py
│   ├── cogs/
│   │   ├── base.py
│   │   ├── calendar.py
│   │   ├── help.py
│   │   ├── settings.py
│   │   ├── timezone.py
│   │   └── utility.py
│   ├── database/
│   │   ├── models.py
│   │   └── repository.py
│   └── utils/
│       ├── datetime_parser.py
│       └── views.py
├── tests/
├── pyproject.toml
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Credits

- [discord.py](https://discordpy.readthedocs.io/) - Discord API wrapper
- [aiosqlite](https://aiosqlite.omnilib.dev/) - Async SQLite
- [pytz](https://pythonhosted.org/pytz/) - Timezone handling

## License

This project is licensed under the [GPL-3.0 License](LICENSE).
