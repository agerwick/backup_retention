import os
import sys
import argparse
import math
from datetime import datetime
from glob import glob
import re
import shutil

def get_matching_files(directory, file_format):
    """
    Retrieve a list of files in the specified directory that match the given file format.

    Args:
        directory (str): The directory path where the files will be searched.
        file_format (str): The file format pattern to match. Use "{YYYY}" for year,
            "{MM}" for month, "{DD}" for day, "{hh}" for hour, and "{mm}" for minute.
            Any of these placeholders will be replaced with "*" in the file pattern.
            Literal characters as well as wildcards * and ? may of course also be added.

    Returns:
        list: A list of file paths that match the specified file format.

    Example:
        directory = "/path/to/files"
        file_format = "data_{YYYY}{MM}{DD}.txt"
        matching_files = get_matching_files(directory, file_format)
        # Returns a list of files in the directory that match the format "data_YYYYMMDD.txt".

    Note:
        - The file format should follow the specified placeholders for year, month, day, hour, and minute.
        - Any other parts of the file format will be treated as literal characters.
        - The function uses the `glob` module to find files based on the generated file pattern.

    """
    file_pattern = file_format.replace("{YYYY}", "*").replace("{MM}", "*").replace("{DD}", "*").replace("{hh}", "*").replace("{mm}", "*")
    files = glob(os.path.join(directory, file_pattern))
    return files

def generate_regex_pattern(file_format):
    """
    Generates a regular expression pattern based on the given file format.

    Args:
        file_format (str): The file format string containing wildcards and placeholders.

    Returns:
        str: The generated regular expression pattern.

    The function replaces specific characters and placeholders in the file format with
    corresponding regular expression patterns. It converts "?" to a regex pattern matching
    any single character, "*" to a regex pattern matching zero or more characters, and
    "{YYYY}", "{MM}", "{DD}", "{hh}", "{mm}" to corresponding regex patterns for year,
    month, day, hour, and minute respectively. The resulting pattern is anchored at the
    start and end to match the entire file name.

    Examples:
        file_format = "file_*.txt"
        regex_pattern = generate_regex_pattern(file_format)
        # regex_pattern = r"^file_\w*\.txt$"
        
        file_format = '{YYYY}{MM}{DD}T{hh}{mm}'
        regex_pattern = generate_regex_pattern(file_format)
        # regex_pattern = '^(?P<YYYY>\\d{4})(?P<MM>\\d{2})(?P<DD>\\d{2})T(?P<hh>\\d{2})(?P<mm>\\d{2})$'

    """
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
    """
    Extracts the datetime from a file name based on the specified file format.

    Args:
        file_path (str): The path of the file.
        file_format (str): The file format string containing placeholders for datetime elements.

    Returns:
        datetime or None: The datetime extracted from the file name, or None if extraction failed.

    The function uses a regular expression pattern generated from the provided file format
    to match and extract the datetime elements from the file name. It attempts to extract
    the year, month, day, hour, and minute from the matched groups and creates a datetime object.
    If any extraction or conversion to integers fails, it returns None.

    Example:
        file_path = "/path/to/file_20220523T0830.txt"
        file_format = "file_{YYYY}{MM}{DD}T{hh}{mm}.txt"
        file_datetime = get_file_datetime(file_path, file_format)
        # file_datetime = datetime.datetime(2022, 5, 23, 8, 30)
    """
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
    """
    Prints files indicating which would be retained if a different action is chosen.

    Args:
        file_flags (dict): A dictionary containing file paths as keys and their corresponding retention flags as values.
        verbose (bool): If True, provides detailed information for each file. If False, summarizes the number of files to be kept and deleted.

    If no files are found matching the specified file format, a message is printed. Otherwise,
    if 'verbose' is True, each file is listed with the reasons to keep it. Files with no reason to keep
    can be deleted or moved using '--action=delete' or '--action=move'. If 'verbose' is False,
    a summary is printed with the number of files to be kept and deleted.

    Example:
        file_flags = {
            'file1.txt': ['Reason1', 'Reason2'],
            'file2.txt': [],
            'file3.txt': ['Reason1']
        }
        list_files(file_flags, True)
        # Output:
        # file1.txt - Reasons to keep: Reason1, Reason2
        # file2.txt - No reason to keep
        # file3.txt - Reasons to keep: Reason1
        # Files with no reason to keep can be deleted or moved using --action=delete or --action=move, see --help

    """
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
    """
    Moves files not to be retained to a different directory.

    Args:
        file_flags (dict): A dictionary containing file paths as keys and their corresponding retention flags as values.
        destination (str): The destination directory where the files will be moved.
        verbose (bool): If True, provides detailed information about each file move.

    If the destination directory exists, files not to be retained are moved to that directory.
    If the destination directory does not exist, it is created. If any errors occur during the move operation,
    an error message is printed.

    Example:
        file_flags = {
            'file1.txt': ['Reason1', 'Reason2'],
            'file2.txt': [],
            'file3.txt': ['Reason1']
        }
        destination = '/path/to/destination'
        move_files(file_flags, destination, True)
        # Output:
        # moving file2.txt to /path/to/destination...
        # Files not to be retained have been moved to the destination directory.

    """
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
            print(f"moving {file} to {destination}...", flush=True) if verbose else None
            shutil.move(file, destination)
        else:
            flags_str = ", ".join(flags)
            print(f"keeping  {file} -- {flags_str}") if verbose else None


