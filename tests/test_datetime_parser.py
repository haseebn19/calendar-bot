"""Tests for the datetime parser utility."""

from __future__ import annotations

import pytest

from calendar_bot.utils.datetime_parser import DateTimeParser


class TestTimeParser:
    """Tests for time parsing functionality."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        """Create a parser with a fixed timezone."""
        return DateTimeParser("America/New_York")

    def test_parse_time_12h_with_minutes_am(self, parser: DateTimeParser) -> None:
        """Test parsing 12-hour time with minutes (AM)."""
        hours, minutes = parser.parse_time("10:30am")
        assert hours == 10
        assert minutes == 30

    def test_parse_time_12h_with_minutes_pm(self, parser: DateTimeParser) -> None:
        """Test parsing 12-hour time with minutes (PM)."""
        hours, minutes = parser.parse_time("10:30pm")
        assert hours == 22
        assert minutes == 30

    def test_parse_time_12h_noon(self, parser: DateTimeParser) -> None:
        """Test parsing noon."""
        hours, minutes = parser.parse_time("12pm")
        assert hours == 12
        assert minutes == 0

    def test_parse_time_12h_midnight(self, parser: DateTimeParser) -> None:
        """Test parsing midnight."""
        hours, minutes = parser.parse_time("12am")
        assert hours == 0
        assert minutes == 0

    def test_parse_time_24h_with_minutes(self, parser: DateTimeParser) -> None:
        """Test parsing 24-hour time with minutes."""
        hours, minutes = parser.parse_time("14:30")
        assert hours == 14
        assert minutes == 30

    def test_parse_time_24h_no_minutes(self, parser: DateTimeParser) -> None:
        """Test parsing 24-hour time without minutes."""
        hours, minutes = parser.parse_time("14")
        assert hours == 14
        assert minutes == 0

    def test_parse_time_invalid(self, parser: DateTimeParser) -> None:
        """Test parsing invalid time."""
        hours, minutes = parser.parse_time("invalid")
        assert hours == -1
        assert minutes == -1

    def test_parse_time_none(self, parser: DateTimeParser) -> None:
        """Test parsing None time."""
        hours, minutes = parser.parse_time(None)
        assert hours is None
        assert minutes is None

    def test_parse_time_case_insensitive(self, parser: DateTimeParser) -> None:
        """Test that time parsing is case insensitive."""
        hours1, _ = parser.parse_time("10AM")
        hours2, _ = parser.parse_time("10am")
        hours3, _ = parser.parse_time("10Am")
        assert hours1 == hours2 == hours3 == 10


class TestMonthParser:
    """Tests for month parsing functionality."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        """Create a parser with a fixed timezone."""
        return DateTimeParser("UTC")

    def test_parse_month_full_name(self, parser: DateTimeParser) -> None:
        """Test parsing full month name."""
        assert parser.parse_month("January") == 1
        assert parser.parse_month("December") == 12

    def test_parse_month_abbreviated(self, parser: DateTimeParser) -> None:
        """Test parsing abbreviated month name."""
        assert parser.parse_month("Jan") == 1
        assert parser.parse_month("Dec") == 12

    def test_parse_month_number_string(self, parser: DateTimeParser) -> None:
        """Test parsing month as number string."""
        assert parser.parse_month("1") == 1
        assert parser.parse_month("12") == 12

    def test_parse_month_integer(self, parser: DateTimeParser) -> None:
        """Test parsing month as integer."""
        assert parser.parse_month(1) == 1
        assert parser.parse_month(12) == 12

    def test_parse_month_invalid_number(self, parser: DateTimeParser) -> None:
        """Test parsing invalid month number."""
        assert parser.parse_month(0) is None
        assert parser.parse_month(13) is None

    def test_parse_month_invalid_string(self, parser: DateTimeParser) -> None:
        """Test parsing invalid month string."""
        assert parser.parse_month("NotAMonth") is None

    def test_parse_month_none(self, parser: DateTimeParser) -> None:
        """Test parsing None month."""
        assert parser.parse_month(None) is None


class TestDateTimeParsing:
    """Tests for full datetime parsing."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        """Create a parser with a fixed timezone."""
        return DateTimeParser("UTC")

    def test_parse_full_datetime(self, parser: DateTimeParser) -> None:
        """Test parsing a complete datetime."""
        result = parser.parse(year=2024, month="January", day="15", time="10:30am")

        assert result.is_valid
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_with_defaults(self, parser: DateTimeParser) -> None:
        """Test parsing with default values."""
        result = parser.parse(time="10am")

        assert result.is_valid
        assert result.hour == 10
        assert result.minute == 0

    def test_parse_invalid_month_returns_error(self, parser: DateTimeParser) -> None:
        """Test that invalid month returns error."""
        result = parser.parse(month="NotAMonth")

        assert not result.is_valid
        assert result.error_message is not None
        assert "Invalid month" in result.error_message

    def test_parse_invalid_time_returns_error(self, parser: DateTimeParser) -> None:
        """Test that invalid time returns error."""
        result = parser.parse(time="invalid")

        assert not result.is_valid
        assert result.error_message is not None
        assert "Invalid time" in result.error_message

    def test_to_utc_timestamp(self, parser: DateTimeParser) -> None:
        """Test converting parsed datetime to UTC timestamp."""
        result = parser.parse(year=2024, month=1, day=1, time="00:00")
        timestamp = parser.to_utc_timestamp(result)

        assert timestamp is not None
        assert timestamp == 1704067200  # Jan 1, 2024 00:00 UTC

    def test_to_utc_timestamp_with_timezone(self) -> None:
        """Test timestamp conversion with different timezone."""
        parser = DateTimeParser("America/New_York")
        result = parser.parse(year=2024, month=1, day=1, time="00:00")
        timestamp = parser.to_utc_timestamp(result)

        # New York is UTC-5, so midnight local = 5:00 UTC
        assert timestamp is not None
        assert timestamp == 1704085200  # Jan 1, 2024 05:00 UTC

    def test_to_utc_timestamp_invalid(self, parser: DateTimeParser) -> None:
        """Test that invalid datetime returns None timestamp."""
        result = parser.parse(month="invalid")
        timestamp = parser.to_utc_timestamp(result)

        assert timestamp is None


class TestDayNameParsing:
    """Tests for day name parsing functionality."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        """Create a parser with a fixed timezone."""
        return DateTimeParser("UTC")

    def test_parse_day_number(self, parser: DateTimeParser) -> None:
        """Test parsing day as number."""
        day, is_name = parser.parse_day("15")
        assert day == 15
        assert is_name is False

    def test_parse_day_integer(self, parser: DateTimeParser) -> None:
        """Test parsing day as integer."""
        day, is_name = parser.parse_day(15)
        assert day == 15
        assert is_name is False

    def test_parse_day_none(self, parser: DateTimeParser) -> None:
        """Test parsing None day."""
        day, is_name = parser.parse_day(None)
        assert day is None
        assert is_name is False

    def test_parse_day_invalid_number(self, parser: DateTimeParser) -> None:
        """Test parsing invalid day number."""
        day, _ = parser.parse_day(32)
        assert day == -1

        day, _ = parser.parse_day(0)
        assert day == -1
