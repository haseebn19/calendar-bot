"""Tests for the datetime parser utility."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from calendar_bot.utils.datetime_parser import DateTimeParser, ParsedDateTime, days_in_month

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def parser() -> DateTimeParser:
    return DateTimeParser("UTC")


@pytest.fixture
def parser_at(monkeypatch: pytest.MonkeyPatch) -> Callable[..., DateTimeParser]:
    """Return a function that makes a UTC parser whose current time is the given moment."""

    def make(*when: int) -> DateTimeParser:
        fixed = datetime(*when, tzinfo=UTC)
        monkeypatch.setattr(DateTimeParser, "now", property(lambda _self: fixed))
        return DateTimeParser("UTC")

    return make


def date_of(result: ParsedDateTime) -> tuple[int, int, int, int, int]:
    assert result.is_valid, result.error_message
    return result.year, result.month, result.day, result.hour, result.minute


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("10:30am", (10, 30)),
        ("10:30PM", (22, 30)),
        ("12pm", (12, 0)),
        ("12am", (0, 0)),
        ("14:30", (14, 30)),
        ("14", (14, 0)),
        (None, (None, None)),
        ("", (None, None)),
        ("25:00", (-1, -1)),
        ("noon", (-1, -1)),
        ("0am", (-1, -1)),
        ("00:30am", (-1, -1)),
        ("13pm", (-1, -1)),
    ],
)
def test_parse_time(parser: DateTimeParser, text: str | None, expected: tuple) -> None:
    assert parser.parse_time(text) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("January", 1),
        ("feb", 2),
        ("Sept", 9),
        ("3", 3),
        (12, 12),
        ("13", None),
        (0, None),
        ("Ju", None),  # Too short to tell June from July
        ("NotAMonth", None),
        (None, None),
    ],
)
def test_parse_month(parser: DateTimeParser, value: str | int | None, expected: int | None) -> None:
    assert parser.parse_month(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("15", (15, False)),
        (31, (31, False)),
        (None, (None, False)),
        ("32", (-1, False)),
        (0, (-1, False)),
        ("Monday", (0, True)),
        ("SUN", (6, True)),
        ("th", (3, True)),
        ("t", (-1, False)),  # Tuesday or Thursday
        ("someday", (-1, False)),
    ],
)
def test_parse_day(parser: DateTimeParser, value: str | int | None, expected: tuple) -> None:
    assert parser.parse_day(value) == expected


def test_days_in_month() -> None:
    assert [days_in_month(2023, 2), days_in_month(2024, 2), days_in_month(2024, 4)] == [28, 29, 30]


class TestParse:
    def test_a_given_year_is_used_exactly(self, parser: DateTimeParser) -> None:
        assert date_of(parser.parse(year=2024, month="January", day="15", time="10:30am")) == (
            2024,
            1,
            15,
            10,
            30,
        )
        assert date_of(parser.parse(year=2025)) == (2025, 1, 1, 0, 0)
        assert date_of(parser.parse(year=2024, month="February", day="29"))[:3] == (2024, 2, 29)

    @pytest.mark.parametrize(
        ("parts", "message"),
        [
            ({"time": "invalid"}, "Invalid time: 'invalid'"),
            ({"month": "NotAMonth"}, "Invalid month: 'NotAMonth'"),
            ({"day": "someday"}, "Invalid day: 'someday'"),
            ({"month": "February", "day": "30"}, "Invalid date: February doesn't have 30 days."),
            ({"month": "April", "day": "31"}, "Invalid date: April doesn't have 31 days."),
            (
                {"year": 2023, "month": "February", "day": "29"},
                "Invalid date: February 2023 doesn't have 29 days.",
            ),
            ({"year": 0}, "Invalid year: 0. Use a year from 1 to 9999."),
            ({"year": 10000}, "Invalid year: 10000. Use a year from 1 to 9999."),
        ],
    )
    def test_invalid_parts_explain_the_problem(
        self, parser: DateTimeParser, parts: dict, message: str
    ) -> None:
        result = parser.parse(**parts)
        assert not result.is_valid
        assert result.error_message is not None
        assert result.error_message.startswith(message)


class TestNextOccurrence:
    @pytest.fixture
    def monday_9am(self, parser_at: Callable[..., DateTimeParser]) -> DateTimeParser:
        return parser_at(2026, 3, 9, 9, 0)

    @pytest.mark.parametrize(
        ("parts", "expected"),
        [
            ({"time": "5pm"}, (2026, 3, 9, 17, 0)),
            ({"time": "8am"}, (2026, 3, 10, 8, 0)),
            ({"day": "Monday", "time": "5pm"}, (2026, 3, 9, 17, 0)),
            ({"day": "Mon", "time": "8am"}, (2026, 3, 16, 8, 0)),
            ({"day": "Friday"}, (2026, 3, 13, 0, 0)),
            ({"day": "9", "time": "5pm"}, (2026, 3, 9, 17, 0)),
            ({"day": "9", "time": "8am"}, (2026, 4, 9, 8, 0)),
            ({"month": "February"}, (2027, 2, 1, 0, 0)),
            ({"month": "March", "day": "1"}, (2027, 3, 1, 0, 0)),
            ({"month": "March", "day": "20", "time": "12pm"}, (2026, 3, 20, 12, 0)),
            ({"month": "February", "day": "29"}, (2028, 2, 29, 0, 0)),
            ({"year": 2026, "time": "8am"}, (2026, 1, 1, 8, 0)),
        ],
    )
    def test_next_matching_date(
        self, monday_9am: DateTimeParser, parts: dict, expected: tuple
    ) -> None:
        assert date_of(monday_9am.parse(**parts)) == expected

    def test_day_31_skips_months_without_one(
        self, parser_at: Callable[..., DateTimeParser]
    ) -> None:
        parser = parser_at(2026, 3, 31, 10, 0)
        assert date_of(parser.parse(day=31, time="9am")) == (2026, 5, 31, 9, 0)

    def test_month_only_on_the_first_with_time_still_to_come(
        self, parser_at: Callable[..., DateTimeParser]
    ) -> None:
        parser = parser_at(2026, 3, 1, 9, 0)
        assert date_of(parser.parse(month="March", time="5pm")) == (2026, 3, 1, 17, 0)


class TestTimestamps:
    def test_utc(self, parser: DateTimeParser) -> None:
        result = parser.parse(year=2024, month=1, day=1, time="00:00")
        assert parser.to_utc_timestamp(result) == 1704067200

    def test_local_time_in_another_timezone(self) -> None:
        # Midnight in New York in January is 05:00 UTC
        parser = DateTimeParser("America/New_York")
        result = parser.parse(year=2024, month=1, day=1, time="00:00")
        assert parser.to_utc_timestamp(result) == 1704085200

    def test_invalid_or_out_of_range_dates_have_no_timestamp(self, parser: DateTimeParser) -> None:
        assert parser.to_utc_timestamp(parser.parse(month="invalid")) is None
        assert parser.to_utc_timestamp(ParsedDateTime(99999, 1, 1, 0, 0)) is None