def delete_files(file_flags, verbose):
    """
    Deletes files not to be retained.

    Args:
        file_flags (dict): A dictionary containing file paths as keys and their corresponding retention flags as values.
        verbose (bool): If True, provides detailed information about each file deletion.

    Files not to be retained are deleted from the file system. If any errors occur during the deletion process,
    an error message is printed.

    Example:
        file_flags = {
            'file1.txt': ['Reason1', 'Reason2'],
            'file2.txt': [],
            'file3.txt': ['Reason1']
        }
        delete_files(file_flags, True)
        # Output:
        # deleting file2.txt...
        # Files not to be retained have been deleted.

    """
    for file, flags in sorted(file_flags.items()):
        if not flags:  # No flags present for the file
            print(f"deleting {file}...", flush=True) if verbose else None
            try:
                if os.path.isfile(file):
                    os.remove(file)
                elif os.path.isdir(file):
                    shutil.rmtree(file)
            except OSError as e:
                print(f"Error deleting file or directory '{file}': {e}")
        else:
            flags_str = ", ".join(flags)
            print(f"keeping  {file} -- {flags_str}") if verbose else None

def parse_retention(retention_string):
    """
    Parses the retention string and returns a dictionary representing the retention configuration.

    Args:
        retention_string (str): A string specifying the retention configuration in the format "mode=count".
            Modes can include 'years', 'half-years', 'quarters', 'months', 'fortnights', 'weeks', 'days', 'hours', 'latest'.
            The count value represents the number of units to retain.

    Returns:
        dict: A dictionary representing the retention configuration, where keys are the modes and values are the corresponding counts.

    If the retention string is invalid or contains errors, appropriate error messages are printed and the program exits.

    Example:
        retention_string = "days=5 weeks months=3"
        retention_config = parse_retention(retention_string)
        # Output:
        # {'days': 5, 'weeks': 1, 'months': 3}

    """
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
        if parts[0] in ['years', 'half-years', 'quarters', 'months', 'fortnights', 'weeks', 'days', 'hours', 'latest']:
            retention_dict[parts[0]] = count
        elif parts[0] == ("all"):
            retention_dict = {'all': '*'}
            return retention_dict # override all other input
        else:
            print(f"Invalid retention format \"{mode}\"")
            sys.exit(1)
    if len(modes) == 0:
        retention_dict = {'all', '*'}
    return retention_dict

