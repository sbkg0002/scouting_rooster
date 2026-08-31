"""Genereer het schoonmaakrooster voor Scouting als CSV (rooster.csv)."""

import calendar
import csv
import locale
import random
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, fields
from datetime import date, timedelta
from pathlib import Path

# Het jaar hoort er echt bij: zonder jaartal gokt Excel er zelf een bij het inlezen
# en dat wordt het verkeerde jaar zodra het seizoen over de jaarwissel loopt --
# januari-rijen kwamen dan op een zondag uit terwijl de groep "Welpen maandag" is.
DATE_FORMAT = "%A %d %B %Y"
DUTCH_LOCALES = ("nl_NL.UTF-8", "nl_NL", "nl")

SEASON_START = date(2026, 9, 7)
SEASON_END = date(2027, 7, 16)
OUTPUT_PATH = Path("rooster.csv")

ACTIVITIES: tuple[str, ...] = (
    "Toiletten schoonmaken",
    "Grote zaal opruimen / goed vegen",
    "Keuken opruimen / dweilen",
    "Hal vegen / dweilen",
    "Toiletten schoonmaken",
    "Zolder opruimen",
    "Buiten opruimen",
)
SHUFFLE_SEED_FACTOR = 42
MAX_SHUFFLE_ATTEMPTS = 1000

HALL_MOPPING = "Zaal dweilen"
PLASTIC_NOTE = "Plastic buiten zetten"
PAPER_NOTE = "Papier naar buiten"
WASHING_MACHINE_ON = "Wasmachine aan!"
WASHING_MACHINE_OFF = "Wasmachine leeg!"
NOTES_SEPARATOR = " / "


@dataclass(frozen=True, slots=True)
class DutyGroup:
    """The group on duty on a given weekday, plus its fixed roster details."""

    name: str
    shows_week_number: bool = False
    remark: str = ""


DUTY_GROUPS: Mapping[calendar.Day, DutyGroup] = {
    calendar.Day.MONDAY: DutyGroup("Welpen maandag", shows_week_number=True),
    calendar.Day.TUESDAY: DutyGroup("Explorers"),
    calendar.Day.WEDNESDAY: DutyGroup("Scouts woensdag"),
    calendar.Day.THURSDAY: DutyGroup("Welpen donderdag"),
    calendar.Day.FRIDAY: DutyGroup("Scouts vrijdag", remark=WASHING_MACHINE_ON),
    calendar.Day.SATURDAY: DutyGroup("Bevers zaterdag", remark=WASHING_MACHINE_OFF),
    # zondag: geen dienst
}


@dataclass(frozen=True, slots=True)
class RosterRow:
    """One roster line; the field order below is the CSV column order."""

    week_number: str = field(metadata={"header": "wk"})
    date: str = field(metadata={"header": "Datum"})
    group: str = field(metadata={"header": "Groep"})
    activity: str = field(metadata={"header": "Ruimte"})
    done: str = field(metadata={"header": "Gedaan?"})
    notes: str = field(metadata={"header": "Containers / Bijzonderheden?"})


def week_ordinal(day: date) -> int:
    """Return a running week counter that increments on every Monday.

    Day ordinal 1 (0001-01-01) was a Monday, so this counts Monday-aligned weeks
    since then. Unlike an ISO week number it never wraps at new year, which keeps
    the activity rotation continuous across seasons.
    """
    return (day.toordinal() - 1) // 7


def is_even_week(day: date) -> bool:
    """Return whether the day falls in an even ISO week."""
    return day.isocalendar().week % 2 == 0


def is_last_saturday_of_month(day: date) -> bool:
    """Return whether the day is the last Saturday of its month."""
    if day.weekday() != calendar.Day.SATURDAY:
        return False
    next_month = day.replace(day=28) + timedelta(days=4)  # never overflows
    last_of_month = next_month - timedelta(days=next_month.day)
    return day + timedelta(days=7) > last_of_month


def is_day_before_third_saturday(day: date) -> bool:
    """Return whether the next day is the third Saturday of its month."""
    tomorrow = day + timedelta(days=1)
    if tomorrow.weekday() != calendar.Day.SATURDAY:
        return False
    first_of_month = tomorrow.replace(day=1)
    days_until_saturday = (calendar.Day.SATURDAY - first_of_month.weekday()) % 7
    third_saturday = first_of_month + timedelta(days=days_until_saturday, weeks=2)
    return tomorrow == third_saturday


CONTAINER_RULES: tuple[tuple[calendar.Day, Callable[[date], bool], str], ...] = (
    (calendar.Day.WEDNESDAY, is_even_week, PLASTIC_NOTE),
    (calendar.Day.FRIDAY, is_day_before_third_saturday, PAPER_NOTE),
    # (calendar.Day.THURSDAY, is_even_week, "Groen buiten zetten"),  # uitgeschakeld
)


def format_dutch_date(day: date) -> str:
    """Format a date the way it appears in the roster, e.g. 'maandag 10 november'."""
    return day.strftime(DATE_FORMAT)


