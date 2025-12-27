"""Tests for configuration module."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from calendar_bot.config import Config, setup_logging


class TestConfig:

    def test_config_creation(self) -> None:
        config = Config(
            discord_token="test_token",
            database_path=Path("./test.db"),
            log_level="DEBUG",
        )

        assert config.discord_token == "test_token"
        assert config.database_path == Path("./test.db")
        assert config.log_level == "DEBUG"

    def test_config_defaults(self) -> None:
        config = Config(
            discord_token="test_token",
            database_path=Path("./test.db"),
        )

        assert config.log_level == "INFO"

    def test_config_immutable(self) -> None:
        config = Config(
            discord_token="test_token",
            database_path=Path("./test.db"),
        )

        with pytest.raises(AttributeError):
            config.discord_token = "new_token"


class TestConfigFromEnv:
    """Tests for Config.from_env that need to mock load_dotenv."""

    def test_from_env_with_all_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Mock load_dotenv to prevent it from loading .env file
        with patch("calendar_bot.config.load_dotenv"):
            monkeypatch.setenv("DISCORD_TOKEN", "my_secret_token")
            monkeypatch.setenv("DATABASE_PATH", "./custom/path.db")
            monkeypatch.setenv("LOG_LEVEL", "debug")

            config = Config.from_env()

        assert config.discord_token == "my_secret_token"
        assert config.database_path == Path("./custom/path.db")
        assert config.log_level == "DEBUG"

    def test_from_env_missing_token_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with patch("calendar_bot.config.load_dotenv"):
            monkeypatch.delenv("DISCORD_TOKEN", raising=False)
            monkeypatch.delenv("DATABASE_PATH", raising=False)
            monkeypatch.delenv("LOG_LEVEL", raising=False)

            with pytest.raises(ValueError, match="DISCORD_TOKEN"):
                Config.from_env()

    def test_from_env_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with patch("calendar_bot.config.load_dotenv"):
            monkeypatch.setenv("DISCORD_TOKEN", "token")
            monkeypatch.delenv("DATABASE_PATH", raising=False)
            monkeypatch.delenv("LOG_LEVEL", raising=False)

            config = Config.from_env()

        assert config.database_path == Path("./data/calendar.db")
        assert config.log_level == "INFO"

    def test_from_env_lowercase_log_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with patch("calendar_bot.config.load_dotenv"):
            monkeypatch.setenv("DISCORD_TOKEN", "token")
            monkeypatch.setenv("LOG_LEVEL", "warning")

            config = Config.from_env()

        assert config.log_level == "WARNING"


class TestSetupLogging:

    def test_setup_logging_returns_logger(self) -> None:
        config = Config(
            discord_token="test",
            database_path=Path("./test.db"),
            log_level="INFO",
        )

        logger = setup_logging(config)

        assert isinstance(logger, logging.Logger)
        assert logger.name == "calendar_bot"

    def test_discord_loggers_reduced(self) -> None:
        config = Config(
            discord_token="test",
            database_path=Path("./test.db"),
        )

        setup_logging(config)

        discord_logger = logging.getLogger("discord")
        http_logger = logging.getLogger("discord.http")

        assert discord_logger.level == logging.WARNING
        assert http_logger.level == logging.WARNING

