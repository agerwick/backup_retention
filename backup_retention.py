import os
import argparse
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
                os.remove(file)
            except OSError as e:
                print(f"Error deleting file '{file}': {e}")
        else:
            print(f"keeping  {file}...") if verbose else None

def parse_retention(retention):
    modes = retention.split()
    retention_dict = {}
    for mode in modes:
        if mode.startswith("keep-all"):
            retention_dict = {}
        elif mode.startswith("keep-last"):
            count = int(mode.split("=")[-1])
            retention_dict['last'] = count
        elif mode.startswith("keep-yearly"):
            count = int(mode.split("=")[-1])
            retention_dict['years'] = count
        elif mode.startswith("keep-monthly"):
            count = int(mode.split("=")[-1])
            retention_dict['months'] = count
        elif mode.startswith("keep-weekly"):
            count = int(mode.split("=")[-1])
            retention_dict['weeks'] = count
        elif mode.startswith("keep-daily"):
            count = int(mode.split("=")[-1])
            retention_dict['days'] = count
        elif mode.startswith("keep-hourly"):
            count = int(mode.split("=")[-1])
            retention_dict['hours'] = count
        else:
            raise ValueError(f"Invalid retention format \"{mode}\"")
    return retention_dict

def get_next_time_unit(time_units, current_time_unit):
    """
    Get the next time unit from the given list, excluding the time 
    unit 'last'.

    Args:
        time_units (list): List of time units.
        current_time_unit (str): Current time unit.

    Returns:
        str or None: The next time unit if it exists, otherwise None.

    """
    index = time_units.index(current_time_unit)
    if current_time_unit == 'last' or index == len(time_units) - 1:
        return None
    return time_units[index + 1]

def get_group_number(grouped_files, file):
    """
    Get the group number based on the file's presence in the corresponding group.

    Args:
        grouped_files (dict): Dictionary containing grouped files for a single time unit.
        file (str): The file to search for.

    Returns:
        int: The group number where the file is found, or 0 if not found.
    """
    if grouped_files:
        for group_number, files in enumerate(grouped_files.values(), start=1):
            if file in files:
                return group_number
    return 0

