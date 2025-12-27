"""Database models for Calendar Bot."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Self


class PrivacySetting(str, Enum):
    """User privacy setting."""

    PUBLIC = "public"
    PRIVATE = "private"

    def __str__(self) -> str:
        return self.value


@dataclass(slots=True)
class User:
    """Discord user data."""

    discord_id: int
    timezone: str | None = None
    privacy: PrivacySetting = PrivacySetting.PRIVATE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_private(self) -> bool:
        return self.privacy == PrivacySetting.PRIVATE

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        return cls(
            discord_id=row[0],
            timezone=row[1],
            privacy=PrivacySetting(row[2]) if row[2] else PrivacySetting.PRIVATE,
            created_at=datetime.fromisoformat(row[3]) if row[3] else datetime.now(UTC),
            updated_at=datetime.fromisoformat(row[4]) if row[4] else datetime.now(UTC),
        )


@dataclass(slots=True)
class Event:
    """Calendar event."""

    id: int | None
    user_id: int
    title: str
    timestamp: int  # Unix timestamp (UTC)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp, tz=UTC)

    @property
    def discord_timestamp(self) -> str:
        return f"<t:{self.timestamp}:f>"

    @property
    def discord_relative(self) -> str:
        return f"<t:{self.timestamp}:R>"

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        return cls(
            id=row[0],
            user_id=row[1],
            title=row[2],
            timestamp=row[3],
            created_at=datetime.fromisoformat(row[4]) if row[4] else datetime.now(UTC),
        )
