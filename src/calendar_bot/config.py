"""Configuration management for Calendar Bot."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Config:
    """Bot configuration."""

    discord_token: str
    database_path: Path
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> Self:
        """Load configuration from environment variables."""
        load_dotenv(env_path)

        discord_token = os.getenv("DISCORD_TOKEN")
        if not discord_token:
            raise ValueError("DISCORD_TOKEN environment variable is required")

        database_path = Path(os.getenv("DATABASE_PATH", "./data/calendar.db"))
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        return cls(
            discord_token=discord_token,
            database_path=database_path,
            log_level=log_level,
        )


def setup_logging(config: Config) -> logging.Logger:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Reduce discord.py noise
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)

    return logging.getLogger("calendar_bot")