def main():
    parser = argparse.ArgumentParser(description="Backup retention script")
    parser.add_argument("directory", nargs="?", default=os.getcwd(), help="Directory to process. default=current. Will attempt to create directory if it doesn't exist")
    parser.add_argument("--action", choices=["list", "move", "delete"], default="list", help="Action to perform. default=list")
    parser.add_argument("--destination", help="Destination directory for move action")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output (list moved/deleted files. For list action, list reason to keep each file)")
    parser.add_argument("--retention", default="keep-all", help="Retention mode. Specify the retention policy for file backups. The default value is 'keep-all', which keeps all files. Other supported retention modes include 'keep-last=N' (keep the last N files), 'keep-yearly=N' (keep N files per year), 'keep-monthly=N' (keep N files per month), 'keep-weekly=N' (keep N files per week), 'keep-daily=N' (keep N files per day), and 'keep-hourly=N' (keep N files per hour). If you have 10 files per day and specify 'keep-daily=2', then the last (newest) two files per day will be kept. Multiple retention modes can be combined by separating them with spaces, e.g., 'keep-last=3 keep-daily=1 keep-monthly=1 keep-yearly=1'. Each time unit will be kept until the start of the next time unit. For example, 1 daily file will be kept this month, but not next. If keep-weekly is specified, 1 daily file will only be kept this week. keep-last overrides everything, but after the specified number of files, the rest of the rules apply.")
    parser.add_argument("--format", default="{YYYY}{MM}{DD}T{hh}{mm}", help="File format. Specify the format for the file names or directory names to match. The default format is '{YYYY}{MM}{DD}T{hh}{mm}'. You can customize the format by using placeholders: {YYYY} for year, {MM} for month, {DD} for day, {hh} for hour, and {mm} for minute. You can use wildcards ? and *. For example, '{YYYY}-{MM}-{DD}' represents a format like '2023-05-20'. '?{YYYY}{MM}{DD}*' represents a format like 'X20230520' or 'X20210101T0100'.")

    args = parser.parse_args()

    if args.action == "move":
        if not args.destination:
            parser.error("Destination directory required for move action")

    retention = parse_retention(args.retention)
    # get files matching the format
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
                    file_flags[file] = ["future datetime"]
                else:
                    file_datetime_map[file] = file_datetime
                    file_flags[file] = [] # empty means it will be deleted unless a reason to keep it is added later
            else:
                file_flags[file] = ["invalid datetime"]
        
    # print("file_datetime_map:", file_datetime_map) # debug
        
    files_grouped_by_nothing = {} # simple list of datetime, week_number, file
    files_grouped_by_hour    = {} # the key is Year, month, day, hour
    files_grouped_by_day     = {} # the key is Year, month, day
    files_grouped_by_week    = {} # the key is Year, week
    files_grouped_by_month   = {} # the key is Year, month
    files_grouped_by_year    = {} # the key is Year

    # loop through files sorted by latest file first, ensuring the latest file(s) in each group is selected for retention
    for file, file_datetime in sorted(file_datetime_map.items(), key=lambda x: x[1], reverse=True):
        # populate files_grouped_by_nothing, but sorted by datetime, newest first, unlike file_datetime_map, which is random order
        #files_grouped_by_nothing.append(file)
        files_grouped_by_nothing.setdefault("last", []).append(file)

        # populate files_grouped_by_hour
        hour_key = file_datetime.strftime("%Y-%m-%d %H")
        files_grouped_by_hour.setdefault(hour_key, []).append(file)

        # populate files_grouped_by_day
        day_key = file_datetime.strftime("%Y-%m-%d")
        files_grouped_by_day.setdefault(day_key, []).append(file)

        # populate files_grouped_by_week
        week_key = file_datetime.strftime("%Yw%W")
        files_grouped_by_week.setdefault(week_key, []).append(file)

        # populate files_grouped_by_month
        month_key = file_datetime.strftime("%Y-%m")
        files_grouped_by_month.setdefault(month_key, []).append(file)

        # populate files_grouped_by_year
        year_key = file_datetime.strftime("%Y")
        files_grouped_by_year.setdefault(year_key, []).append(file)
        
    time_units_and_files = [
        ['last',   files_grouped_by_nothing, "last {i}"             ],
        ['hours',  files_grouped_by_hour,    "last {i} in hour {t}" ],
        ['days',   files_grouped_by_day,     "last {i} in day {t}"  ],
        ['weeks',  files_grouped_by_week,    "last {i} in week {t}" ],
        ['months', files_grouped_by_month,   "last {i} in month {t}"],
        ['years',  files_grouped_by_year,    "last {i} in year {t}" ]]

    # Create a list of the time units above that are also present as keys in the retention dictionary
    # example of contents of retention: {'last': 3, 'months': 2, 'years': 5, 'weeks': 1, 'days': 1}
    time_units = [time_unit for time_unit, _, _ in time_units_and_files if time_unit in retention]
    
    # Create a list of only the grouped files for easy access (used to get next time unit's files)
    grouped_files_by_time_unit = {unit: files for unit, files, _ in time_units_and_files}
    
    for time_unit, grouped_files, status_template in time_units_and_files:
        if time_unit in retention:
            retention_count = retention[time_unit] # number of files to retain

            next_time_unit = get_next_time_unit(time_units, time_unit)
            # next_time_unit is used to find out when to stop applying the keep flag. For example:
            # retention={'last': 3, 'months': 2, 'years': 5, 'weeks': 1, 'days': 1}, which makes:
            # time_unit=['last', 'days', 'weeks', 'months', 'years']
            # time_unit="days"
            # next_time_unit will be "weeks"
            # it will then keep the last file for each day until next week, then the weekly rule will apply until next month, etc.
            # If time_unit is "last" or the last entry (here: "years") it will return None.
            
            # print(time_unit, retention_count, next_time_unit, len(grouped_files)) # debug
            
            for group, files in grouped_files.items():
                status = status_template.format(i=retention_count, t=group)

                #print(f"Number of groups in {time_unit}: {len(grouped_files)} / files in group: {len(files)} / retention_count: {retention_count}, status: {status}") # debug
                for file_number_in_group in range(min(retention_count, len(files))):
                    file = files[file_number_in_group]
                    # find out which group number in the next time unit this file belongs in
                    # if it's the first, then apply the flag, otherwise do nothing.
                    # This ensures that you only keep the files that match for month (for exampe, the last file)
                    # for one year (if year is specified, otherwise forever). 
                    # After that, when the file is in group 2 for the next next time unit, rules for that time unit will apply
                    # get_group_number returns 0 if there's no next time unit
                    group_number_for_next_time_unit = get_group_number(grouped_files_by_time_unit.get(next_time_unit), file)
                    # print(file, group_number_for_next_time_unit) # debug
                    if group_number_for_next_time_unit <= 1:
                        file_flags[file].append(status)
                        #print(f"appended status {status}") # debug

    if args.action=="list":
        list_files(file_flags, args.verbose)
    elif args.action=="delete":
        delete_files(file_flags, args.verbose)
    elif args.action=="move":
        move_files(file_flags, args.destination, args.verbose)


if __name__ == "__main__":
    main()
