"""Tests for the calendar_bot.bot entry point."""

from pathlib import Path
from unittest.mock import patch

import discord
import pytest

from calendar_bot import bot


def test_main_reports_a_configuration_error(capsys: pytest.CaptureFixture[str]) -> None:
    error = ValueError("DISCORD_TOKEN environment variable is required")
    with (
        patch.object(bot.Config, "from_env", side_effect=error),
        pytest.raises(SystemExit) as exit_info,
    ):
        bot.main()

    assert exit_info.value.code == 1
    assert "Configuration error: DISCORD_TOKEN" in capsys.readouterr().err


def test_main_explains_a_rejected_token(caplog: pytest.LogCaptureFixture) -> None:
    config = bot.Config(discord_token="not-a-token", database_path=Path("calendar.db"))
    with (
        patch.object(bot.Config, "from_env", return_value=config),
        patch.object(bot, "setup_logging"),
        patch.object(bot, "run_bot", side_effect=discord.LoginFailure("Improper token")),
        pytest.raises(SystemExit) as exit_info,
    ):
        bot.main()

    assert exit_info.value.code == 1
    assert "Check DISCORD_TOKEN" in caplog.text
