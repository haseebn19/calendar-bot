"""Database models for Calendar Bot."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from collections.abc import Sequence


class PrivacySetting(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"


@dataclass(slots=True)
class User:
    """A user's settings. Users who have not chosen a privacy mode are private."""

    discord_id: int
    timezone: str | None = None
    privacy: PrivacySetting = PrivacySetting.PRIVATE

    @property
    def is_private(self) -> bool:
        return self.privacy == PrivacySetting.PRIVATE

    @classmethod
    def from_row(cls, row: Sequence[Any]) -> Self:
        discord_id, timezone, privacy = row
        return cls(discord_id=discord_id, timezone=timezone, privacy=PrivacySetting(privacy))


@dataclass(slots=True)
class Event:
    id: int | None
    user_id: int
    title: str
    timestamp: int  # Unix timestamp (UTC)

    @property
    def discord_timestamp(self) -> str:
        """Discord markup that shows the date and time in each viewer's own timezone."""
        return f"<t:{self.timestamp}:f>"

    @property
    def discord_relative(self) -> str:
        """Discord markup that shows how long until, or since, the event."""
        return f"<t:{self.timestamp}:R>"

    @classmethod
    def from_row(cls, row: Sequence[Any]) -> Self:
        event_id, user_id, title, timestamp = row
        return cls(id=event_id, user_id=user_id, title=title, timestamp=timestamp)