def main():
    parser = argparse.ArgumentParser(description="Backup retention script")
    parser.add_argument("directory", nargs="?", default=os.getcwd(), help="Directory to process. default=current. Will attempt to create directory if it doesn't exist")
    parser.add_argument("--action", choices=["list", "move", "delete"], default="list", help="Action to perform. default=list")
    parser.add_argument("--destination", help="Destination directory for move action")
    parser.add_argument("--format", default="{YYYY}{MM}{DD}T{hh}{mm}", help="File format. Specify the format for the file names or directory names to match. The default format is '{YYYY}{MM}{DD}T{hh}{mm}'. You can customize the format by using placeholders: {YYYY} for year, {MM} for month, {DD} for day, {hh} for hour, and {mm} for minute. You can use wildcards ? and *. For example, '{YYYY}-{MM}-{DD}' will match names such as '2023-05-20'. '?{YYYY}{MM}{DD}*' will match names like 'X20230520' or 'X20210101T0100'.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output (list moved/deleted files. For list action, list reason to keep each file)")
    parser.add_argument("--retention", default="all", help="Retention mode. Specify the retention policy for backup files/directories. The default value is 'all', which keeps all files. Other supported retention modes are latest, hours, days, weeks, fortnights, months, quarters, half-years and years. Add =N after the mode to specify the number of files to be retained. Defaults to 1 if not specified. Multiple retention modes can be combined by separated by spaces.")
    parser.add_argument("--help_retention", action="store_true", help="display more detailed help on the retention argument")
    parser.add_argument("--method", default="progressive", choices=["progressive", "cumulative"], help="Progressive retention retains files based on specific time intervals, starting from the most recent and extending to older files. Cumulative retention accumulates retention criteria over time, gradually expanding the range of files to be retained based on increasing time intervals.")
    parser.add_argument("--help_method", action="store_true", help="display more detailed help on the method argument")

    args = parser.parse_args()

    quit_now = False
    if args.help_retention:
        print("""
Retention mode
--------------
latest=N     - N is the number of consequtive file(s) with the latest timestamp that you want to retain
hours=N      - N is the number of hours from which you want to retain the latest file.
days=N       - N is the number of days from which you want to retain the latest file.
weeks=N      - N is the number of weeks from which you want to retain the latest file.
fortnights=N - N is the number of fortnights (14 days) from which you want to retain the latest file.
months=N     - N is the number of months from which you want to retain the latest file.
quarters=N   - N is the number of quarters (3 momths) from which you want to retain the latest file.
half-years=N - N is the number of helf-years (6 months) from which you want to retain the latest file.
years=N      - N is the number of years from which you want to retain the latest file.

Leaving out the "=N" part is equal to "=1".
Only files that match file format *exactly* will be processed, all other files in the same directory will be retained (not deleted). If you use the default format of "{YYYY}{MM}{DD}T{hh}{mm}", for example, the file "20230517T0900" will match and be processed to see if it should be retained or not, but "20230517T090000" (with seconds), "20230517T0900.ext" (extra characters) or "202302307T0900" (invalid date) will not match. Such files will be ignored, and will thus be retained.
Any files with a timestamp in the future will also be ignored, and thus retained.

Examples:
'latest=7': keep the latest 7 files
'hours=18': keep the last file per hour for 18 hours
'years': keep the last file of the year (same as 'years=1')
'last=3 days=7 months=6 years=5'. This will keep the last file of the year for 5 years, the last file of the month for 6 months, the last file of the day for 7 days and the last 3 files, regardless of date/time -- unless you specify comulative retension (see --help-method).
Note that if there are no matching files in a specific time period - let's use month, for example, then that month will not be counted. For example if you specify 'months=6', and you have files in months 1-4 and 9-12', but none for months 5-8, the file for months 3,4,9,10,11,12 will be retained - a total of 6 months.""")
        quit_now = True

    if args.help_method:
        print("""
Examples of progressive and cumulative retention
------------------------------------------------
Progressive Retention (default)
python backup_retention.py /home/me/my_backups --retention "latest=3 days=7 weeks=6 months=12 quarters=12 years=10" --verbose --action=list
this results in the following being retained:
- the latest 3 files, regardless of timestamp
- the latest file for the first 7 days
- the latest file for the first 6 weeks (the first week, all files will be retained becuase of days=7, then the next 5 weeks only the latest per week)
- the latest file for the first 12 months (as the first 6 weeks are saved anyway, 10-11 additional files will be retained the first year)
- the latest file for the first 12 quarters (after the first 12 months (4 quarters), an additonal 8 quarters will be retained)
- the latest file for the first 10 years (the first 3 years are already covered by quarters=12. For the remaining 7 years, only one file per year is retained)
- files older than 10 years, and those not covered by the above statements will be listed, moved or deleted, depending on your action.

Cumulative Retention (add --method=cumulative to enable)
python backup_retention.py /home/me/my_backups --retention "latest=3 days=7 weeks=6 months=12 quarters=8 years=5" --verbose --action=list --method=cumulative
this results in the following being retained:
- the latest 3 files, regardless of timestamp
- the latest file for the first 7 days
- the latest file for the first 6 weeks (starting after the first 7 days, the latest file in next 6 weeks will be retained)
- the latest file for the first 12 months (starting after the first 6 weeks+7 days, the latest file in next 12 months will be retained)
- the latest file for the first 8 quarters (starting after the first 12 months+6 weeks+7 days, the latest file in next 8 quarters (two years) will be retained)
- the latest file for the first 10 years (starting after the first 8 quarters+12 months+6 weeks+7 days, the latest file in next 10 years will be retained)
- files older than that, and those not covered by the above statements will be listed, moved or deleted, depending on your action.""")
        quit_now = True

    if quit_now:
        sys.exit(0)

    if args.action == "move":
        if not args.destination:
            parser.error("Destination directory required for move action")

    retention = parse_retention(args.retention)

    if args.verbose:
        print("Backup retention arguments:")
        print(f"  directory: {args.directory}")
        print(f"  action: {args.action}")
        print(f"  destination: {args.destination}") if args.destination else None
        print(f"  format: {args.format}")
        print("  retention:")
        for mode, quantity in retention.items():
            print(f"    - {mode}: {quantity}")
        print(f"  method: {args.method}")
        print("", flush=True)

    files = get_matching_files(args.directory, args.format)
    file_datetime_map = {}
    file_flags = {}

    for file in files:
        if "all" in retention or len(retention) == 0: # len(retention) == 0 should never occur, but better safe than sorry...
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
        ['latest',      files_grouped_by_nothing,   "latest {i}/{j}"          ],
        ['hours',       files_grouped_by_hour,      "hour {i}/{j} ({t})"      ],
        ['days',        files_grouped_by_day,       "day {i}/{j} ({t})"       ],
        ['weeks',       files_grouped_by_week,      "week {i}/{j} ({t})"      ],
        ['fortnights',  files_grouped_by_fortnight, "fortnight {i}/{j} ({t})" ],
        ['months',      files_grouped_by_month,     "month {i}/{j} ({t})"     ],
        ['quarters',    files_grouped_by_quarter,   "quarter {i}/{j} ({t})"   ],
        ['half_years',  files_grouped_by_half_year, "half-year {i}/{j} ({t})" ],
        ['years',       files_grouped_by_year,      "year {i}/{j} ({t})"      ]]

    # Create a list of the time units above that are also present as keys in the retention dictionary
    # example of contents of retention: {'last': (3,1), 'months': (2,1), 'years': (5,1), 'weeks': (1,2), 'days': (1,3)}
    time_units = [time_unit for time_unit, _, _ in time_units_and_files if time_unit in retention]
    
    # Create a list of only the grouped files for easy access (used to get next time unit's files)
    grouped_files_by_time_unit = {unit: files for unit, files, _ in time_units_and_files}
    
    last_file_in_previous_group = None # if cumulative retention is used, the last file in the former group is stored here
    last_group = None
    for time_unit, grouped_files, status_template in time_units_and_files:
        if time_unit in retention: # if user has chosen to retain files based on this time unit
            retention_count = original_retention_count = retention[time_unit]
            if grouped_files.keys():
                last_group = list(grouped_files.keys())[-1]  # Get the last group from the dictionary keys
            group_has_been_iterated_through_at_least_once = False
            for group, files in grouped_files.items(): # iterate through groups with files within that group
                # examples of groups: "2017-W41" for week, "2023-10" for month, "20230517" for day, ...
                if last_file_in_previous_group: # if we're using cumulative retention and the previous time unit is done
                    # check if we've reached the group that the last file in the previous time unit was in
                    if last_file_in_previous_group in files: 
                        last_file_in_previous_group = None # reset this so we won't go into this code block on the next iteration
                    # then just skip to next iteration if we haven't found the file, and if we just found it
                    continue
                group_has_been_iterated_through_at_least_once = True
                current_file = files[0]

                if retention_count > 0: # we still have files left in the given retention count, so we'll add it to the file_flags
                    status_msg = status_template.format(i=original_retention_count-retention_count+1, j=original_retention_count, t=group)
                    file_flags[current_file].append(status_msg)
                    retention_count -= 1
            
                if (retention_count < 1 # no more files from this group to be added
                or group == last_group): # ran out of files (retention_count still not 0 even at the last group
                    if args.method == "cumulative":
                        last_file_in_previous_group = current_file # where to start processing when iterating over the next time_unit
                    break # no point continuing with further groups in this time_unit if we've already used all of retention_count
            if args.method == "cumulative" and not group_has_been_iterated_through_at_least_once: 
                break # if you run out of files in, say, months, then there's no point processing any subsequent group (like year)
                # this is important, otherwise the next group will get last_file_in_previous_group = None which means it'll start iterating from the first file

    if args.action=="list":
        list_files(file_flags, args.verbose)
    elif args.action=="delete":
        delete_files(file_flags, args.verbose)
    elif args.action=="move":
        move_files(file_flags, args.destination, args.verbose)


if __name__ == "__main__":
    main()
