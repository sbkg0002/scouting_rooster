import csv
import locale
import random
from datetime import datetime, timedelta
from typing import List

locale.setlocale(locale.LC_ALL, "nl_NL")
# current_locale = locale.getlocale()

DATE_NOTATION_STRING = "%A %d %B"
# DATE_NOTATION_STRING = "%d/%m/%Y"
# start_day = datetime(2024, 7, 27)
start_day = datetime(2025, 11, 10)
end_day = datetime(2026, 7, 16)
activities = [
    "Toiletten-1 schoonmaken",
    "Grote zaal opruimen / goed vegen",
    "Keuken opruimen / dweilen",
    "Hal vegen / dweilen",
    "Toiletten-2 schoonmaken",
    "Zolder opruimen",
    "Buiten opruimen",
]
activities_per_wk = {}

def generate_grid() -> list[list[str]]:
    """
    Generate the schedule grid as a list of rows for CSV output.

    Each row is a list of strings with the following columns:
      - Datum: formatted using DATE_NOTATION_STRING
      - Groep: group name (e.g., "Welpen ma", "Scouts vr")
      - Ruimte: assigned activity returned by get_activity()
      - Gedaan?: placeholder for completion status
      - Containers: notes about containers (e.g., recycling instructions)
      - Bijzonderheden?: special notes

    Iteration details:
    - Iterates from module-level start_day (inclusive) up to end_day (exclusive).
    - Increments one day at a time and uses weekday matching to determine group rows.
    - Sundays are skipped (not included in the returned grid).
    - The day_counter is used to select activities cyclically via get_activity().
    """
    day_counter = 0
    csv_data = []
    date = start_day
    while date < end_day:
        container = ""
        bijzonderheden = ""
        match date.weekday():
            # Mondays
            case 0:
                csv_data.append([
                    get_week_number(date),
                    date.strftime(DATE_NOTATION_STRING),
                    "Welpen maandag",
                    get_activity(day_counter, date),
                    "",
                    container,
                    bijzonderheden,
                ])
            # Tuesdays
            case 1:
                csv_data.append([
                    "",
                    date.strftime(DATE_NOTATION_STRING),
                    "Explorers",
                    get_activity(day_counter, date),
                    "",
                    container,
                    bijzonderheden,
                ])
            # Wednesdays
            case 2:
                if is_week_number_even(date):
                    container = "Plastic buiten zetten"
                csv_data.append([
                    "",
                    date.strftime(DATE_NOTATION_STRING),
                    "Scouts woensdag",
                    get_activity(day_counter, date),
                    "",
                    container,
                    bijzonderheden,
                ])
            # Thursdays
            case 3:
                # if is_week_number_even(date):
                #     container = "Groen buiten zetten"
                csv_data.append([
                    "",
                    date.strftime(DATE_NOTATION_STRING),
                    "Welpen donderdag",
                    get_activity(day_counter, date),
                    "",
                    container,
                    bijzonderheden,
                ])
            # Print Fridays twice
            case 4:
                if is_third_saturday_of_month(date):
                    container = "Papier naar buiten"
                csv_data.append([
                    "",
                    date.strftime(DATE_NOTATION_STRING),
                    "Scouts vrijdag",
                    get_activity(day_counter, date),
                    "",
                    container,
                    bijzonderheden,
                ])
            # Saturdays
            case 5:
                dwijlen = get_activity(day_counter, date)
                if is_last_saturday_of_month(date):
                    dwijlen = "Zaal dwijlen"
                csv_data.append([
                    "",
                    date.strftime(DATE_NOTATION_STRING),
                    "Bevers zaterdag",
                    dwijlen,
                    "",
                    container,
                    "Wasmachine aan!",
                ])
            # Do not print Sundays
            case 6:
                # print(f'skipping: {date.strftime("%A")}')
                date = date + timedelta(days=1)
                continue

        # csv_data.append([date.strftime(DATE_NOTATION_STRING))
        # print(day_of_season)
        date = date + timedelta(days=1)
        day_counter = day_counter + 1
    return csv_data


def generate_header() -> List[str]:
    return [
        "wk",
        "Datum",
        "Groep",
        "Ruimte",
        "Gedaan?",
        "Containers",
        "Bijzonderheden?",
    ]


def write_csv_from_lists(
    data: list[list[str]], header: list[str], filename: str
) -> None:
    with open(filename, "w") as csv_file:
        csv_file.write("sep=,\n")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(header)  # write header
        for row in data:
            csv_writer.writerow(row)  # write each row


def is_last_saturday_of_month(dt) -> bool:
    # Check if the given date is a Saturday
    if dt.weekday() != 5:
        return False
    # Get the last day of the month
    next_month = dt.replace(day=28) + timedelta(days=4)  # this will never fail
    last_day = next_month - timedelta(days=next_month.day)
    # Check if the given date is the last Saturday
    return dt + timedelta(days=7) > last_day


def is_third_saturday_of_month(dt):
    # we check on Friday
    sat = dt + timedelta(days=1)
    # print(sat.strftime(DATE_NOTATION_STRING))
    if sat.weekday() != 5:
        return False
    # Get the first day of the month
    first_day_of_month = sat.replace(day=1)
    # Calculate the first Saturday of the month
    first_saturday = first_day_of_month + timedelta(
        days=(5 - first_day_of_month.weekday() + 7) % 7
    )
    # Calculate the third Saturday
    third_saturday = first_saturday + timedelta(weeks=2)
    return sat.date() == third_saturday.date()


def is_week_number_even(date):
    week_number = date.isocalendar()[1]
    # print(
    #     f"{date.strftime(DATE_NOTATION_STRING)}: {week_number % 2 == 0} ({date.isocalendar()})"
    # )
    return week_number % 2 == 0


def get_week_number(date) -> int:
    """
    Return the ISO week number for the given date.

    Accepts either a datetime or date object. The returned value is the
    week number as an integer (1-53) according to ISO-8601.
    """
    try:
        dt = date.date()
    except Exception:
        dt = date
    return dt.isocalendar()[1]


def per_week(number: int) -> int:
    """Return how many times 7 fits in the given number."""
    return number // 7


def get_random_weekly_activities(week_number: int) -> List[str]:
    """
    Generate a random permutation of all activities for a given week.

    Each week gets a shuffled version of all activities, ensuring each
    activity is used exactly once per week.

    Args:
        week_number: The week number to generate activities for

    Returns:
        List of activities in random order for the week
    """
    # Use week number as seed for consistent randomization
    random.seed(week_number * 42)  # Multiply by arbitrary number for better distribution
    shuffled_activities = activities.copy()
    random.shuffle(shuffled_activities)
    return shuffled_activities

def get_activity(day_counter: int, date: datetime) -> str:
    """
    Get the activity for a specific day, ensuring all activities are used per week.

    This function ensures that:
    - All 7 activities are used exactly once per week
    - Activities are randomly distributed within each week
    - The same week always gets the same random arrangement (deterministic)
    - Uses ISO week numbers for proper calendar week alignment

    Args:
        day_counter: The day counter (0-based)
        date: The actual date for this day

    Returns:
        The activity name for that day
    """
    week_number = date.isocalendar()[1]  # Use ISO week number
    day_in_week = day_counter % 7  # 0-6 for days within the week

    # Get or generate the activities for this week
    if week_number not in activities_per_wk:
        activities_per_wk[week_number] = get_random_weekly_activities(week_number)

    return activities_per_wk[week_number][day_in_week]


if __name__ == "__main__":
    write_csv_from_lists(
        data=generate_grid(), header=generate_header(), filename="rooster.csv"
    )
