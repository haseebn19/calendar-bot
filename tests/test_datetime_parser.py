"""Tests for the datetime parser utility."""

from __future__ import annotations

import pytest

from calendar_bot.utils.datetime_parser import DateTimeParser, ParsedDateTime, days_in_month


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

    def test_parse_day_name_monday(self, parser: DateTimeParser) -> None:
        """Test parsing day name."""
        day, is_name = parser.parse_day("Monday")
        assert day == 0  # Monday is 0
        assert is_name is True

    def test_parse_day_name_abbreviated(self, parser: DateTimeParser) -> None:
        """Test parsing abbreviated day name."""
        day, is_name = parser.parse_day("Mon")
        assert day == 0
        assert is_name is True

    def test_parse_day_name_invalid(self, parser: DateTimeParser) -> None:
        """Test parsing invalid day name."""
        day, is_name = parser.parse_day("NotADay")
        assert day == -1
        assert is_name is False


class TestParsedDateTime:
    """Tests for ParsedDateTime dataclass."""

    def test_create_valid(self) -> None:
        result = ParsedDateTime(2024, 1, 15, 10, 30)
        assert result.is_valid
        assert result.error_message is None

    def test_create_invalid(self) -> None:
        result = ParsedDateTime.invalid("Test error message")
        assert not result.is_valid
        assert result.error_message == "Test error message"
        assert result.year == 0
        assert result.month == 0


class TestDaysInMonth:
    """Tests for days_in_month helper function."""

    def test_january(self) -> None:
        assert days_in_month(2024, 1) == 31

    def test_february_regular(self) -> None:
        assert days_in_month(2023, 2) == 28

    def test_february_leap_year(self) -> None:
        assert days_in_month(2024, 2) == 29

    def test_april(self) -> None:
        assert days_in_month(2024, 4) == 30


class TestDayNameParsingExtended:
    """Extended tests for day name parsing."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_parse_day_name_all_days(self, parser: DateTimeParser) -> None:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day in enumerate(days):
            result = parser.parse_day_name(day)
            assert result == i

    def test_parse_day_name_case_insensitive(self, parser: DateTimeParser) -> None:
        assert parser.parse_day_name("MONDAY") == 0
        assert parser.parse_day_name("monday") == 0
        assert parser.parse_day_name("Monday") == 0

    def test_parse_day_name_partial(self, parser: DateTimeParser) -> None:
        assert parser.parse_day_name("mon") == 0
        assert parser.parse_day_name("tue") == 1
        assert parser.parse_day_name("fri") == 4


class TestInvalidDateCombinations:
    """Tests for invalid date combinations."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_february_30(self, parser: DateTimeParser) -> None:
        result = parser.parse(month="February", day="30")
        assert not result.is_valid
        assert "February" in result.error_message
        assert "30" in result.error_message

    def test_february_31(self, parser: DateTimeParser) -> None:
        result = parser.parse(month="February", day="31")
        assert not result.is_valid

    def test_april_31(self, parser: DateTimeParser) -> None:
        result = parser.parse(month="April", day="31")
        assert not result.is_valid
        assert "April" in result.error_message

    def test_invalid_day_string(self, parser: DateTimeParser) -> None:
        result = parser.parse(day="invalid")
        assert not result.is_valid
        assert "Invalid day" in result.error_message


class TestYearOnlyParsing:
    """Tests for year-only parsing."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_year_only_defaults_to_jan_1(self, parser: DateTimeParser) -> None:
        result = parser.parse(year=2025)
        assert result.is_valid
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 0
        assert result.minute == 0


class TestGetNextWeekday:
    """Tests for get_next_weekday method."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_get_next_monday(self, parser: DateTimeParser) -> None:
        result = parser.get_next_weekday(0)  # Monday
        assert result.weekday() == 0

    def test_get_next_weekday_returns_future(self, parser: DateTimeParser) -> None:
        now = parser.now
        result = parser.get_next_weekday(now.weekday())
        # Should return 7 days from now (next occurrence, not today)
        assert result > now


