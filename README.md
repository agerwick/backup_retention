backup_retention
================
backup_retention is a script to move/delete old backups, while keeping some selected ones.
It is highly configurable and can work with files or directories of any time and date format (except am/pm - who uses that on file names anyway?).

Example usage
-------------
python backup_retention.py /home/me/my_backups --retention "keep-last=3 keep-daily=1 keep-weekly=1 keep-monthly=1 keep-yearly=1" --verbose --action=list

You can experiment with the input parameters until you find something that works for you, then change --action=list to --action=delete or --action-move destination=/my_other_backup_space

The default action is list, to prevent accidental deletion.

To get a complete list of input parameters, use --help

usage: backup_retention.py [-h] [--action {list,move,delete}]
                           [--destination DESTINATION] [--verbose]
                           [--retention RETENTION] [--format FORMAT]
                           [directory]

Backup retention script

positional arguments:
  directory             Directory to process. default=current.
                        Will attempt to create directory if it doesn't exist

optional arguments:
  -h, --help            show this help message and exit
  --action {list,move,delete}
                        Action to perform
  --destination DESTINATION
                        Destination directory for move action
  --verbose             Enable verbose output (list moved/deleted files. For
                        list action, list reason to keep each file)
  --retention RETENTION
                        Retention mode. Specify the retention policy for file
                        backups. The default value is 'keep-all', which keeps
                        all files. Other supported retention modes include
                        'keep-last=N' (keep the last N files), 'keep-yearly=N'
                        (keep N files per year), 'keep-monthly=N' (keep N
                        files per month), 'keep-weekly=N' (keep N files per
                        week), 'keep-daily=N' (keep N files per day), and
                        'keep-hourly=N' (keep N files per hour). If you have
                        10 files per day and specify 'keep-daily=2', then the
                        last (newest) two files per day will be kept. Multiple
                        retention modes can be combined by separating them
                        with spaces, e.g., 'keep-last=3 keep-daily=1 keep-
                        monthly=1 keep-yearly=1'. Each time unit will be kept
                        until the start of the next time unit. For example, 1
                        daily file will be kept this month, but not next. If
                        keep-weekly is specified, 1 daily file will only be
                        kept this week. keep-last overrides everything, but
                        after the specified number of files, the rest of the
                        rules apply.
  --format FORMAT       File format. Specify the format for the file names or
                        directory names to match. The default format is
                        '{YYYY}{MM}{DD}T{hh}{mm}'. You can customize the
                        format by using placeholders: {YYYY} for year, {MM}
                        for month, {DD} for day, {hh} for hour, and {mm} for
                        minute. You can use wildcards ? and *. For example,
                        '{YYYY}-{MM}-{DD}' represents a format like
                        '2023-05-20'. '?{YYYY}{MM}{DD}*' represents a format
                        like 'X20230520' or 'X20210101T0100'.
