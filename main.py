import csv
import locale
from datetime import datetime, timedelta
from typing import List

locale.setlocale(locale.LC_ALL, "nl_NL")
# current_locale = locale.getlocale()

DATE_NOTATION_STRING = "%A %d %B"
# DATE_NOTATION_STRING = "%d/%m/%Y"
# start_day = datetime(2024, 7, 27)
start_day = datetime(2025, 9, 15)
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
        bijzonderheden = is_every_eighth_day(day_counter)
        match date.weekday():
            # Mondays
            case 0:
                csv_data.append([
                    get_week_number(date),
                    date.strftime(DATE_NOTATION_STRING),
                    "Welpen maaandag",
                    get_activity(day_counter),
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
                    get_activity(day_counter),
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
                    get_activity(day_counter),
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
                    get_activity(day_counter),
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
                    get_activity(day_counter),
                    "",
                    container,
                    bijzonderheden,
                ])
                # day_counter = day_counter + 1
                # if is_third_saturday_of_month(date):
                #     container = "Papier naar buiten"
                # csv_data.append([
                #     date.strftime(DATE_NOTATION_STRING),
                #     "Rover / Stam",
                #     get_activity(day_counter),
                #     "",
                #     container,
                #     "",
                # ])
            # Saturdays
            case 5:
                dwijlen = get_activity(day_counter)
                if is_last_saturday_of_month(date):
                    dwijlen = "Zaal dwijlen"
                csv_data.append([
                    "",
                    date.strftime(DATE_NOTATION_STRING),
                    "Bevers zaterdag",
                    dwijlen,
                    "",
                    container,
                    bijzonderheden,
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


def is_every_eighth_day(day_counter: int) -> str:
    """
    Washing machine schedule ("wasmachine") using day_counter:

    - Every 8th counted day (day_counter % 8 == 0): return "Wasmachine aan!"
    - Every 9th counted day (day_counter % 9 == 0): return "Wasmachine uitruimen"
    - Otherwise return an empty string.

    Accepts day_counter (int) where 0 corresponds to the first counted day (the same origin as the existing day_counter variable).
    """
    # Validate and coerce input
    print(day_counter)
    if not isinstance(day_counter, int):
        try:
            day_counter = int(day_counter)
        except Exception:
            return ""
    if day_counter < 0:
        return ""
    # Prioritize the 8-day action when both conditions coincide (e.g., day_counter == 0).
    if day_counter % 8 == 0:
        print("Wasmachine aan!")
        return "Wasmachine aan!"
    if day_counter % 8 == 1:
        print("Wasmachine uitruimen")
        return "Wasmachine uitruimen"
    return ""


def get_activity(day_counter: int) -> str:
    activity_number = day_counter % (len(activities) - 1)
    return activities[activity_number]


if __name__ == "__main__":
    write_csv_from_lists(
        data=generate_grid(), header=generate_header(), filename="rooster.csv"
    )
