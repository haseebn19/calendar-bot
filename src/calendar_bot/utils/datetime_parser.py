"""Date and time parsing utilities."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytz

if TYPE_CHECKING:
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
    "12h_with_minutes": re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])(am|pm)$", re.IGNORECASE),
    "12h_no_minutes": re.compile(r"^([01]?[0-9]|2[0-3])(am|pm)$", re.IGNORECASE),
    "24h_with_minutes": re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$"),
    "24h_no_minutes": re.compile(r"^([01]?[0-9]|2[0-3])$"),
}


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


class DateTimeParser:
    """Parser for date and time strings with timezone support."""

    def __init__(self, timezone_str: str) -> None:
        self.timezone: BaseTzInfo = pytz.timezone(timezone_str)

    @property
    def now(self) -> datetime:
        return datetime.now(self.timezone)

    def parse_month(self, month: str | int | None) -> int | None:
        if month is None:
            return None

        if isinstance(month, int):
            return month if 1 <= month <= 12 else None

        try:
            month_num = int(month)
            return month_num if 1 <= month_num <= 12 else None
        except ValueError:
            pass

        try:
            return datetime.strptime(month, "%B").month
        except ValueError:
            pass

        try:
            return datetime.strptime(month, "%b").month
        except ValueError:
            return None

    def parse_time(self, time_str: str | None) -> tuple[int | None, int | None]:
        """Parse time string. Returns (hour, minute), (None, None) if empty, (-1, -1) if invalid."""
        if not time_str:
            return None, None

        time_str = time_str.strip().lower()

        if match := TIME_PATTERNS["12h_with_minutes"].match(time_str):
            hours = int(match.group(1))
            minutes = int(match.group(2))
            period = match.group(3).lower()
            return self._adjust_12h(hours, minutes, period)

        if match := TIME_PATTERNS["12h_no_minutes"].match(time_str):
            hours = int(match.group(1))
            period = match.group(2).lower()
            return self._adjust_12h(hours, 0, period)

        if match := TIME_PATTERNS["24h_with_minutes"].match(time_str):
            return int(match.group(1)), int(match.group(2))

        if match := TIME_PATTERNS["24h_no_minutes"].match(time_str):
            return int(match.group(1)), 0

        return -1, -1

    @staticmethod
    def _adjust_12h(hours: int, minutes: int, period: str) -> tuple[int, int]:
        if hours > 12:
            return -1, -1

        if period == "pm" and hours != 12:
            hours += 12
        elif period == "am" and hours == 12:
            hours = 0

        return hours, minutes

    def parse_day_name(self, day_name: str) -> int | None:
        """Get day of week number for a day name. Returns None if invalid."""
        day_name = day_name.lower()

        for name, dow in DAYS_OF_WEEK.items():
            if name.startswith(day_name):
                return dow

        return None

    def get_next_weekday(self, target_dow: int) -> datetime:
        """Get the next occurrence of a weekday."""
        now = self.now
        current_dow = now.weekday()
        days_ahead = (target_dow - current_dow + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        return now + timedelta(days=days_ahead)

    def parse_day(self, day: str | int | None) -> tuple[int | None, bool]:
        """Parse day input. Returns (day_number, is_day_name). Returns (None, False) if empty, (-1, False) if invalid."""
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

    def _find_next_month_with_day(
        self, day: int, start_year: int, start_month: int
    ) -> tuple[int, int]:
        """Find the next month that has the given day number."""
        year, month = start_year, start_month
        for _ in range(12):
            if day <= days_in_month(year, month):
                return year, month
            month += 1
            if month > 12:
                month = 1
                year += 1
        return year, month

    def parse(
        self,
        year: int | None = None,
        month: str | int | None = None,
        day: str | int | None = None,
        time: str | None = None,
    ) -> ParsedDateTime:
        """Parse date/time components with next-occurrence defaults."""
        now = self.now

        # Parse time first
        hours, minutes = self.parse_time(time)
        if hours == -1 and minutes == -1:
            return ParsedDateTime.invalid(
                f"Invalid time: '{time}'. Use formats like '10am', '14:30', or '10:30pm'."
            )
        if hours is None:
            hours, minutes = 0, 0

        # Parse day (could be number or day name)
        parsed_day, is_day_name = self.parse_day(day)
        if parsed_day == -1:
            return ParsedDateTime.invalid(
                f"Invalid day: '{day}'. Use day number (1-31) or day name (e.g., 'Monday')."
            )

        # Handle day name (e.g., "Monday") - ignores month/year, finds next occurrence
        if is_day_name:
            next_date = self.get_next_weekday(parsed_day)
            return ParsedDateTime(
                year=next_date.year,
                month=next_date.month,
                day=next_date.day,
                hour=hours,
                minute=minutes or 0,
            )

        # Parse month
        parsed_month: int | None = None
        month_was_specified = month is not None
        if month is not None:
            parsed_month = self.parse_month(month)
            if parsed_month is None:
                return ParsedDateTime.invalid(
                    f"Invalid month: '{month}'. Use month name or number (1-12)."
                )

        # Parse year
        year_was_specified = year is not None
        parsed_year = year if year is not None else now.year

        # Determine final date based on what was specified
        if month_was_specified and parsed_day is not None:
            # Both month and day specified - validate the combination
            if parsed_day > days_in_month(parsed_year, parsed_month):
                month_name = calendar.month_name[parsed_month]
                return ParsedDateTime.invalid(
                    f"Invalid date: {month_name} doesn't have {parsed_day} days."
                )
            # Check if date is in the past, bump year if needed
            if not year_was_specified:
                target = datetime(parsed_year, parsed_month, parsed_day, hours, minutes or 0)
                target = self.timezone.localize(target)
                if target <= now:
                    parsed_year += 1
                    # Re-validate for leap year edge case (Feb 29)
                    if parsed_day > days_in_month(parsed_year, parsed_month):
                        month_name = calendar.month_name[parsed_month]
                        return ParsedDateTime.invalid(
                            f"Invalid date: {month_name} {parsed_year} doesn't have {parsed_day} days."
                        )

        elif month_was_specified and parsed_day is None:
            # Only month specified - use 1st of that month, next occurrence
            parsed_day = 1
            if not year_was_specified and parsed_month <= now.month:
                parsed_year += 1

        elif not month_was_specified and parsed_day is not None:
            # Only day specified - find next month with that day
            # Start from current month if day hasn't passed, otherwise next month
            start_month = now.month
            start_year = now.year
            if parsed_day <= now.day:
                start_month += 1
                if start_month > 12:
                    start_month = 1
                    start_year += 1
            parsed_year, parsed_month = self._find_next_month_with_day(
                parsed_day, start_year, start_month
            )

        elif year_was_specified and not month_was_specified and parsed_day is None:
            # Only year specified - use January 1st of that year
            parsed_month = 1
            parsed_day = 1

        else:
            # Nothing specified - use current date
            parsed_year = now.year
            parsed_month = now.month
            parsed_day = now.day

        # Final time-based adjustment: if only time specified and it's passed, use tomorrow
        if not month_was_specified and day is None and time is not None:
            target = datetime(parsed_year, parsed_month, parsed_day, hours, minutes or 0)
            target = self.timezone.localize(target)
            if target <= now:
                tomorrow = now + timedelta(days=1)
                parsed_year = tomorrow.year
                parsed_month = tomorrow.month
                parsed_day = tomorrow.day

        return ParsedDateTime(
            year=parsed_year,
            month=parsed_month,
            day=parsed_day,
            hour=hours,
            minute=minutes or 0,
        )

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
