"""Tests for configuration module."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from calendar_bot.config import Config, setup_logging

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> Iterator[pytest.MonkeyPatch]:
    """The environment, with no .env file loaded and none of the bot's settings set."""
    for name in ("DISCORD_TOKEN", "DATABASE_PATH", "LOG_LEVEL"):
        monkeypatch.delenv(name, raising=False)
    with patch("calendar_bot.config.load_dotenv"):
        yield monkeypatch


def test_reads_every_setting(env: pytest.MonkeyPatch) -> None:
    env.setenv("DISCORD_TOKEN", "my_secret_token")
    env.setenv("DATABASE_PATH", "./custom/path.db")
    env.setenv("LOG_LEVEL", "debug")

    assert Config.from_env() == Config("my_secret_token", Path("./custom/path.db"), "DEBUG")


def test_defaults(env: pytest.MonkeyPatch) -> None:
    env.setenv("DISCORD_TOKEN", "token")
    assert Config.from_env() == Config("token", Path("./data/calendar.db"), "INFO")


@pytest.mark.usefixtures("env")
def test_token_is_required() -> None:
    with pytest.raises(ValueError, match="DISCORD_TOKEN"):
        Config.from_env()


def test_log_level_must_be_a_logging_level(env: pytest.MonkeyPatch) -> None:
    env.setenv("DISCORD_TOKEN", "token")
    env.setenv("LOG_LEVEL", "verbose")
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        Config.from_env()


def test_setup_logging_quiets_discord() -> None:
    setup_logging(Config("token", Path("./test.db")))
    assert logging.getLogger("discord").level == logging.WARNING
    assert logging.getLogger("discord.http").getEffectiveLevel() == logging.WARNING
