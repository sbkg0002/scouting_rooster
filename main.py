import csv
import locale
from datetime import datetime, timedelta
from typing import List

locale.setlocale(locale.LC_ALL, 'nl_NL')
# current_locale = locale.getlocale()

DATE_NOTATION_STRING = "%A %d %B %Y"
# DATE_NOTATION_STRING = "%d/%m/%Y"
# start_day = datetime(2024, 7, 27)
start_day = datetime(2024, 9, 2)
end_day = datetime(2025, 7, 16)
activities = ['Toiletten-1 schoonmaken', 'Grote zaal opruimen / goed vegen', 'Keuken opruimen / dweilen',
              'Hal vegen / dweilen', 'Toiletten-2 schoonmaken', 'Zolder opruimen', 'Buiten opruimen']


def generate_grid() -> list[list[str]]:
    day_counter = 0
    csv_data = []
    date = start_day
    while date < end_day:
        # day_of_year = date.timetuple().tm_yday
        bijzonderheden = ''
        match date.weekday():
            # Mondays
            case 0:
                csv_data.append(
                    [date.strftime(DATE_NOTATION_STRING), 'Welpen maandag', get_activity(day_counter), '',
                     bijzonderheden, ''])
            # Tuesdays
            case 1:
                csv_data.append(
                    [date.strftime(DATE_NOTATION_STRING), 'Explorers', get_activity(day_counter), '', bijzonderheden,
                     ''])
            # Wednesdays
            case 2:
                if is_week_number_even(date):
                    bijzonderheden = 'Plastic buiten zetten'
                csv_data.append(
                    [date.strftime(DATE_NOTATION_STRING), 'Scouts woensdag', get_activity(day_counter), '',
                     bijzonderheden, ''])
            # Thursdays
            case 3:
                if is_week_number_even(date):
                    bijzonderheden = 'Groen buiten zetten'
                csv_data.append(
                    [date.strftime(DATE_NOTATION_STRING), 'Welpen donderdag', get_activity(day_counter), '',
                     bijzonderheden, ''])
            # Print Fridays twice
            case 4:
                csv_data.append(
                    [date.strftime(DATE_NOTATION_STRING), 'Scouts Vrijdag', get_activity(day_counter), '',
                     bijzonderheden, ''])
                day_counter = day_counter + 1
                if is_third_friday_of_month(date):
                    bijzonderheden = 'Papier naar buiten'
                csv_data.append(
                    [date.strftime(DATE_NOTATION_STRING), 'Rover / Stam', get_activity(day_counter), '', bijzonderheden, ''])
            # Saturdays
            case 5:
                dwijlen = get_activity(day_counter)
                if is_last_saturday_of_month(date):
                    dwijlen = 'Zaal dwijlen'
                csv_data.append(
                    [date.strftime(DATE_NOTATION_STRING), 'Bevers zaterdag', dwijlen, bijzonderheden, '', ''])
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
    return ['Datum', 'Groep', 'Ruimte', 'Gedaan?', 'Containers', 'Bijzonderheden?']


def write_csv_from_lists(data: list[list[str]], header: list[str], filename: str) -> None:
    with open(filename, "w") as csv_file:
        csv_file.write('sep=,\n')
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


def is_third_friday_of_month(dt):
    if dt.weekday() != 5:
        return False
    first_day_of_month = dt.replace(day=1)
    first_friday = first_day_of_month + timedelta(days=(4 - first_day_of_month.weekday() + 7) % 7)
    third_friday = first_friday + timedelta(weeks=2)
    print(f'Friday: {dt.date() == third_friday.date()}')
    return dt.date() == third_friday.date()

def is_week_number_even(date):
    week_number = date.isocalendar()[1]
    print(f'{date.strftime(DATE_NOTATION_STRING)}: {week_number % 2 == 0} ({date.isocalendar()})')
    return week_number % 2 == 0

def get_activity(day_counter: int) -> str:
    activity_number = day_counter % (len(activities) - 1)
    return activities[activity_number]


if __name__ == '__main__':
    write_csv_from_lists(data=generate_grid(), header=generate_header(), filename="rooster.csv")

