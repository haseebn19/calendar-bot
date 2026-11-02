"""Date and time parsing utilities."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import MAXYEAR, MINYEAR, date, datetime, timedelta
from itertools import islice
from typing import TYPE_CHECKING

import pytz

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytz.tzinfo import BaseTzInfo

DAYS_OF_WEEK = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

TIME_PATTERNS = {
    "12h_with_minutes": re.compile(r"^([01]?[0-9]):([0-5][0-9])(am|pm)$", re.IGNORECASE),
    "12h_no_minutes": re.compile(r"^([01]?[0-9])(am|pm)$", re.IGNORECASE),
    "24h_with_minutes": re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$"),
    "24h_no_minutes": re.compile(r"^([01]?[0-9]|2[0-3])$"),
}

# Month names must be at least this long to be recognized ("Sep", "Sept", "September")
MIN_MONTH_PREFIX = 3

# February 29 can be up to eight years away (leap years skip 2100, 2200, and 2300)
MAX_MONTHS_AHEAD = 12 * 8


@dataclass(frozen=True, slots=True)
class ParsedDateTime:
    """Result of parsing a datetime."""

    year: int
    month: int
    day: int
    hour: int
    minute: int
    is_valid: bool = True
    error_message: str | None = None

    @classmethod
    def invalid(cls, message: str) -> ParsedDateTime:
        return cls(0, 0, 0, 0, 0, is_valid=False, error_message=message)


def days_in_month(year: int, month: int) -> int:
    """Get the number of days in a given month."""
    return calendar.monthrange(year, month)[1]


def _months_from(year: int, month: int) -> Iterator[tuple[int, int]]:
    """Yield (year, month) pairs starting at the given month."""
    while True:
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


class DateTimeParser:
    """Parser for date and time strings with timezone support."""

    def __init__(self, timezone_str: str) -> None:
        self.timezone: BaseTzInfo = pytz.timezone(timezone_str)

    @property
    def now(self) -> datetime:
        return datetime.now(self.timezone)

    def parse_month(self, month: str | int | None) -> int | None:
        """Parse a month number, name, or abbreviation. Returns None if invalid."""
        if month is None:
            return None

        if isinstance(month, int):
            return month if 1 <= month <= 12 else None

        text = month.strip().lower()
        if text.isdigit():
            number = int(text)
            return number if 1 <= number <= 12 else None

        if len(text) < MIN_MONTH_PREFIX:
            return None
        for number in range(1, 13):
            if calendar.month_name[number].lower().startswith(text):
                return number
        return None

    def parse_time(self, time_str: str | None) -> tuple[int | None, int | None]:
        """Parse time string. Returns (hour, minute), (None, None) if empty, (-1, -1) if invalid."""
        if not time_str:
            return None, None

        time_str = time_str.strip().lower()

        if match := TIME_PATTERNS["12h_with_minutes"].match(time_str):
            return self._adjust_12h(int(match.group(1)), int(match.group(2)), match.group(3))

        if match := TIME_PATTERNS["12h_no_minutes"].match(time_str):
            return self._adjust_12h(int(match.group(1)), 0, match.group(2))

        if match := TIME_PATTERNS["24h_with_minutes"].match(time_str):
            return int(match.group(1)), int(match.group(2))

        if match := TIME_PATTERNS["24h_no_minutes"].match(time_str):
            return int(match.group(1)), 0

        return -1, -1

    @staticmethod
    def _adjust_12h(hours: int, minutes: int, period: str) -> tuple[int, int]:
        """Convert a 12-hour time to 24-hour. Hours must be 1 to 12."""
        if not 1 <= hours <= 12:
            return -1, -1

        if period == "pm" and hours != 12:
            hours += 12
        elif period == "am" and hours == 12:
            hours = 0

        return hours, minutes

    def parse_day_name(self, day_name: str) -> int | None:
        """Get the weekday number (Monday is 0) for a day name or unambiguous prefix."""
        day_name = day_name.strip().lower()
        if not day_name:
            return None

        matches = [dow for name, dow in DAYS_OF_WEEK.items() if name.startswith(day_name)]
        return matches[0] if len(matches) == 1 else None

    def parse_day(self, day: str | int | None) -> tuple[int | None, bool]:
        """Parse day input. Returns (day_number, is_day_name).

        Returns (None, False) if empty and (-1, False) if invalid. For a day name, day_number is
        the weekday (Monday is 0).
        """
        if day is None:
            return None, False

        if isinstance(day, int):
            return (day, False) if 1 <= day <= 31 else (-1, False)

        try:
            day_num = int(day)
            return (day_num, False) if 1 <= day_num <= 31 else (-1, False)
        except ValueError:
            pass

        dow = self.parse_day_name(day)
        if dow is not None:
            return dow, True

        return -1, False

    def parse(
        self,
        year: int | None = None,
        month: str | int | None = None,
        day: str | int | None = None,
        time: str | None = None,
    ) -> ParsedDateTime:
        """Parse date and time parts into the date they describe.

        With a year, the date is exactly the one given: the month and day default to January
        and the 1st. Without a year, the result is the next date and time that matches every
        part given, so "the 15th" is the next 15th and "10am" is today or tomorrow. A month on
        its own means the 1st of that month, and a day name means the next such weekday. The
        time defaults to midnight.
        """
        hour, minute = self.parse_time(time)
        if hour == -1:
            return ParsedDateTime.invalid(
                f"Invalid time: '{time}'. Use formats like '10am', '14:30', or '10:30pm'."
            )
        if hour is None or minute is None:
            hour, minute = 0, 0

        day_number, is_day_name = self.parse_day(day)
        if day_number == -1:
            return ParsedDateTime.invalid(
                f"Invalid day: '{day}'. Use day number (1-31) or day name (e.g., 'Monday')."
            )

        if year is not None and not MINYEAR <= year <= MAXYEAR:
            return ParsedDateTime.invalid(
                f"Invalid year: {year}. Use a year from {MINYEAR} to {MAXYEAR}."
            )

        month_number = None
        if month is not None:
            month_number = self.parse_month(month)
            if month_number is None:
                return ParsedDateTime.invalid(
                    f"Invalid month: '{month}'. Use month name or number (1-12)."
                )

        if is_day_name and day_number is not None:
            # A day name picks the next such weekday, so any year or month given is not used
            found = self._next_weekday(day_number, hour, minute)
        elif year is not None:
            found_month = month_number or 1
            found_day = day_number or 1
            if found_day > days_in_month(year, found_month):
                return ParsedDateTime.invalid(
                    f"Invalid date: {calendar.month_name[found_month]} {year} "
                    f"doesn't have {found_day} days."
                )
            found = date(year, found_month, found_day)
        elif month_number is not None:
            found_day = day_number or 1
            # February 29 exists in leap years, so only reject days no year has
            if found_day > days_in_month(2000, month_number):
                return ParsedDateTime.invalid(
                    f"Invalid date: {calendar.month_name[month_number]} "
                    f"doesn't have {found_day} days."
                )
            found = self._next_date(month_number, found_day, hour, minute)
        elif day_number is not None:
            found = self._next_date(None, day_number, hour, minute)
        else:
            found = self._next_day_at(self.now.date(), hour, minute)

        return ParsedDateTime(found.year, found.month, found.day, hour, minute)

    def _is_ahead(self, day: date, hour: int, minute: int) -> bool:
        """Return True if the given day and time are still to come in this timezone."""
        local: datetime = self.timezone.localize(
            datetime(day.year, day.month, day.day, hour, minute)
        )
        return local > self.now

    def _next_day_at(self, start: date, hour: int, minute: int, step: int = 1) -> date:
        """Return `start` if the time is still to come that day, otherwise `step` days later."""
        return start if self._is_ahead(start, hour, minute) else start + timedelta(days=step)

    def _next_weekday(self, weekday: int, hour: int, minute: int) -> date:
        """Return the next day with this weekday (Monday is 0) whose time is still to come."""
        today = self.now.date()
        candidate = today + timedelta(days=(weekday - today.weekday()) % 7)
        return self._next_day_at(candidate, hour, minute, step=7)

    def _next_date(self, month: int | None, day: int, hour: int, minute: int) -> date:
        """Return the next date with this day (and month, if given) whose time is still to come."""
        now = self.now
        months = islice(_months_from(now.year, now.month), MAX_MONTHS_AHEAD + 1)
        for year, candidate_month in months:
            if month is not None and candidate_month != month:
                continue
            if day > days_in_month(year, candidate_month):
                continue
            candidate = date(year, candidate_month, day)
            if self._is_ahead(candidate, hour, minute):
                return candidate
        # parse() only asks for dates that exist, so this is not reached
        raise ValueError(f"No upcoming date has day {day} in month {month}")

    def to_utc_timestamp(self, parsed: ParsedDateTime) -> int | None:
        """Convert parsed datetime to UTC Unix timestamp."""
        if not parsed.is_valid:
            return None

        try:
            local_dt = self.timezone.localize(
                datetime(
                    parsed.year,
                    parsed.month,
                    parsed.day,
                    parsed.hour,
                    parsed.minute,
                )
            )
            utc_dt = local_dt.astimezone(pytz.UTC)
            return int(utc_dt.timestamp())
        except (ValueError, OverflowError):
            return None