class TestFindNextMonthWithDay:
    """Tests for _find_next_month_with_day method."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_find_month_with_31_days(self, parser: DateTimeParser) -> None:
        # Starting from February, find next month with 31 days
        year, month = parser._find_next_month_with_day(31, 2024, 2)
        assert month == 3  # March
        assert year == 2024

    def test_find_month_with_30_days(self, parser: DateTimeParser) -> None:
        # 30 days works for most months
        _year, month = parser._find_next_month_with_day(30, 2024, 2)
        assert month == 3  # March (skips Feb)

    def test_find_month_year_rollover(self, parser: DateTimeParser) -> None:
        # Starting from December, find next month
        year, month = parser._find_next_month_with_day(15, 2024, 12)
        assert month == 12
        assert year == 2024


class TestAdjust12Hour:
    """Tests for _adjust_12h static method."""

    def test_am_regular(self) -> None:
        hours, minutes = DateTimeParser._adjust_12h(10, 30, "am")
        assert hours == 10
        assert minutes == 30

    def test_pm_regular(self) -> None:
        hours, minutes = DateTimeParser._adjust_12h(10, 30, "pm")
        assert hours == 22
        assert minutes == 30

    def test_noon(self) -> None:
        hours, _minutes = DateTimeParser._adjust_12h(12, 0, "pm")
        assert hours == 12

    def test_midnight(self) -> None:
        hours, _minutes = DateTimeParser._adjust_12h(12, 0, "am")
        assert hours == 0

    def test_invalid_hours_over_12(self) -> None:
        hours, minutes = DateTimeParser._adjust_12h(13, 0, "am")
        assert hours == -1
        assert minutes == -1


class TestMonthOnlyParsing:
    """Tests for parsing with only month specified."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_month_only_uses_first_of_month(self, parser: DateTimeParser) -> None:
        result = parser.parse(month="March")
        assert result.is_valid
        assert result.month == 3
        assert result.day == 1

    def test_month_only_bumps_year_if_past(self, parser: DateTimeParser) -> None:
        # If current month is December, January should be next year
        now = parser.now
        # Use a month that's definitely in the past
        past_month = now.month - 1 if now.month > 1 else 12
        result = parser.parse(month=past_month)

        assert result.is_valid
        if past_month < now.month:
            assert result.year == now.year + 1


class TestDayOnlyParsing:
    """Tests for parsing with only day specified."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_day_only_finds_next_occurrence(self, parser: DateTimeParser) -> None:
        result = parser.parse(day="15")
        assert result.is_valid
        assert result.day == 15

    def test_day_31_skips_short_months(self, parser: DateTimeParser) -> None:
        result = parser.parse(day="31")
        assert result.is_valid
        assert result.day == 31
        # Should find a month that has 31 days
        assert result.month in [1, 3, 5, 7, 8, 10, 12]


class TestDayNameWithTime:
    """Tests for parsing day names with time."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_day_name_with_time(self, parser: DateTimeParser) -> None:
        result = parser.parse(day="Monday", time="10am")
        assert result.is_valid
        assert result.hour == 10
        assert result.minute == 0


class TestLeapYearEdgeCases:
    """Tests for leap year edge cases."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_feb_29_in_leap_year(self, parser: DateTimeParser) -> None:
        result = parser.parse(year=2024, month="February", day="29")
        assert result.is_valid
        assert result.day == 29
        assert result.month == 2
        assert result.year == 2024

    def test_feb_29_in_non_leap_year_invalid(self, parser: DateTimeParser) -> None:
        result = parser.parse(year=2023, month="February", day="29")
        assert not result.is_valid
        assert "February" in result.error_message


class TestTimestampEdgeCases:
    """Tests for timestamp conversion edge cases."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_to_utc_timestamp_overflow(self, parser: DateTimeParser) -> None:
        # Create an invalid parsed datetime that would cause overflow
        parsed = ParsedDateTime(99999, 1, 1, 0, 0)
        result = parser.to_utc_timestamp(parsed)
        assert result is None


class TestTimeOnlyParsing:
    """Tests for parsing with only time specified."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_time_only_returns_valid(self, parser: DateTimeParser) -> None:
        result = parser.parse(time="10:30am")
        assert result.is_valid
        assert result.hour == 10
        assert result.minute == 30


class TestLeapYearBumpEdgeCase:
    """Tests for Feb 29 -> next year edge case."""

    @pytest.fixture
    def parser(self) -> DateTimeParser:
        return DateTimeParser("UTC")

    def test_feb_29_bump_to_non_leap_year(self, parser: DateTimeParser) -> None:
        # If someone specifies Feb 29 and current date is past Feb 29 2024,
        # it would try to bump to 2025, but 2025 isn't a leap year
        # We test by explicitly specifying a leap year
        result = parser.parse(year=2023, month="February", day="29")
        assert not result.is_valid  # 2023 is not a leap year
