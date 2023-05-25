import os
import sys
import argparse
import math
from datetime import datetime
from glob import glob
import re
import shutil

def get_matching_files(directory, file_format):
    file_pattern = file_format.replace("{YYYY}", "*").replace("{MM}", "*").replace("{DD}", "*").replace("{hh}", "*").replace("{mm}", "*")
    files = glob(os.path.join(directory, file_pattern))
    return files

def generate_regex_pattern(file_format):
    regex_pattern = file_format
    # Replace ? with regex pattern matching any single character
    regex_pattern = regex_pattern.replace("?", r"\w")
    # Replace * with regex pattern matching zero or more characters
    regex_pattern = regex_pattern.replace("*", r"\w*")
    # Replace {YYYY}, {MM}, {DD}, {hh}, {mm} with corresponding regex patterns
    regex_pattern = regex_pattern.replace("{YYYY}", r"(?P<YYYY>\d{4})")
    regex_pattern = regex_pattern.replace("{MM}", r"(?P<MM>\d{2})")
    regex_pattern = regex_pattern.replace("{DD}", r"(?P<DD>\d{2})")
    regex_pattern = regex_pattern.replace("{hh}", r"(?P<hh>\d{2})")
    regex_pattern = regex_pattern.replace("{mm}", r"(?P<mm>\d{2})")
    # Add start and end anchors to match the entire file name
    regex_pattern = r"^" + regex_pattern + r"$"
    return regex_pattern

def get_file_datetime(file_path, file_format):
    regex_pattern = generate_regex_pattern(file_format)
    filename = os.path.basename(file_path) # remove directories, if any
    match = re.search(regex_pattern, filename)
    if match:
        try:
            year = int(match.group('YYYY'))
            month = int(match.group('MM'))
            day = int(match.group('DD'))
            hour = int(match.group('hh'))
            minute = int(match.group('mm'))
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None
    return None

def list_files(file_flags, verbose):
    if len(file_flags) == 0:
        print("No files matching the specified file format found. See --help if in doubt.")
    else:
        file_flags_items = sorted(file_flags.items())
        if verbose:
            for file, flags in file_flags_items:
                flags_str = ", ".join(flags)
                if flags_str:
                    print(f"{file} - Reasons to keep: {flags_str}")
                else:
                    print(f"{file} - No reason to keep")
            print("Files with no reason to keep can be deleted or moved using --action=delete or --action=move, see --help")
        else:
            number_of_files_to_be_kept = 0
            number_of_files_to_be_deleted = 0
            for file, flags in file_flags_items:
                if flags:  # One or more reason to keep the file
                    number_of_files_to_be_kept += 1
                else:
                    number_of_files_to_be_deleted += 1
            print(f"Files to keep: {number_of_files_to_be_kept}")
            for file, flags in file_flags_items:
                print(file) if flags else None
            print(f"Files to move or delete: {number_of_files_to_be_deleted}")
            for file, flags in file_flags_items:
                print(file) if not flags else None

def move_files(file_flags, destination, verbose):
    if os.path.exists(destination):
        if not os.path.isdir(destination):
            print(f"Error: Destination '{destination}' is not a directory.")
            sys.exit(1)
    else:
        try:
            os.makedirs(destination)
        except OSError as e:
            print(f"Error creating destination directory: {e}")
            sys.exit(1)

    for file, flags in sorted(file_flags.items()):
        if not flags:  # No flags present for the file
            print(f"moving {file} to {destination}...") if verbose else None
            shutil.move(file, destination)
        else:
            print(f"keeping  {file}...") if verbose else None


def delete_files(file_flags, verbose):
    for file, flags in sorted(file_flags.items()):
        if not flags:  # No flags present for the file
            print(f"deleting {file}...") if verbose else None
            try:
                if os.path.isfile(file):
                    os.remove(file)
                elif os.path.isdir(file):
                    shutil.rmtree(file)
            except OSError as e:
                print(f"Error deleting file or directory '{file}': {e}")
        else:
            print(f"keeping  {file}...") if verbose else None