def repeats_an_activity(order: Sequence[str], previous_activity: str) -> bool:
    """Return whether any activity in the order follows itself.

    The previous week's final activity counts as coming before the first one, so
    the Saturday/Monday seam is checked too.
    """
    return any(
        earlier == later
        for earlier, later in zip((previous_activity, *order), order, strict=False)
    )


def weekly_activity_order(week: int, previous_activity: str = "") -> tuple[str, ...]:
    """Return one week's activities, indexed by weekday (0 = Monday .. 5 = Saturday).

    A week has six duty days but there are seven activities, so exactly one is
    skipped. The skipped one advances by one each week, so every activity is done
    six weeks out of seven.

    The remaining six are shuffled deterministically -- regenerating the roster
    always yields the same result -- and reshuffled until no activity is scheduled
    on two consecutive duty days, including directly after previous_activity (pass
    the previous week's Saturday activity).
    """
    skipped = week % len(ACTIVITIES)
    order = [activity for i, activity in enumerate(ACTIVITIES) if i != skipped]
    rng = random.Random(week * SHUFFLE_SEED_FACTOR)
    for _ in range(MAX_SHUFFLE_ATTEMPTS):
        rng.shuffle(order)
        if not repeats_an_activity(order, previous_activity):
            return tuple(order)
    raise ValueError(
        f"Kan week {week} niet indelen zonder herhaling; "
        f"staan er te veel dezelfde activiteiten in ACTIVITIES?"
    )


def season_activities(days: Sequence[date]) -> Iterator[str]:
    """Yield the activity for each duty day, never repeating two days in a row.

    On the last Saturday of the month the whole hall is mopped instead, so that
    week uses one activity fewer than usual.
    """
    previous_activity = ""
    week: int | None = None
    order: tuple[str, ...] = ()
    for day in days:
        if week_ordinal(day) != week:
            week = week_ordinal(day)
            order = weekly_activity_order(week, previous_activity)
        previous_activity = (
            HALL_MOPPING if is_last_saturday_of_month(day) else order[day.weekday()]
        )
        yield previous_activity


def container_note_for(day: date) -> str:
    """Return the bin instruction for this day, or an empty string when none applies."""
    for weekday, applies, note in CONTAINER_RULES:
        if day.weekday() == weekday and applies(day):
            return note
    return ""


def notes_for(day: date, group: DutyGroup) -> str:
    """Combine this day's bin instruction and the group's remark into one cell."""
    notes = (container_note_for(day), group.remark)
    return NOTES_SEPARATOR.join(note for note in notes if note)


def duty_dates(start: date, end: date) -> Iterator[date]:
    """Yield every date in [start, end) that has a group on duty, skipping Sundays."""
    day = start
    while day < end:
        if day.weekday() in DUTY_GROUPS:
            yield day
        day += timedelta(days=1)


def build_row(day: date, activity: str) -> RosterRow:
    """Build the roster line for one duty day."""
    group = DUTY_GROUPS[calendar.Day(day.weekday())]
    return RosterRow(
        week_number=str(day.isocalendar().week) if group.shows_week_number else "",
        date=format_dutch_date(day),
        group=group.name,
        activity=activity,
        done="",
        notes=notes_for(day, group),
    )


def build_roster(start: date, end: date) -> list[RosterRow]:
    """Build every roster line for the season, in date order."""
    days = list(duty_dates(start, end))
    return [
        build_row(day, activity)
        for day, activity in zip(days, season_activities(days), strict=True)
    ]


def column_headers() -> list[str]:
    """Return the CSV header row, derived from the RosterRow field order."""
    return [column.metadata["header"] for column in fields(RosterRow)]


def row_values(row: RosterRow) -> list[str]:
    """Return one row as CSV cells, in the same order as column_headers()."""
    return [getattr(row, column.name) for column in fields(RosterRow)]


def write_roster_csv(rows: Sequence[RosterRow], path: Path) -> None:
    """Write the roster to an Excel-friendly CSV file."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        csv_file.write("sep=,\n")  # hint voor Excel
        writer = csv.writer(csv_file)
        writer.writerow(column_headers())
        writer.writerows(row_values(row) for row in rows)


def use_dutch_locale(candidates: Sequence[str] = DUTCH_LOCALES) -> bool:
    """Set LC_TIME to Dutch, or warn and keep the default locale if none is found."""
    for name in candidates:
        try:
            locale.setlocale(locale.LC_TIME, name)
            return True
        except locale.Error:
            continue
    print(
        "Waarschuwing: geen Nederlandse locale gevonden; datums in het Engels.",
        file=sys.stderr,
    )
    return False


def main() -> None:
    """Genereer het rooster en schrijf het naar rooster.csv."""
    use_dutch_locale()
    rows = build_roster(SEASON_START, SEASON_END)
    write_roster_csv(rows, OUTPUT_PATH)
    print(f"{len(rows)} diensten geschreven naar {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