def parse_retention(retention_string): # example retention string: "keep-daily=5 keep-weekly keep-monthly=3"
    modes = retention_string.replace(",", " ").split() # replace comma in case of comma separated input like "keep-daily,keep-weekly", then split on space
    retention_dict = {}
    for mode in modes:
        parts = mode.replace(":", "=").split("=") # and make : same as =, then split on =
        if len(parts) == 1:
            count = 1  # Default count value
        else:
            try:
                count = int(parts[1])
            except ValueError as e:
                print(f"Error in retention input \"{parts[1]}\" in \"{parts}\"")
                sys.exit(1)
        if parts[0] in ['years', 'half-years', 'quarters', 'months', 'fortnights', 'weeks', 'days', 'hours', 'last']:
            retention_dict[parts[0]] = count
        elif parts[0] == ("all"):
            retention_dict = {}
            return retention_dict # override all other input
        else:
            print(f"Invalid retention format \"{mode}\"")
            sys.exit(1)
    return retention_dict # example return value: {'days': 5, 'weeks': 1, 'months': 3}

def main():
    parser = argparse.ArgumentParser(description="Backup retention script")
    parser.add_argument("directory", nargs="?", default=os.getcwd(), help="Directory to process. default=current. Will attempt to create directory if it doesn't exist")
    parser.add_argument("--action", choices=["list", "move", "delete"], default="list", help="Action to perform. default=list")
    parser.add_argument("--destination", help="Destination directory for move action")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output (list moved/deleted files. For list action, list reason to keep each file)")
    parser.add_argument("--retention", default="all", help="Retention mode. Specify the retention policy for file backups. The default value is 'all', which keeps all files. Other supported retention modes are 'last=N' (keep the last N files), 'hours=N' (keep the last file per hour for N hour), 'days=N' (keep the last file per day for N days), 'weeks', 'fortnights', 'monthls', 'quarters', 'half-years' and 'years' -- all of which can have =N added like in the first examples. If you for example have 10 files per day and specify 'days=2', then the latest file from the last two days will be kept. Multiple retention modes can be combined by separating them with spaces, e.g., 'last=3 days=7 months=6 years=5'. This will keep the last file of the year for 5 years, the last file of the month for 6 months, the last file of the day for 7 days and the last 3 files, regardless of date/time. Note that if there are no matching files in a specific month, for example, then that month will not be counted. For example if you specify 'months=6', and you have files in months 1-4 and 9-12', the file for moths 3,4,9,10,11,12 will be kept - a total of 6 months.")
    parser.add_argument("--format", default="{YYYY}{MM}{DD}T{hh}{mm}", help="File format. Specify the format for the file names or directory names to match. The default format is '{YYYY}{MM}{DD}T{hh}{mm}'. You can customize the format by using placeholders: {YYYY} for year, {MM} for month, {DD} for day, {hh} for hour, and {mm} for minute. You can use wildcards ? and *. For example, '{YYYY}-{MM}-{DD}' will match names such as '2023-05-20'. '?{YYYY}{MM}{DD}*' will match names like 'X20230520' or 'X20210101T0100'.")

    args = parser.parse_args()

    if args.action == "move":
        if not args.destination:
            parser.error("Destination directory required for move action")

    retention = parse_retention(args.retention)
    files = get_matching_files(args.directory, args.format)
    file_datetime_map = {}
    file_flags = {}

    for file in files:
        if len(retention) == 0:
            file_flags[file] = ["command line argument set to retain all files"]
        else:
            file_datetime = get_file_datetime(file, args.format)
            if file_datetime: # the datetime is valid
                if file_datetime > datetime.now(): # date/time is in the future
                    file_flags[file] = ["timestamp is in the future"]
                else:
                    file_datetime_map[file] = file_datetime
                    file_flags[file] = [] # empty means it will be deleted unless a reason to keep it is added later
            else:
                file_flags[file] = ["invalid timestamp"]
        
    # print("file_datetime_map:", file_datetime_map) # debug
        
    files_grouped_by_nothing    = {} # simple list of datetime, week_number, file
    files_grouped_by_hour       = {} # the key is Year, month, day, hour
    files_grouped_by_day        = {} # the key is Year, month, day
    files_grouped_by_week       = {} # the key is Year, week
    files_grouped_by_fortnight  = {} # the key is Year, fortnight
    files_grouped_by_month      = {} # the key is Year, month
    files_grouped_by_quarter    = {} # the key is Year, quarter
    files_grouped_by_half_year  = {} # the key is Year, half_year
    files_grouped_by_year       = {} # the key is Year

    # loop through files sorted by latest file first, ensuring the latest file(s) in each group is selected for retention
    for file, file_datetime in sorted(file_datetime_map.items(), key=lambda x: x[1], reverse=True):
        # group files, internally sorted by datetime, newest first, unlike file_datetime_map, which is random order

        # populate files_grouped_by_nothing - each file has its own group
        # if "last=3" is specified, the last 3 files will be in the first 3 groups
        files_grouped_by_nothing.setdefault(file, []).append(file)

        # populate files_grouped_by_hour
        hour_key = file_datetime.strftime("%Y-%m-%d %H")
        files_grouped_by_hour.setdefault(hour_key, []).append(file)

        # populate files_grouped_by_day
        day_key = file_datetime.strftime("%Y-%m-%d")
        files_grouped_by_day.setdefault(day_key, []).append(file)

        # populate files_grouped_by_week # ISO week, where the first week of the year is the week that contains at least four days of the new year.
        week_key = file_datetime.strftime("%G-W%V")
        files_grouped_by_week.setdefault(week_key, []).append(file)
        
        # populate files_grouped_by_fortnight
        iso_year, iso_week, _ = file_datetime.isocalendar()
        fortnight = math.ceil(iso_week / 2)
        fortnight_key = f"{iso_year}-F{fortnight}"
        files_grouped_by_fortnight.setdefault(fortnight_key, []).append(file)

        # populate files_grouped_by_month
        month_key = file_datetime.strftime("%Y-%m")
        files_grouped_by_month.setdefault(month_key, []).append(file)

        # populate files_grouped_by_quarter
        quarter = math.ceil(file_datetime.month / 3)
        quarter_key = file_datetime.strftime(f"%Y-Q{quarter}")
        files_grouped_by_quarter.setdefault(quarter_key, []).append(file)

        # populate files_grouped_by_half_year
        half_year = math.ceil(file_datetime.month / 6)
        half_year_key = file_datetime.strftime(f"%Y-H{half_year}")
        files_grouped_by_half_year.setdefault(half_year_key, []).append(file)

        # populate files_grouped_by_year
        year_key = file_datetime.strftime("%Y")
        files_grouped_by_year.setdefault(year_key, []).append(file)
        
    time_units_and_files = [
        ['last',        files_grouped_by_nothing,   "entry {i}/{j}"          ],
        ['hours',       files_grouped_by_hour,      "hour {i}/{j} ({t})"      ],
        ['days',        files_grouped_by_day,       "day {i}/{j} ({t})"       ],
        ['weeks',       files_grouped_by_week,      "week {i}/{j} ({t})"      ],
        ['fortnights',  files_grouped_by_week,      "fortnight {i}/{j} ({t})" ],
        ['months',      files_grouped_by_month,     "month {i}/{j} ({t})"     ],
        ['quarters',    files_grouped_by_quarter,   "quarter {i}/{j} ({t})"   ],
        ['half_years',  files_grouped_by_half_year, "half-year {i}/{j} ({t})" ],
        ['years',       files_grouped_by_year,      "year {i}/{j} ({t})"      ]]

    # Create a list of the time units above that are also present as keys in the retention dictionary
    # example of contents of retention: {'last': (3,1), 'months': (2,1), 'years': (5,1), 'weeks': (1,2), 'days': (1,3)}
    time_units = [time_unit for time_unit, _, _ in time_units_and_files if time_unit in retention]
    
    # Create a list of only the grouped files for easy access (used to get next time unit's files)
    grouped_files_by_time_unit = {unit: files for unit, files, _ in time_units_and_files}
    
    for time_unit, grouped_files, status_template in time_units_and_files:
        if time_unit in retention:
            retention_count = original_retention_count = retention[time_unit] # number of days/weeks/etc. to retain files
            # print(time_unit, retention_count, len(grouped_files)) # debug
            for group, files in grouped_files.items():
                if retention_count < 1:
                    break # no more files are to be retained for this group, so no need to continue processing
                status_msg = status_template.format(i=original_retention_count-retention_count+1, j=original_retention_count, t=group)
                file_flags[files[0]].append(status_msg) # append the status to the first file in the group (the one with the latest time)
                retention_count -= 1
                # print(f"appended status {status} to {file}") # debug
                
    if args.action=="list":
        list_files(file_flags, args.verbose)
    elif args.action=="delete":
        delete_files(file_flags, args.verbose)
    elif args.action=="move":
        move_files(file_flags, args.destination, args.verbose)


if __name__ == "__main__":
    main()
